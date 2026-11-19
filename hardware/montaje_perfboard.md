# Montaje en perfboard

Guía para pasar el circuito del protoboard a una perfboard soldada dentro del encapsulado. Complementa a [`esquematico.pdf`](esquematico.pdf).

## Principios de diseño
- **ESP32 en zócalos hembra (no se suelda):** se puede retirar para reprogramarlo o reemplazarlo.
- **Sondas y servo con conectores:** borneras atornillables (J2–J4) para las sondas y regleta de 3 pines (J5) para el servo. Ninguno va soldado a la placa.
- **Código de colores:** rojo = +5 V o VDD, negro = GND, amarillo = datos/señal.
- **Un solo riel de GND** que une fuente, ESP32, servo, sondas y LED.

## Orden de montaje
1. **Posicionar** sobre la perfboard (7 × 9 cm): zócalos del ESP32 al centro, con el USB hacia un borde; borneras J2–J4 y J5 en el borde que da a la pared con las perforaciones; jack/bornera J1 en el borde de alimentación.
2. **Soldar** zócalos, borneras y regleta. Verificar que no hay puentes de estaño entre pistas.
3. **Soldar los pasivos:** R1 (4.7 kΩ) entre la pista de datos del bus y la de 3V3; R2 y R3 (220 Ω) a los LED; C1 (470 µF) lo más cerca posible de J5, respetando la polaridad (la franja del condensador es el negativo).
4. **Cablear** las pistas de +5V, 3V3, GND, ONEWIRE y SERVO_PWM según la tabla de conexiones del esquemático.
5. **Revisar con multímetro, sin el ESP32 puesto:** continuidad de cada red y **ausencia de cortocircuito entre +5V y GND, y entre 3V3 y GND**.
6. **Encender sin el ESP32** y comprobar 5.0 V entre +5V y GND en los zócalos. Apagar, insertar el ESP32 y volver a encender.
7. **Cargar el firmware**, conectar las sondas y el servo y verificar en el Monitor Serie.

## Pines usados (ESP32 DevKit V1)

| Pin | Red | Conecta a |
|---|---|---|
| VIN | +5V | Fuente y servo (rojo) |
| GND | GND | Riel común |
| 3V3 | +3V3 | VDD de las sondas y R1 |
| GPIO4 | ONEWIRE | DQ de las sondas (2 instaladas; J4 reservado a la opcional de ambiente), R1 |
| GPIO18 | SERVO_PWM | Servo (naranja) |
| GPIO26 | LED_OK | R2 → LED verde → GND |
| GPIO27 | LED_FAIL | R3 → LED rojo → GND |

## Lista de verificación antes de cerrar el encapsulado
- [ ] Sin cortocircuitos entre redes (medido con multímetro)
- [ ] Todas las soldaduras brillantes y firmes (tirar suavemente de los cables)
- [ ] Polaridad de C1 correcta
- [ ] Cada sonda etiquetada (COL, TANK y, si existe, AMB) y coincide con `config.h`
- [ ] El servo se mueve libre, sin forzar el tope
- [ ] Cables sujetos con amarras para que no tiren de las soldaduras
- [ ] Fotografías tomadas **desde al menos 3 ángulos** (pedido en la rúbrica)
