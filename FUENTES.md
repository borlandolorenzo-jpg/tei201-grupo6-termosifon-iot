# FUENTES.md — Declaración de librerías, código externo y uso de IA

**Proyecto:** Colector solar termosifón con válvula anti-flujo-inverso (IoT) · TEI201 · Grupo 6
**Integrantes:** Lorenzo Borlando · Cristóbal Fuentes · Micaela Miserda
**Fecha de la declaración:** 18 de noviembre de 2026

> Los campos marcados **[COMPLETAR]** deben ser revisados por el equipo antes de entregar: versiones instaladas y cualquier cambio que hayan hecho al probar con el hardware real.

---

## 1. Librerías y dependencias

### Firmware (ESP32, Arduino IDE)

| Librería | Versión | Uso en el proyecto | Fuente |
|---|---|---|---|
| OneWire (Paul Stoffregen) | **[COMPLETAR: versión instalada]** | Protocolo 1-Wire para comunicar las 3 sondas DS18B20 en un solo pin (GPIO4) | https://github.com/PaulStoffregen/OneWire |
| DallasTemperature (Miles Burton) | **[COMPLETAR]** | Lectura de temperatura de las DS18B20 por dirección ROM, resolución de 12 bits, conversión sin bloqueo | https://github.com/milesburton/Arduino-Temperature-Control-Library |
| ESP32Servo | **[COMPLETAR]** | Control PWM a 50 Hz del servo SG90 que simula la válvula | https://github.com/madhephaestus/ESP32Servo |
| Arduino core para ESP32 (Espressif): `WiFi.h`, `WiFiClientSecure.h`, `HTTPClient.h`, `time.h` | **[COMPLETAR: versión del core]** | Conexión WiFi, peticiones HTTPS a Firebase y hora por NTP | https://github.com/espressif/arduino-esp32 |

### Dashboard (navegador)

| Librería | Versión | Uso en el proyecto | Fuente |
|---|---|---|---|
| Chart.js | 4.4.1 | Gráficos de temperaturas, ΔT y estado de la válvula | https://www.chartjs.org/ (cargada desde cdnjs.cloudflare.com) |

### Servicios

| Servicio | Uso | Fuente |
|---|---|---|
| Firebase Realtime Database (API REST) | Repositorio persistente de las lecturas | https://firebase.google.com/docs/reference/rest/database |

### Pruebas y análisis (PC)

| Librería | Uso | Fuente |
|---|---|---|
| pandas, NumPy, Matplotlib (Python 3) | `testing/analisis.py`: cálculo de indicadores y gráficos | https://pandas.pydata.org · https://numpy.org · https://matplotlib.org |
| Node.js (solo `assert`, módulo estándar) | `testing/unit/test_analytics.js` | https://nodejs.org |

---

## 2. Código externo adaptado

No se copió código de repositorios, foros ni tutoriales. Los siguientes elementos siguen patrones públicos de la documentación oficial, pero se escribieron para este proyecto:

### Lectura no bloqueante de DS18B20 (`finishCycle` y `loop` en `firmware/main/main.ino`)
- Fuente del patrón: ejemplos de la librería DallasTemperature (`setWaitForConversion(false)` + `requestTemperatures()` y lectura posterior).
- Adaptación: máquina de estados con `millis()` (espera de 800 ms para 12 bits), lectura por dirección ROM de cada sonda, validación de los valores de falla (−127 °C y 85 °C de arranque) y descarte de lecturas fuera de rango.

### Petición HTTPS a Firebase (`firebaseSend` en `main.ino`)
- Fuente del patrón: documentación REST de Firebase Realtime Database (`POST` agrega un registro, `PUT` reemplaza un nodo) y ejemplos de `HTTPClient` del core ESP32.
- Adaptación: cola circular de 180 muestras en RAM para no perder datos si se cae el WiFi, reintentos con la muestra más antigua primero, y envío del nodo `/estado` solo cuando la cola queda vacía.
- Limitación declarada: se usa `setInsecure()` (no valida el certificado del servidor), aceptable en un prototipo de curso pero no en producción.

---

## 3. Uso de Inteligencia Artificial

**Herramienta:** Claude (Anthropic), conversación de noviembre de 2026.
**Contexto entregado a la IA:** pautas de los Avances 2 y 3, clases del curso (arquitectura electrónica, histéresis, PI/PID, CAD) y el diseño del proyecto (termosifón, válvula, sensores DS18B20, servo SG90 en lugar de la válvula solenoide).

### 3.1 Firmware `firmware/main/control.h` — controlador diferencial con histéresis
- **Qué generó la IA:** estructura de la clase `DiffController`, reglas de apertura/cierre por ΔT, modo de falla (válvula abierta tras 3 lecturas inválidas), protección por sobretemperatura y tiempo mínimo entre movimientos.
- **Adaptación al proyecto:** umbrales iniciales ΔT_on = 5 K y ΔT_off = 2 K elegidos para que la banda de 3 K supere el error combinado de dos sondas (±0.5 °C cada una); límite de 65 °C para el tanque de plástico. **[COMPLETAR: valores finales tras las pruebas]**.
- **Comprensión del equipo:** la válvula se abre cuando el colector está al menos 5 K más caliente que el tanque (hay sol) y se cierra cuando la diferencia baja a 2 K o menos (de noche, para evitar el flujo inverso). Entre ambos valores mantiene su estado para no conmutar por ruido. Si falla un sensor, queda abierta para que el sistema funcione como un termosifón común y no se sobrecaliente el colector. Se probó en PC con `testing/unit/test_control.cpp` (siete grupos de pruebas, resultado en `testing/unit/resultado_test_control.txt`).

### 3.2 Firmware `firmware/main/main.ino`, `config.h.example` y `firmware/utils/escanear_ds18b20`
- **Qué generó la IA:** estructura general del programa, cola de muestras, envío a Firebase, indicadores LED, utilidad para leer las direcciones de las sondas.
- **Adaptación:** pines (GPIO4, 18, 26, 27), periodo de muestreo de 10 s justificado por la inercia térmica del tanque, modo `CONTROL_ENABLED` para el ensayo B (sin válvula). **[COMPLETAR: cambios hechos al probar con el hardware]**.
- **Comprensión del equipo:** cada 10 s se pide la temperatura, se espera 800 ms, se leen las tres sondas, el controlador decide el estado de la válvula, se mueve el servo, la muestra entra a la cola y se envía a Firebase si hay WiFi.
- **Verificación:** el código se revisó contra cabeceras simuladas de Arduino para detectar errores de sintaxis en PC; la compilación y carga en el ESP32 real la realiza el equipo. **[COMPLETAR: confirmar que compiló y cargó]**.

### 3.3 Dashboard `dashboard/` (HTML, CSS, JavaScript)
- **Qué generó la IA:** interfaz, gráficos con Chart.js, indicadores del periodo, alertas, exportación a CSV, modo de demostración con datos simulados (`?demo=1`, claramente rotulado y no usado como evidencia).
- **Adaptación:** definiciones de los indicadores del problema (tiempo de flujo inverso evitado, horas captando calor, cierres, calor almacenado), alertas de agua lista (≥ 45 °C), sobretemperatura, falla de sensor y dispositivo sin reportar.
- **Comprensión del equipo:** el dashboard descarga las últimas lecturas de Firebase, las convierte en indicadores (`dashboard/analytics.js`) y las grafica; si no recibe datos por más de 60 s marca "Sin conexión".
- **Verificación:** nueve pruebas unitarias en `testing/unit/test_analytics.js` y revisión visual en navegador con datos de demostración.

### 3.4 `testing/analisis.py` y pruebas unitarias
- **Qué generó la IA:** script de análisis de los ensayos P1–P6 y las pruebas unitarias.
- **Adaptación:** criterios de aceptación y fórmulas ligados al protocolo del proyecto.
- **Verificación:** el script se probó con datos **sintéticos generados solo para validar el código**; esos datos no se incluyen en el repositorio ni se usan como resultados.

### 3.5 Documentación y diseño
- **Qué generó la IA:** borradores del protocolo de testing, README, esquemático en SVG (`hardware/esquematico.svg`), BOM, guía del gemelo 3D, guion de presentación y diapositivas.
- **Adaptación:** el equipo revisó el contenido contra el diseño real del proyecto y completó los valores marcados como pendientes (costos reales de la BOM, medidas con pie de metro, resultados). **[COMPLETAR]**
- **Costos de la BOM:** los valores unitarios son estimados y deben reemplazarse por los de las boletas.

---

## 4. Elementos creados enteramente por el equipo
**[COMPLETAR por el equipo]** — por ejemplo: diseño del colector solar, montaje físico, soldadura de la perfboard, modelo 3D en Fusion 360, fotografías y ensayos.
