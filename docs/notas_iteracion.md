# Notas de iteración

Registro de cambios, problemas y decisiones. La rúbrica de Testing y Validación pide al menos **una falla encontrada y cómo se resolvió**. Completar las filas vacías con lo que ocurra al probar el hardware real.

## Decisiones tomadas

| Fecha | Cambio | Motivo | Efecto en el diseño |
|---|---|---|---|
| nov 2026 | Se descarta la **válvula solenoide de 12 V** | No funcionaba para el proyecto y su costo es alto | Se usa un **servo SG90** que simula la válvula (abierta/cerrada); desaparece el riel de 12 V y la fuente pasa a 5 V / 2 A |
| nov 2026 | Toda la electrónica pasa a **perfboard** soldada | Conexiones firmes dentro del encapsulado | ESP32 en zócalos hembra; sondas y servo con conectores (reparación en campo) |
| nov 2026 | Control con **histéresis diferencial** (5 K / 2 K) en vez de umbral simple | Con un solo umbral el ruido de las sondas hace conmutar la válvula | Banda de 3 K > error combinado de dos sondas (±0.5 °C cada una) |
| nov 2026 | **Modo seguro**: válvula abierta ante falla de sensor | Un servo cerrado con colector al sol podría sobrecalentar | Se prueba en P2 |

## Problemas encontrados en pruebas con el hardware

| Fecha | Síntoma | Causa | Solución | Evidencia |
|---|---|---|---|---|
| | | | | |
| | | | | |
| | | | | |

*Ejemplo del nivel de detalle esperado:* «El ESP32 se reiniciaba al mover el servo (corriente de arranque). Se agregó un condensador de 470 µF junto al servo y el riel se mantuvo sobre 4.75 V en 20 ciclos.»

## Aprendizajes
-
