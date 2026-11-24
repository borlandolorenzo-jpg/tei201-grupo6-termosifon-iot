# Guion de presentación — Avance 3 (23 de noviembre de 2026)

**Tiempo:** 8–10 min de presentación + 3 min de preguntas. **Todos deben hablar.**
**Roles sugeridos:** *Lorenzo* → electrónica, firmware, diseño 3D y demo · *Cristóbal* → solución y arquitectura, GitHub y apoyo en la demo · *Micaela* → problema, dashboard y testing. Ajustar según quién hizo cada parte: cada persona debe poder explicar lo que presenta.

## Secuencia (10 min)

| Min | Diapositiva | Quién | Qué decir |
|---|---|---|---|
| 0:00–1:00 | 1. Problema | Micaela | Pobreza energética en Chile: calentar agua es caro. El termosifón solar la calienta sin electricidad, pero de noche el flujo se invierte y el tanque pierde calor (hasta ≈ 40 % de lo captado en algunos sistemas). ODS 7 |
| 1:00–2:00 | 2. Solución y arquitectura | Cristóbal | Mide, decide, actúa y registra: 2 sondas DS18B20 (colector y tanque) → ESP32 → válvula (servo SG90 que la simula) → Firebase → dashboard. Controlador diferencial con histéresis, no PID: es la solución más simple que cumple |
| 2:00–5:30 | 3. **Demo en vivo** | Lorenzo y Micaela | Ver guion de demo abajo |
| 5:30–6:30 | 4. Hardware | Lorenzo | Perfboard soldada, ESP32 en zócalos, sondas y servo con conectores. Mostrar fotos de 3 ángulos, BOM con costo total y justificación de componentes |
| 6:30–7:30 | 5. Diseño 3D | Lorenzo | Gemelo 3D: todos los componentes con volúmenes reales. Decisiones: dos piezas con 4 tornillos, compartimiento del servo, accesos USB y jack. Abrir Fusion y mostrar el interior; planos y renders |
| 7:30–9:00 | 6. Testing y validación | Micaela | Protocolo P1–P6: calibración vs. referencia, lógica de control, conectividad, alimentación, ensayo nocturno A/B (con y sin válvula) y desempeño diurno. Criterios medibles. Resultados **por simulación** (acordado con el profesor; decirlo explícitamente): P2 6/6 transiciones correctas y modo seguro; P5 la válvula reduce 25 % la pérdida nocturna (≈ 135 Wh/noche); P6 el tanque llega a 45 °C a las 16:09. Hallazgo: con tanque aislado la reducción sube a 52 % → aislar el tanque es la próxima mejora. Mostrar `dashboard/index.html?sim=1` |
| 9:00–9:30 | 7. GitHub | Cristóbal | Mostrar el repositorio: carpetas, README, FUENTES.md |
| 9:30–10:00 | 8. Cierre | Todos | Qué resolvimos, qué falta (ensayos y análisis) y próximos pasos |

## Guion de la demo en vivo (3 min)

**Antes de empezar (preparación obligatoria):** sistema encendido y "En línea" en el dashboard, WiFi probado, dashboard abierto en una pestaña, Monitor Serie abierto en otra, sondas ubicadas (colector, tanque, ambiente) y dos vasos con agua fría y caliente listos para provocar ΔT.

1. **Datos reales (30 s).** Mostrar el dashboard actualizándose: temperaturas de las sondas (colector y tanque), hora de la última lectura.
2. **Sensor → decisión → actuador (60 s).** Con la válvula cerrada, sumergir la sonda del colector en el agua caliente: ΔT sube; al superar 5 K el servo se abre y el chip del dashboard cambia a ABIERTA (el LED verde se enciende). Sacar la sonda y enfriarla: al bajar de 2 K la válvula se cierra.
3. **Información útil (30 s).** Mostrar los indicadores: cierres, horas de flujo inverso evitado, temperatura máxima. Explicar cómo ayudan a decidir.
4. **Robustez (30 s).** Desconectar la sonda del tanque: LED rojo parpadea, el dashboard muestra la alerta y la válvula queda abierta (modo seguro). Reconectar.
5. **Persistencia (30 s).** Cambiar el periodo a "Últimas 24 h" para mostrar el histórico guardado en Firebase.

**Plan B:** celular como punto de acceso WiFi, segundo ESP32 cargado, sondas de repuesto, y captura de pantalla del dashboard con datos reales de los ensayos (como respaldo, **no** como reemplazo de la demo: el video o las capturas no cuentan como demo).

## Preguntas probables y cómo responderlas

| Pregunta | Idea de respuesta |
|---|---|
| ¿Por qué histéresis y no PID? | La salida es abrir o cerrar, no una referencia continua. La banda de 3 K supera el error combinado de dos sondas (±0.5 °C), así el ruido no hace conmutar la válvula. Con PID habría que justificar una variable continua |
| ¿Por qué 5 K y 2 K? | Son valores iniciales fundamentados en el error de sondas y se ajustan con P2 y P5. Se pueden modificar en `control.h` |
| ¿Por qué se cierra de noche? | Si el tanque está más caliente que el colector, el agua caliente sube por el tanque y baja por el colector, lo enfría y pierde energía. Cerrar corta esa circulación |
| ¿Qué pasa si falla una sonda? | Tras 3 lecturas inválidas la válvula queda abierta (el sistema se comporta como un termosifón común), el LED rojo parpadea y el dashboard avisa |
| ¿Y si se cae el WiFi? | El ESP32 sigue controlando localmente, guarda 180 muestras (30 min) y las envía al reconectar |
| ¿Por qué un servo y no una válvula? | La solenoide de 12 V no sirvió para el proyecto y es cara. El servo simula la válvula para demostrar la lógica; el efecto hidráulico real se valida después |
| ¿Por qué DS18B20? | Digitales, ±0.5 °C, sumergibles y tres en un solo pin. No necesitan ADC ni calibración analógica |
| ¿Por qué 10 s de muestreo? | El tanque cambia de temperatura en minutos, 10 s sobra y genera ≈ 8 600 registros al día, dentro del plan gratuito de Firebase |
| ¿Cómo validan que funciona? | Ensayo nocturno A/B: misma temperatura inicial con y sin válvula; reducción de pérdida ≥ 25 % (criterio propuesto). Más calibración, lógica de control y conectividad |
| ¿Qué parte del código usó IA? | Está declarado en FUENTES.md: firmware, dashboard, análisis y documentos. Hay que poder explicar cualquier función (ver sección siguiente) |
| ¿Cómo se repara? | Perfboard atornillada, ESP32 en zócalos, sondas y servo con conectores, tapa con 4 tornillos M3 |

## Repaso de funciones del código (cualquiera puede preguntarlas)

| Función / archivo | Qué hace |
|---|---|
| `DiffController::update` (`control.h`) | Decide abrir/cerrar con ΔT, histéresis, tiempo mínimo, falla de sensor y sobretemperatura |
| `validReading` (`main.ino`) | Descarta −127 °C (sonda desconectada), 85 °C de arranque y valores fuera de rango |
| `loop` + `finishCycle` | Pide la medición, espera 800 ms sin bloquear, lee, controla, mueve el servo y encola la muestra |
| `queuePush` / `queuePop` | Cola circular de 180 muestras para no perder datos sin WiFi |
| `firebaseSend` / `uploadOne` | Envía la muestra más antigua por HTTPS: `POST` al histórico y `PUT` al estado |
| `updateLeds` | Verde = abierta; rojo parpadea si hay falla o sin WiFi |
| `computeKPIs` (`dashboard/analytics.js`) | Convierte las lecturas en indicadores y alertas, sin integrar huecos de más de 60 s |

## Antes de presentar
- [ ] Ensayar completo **3 veces** con cronómetro (8–10 min)
- [ ] Cada persona sabe qué diapositiva y qué parte de la demo le toca
- [ ] Dashboard abierto, repositorio abierto, Fusion 360 abierto con el ensamble
- [x] URL del repositorio en la diapositiva final
- [ ] Todas las cosas subidas a GitHub **antes** de la presentación
