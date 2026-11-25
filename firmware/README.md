# Firmware — ESP32

| Archivo | Qué hace |
|---|---|
| `main/main.ino` | Programa principal: lee las 2 sondas DS18B20 cada 10 s, decide con `control.h`, mueve el servo, enciende los LED y envía cada lectura a Firebase (guarda 30 min en memoria si se cae el WiFi) |
| `main/control.h` | Controlador diferencial con histéresis: abre con ΔT ≥ 5 K, cierra con ΔT ≤ 2 K, 60 s mínimo entre movimientos, modo seguro (abre) tras 3 lecturas inválidas y cierre por sobretemperatura del tanque (65 °C). Sin dependencias de Arduino: se prueba en el PC con `testing/unit/test_control.cpp` |
| `main/config.h.example` | Plantilla de configuración: WiFi, URL de Firebase, pines y direcciones de las sondas. Se copia como `config.h` (no se sube a GitHub) |
| `utils/escanear_ds18b20/escanear_ds18b20.ino` | Utilidad para leer la dirección ROM de cada sonda |

## Pines (perfboard final, ESP32 de 38 pines)

| Señal | GPIO |
|---|---|
| Bus 1-Wire de las sondas (pull-up 4.7 kΩ a 3V3) | 33 |
| Servo SG90 (señal PWM 50 Hz) | 13 |
| LED verde / rojo | 26 / 27 |

## Librerías (Gestor de librerías del Arduino IDE)

| Librería | Versión probada |
|---|---|
| OneWire (Paul Stoffregen) | 2.3.8 |
| DallasTemperature (Miles Burton) | 4.0.6 |
| ESP32Servo (Kevin Harrington, John K. Bennett) | 3.2.1 |
| Placas *esp32* (Espressif Systems) | 3.3.4 |

No se copian las librerías al repositorio: se instalan desde el Gestor de librerías con las versiones de la tabla. Fuentes y URL en [`FUENTES.md`](../FUENTES.md).

## Cargar el programa

1. Copiar `main/config.h.example` como `main/config.h` y completar el WiFi (hotspot del celular, 2.4 GHz) y la URL de Firebase.
2. Cargar `utils/escanear_ds18b20` y copiar las direcciones de las sondas en `ADDR_COL` y `ADDR_TANK`.
3. Placa **ESP32 Dev Module**, abrir `main/main.ino` y cargar. Monitor Serie a 115200 baudios.
