# 🤖 Robot Mini-Sumo con Lógica Difusa
![MicroPython](https://img.shields.io/badge/MicroPython-303030?style=for-the-badge&logo=micropython&logoColor=white)
![ESP32](https://img.shields.io/badge/ESP32-E7352C?style=for-the-badge&logo=espressif&logoColor=white)

![front](https://github.com/user-attachments/assets/0ce206fe-55a5-4391-affa-6796f10fd220)
![lateral](https://github.com/user-attachments/assets/3919ed10-c522-4b54-a2c0-51d253baeee5)

El objetivo de este robot es competir en combates de sumo, empujando a su oponente fuera de un dojo. Su principal característica es el uso de un **controlador de lógica difusa tipo Sugeno** para una toma de decisiones inteligente y adaptativa, en lugar de depender de una lógica binaria tradicional.

---

## ✨ Características Principales

**Estrategia Autónoma:** El robot opera de forma 100% autónoma para detectar y atacar a su oponente.
**Controlador de Lógica Difusa:** Utiliza un sistema de inferencia Sugeno para procesar las lecturas de los sensores y generar respuestas de motor suaves y eficientes[cite: 20, 106].
**Detección con Sensores Infrarrojos:** Emplea sensores Sharp para medir la distancia al rival y planificar su estrategia[cite: 20].
**Filtrado de Ruido:** Implementa un umbral para ignorar pequeñas variaciones en las mediciones de distancia, lo que le da mayor estabilidad y evita movimientos erráticos[cite: 23, 80].

---

## 🧠 ¿Cómo Funciona la Lógica Difusa?

El "cerebro" del robot no piensa en términos absolutos, sino en grados de verdad. El proceso es el siguiente:

1.**Fuzzificación:** Las distancias leídas por los sensores se convierten en conceptos lingüísticos como **"Cerca"**, **"Lejos"** y **"No Detectado"**.
2. **Evaluación de Reglas:** Un conjunto de **9 reglas** combina los estados de los sensores izquierdo y derecho para decidir la acción a tomar.Por ejemplo: `"Si el sensor Izquierdo está Cerca y el Derecho está Lejos, entonces gira hacia la derecha"`.
3.**Inferencia y Acción:** El sistema calcula una media ponderada de todas las reglas para determinar la velocidad exacta y fluida de cada motor, permitiendo al robot adaptarse dinámicamente al combate[cite: 59].

---

## ⚙️ Hardware Utilizado

| Cantidad | Componente                  |
| :------: | --------------------------- |
|    2     | Motores DC                  |
|    1     | ESP32 C3 Super Mini + Shield |
|    1     | Driver de Motor MX1508      |
|    2     | Sensores de Distancia Sharp |
|    2     | Ruedas                      |
|    1     | Batería Lipo                |
|    1     | Regulador Step-Down MP1584  |
|    1     | Switch                      |
