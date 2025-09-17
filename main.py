from machine import Pin, PWM, ADC
import time

# --- PINES ---
motor_izquierdo_adelante = PWM(Pin(7))
motor_izquierdo_atras = PWM(Pin(8))
motor_derecho_adelante = PWM(Pin(5))
motor_derecho_atras = PWM(Pin(6))

sensor_frontal_derecho_pin = ADC(Pin(0))
sensor_frontal_izquierdo_pin = ADC(Pin(1))

# --- CONFIGURACIÓN ADC y PWM ---
sensor_frontal_derecho_pin.atten(ADC.ATTN_11DB)
sensor_frontal_izquierdo_pin.atten(ADC.ATTN_11DB)

frecuencia_pwm = 1000
for motor in [motor_izquierdo_adelante, motor_izquierdo_atras, motor_derecho_adelante, motor_derecho_atras]:
    motor.freq(frecuencia_pwm)

# --- CONSTANTES DE CALIBRACIÓN SHARP ---
MIN_DISTANCIA_SHARP = 5.0
MAX_DISTANCIA_SHARP = 80.0
ADC_REFERENCIA_VOLTAJE = 3.3
ADC_RESOLUCION = 4095.0
VOLT_UMBRAL_BAJO = 0.4

# --- CONVERSIÓN PWM ---
def pwm255_to_duty16(valor):
    return int(round(max(0, min(valor, 255)) * 65535 / 255))

# --- FUNCIONES DE CONTROL DE MOTORES ---
def motor_adelante(velocidad_izq, velocidad_der):
    motor_izquierdo_adelante.duty_u16(pwm255_to_duty16(velocidad_izq))
    motor_izquierdo_atras.duty_u16(0)
    motor_derecho_adelante.duty_u16(pwm255_to_duty16(velocidad_der))
    motor_derecho_atras.duty_u16(0)

def motor_atras(velocidad_izq, velocidad_der):
    motor_izquierdo_adelante.duty_u16(0)
    motor_izquierdo_atras.duty_u16(pwm255_to_duty16(velocidad_izq))
    motor_derecho_adelante.duty_u16(0)
    motor_derecho_atras.duty_u16(pwm255_to_duty16(velocidad_der))

def motor_izquierda(velocidad):
    motor_izquierdo_adelante.duty_u16(0)
    motor_izquierdo_atras.duty_u16(pwm255_to_duty16(velocidad))
    motor_derecho_adelante.duty_u16(pwm255_to_duty16(velocidad))
    motor_derecho_atras.duty_u16(0)

def motor_derecha(velocidad):
    motor_izquierdo_adelante.duty_u16(pwm255_to_duty16(velocidad))
    motor_izquierdo_atras.duty_u16(0)
    motor_derecho_adelante.duty_u16(0)
    motor_derecho_atras.duty_u16(pwm255_to_duty16(velocidad))

def motor_detener():
    motor_izquierdo_adelante.duty_u16(0)
    motor_izquierdo_atras.duty_u16(0)
    motor_derecho_adelante.duty_u16(0)
    motor_derecho_atras.duty_u16(0)

# --- LECTURA DE SENSORES SHARP OPTIMIZADA ---
def leer_distancia_sharp(sensor_pin):
    try:
        raw_value = sensor_pin.read()
        volt = raw_value * (ADC_REFERENCIA_VOLTAJE / ADC_RESOLUCION)
        if volt <= VOLT_UMBRAL_BAJO:
            return MIN_DISTANCIA_SHARP
        distancia_calculada = 29.988 * pow(volt, -1.173)
        return max(MIN_DISTANCIA_SHARP, min(distancia_calculada, MAX_DISTANCIA_SHARP))
    except Exception:
        return MAX_DISTANCIA_SHARP

# --- VARIABLES PARA FILTRADO DE CAMBIOS PEQUEÑOS ---
ULTIMA_IZQ = None
ULTIMA_DER = None
UMBRAL_CAMBIO_CM = 3.0  # Ignorar variaciones menores a esto

def filtrar_distancia(valor_actual, ultimo_valor):
    if ultimo_valor is None:
        return valor_actual
    if abs(valor_actual - ultimo_valor) < UMBRAL_CAMBIO_CM:
        return ultimo_valor
    return valor_actual

# --- FUNCIONES DIFUSAS (SUAVES Y ESCALADAS A 180) ---
def trapmf(x, a, b, c, d):
    if x <= a or x >= d:
        return 0.0
    elif b <= x <= c:
        return 1.0
    elif a < x < b:
        return (x - a) / (b - a)
    elif c < x < d:
        return (d - x) / (d - c)
    return 0.0

def evaluar_sugeno(sensor_izq, sensor_der):
    s_izq = min(max(sensor_izq, 0), 100)
    s_der = min(max(sensor_der, 0), 100)

    CERCA = lambda x: trapmf(x, 0, 0, 25, 50)
    LEJOS = lambda x: trapmf(x, 20, 40, 65, 80)
    NO_D  = lambda x: trapmf(x, 60, 75, 100, 100)

    mf_izq = [CERCA(s_izq), LEJOS(s_izq), NO_D(s_izq)]
    mf_der = [CERCA(s_der), LEJOS(s_der), NO_D(s_der)]

    ALTO = 180
    NORMAL = int(200 * 180 / 255)  # ≈141
    BAJO = 0
    REVERSA = -180  # Ignorado en salida (porque no usamos reversa real aún)

    reglas = [
        (mf_izq[0] * mf_der[0], ALTO, ALTO),
        (mf_izq[0] * mf_der[1], ALTO, NORMAL),
        (mf_izq[0] * mf_der[2], ALTO, ALTO),
        (mf_izq[1] * mf_der[0], NORMAL, ALTO),
        (mf_izq[1] * mf_der[1], ALTO, BAJO),
        (mf_izq[1] * mf_der[2], NORMAL, ALTO),
        (mf_izq[2] * mf_der[0], ALTO, ALTO),
        (mf_izq[2] * mf_der[1], ALTO, NORMAL),
        (mf_izq[2] * mf_der[2], NORMAL, REVERSA),
    ]

    suma_pesos = sum(w for w, _, _ in reglas)
    if suma_pesos == 0:
        return 0, 0

    salida_izq = sum(w * out1 for w, out1, _ in reglas) / suma_pesos
    salida_der = sum(w * out2 for w, _, out2 in reglas) / suma_pesos

    return int(max(0, min(salida_izq, 180))), int(max(0, min(salida_der, 180)))

# --- ESTRATEGIA DE MOVIMIENTO CON FILTRADO ---
def estrategia():
    global ULTIMA_IZQ, ULTIMA_DER

    nueva_izq = leer_distancia_sharp(sensor_frontal_izquierdo_pin)
    nueva_der = leer_distancia_sharp(sensor_frontal_derecho_pin)

    d_izq = filtrar_distancia(nueva_izq, ULTIMA_IZQ)
    d_der = filtrar_distancia(nueva_der, ULTIMA_DER)

    ULTIMA_IZQ = d_izq
    ULTIMA_DER = d_der

    m1, m2 = evaluar_sugeno(d_izq, d_der)

    print(f"Sharp I: {d_izq:.1f} cm, Sharp D: {d_der:.1f} cm -> PWM Izq: {m1}, PWM Der: {m2}")
    motor_adelante(m1, m2)

# --- BUCLE PRINCIPAL ---
if __name__ == "__main__":
    motor_detener()
    print("Iniciando programa de control difuso con Sharp y sensibilidad reducida...")
    time.sleep(2)

    try:
        while True:
            estrategia()
            time.sleep(0.05)
    except KeyboardInterrupt:
        motor_detener()
        print("Programa terminado.")
