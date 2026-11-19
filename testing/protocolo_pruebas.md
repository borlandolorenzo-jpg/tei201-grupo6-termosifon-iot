---
title: "Protocolo experimental — Colector solar termosifón con válvula anti-flujo-inverso"
subtitle: "TEI 201 · Taller de Diseño en Ingeniería · Grupo 6 · Avance N.º 3"
---

**Integrantes:** Lorenzo Borlando · Cristóbal Fuentes · Micaela Miserda
**Versión:** 1.0 (18-11-2026) · **Estado:** protocolo completo; ejecución de los ensayos definitivos pendiente (permitido en el Avance 3)

# 0. Alcance y estado

El prototipo mide tres temperaturas (salida del colector, tanque y ambiente) con sondas DS18B20, decide con un controlador diferencial con histéresis si la válvula debe estar abierta o cerrada, mueve un servo SG90 que **simula** la válvula y envía los datos a Firebase para visualizarlos en un dashboard.

Este documento define **cómo se comprobará** que el sistema funciona y que responde al problema del Avance 1: *el termosifón pierde calor de noche por flujo inverso (el agua caliente del tanque desciende por el colector frío)*. Las pruebas se dividen en seis ensayos, P1 a P6.

| Estado actual | Evidencia |
|---|---|
| Pruebas unitarias del controlador en PC (7 grupos, todas pasan) | `testing/unit/resultado_test_control.txt` |
| Pruebas unitarias de los indicadores del dashboard (9, todas pasan) | `testing/unit/resultado_test_analytics.txt` |
| Ensayos P1–P6 con el hardware | **Pendientes** (se ejecutan después del Avance 3 con el procedimiento de la sección 4) |

**Limitación declarada:** el servo reemplaza a la válvula real (la solenoide de 12 V se descartó por costo). Los ensayos validan la lógica de decisión, la instrumentación y el flujo de datos; el efecto hidráulico de una válvula real sobre el termosifón debe confirmarse en una etapa posterior.

# 1. Objetivo de las pruebas

**Objetivo general.** Demostrar, con evidencia medible, que el sistema captura temperaturas confiables, decide correctamente cuándo cerrar la válvula y reduce la pérdida de calor nocturna del tanque respecto de un termosifón sin válvula.

| ID | Objetivo específico | Por qué es relevante para el problema |
|---|---|---|
| O1 | Verificar la exactitud de las sondas DS18B20 | La decisión depende de ΔT = T_col − T_tanque; un error de sonda puede cerrar o abrir la válvula en el momento equivocado |
| O2 | Verificar que el controlador abre y cierra según los umbrales, sin conmutar por ruido y con modo seguro ante fallas | Evita desgaste del servo y bloqueos de la circulación |
| O3 | Verificar que los datos llegan completos al repositorio y al dashboard | Sin datos confiables no se puede medir el desempeño ni tomar decisiones |
| O4 | Verificar que la alimentación soporta el movimiento del servo sin reinicios | Un reinicio de noche dejaría la válvula en estado desconocido |
| O5 | Cuantificar la reducción de pérdida nocturna con válvula frente a sin válvula | Es la innovación central del proyecto (ODS 7) |
| O6 | Verificar que el sistema acompaña el ciclo diurno y que el agua alcanza la temperatura objetivo | Confirma que la válvula no impide la captación de calor |

**Hipótesis.** Con la válvula operativa, la pérdida de temperatura del tanque durante la noche es al menos 25 % menor que con la válvula fija abierta, bajo las mismas condiciones iniciales.

# 2. Variables y parámetros de medición

## 2.1 Variables

| Variable | Símbolo | Tipo | Instrumento | Unidad | Incertidumbre / resolución |
|---|---|---|---|---|---|
| Temperatura salida del colector | T_col | Medida | DS18B20 (S1) | °C | ±0.5 °C (fabricante); resolución 0.0625 °C |
| Temperatura del tanque | T_tank | Medida / respuesta | DS18B20 (S2) | °C | ±0.5 °C; resolución 0.0625 °C |
| Temperatura ambiente (sombra) | T_amb | Medida / registrada | DS18B20 (S3) | °C | ±0.5 °C; resolución 0.0625 °C |
| Diferencia de temperatura | ΔT = T_col − T_tank | Calculada | — | K | ≈ ±0.7 K (combinación de dos sondas) |
| Estado de la válvula | V | Respuesta | Firmware (registro) | 0 / 1 | — |
| Temperatura de referencia | T_ref | Medida (patrón) | Termómetro de referencia (ver 3.1) | °C | Declarar la del instrumento usado |
| Corriente y tensión de alimentación | I, V_5V | Medida | Multímetro | A, V | Según multímetro |
| Volumen de agua del tanque | V_L | Controlada | Recipiente graduado | L | ±0.1 L |
| Hora | t | Medida | NTP (ESP32) | s | ~1 s |

## 2.2 Parámetros controlados (se fijan y se registran)

| Parámetro | Valor inicial | Dónde se define |
|---|---|---|
| Umbral de apertura ΔT_on | 5.0 K | `firmware/main/control.h` |
| Umbral de cierre ΔT_off | 2.0 K | `firmware/main/control.h` |
| Tiempo mínimo entre movimientos | 60 s | `firmware/main/control.h` |
| Límite de sobretemperatura del tanque / reanudación | 65 °C / 60 °C | `firmware/main/control.h` (confirmar con el material del tanque) |
| Periodo de muestreo | 10 s | `firmware/main/config.h` (`SAMPLE_MS`) |
| Modo de control | `CONTROL_ENABLED` 1 (A) o 0 (B) | `firmware/main/config.h` |
| Volumen del tanque, ubicación de sondas, inclinación y orientación del colector | Anotar en la hoja de registro | Hoja de registro (anexo A) |

## 2.3 Indicadores de desempeño

| Indicador | Definición |
|---|---|
| Error de sonda | e = T_medida − T_ref (media por punto y desviación estándar) |
| Offset de sonda | Media del error en todos los puntos |
| Coherencia de transiciones | % de cambios de la válvula que cumplen la regla (abre si ΔT ≥ ΔT_on; cierra si ΔT ≤ ΔT_off) |
| Tasa de entrega de datos | Muestras recibidas / muestras esperadas × 100 |
| Pérdida nocturna normalizada | (T₀ − T_f) / (T₀ − T_amb,media), con T₀ y T_f la temperatura del tanque al inicio y al final |
| Reducción de pérdida | 1 − (pérdida normalizada con válvula / pérdida normalizada sin válvula) |
| Energía almacenada o perdida | Q = V_L · 1.163 Wh/(L·K) · ΔT |

# 3. Condiciones experimentales

## 3.1 Instrumentos y equipos

- Prototipo completo (ESP32 + 3 DS18B20 + servo SG90 + perfboard + encapsulado), fuente 5 V / 2 A.
- Termómetro de referencia independiente (digital, con resolución ≤ 0.1 °C). Anotar marca, modelo y su incertidumbre.
- Recipientes con agua: hielo triturado (0 °C), agua a temperatura ambiente y agua caliente (≈ 40 °C y ≈ 60 °C), con agitación manual o magnética.
- Multímetro (tensión y corriente continua), cronómetro o cámara a 60 fps.
- Red WiFi con acceso a Internet y notebook con el dashboard abierto.
- Estación de ensayo térmico: colector solar, tanque con volumen conocido, aislación y soporte; protección contra lluvia.
- Notebook con Python 3, `pandas`, `numpy` y `matplotlib` para `testing/analisis.py`.

## 3.2 Rangos de operación

- Temperatura de agua en ensayos: 0 a 70 °C (dentro del rango de la sonda, −55 a +125 °C).
- Alimentación: 5 V ± 5 % (4.75 a 5.25 V).
- Temperatura ambiente de los ensayos nocturnos: registrada; sin lluvia ni viento fuerte.

## 3.3 Condiciones generales

1. El firmware usa las direcciones ROM de cada sonda (`ADDR_COL`, `ADDR_TANK`, `ADDR_AMB`). Etiquetar físicamente cada sonda.
2. Antes de cada ensayo: sondas conectadas, WiFi conectado, dashboard "En línea", hora sincronizada.
3. Un ensayo **no cuenta** si hubo reinicios del ESP32 no planificados; se repite y se anota la causa.
4. Seguridad: agua a más de 50 °C puede causar quemaduras (usar guantes y evitar salpicaduras); la electrónica opera a 5 V, mantenerla seca y alejada del agua.

# 4. Procedimiento experimental

## P1 · Verificación de las sondas contra una referencia (O1)

1. Preparar cuatro baños: hielo (0 °C), ambiente (≈ 20 °C), tibio (≈ 40 °C) y caliente (≈ 60 °C), con agitación.
2. Sumergir en el mismo baño las tres sondas DS18B20 y el termómetro de referencia, a la misma profundidad y sin tocar las paredes.
3. Esperar a que se estabilicen: la referencia debe variar menos de 0.05 °C por minuto durante 3 minutos.
4. Registrar durante 5 minutos: 30 lecturas por sonda (una cada 10 s, desde el Monitor Serie o el dashboard) y la lectura de referencia en cada instante.
5. Anotar cada lectura en `testing/datos/plantilla_P1_calibracion.csv` (columnas `punto, t_ref_c, sensor, t_medida_c`).
6. Repetir para los cuatro puntos. Secar las sondas entre baños.
7. Ejecutar `python testing/analisis.py calibracion testing/datos/P1_calibracion_AAAAMMDD.csv`.
8. Si hay offset sistemático, restarlo en el firmware y repetir el punto de 40 °C para confirmar.

## P2 · Lógica de control en banco (O2)

Se emula ΔT moviendo las sondas entre baños; no requiere sol.

1. Cargar el firmware con `CONTROL_ENABLED 1`. Poner la sonda del tanque en un baño a ≈ 30 °C (estable).
2. **Apertura.** Con la válvula cerrada, calentar el baño de la sonda del colector hasta que ΔT supere 5 K. Registrar la hora de cruce y el movimiento del servo.
3. **Cierre.** Enfriar el baño del colector hasta que ΔT baje de 2 K. Registrar lo mismo.
4. **Banda muerta.** Mantener ΔT entre 2 y 5 K durante 5 minutos agitando el agua (ruido). Contar conmutaciones.
5. **Tiempo mínimo.** Cruzar el umbral dos veces en menos de 60 s y comprobar que la válvula no se mueve dos veces.
6. **Falla de sensor.** Desconectar la sonda del tanque durante 60 s: la válvula debe quedar abierta, el LED rojo parpadear y el dashboard mostrar la alerta. Reconectar y comprobar la recuperación.
7. **Sobretemperatura.** Simular un tanque a ≥ 65 °C (baño caliente con la sonda del tanque): la válvula debe cerrar; al bajar a ≤ 60 °C, reanudar.
8. Medir con cronómetro o video a 60 fps el retardo entre el cruce del umbral (según el registro) y el movimiento del servo.
9. Exportar el registro y ejecutar `python testing/analisis.py control testing/datos/P2_registro_AAAAMMDD.csv`.

## P3 · Conectividad y persistencia de datos (O3)

1. Dejar el sistema funcionando **60 minutos continuos** con el dashboard abierto (el mínimo exigido en la demo es 5 minutos).
2. A los 20 minutos, apagar el WiFi (router o punto de acceso) durante 2 minutos y volver a encenderlo. Comprobar que el LED rojo parpadea y que, al reconectar, los datos acumulados aparecen en el histórico.
3. Medir el retardo de visualización: en 10 eventos, anotar la hora en que cambia un valor (por ejemplo, al tocar una sonda con la mano) y la hora en que se ve en el dashboard.
4. Exportar el CSV y ejecutar `python testing/analisis.py entrega testing/datos/P3_registro_AAAAMMDD.csv`.
5. Cerrar y reabrir el dashboard: el histórico debe seguir disponible (persistencia en Firebase).

## P4 · Alimentación y consumo (O4)

1. Medir con el multímetro la tensión del riel de 5 V en reposo, con WiFi activo y durante el movimiento del servo.
2. Medir la corriente de la fuente (multímetro en serie) en reposo, con WiFi y en el instante de movimiento del servo.
3. Provocar 20 ciclos de abrir y cerrar (modo de prueba con umbrales bajos o con baños) y contar los reinicios del ESP32 (mensaje de arranque en el Monitor Serie).
4. Anotar los valores en la hoja de registro.

## P5 · Ensayo nocturno A/B: con y sin válvula (O5, validación contra el problema)

Este es el ensayo que valida la solución frente al problema del Avance 1.

1. Al atardecer (≈ 19:00) llenar el tanque con un volumen conocido V_L y calentarlo hasta una temperatura inicial T₀ ≈ 50 °C (colector al sol o aporte externo). Todas las noches se debe partir con T₀ igual ± 1 °C y el mismo V_L.
2. Dejar el montaje a la intemperie protegido de lluvia, con el tanque por encima del colector.
3. **Configuración A:** `CONTROL_ENABLED 1`. **Configuración B:** `CONTROL_ENABLED 0` (válvula siempre abierta, equivalente a un termosifón sin válvula).
4. Registrar toda la noche (≈ 12 h, hasta ≈ 07:00) con el dashboard conectado.
5. Alternar configuraciones en noches sucesivas: A, B, A, B, A, B (mínimo **3 noches por configuración**).
6. Anotar en la hoja de registro: fecha, T₀, V_L, nubosidad, viento y T_amb media. Descartar noches con lluvia.
7. Exportar un CSV por noche (`P5_A_noche1.csv`, `P5_B_noche1.csv`, …).
8. Ejecutar `python testing/analisis.py ab --a P5_A_noche1.csv P5_A_noche2.csv P5_A_noche3.csv --b P5_B_noche1.csv P5_B_noche2.csv P5_B_noche3.csv --litros V_L`.

*Alternativa si falta tiempo:* ensayo de 4 horas (19:00 a 23:00) con el mismo procedimiento; se debe declarar la duración en el informe.

## P6 · Desempeño diurno (O6)

1. En un día soleado, con el tanque lleno a temperatura ambiente y `CONTROL_ENABLED 1`, iniciar el registro a las 08:00 y mantenerlo hasta las 20:00.
2. Registrar nubosidad y T_amb. Anotar la hora en que el tanque alcanza el objetivo.
3. Exportar el CSV y ejecutar `python testing/analisis.py diurno testing/datos/P6_registro_AAAAMMDD.csv --objetivo 45`.

# 5. Criterios de aceptación y validación

| Ensayo | Métrica | Criterio de aceptación | Origen del criterio |
|---|---|---|---|
| P1 | Error medio por sonda y punto | \|e\| ≤ 0.5 °C | Exactitud declarada por el fabricante |
| P1 | Desviación estándar de las 30 lecturas | ≤ 0.1 °C | Resolución 0.0625 °C; ruido bajo |
| P1 | Diferencia de error entre sondas en un mismo baño | ≤ 0.5 K (el error de ΔT queda bajo la banda de histéresis de 3 K) | Diseño del controlador |
| P2 | Transiciones coherentes con las reglas | 100 % | Especificación del controlador |
| P2 | Conmutaciones dentro de la banda muerta (ΔT entre 2 y 5 K) | 0 | Función de la histéresis |
| P2 | Ventanas con más de 2 transiciones en 10 min | 0 | Protección del servo |
| P2 | Movimiento del servo tras la decisión | ≤ 1 s | Requisito de operación |
| P2 | Falla de sensor: válvula abierta y alerta | Abierta en ≤ 40 s (3 ciclos de 10 s + 1) y alerta en el dashboard en ≤ 60 s | Diseño fail-open |
| P2 | Sobretemperatura | Cierra a ≥ 65 °C y reanuda a ≤ 60 °C | Protección del tanque |
| P3 | Tasa de entrega de datos (60 min) | ≥ 98 % | Confiabilidad de la medición |
| P3 | Recuperación tras corte de WiFi de 2 min | ≥ 95 % de las muestras del corte recuperadas | Cola de 180 muestras |
| P3 | Retardo de visualización | ≤ 25 s (10 s de muestreo + 10 s de refresco + envío) | Periodos configurados |
| P3 | Reinicios del ESP32 en 60 min | 0 | Estabilidad (mín. 5 min exigidos en demo) |
| P4 | Tensión del riel de 5 V durante el movimiento del servo | ≥ 4.75 V | Tolerancia −5 % |
| P4 | Corriente pico de la fuente | ≤ 1.6 A (80 % de 2 A) | Margen de diseño |
| P4 | Reinicios en 20 ciclos de la válvula | 0 | Robustez eléctrica |
| P5 | Reducción de la pérdida nocturna (A frente a B, promedio de ≥ 3 noches) | ≥ 25 % | **Valor propuesto**: la literatura reporta pérdidas por flujo inverso de hasta ≈ 40 % de la energía captada; se confirma o ajusta con el equipo docente |
| P5 | Flujo inverso con la válvula abierta en la configuración A | ≤ 0.25 h por noche | Eficacia del control |
| P6 | Temperatura máxima del tanque en un día soleado | ≥ 45 °C (objetivo de agua caliente) | Requisito del Avance 1 |
| P6 | Horas captando calor con la válvula abierta | Se registra; sin criterio mínimo (depende del clima) | — |

**Validación contra el problema original.** El proyecto se considera validado si se cumplen P2 (la lógica decide bien), P3 (los datos son confiables) y P5 (la válvula reduce la pérdida nocturna), y P6 muestra que la válvula no impide calentar el agua. Si P5 no alcanza el criterio, el análisis debe identificar la causa (umbrales, aislación, estratificación del tanque) y proponer un ajuste.

# 6. Tratamiento y análisis de datos

1. **Adquisición.** Cada muestra se guarda en Firebase y se exporta desde el dashboard (botón *Exportar CSV*) con el formato `ts_epoch, ts_iso_utc, t_col_c, t_tank_c, t_amb_c, valvula_abierta, falla, rssi_dbm, cierres`.
2. **Depuración.** Se eliminan duplicados por `ts_epoch` y se identifican huecos. Los intervalos mayores a 60 s no se integran en los indicadores.
3. **Cálculo.** `testing/analisis.py` calcula los indicadores de la sección 2.3:
   - P1: error medio, desviación estándar, incertidumbre tipo A (s/√n), offset por sonda y error residual tras la corrección.
   - P2: tabla de transiciones con ΔT en el instante del cambio y verificación contra las reglas.
   - P3: tasa de entrega, mayor hueco y lecturas inválidas.
   - P5: pérdida normalizada por noche, promedio y dispersión por configuración y reducción porcentual.
   - P6: temperatura máxima, hora en que se alcanza el objetivo, horas de captación y cierres.
4. **Incertidumbre.** Se combina la incertidumbre tipo A (dispersión de las lecturas) con la tipo B (±0.5 °C de la sonda y la incertidumbre del termómetro de referencia). Con solo 3 noches por configuración, se reporta la dispersión y se evita extrapolar.
5. **Gráficos.** Error vs. temperatura de referencia (P1), ΔT y estado de la válvula en el tiempo (P2), pérdida normalizada A/B con barras de error (P5), temperaturas del ciclo diurno (P6). Se guardan en `testing/resultados/`.
6. **Comparación con criterios.** Cada resultado se compara con la tabla de la sección 5 y se declara *cumple* o *no cumple*; en caso de no cumplir se documenta la causa y la corrección.

# 7. Evidencia experimental esperada

| Ensayo | Archivos y registros | Ubicación |
|---|---|---|
| P1 | CSV de calibración, tabla de errores, gráfico error vs. referencia, foto del montaje con el termómetro de referencia | `testing/datos/`, `testing/resultados/`, `testing/evidencia/` |
| P2 | CSV de registro, tabla de transiciones, gráfico ΔT / válvula, video del servo, captura de la alerta de falla | ídem |
| P3 | CSV de 60 min, resumen de entrega, captura del dashboard antes y después del corte de WiFi | ídem |
| P4 | Hoja de registro con tensiones, corrientes y reinicios; foto del multímetro | `testing/evidencia/` |
| P5 | Seis CSV (3 por configuración), hoja de registro de cada noche, gráfico A/B, fotos del montaje | ídem |
| P6 | CSV de 12 h, gráfico diurno, captura del dashboard | ídem |
| Transversal | Pruebas unitarias del controlador y del dashboard | `testing/unit/` |

**Nomenclatura:** `P<n>_<descripción>_<AAAAMMDD>.csv`; fotos y capturas con el mismo prefijo.

# 8. Riesgos y contingencias

| Riesgo | Mitigación |
|---|---|
| Clima impide ejecutar P5/P6 | Registrar la fecha y condiciones; usar el ensayo alternativo de 4 h; repetir otra noche |
| Corte de WiFi | La cola de 180 muestras conserva 30 min; el sistema sigue controlando localmente |
| Sonda defectuosa | Reemplazo por bornera sin soldar; repetir P1 solo con esa sonda |
| Reinicio del ESP32 durante un ensayo | El ensayo se descarta y se repite; se anota la causa |
| Condensación o agua en la electrónica | Encapsulado cerrado, sondas sumergibles, cableado elevado |

# Anexo A · Hoja de registro de ensayos

| Fecha | Ensayo | Config. (A/B) | V_L [L] | T₀ [°C] | T_amb media [°C] | Nubosidad / viento | Reinicios | Observaciones | Responsable |
|---|---|---|---|---|---|---|---|---|---|
| | | | | | | | | | |
| | | | | | | | | | |
| | | | | | | | | | |
