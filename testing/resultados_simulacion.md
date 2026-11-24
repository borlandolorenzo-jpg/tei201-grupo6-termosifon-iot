# Resultados por simulación — ensayos P2, P5 y P6

**TEI 201 · Grupo 6** · Lorenzo Borlando · Cristóbal Fuentes · Micaela Miserda

> **Estos resultados provienen de una simulación, no de mediciones del hardware.**
> Según lo acordado con el profesor y el ayudante del curso, los ensayos con registro en la nube se reemplazaron por una simulación porque el ESP32 no puede conectarse a la red WiFi pública de la universidad (requiere usuario institucional o portal de acceso, que el firmware no maneja). Todos los archivos simulados llevan el prefijo `SIM_` y el dashboard los muestra solo con `?sim=1`, rotulados como "SIMULACIÓN".

## 1. Qué se simuló y cómo

`testing/simulacion/simular.py` modela el colector y el tanque como dos masas térmicas con un balance de energía cada 10 s (el mismo periodo de muestreo del firmware):

| Elemento | Modelo | Valor supuesto |
|---|---|---|
| Radiación solar | Senoide entre 06:36 y 20:48 (noviembre, Santiago), pico 900–1000 W/m² según el día | 4 días distintos |
| Temperatura ambiente | Mínima 06:30, máxima 16:30 | 12.5–30.5 °C |
| Colector | Área 0.3 m², τα = 0.70, U_L = 10 W/m²K, capacidad 8 kJ/K, enfriamiento hacia el cielo de noche 15 W | Colector artesanal pequeño |
| Tanque | 20 L de agua, pérdidas UA = 2.5 W/K (tanque plástico sin aislar) | Igual al `config.js` del dashboard |
| Termosifón | Directo: 15 W/K × ΔT cuando el colector está más caliente; **inverso: 4 W/K × ΔT** cuando el tanque está más caliente | Solo con la válvula abierta |
| Sondas | Resolución del DS18B20 (0.0625 °C) + ruido de 0.05 °C | — |
| Controlador | Copia exacta de `firmware/main/control.h` en Python: abre con ΔT ≥ 5 K, cierra con ΔT ≤ 2 K, 60 s mínimo entre movimientos, modo seguro tras 3 lecturas inválidas | — |

Se corrieron dos configuraciones con **el mismo clima y el mismo ruido**: **A** con válvula (controlador activo) y **B** sin válvula (siempre abierta). En la segunda noche de A se desconecta la sonda del colector 2 minutos (23:00) para probar el modo seguro.

Los datos quedan en `testing/datos/simulacion/` y se analizaron con el mismo script que se usará con datos reales (`testing/analisis.py`). Salidas y gráficos en `testing/resultados/simulacion/`.

## 2. Resultados

### P2 — Lógica de control (24 h, 20-11)

| Hora | Evento | T col [°C] | T tanque [°C] | ΔT [K] | Motivo |
|---|---|---|---|---|---|
| 08:43 | ABRE | 28.8 | 23.8 | 5.0 | Sale el sol: ΔT llega al umbral de apertura |
| 18:03 | CIERRA | 47.9 | 45.9 | 2.0 | El sol baja: ΔT cae al umbral de cierre |
| 18:19 | ABRE | 50.3 | 45.3 | 5.0 | Sin flujo, el colector se recalienta con el último sol |
| 18:30 | CIERRA | 47.4 | 45.4 | 2.0 | Cierre definitivo de la tarde |
| 23:00 | ABRE | — | 37.1 | — | **Modo seguro:** sonda del colector desconectada |
| 23:02 | CIERRA | 18.7 | 37.0 | −18.3 | Vuelve la sonda: cierra para evitar el flujo inverso |

- 6 de 6 transiciones coherentes con las reglas (**criterio 100 %: cumple**).
- 0 ventanas con más de 2 cambios en 10 min (**sin conmutación por ruido: cumple**). Hubo 1 597 muestras dentro de la banda de histéresis (2–5 K) en las que la válvula mantuvo su estado.
- El modo seguro abrió la válvula a los 20 s (3 lecturas inválidas) y la cerró al volver la sonda.

### P5 — Ensayo nocturno A/B (3 noches, 20:30 → 07:30)

| | Noche 1 | Noche 2 | Noche 3 | Media |
|---|---|---|---|---|
| A: con válvula — pérdida normalizada | 0.723 | 0.732 | 0.728 | **0.728** |
| B: sin válvula — pérdida normalizada | 0.966 | 0.981 | 0.970 | **0.972** |

Pérdida normalizada = (T₀ − T_final) / (T₀ − T_ambiente media): fracción del "calor por encima del ambiente" que el tanque pierde en la noche.

- **Reducción de la pérdida nocturna con válvula: 25.1 %** (criterio propuesto ≥ 25 %: cumple, justo en el límite).
- Energía perdida por noche (20 L): **A = 434 Wh · B = 569 Wh → la válvula evita ≈ 135 Wh por noche**.

### P6 — Desempeño diurno (20-11)

- Temperatura máxima del tanque: **46.1 °C**; el objetivo de 45 °C (Avance 1) se alcanzó a las **16:09** (cumple).
- Horas captando calor: 9.5 h · flujo inverso con la válvula abierta: **0.00 h** · cierres: 3.

## 3. Análisis

**La válvula funciona como se diseñó, pero su beneficio depende del tanque.** Con el tanque sin aislar, la mayor parte de la pérdida nocturna ocurre por las paredes del tanque y no por el colector, así que cerrar la válvula reduce la pérdida "solo" un 25 %. La sensibilidad lo muestra:

| Aislación del tanque (UA) | Reducción de la pérdida nocturna con válvula |
|---|---|
| 1.0 W/K (tanque aislado) | **51.9 %** |
| 2.5 W/K (plástico sin aislar, caso base) | 25.1 % |
| 4.0 W/K (tanque muy expuesto) | 14.3 % |

(`testing/resultados/simulacion/SIM_sensibilidad_aislacion_tanque.csv`)

**Conclusión de diseño:** la válvula anti-flujo-inverso y la aislación del tanque se complementan; sin aislación, la válvula protege un calor que igual se pierde por el tanque. La mejora de mayor impacto para la próxima iteración es **aislar el tanque**.

**Comportamiento al atardecer:** la válvula abrió y cerró dos veces entre las 18:03 y 18:30 (el colector sin flujo se recalienta con el último sol). No es ruido: son cambios separados por más de 10 minutos y cada uno respeta los umbrales. Si en el hardware real molesta, se puede subir el tiempo mínimo entre movimientos.

## 4. Conexión con el problema del Avance 1

En el Avance 1 se identificó que el termosifón pierde de noche parte del calor captado de día por flujo inverso: el agua caliente del tanque baja por el colector frío y se enfría. La simulación muestra que el controlador:

1. **Detecta el fenómeno** con solo dos temperaturas: de noche ΔT llega a −20 K y la válvula queda cerrada 38 h en 3 días (indicador "flujo inverso evitado" del dashboard).
2. **Lo evita sin perjudicar la captación de día**: la válvula está abierta todo el periodo útil (9.5 h) y el agua llega a 45 °C.
3. **Entrega información para decidir**: el dashboard muestra cuándo el agua está lista (≥ 45 °C) y cuánto calor se protegió, y la comparación A/B indica que la siguiente inversión debe ser aislar el tanque.

## 5. Limitaciones

- **No son mediciones.** Los parámetros del modelo (área, pérdidas, conductancias del termosifón) son supuestos de órdenes de magnitud típicos, no medidos en el colector del grupo.
- El servo simula la válvula también en el prototipo físico; el efecto hidráulico real no se ha medido.
- La validación con el hardware queda definida en `testing/protocolo_pruebas.md`: los mismos comandos de `analisis.py` sirven para los CSV reales, conectando el ESP32 al **hotspot de un celular** (red 2.4 GHz) en vez de la red de la universidad.
