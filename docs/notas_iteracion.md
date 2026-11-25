# Notas de iteración

Registro de cambios, problemas y decisiones. La rúbrica de Testing y Validación pide al menos **una falla encontrada y cómo se resolvió**. 

## Decisiones tomadas

| Fecha | Cambio | Motivo | Efecto en el diseño |
|---|---|---|---|
| nov 2026 | Se descarta la **válvula solenoide de 12 V** | No funcionaba para el proyecto y su costo es alto | Se usa un **servo SG90** que simula la válvula (abierta/cerrada); desaparece el riel de 12 V y la fuente pasa a 5 V / 2 A |
| nov 2026 | Toda la electrónica pasa a **perfboard** soldada | Conexiones firmes dentro del encapsulado | ESP32 en zócalos hembra; sondas y servo con conectores (reparación en campo) |
| nov 2026 | Control con **histéresis diferencial** (5 K / 2 K) en vez de umbral simple | Con un solo umbral el ruido de las sondas hace conmutar la válvula | Banda de 3 K > error combinado de dos sondas (±0.5 °C cada una) |
| nov 2026 | Se pasa de **3 a 2 sondas** DS18B20 (colector y tanque) | Solo se dispone de 2 sondas | La sonda de ambiente queda opcional (`HAS_AMBIENT` = 0); la temperatura ambiente de los ensayos se toma con el termómetro de referencia |
| 23 nov 2026 | Pines finales en la perfboard: **GPIO33** (sondas) y **GPIO13** (servo), con ESP32 de **38 pines** | Ubicación en la placa soldada | Se actualizan `config.h`, esquemático y guía de montaje |
| nov 2026 | El ensamble 3D con componentes en Fusion 360 se mantiene en la versión Alpha (relé y válvula solenoide) | Al simplificar la electrónica no hubo tiempo de rehacer el ensamble; el encapsulado impreso sí es el final | Componentes finales en el modelo de referencia STEP; ensamble Alpha en `diseño-3d/iteraciones/` |
| 24 nov 2026 | Ensayos P2, P5 y P6 **por simulación** (acordado con el profesor y el ayudante) | El ESP32 no se conecta a la red WiFi pública de la universidad | Resultados en `testing/resultados_simulacion.md`; para el hardware se usará el hotspot de un celular (2.4 GHz) |
| nov 2026 | **Modo seguro**: válvula abierta ante falla de sensor | Un servo cerrado con colector al sol podría sobrecalentar | Se prueba en P2 |

## Problemas encontrados en pruebas con el hardware

| Fecha | Síntoma | Causa | Solución | Evidencia |
|---|---|---|---|---|
| nov 2026 | La válvula solenoide de 12 V no servía para el prototipo | No era adecuada para el montaje y reemplazarla era muy caro | Se reemplaza por un servo SG90 que simula la válvula; la fuente se simplifica a 5 V | `hardware/fotos/iteraciones/alpha_protoboard_rele.jpg` (antes) y `hardware/fotos/01_encapsulado_abierto_componentes.jpg` (después) |
| 24 nov 2026 | Revisión del código: con solo 2 sondas el firmware habría marcado falla de sensor permanente (LED rojo) | `HAS_AMBIENT` venía en 1 y el código esperaba una tercera sonda de ambiente | `HAS_AMBIENT` = 0 por defecto en `main.ino` y `config.h.example` | Commit del 24-11-2026 |
| 24 nov 2026 | Firmware y esquemático con pines distintos a los de la placa soldada (GPIO4/18 vs GPIO33/13) | La documentación se escribió antes de soldar la perfboard | Se actualizan firmware, esquemático y guía de montaje a GPIO33/13 | Commit del 24-11-2026 |

*Ejemplo del nivel de detalle esperado:* «El ESP32 se reiniciaba al mover el servo (corriente de arranque). Se agregó un condensador de 470 µF junto al servo y el riel se mantuvo sobre 4.75 V en 20 ciclos.»

## Aprendizajes
-
