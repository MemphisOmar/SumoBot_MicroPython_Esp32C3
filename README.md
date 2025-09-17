# Robot Sumo - Controlador Difuso Sugeno
![front](https://github.com/user-attachments/assets/0ce206fe-55a5-4391-affa-6796f10fd220)

![lateral](https://github.com/user-attachments/assets/3919ed10-c522-4b54-a2c0-51d253baeee5)


Este proyecto implementa un controlador difuso tipo Sugeno para un robot sumo, utilizando sensores de distancia y sensores de piso para la toma de decisiones y control de motores.

---

## ¿Dónde y cómo se usa la lógica difusa en el código?

### 1. Fuzzificación (Funciones de Membresía)

Se usan funciones triangulares para calcular el grado de pertenencia de las distancias a los conjuntos "Cerca", "Media" y "Lejos":

python
def trimf(x, a, b, c):
    if x <= a or x >= c:
        return 0.0
    elif a < x < b:
        return (x - a) / (b - a)
    elif b <= x < c:
        return (c - x) / (c - b)
    elif x == b:
        return 1.0


En la función evaluar_sugeno, se calcula para cada sensor:

python
izq = [trimf(sensor_izq, 0, 15, 30), trimf(sensor_izq, 25, 45, 60), trimf(sensor_izq, 50, 70, 80)]
der = [trimf(sensor_der, 0, 15, 30), trimf(sensor_der, 25, 45, 60), trimf(sensor_der, 50, 70, 80)]


---

### 2. Evaluación de Reglas Difusas

Cada regla representa una posible situación de los sensores y la acción correspondiente para los motores.  
El grado de activación de cada regla es el producto de los grados de pertenencia de las entradas:

python
reglas = [
    (izq[0]*der[1], 200, 200),
    (izq[1]*der[1], 200, 200),
    (izq[0]*der[0], 255, 255),
    (izq[1]*der[1], 0, 0),
    (izq[0]*der[2], 0, 255),
    (izq[1]*der[2], 0, 200),
    (izq[2]*der[0], 255, 255),
    (izq[1]*der[2], 200, 0),
    (izq[2]*der[1], 200, 0),
]


---

### 3. Inferencia Sugeno (Agregación)

Se calcula la salida de cada motor como una media ponderada de las salidas de las reglas activadas:

python
suma_pesos = sum(w for w, _, _ in reglas)
if suma_pesos == 0:
    return 0, 0

m1 = sum(w * out1 for w, out1, _ in reglas) / suma_pesos
m2 = sum(w * out2 for w, _, out2 in reglas) / suma_pesos


---

### 4. Salida directa en escala 0-255

Las salidas de los motores (m1 para el izquierdo, m2 para el derecho) ya están en el rango [0, 255], por lo que se pueden usar directamente para el control PWM:

python
m1 = max(0, min(int(m1), 255))
m2 = max(0, min(int(m2), 255))
return m1, m2


---

### 5. Uso en la Estrategia de Control

En la función estrategia, se llama a evaluar_sugeno para obtener las velocidades y se pasan directamente a las funciones de control de motores:

python
m1, m2 = evaluar_sugeno(d_izq, d_der)
motor_adelante(m1, m2)


Esto ocurre en los diferentes estados del robot (buscando, atacando, etc.), permitiendo que la lógica difusa decida la velocidad y dirección de los motores en cada ciclo.

---

### ¿Cómo se utiliza la lógica difusa en la estrategia?

En la función estrategia, la lógica difusa se usa para decidir las velocidades de los motores en tiempo real, según las lecturas de los sensores de distancia. El flujo es el siguiente:

1. *Lectura de sensores:*  
   Se obtienen las distancias actuales de los sensores izquierdo (d_izq) y derecho (d_der).

2. *Evaluación difusa:*  
   Se llama a la función evaluar_sugeno(d_izq, d_der), que aplica la lógica difusa y devuelve dos valores:  
   - m1: velocidad para el motor izquierdo (0-255)  
   - m2: velocidad para el motor derecho (0-255)

3. *Control de motores:*  
   Estos valores se pasan directamente a la función de control de motores, por ejemplo:  
   python
   m1, m2 = evaluar_sugeno(d_izq, d_der)
   motor_adelante(m1, m2)
   
   Así, la lógica difusa determina en cada ciclo la acción óptima para los motores, adaptándose a la situación detectada por los sensores.

Esto ocurre en los diferentes estados del robot (buscando, atacando, etc.), permitiendo que la lógica difusa decida la velocidad y dirección de los motores en cada ciclo de la estrategia.

---

## Resumen

- *Fuzzificación:* Convierte las lecturas de los sensores en grados de pertenencia.
- *Reglas difusas:* Deciden la acción según la situación de los sensores.
- *Inferencia Sugeno:* Calcula la salida como media ponderada.
- *Salida directa:* La salida ya está en el rango 0-255, lista para usarse en el PWM de los motores.
- *Control de motores:* El usuario solo usa valores de 0 a 255, pero internamente la lógica difusa toma decisiones suaves y adaptativas.

---
