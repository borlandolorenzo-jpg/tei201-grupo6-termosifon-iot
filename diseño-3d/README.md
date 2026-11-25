# Diseño 3D — Gemelo digital y encapsulado

Guía para modelar en **Fusion 360** el encapsulado y el ensamble completo (gemelo 3D) del controlador. La rúbrica del Avance 3 pide: ensamble con todos los componentes, modelo paramétrico, encapsulado funcional y diseñado para reparación, planos con cotas y escala, renders exterior e interior/explosionado y archivo `.f3d` o `.f3z`.

> **Las medidas de esta guía son valores iniciales de partida.** Medir cada componente real con pie de metro antes de modelar y corregir la tabla de parámetros. El CAD debe ser **consistente con el prototipo físico**.

## 1. Archivos de esta carpeta

| Archivo | Contenido | Estado |
|---|---|---|
| `layout_interno_propuesto.svg/.png` | Distribución interna en planta (referencia para el boceto) | Listo |
| `modelo_referencia/` | **Modelo 3D de referencia** generado con CadQuery: `base.step`, `tapa.step`, `ensamble_completo.step` (con todos los componentes), STL de la base y la tapa, `componentes.csv` y los scripts que los generan. Se importa a Fusion 360 como punto de partida | Listo (medidas nominales) |
| `CW_LB_106_11.f3d` · `CW_LB_106_21.f3d` | Archivos de Fusion 360 del encapsulado impreso, hechos por el equipo (se abren con *Archivo → Abrir → Abrir desde mi equipo*) | Listo |
| `iteraciones/ensamble_prototipo_alpha_rele_valvula.f3d` | **Ensamble completo en Fusion 360 con todos los componentes, de la versión anterior (Alpha)**: ESP32, relé, válvula solenoide de 12 V y su alimentación, sondas y LED | Listo · corresponde al prototipo antiguo (ver nota abajo) |
| `planos/plano_referencia.pdf/.svg` | Plano A3 1:1 de referencia: vista frontal, lateral, planta y corte A-A con cotas y tolerancias | Listo como referencia · **reemplazar por el plano exportado de Fusion 360** |
| `renders/` | `render_exterior.png`, `render_interior.png`, `render_explosionado.png` (del modelo de referencia) | Listo como referencia · **rehacer con materiales en Fusion 360 (espacio Render)** |

> **Cómo usar el modelo de referencia:** en Fusion 360 usa *Insertar → Insertar malla / Abrir* con `modelo_referencia/ensamble_completo.step` para ver el ensamble y comparar tus medidas reales. Es un sólido importado, no paramétrico: la rúbrica pide un modelo **paramétrico**, así que rehaz la base y la tapa con los parámetros de la sección 3 (puedes copiar las cotas del plano) y guarda el `.f3z`. Las medidas del modelo son nominales y **deben verificarse con pie de metro** para que coincidan con el prototipo físico. Para regenerar el modelo con otras medidas: edita los parámetros al inicio de `modelo_referencia/generar_modelo.py` y ejecuta `python3 generar_modelo.py` (requiere `pip install cadquery`).

## Nota sobre la versión final

El ensamble con componentes en Fusion 360 (`iteraciones/ensamble_prototipo_alpha_rele_valvula.f3d`) se hizo para el **prototipo Alpha**, que usaba relé y válvula solenoide de 12 V. Para el prototipo final **se simplificó la electrónica**: la válvula solenoide y el relé se reemplazaron por un servo SG90 que simula la válvula, se eliminó la etapa de 12 V y la placa pasó a una perfboard de 50 × 70 mm. **No se rehízo el ensamble en Fusion 360** con esta electrónica simplificada; el encapsulado impreso (`CW_LB_106_*.f3d`) sí es el final.

Los componentes de la versión final (ESP32, perfboard, servo, 2 sondas y alimentación de 5 V) están en el **modelo de referencia** `modelo_referencia/ensamble_completo.step` (lista en `componentes.csv`), con sus renders y plano. Los motivos del cambio están en `docs/notas_iteracion.md`.

## 2. Componentes del gemelo (volúmenes referenciales)

La rúbrica acepta sólidos simples (cajas y cilindros) con el volumen y la posición reales.

| Componente | Dimensiones iniciales (mm) | Notas para el modelo |
|---|---|---|
| ESP32 DevKit (38 pines) | ≈ 52 × 28 × 12 (incluye zócalos) | Medir; dejar libre la antena y el acceso al conector USB |
| Perfboard | 90 × 70 × 1.6 | Sobre 4 separadores M3 de 6 mm |
| Servo SG90 | cuerpo 23 × 12.5 × 22.7; con orejas 32.5 de largo | Compartimiento propio; paso del cable y del eje |
| Borneras 3 pines (×3) | 16 × 8 × 10 | Cables de sondas salen por la pared superior |
| Jack DC 5.5 × 2.1 | 14 × 12 × 11 | Debe quedar accesible desde la pared |
| LED 5 mm (×2) | Ø 5 × 9 | Visibles desde la tapa o la pared |
| Condensador 470 µF | Ø 8 × 12 | Junto al conector del servo |
| Tornillos M3 × 8 (×8) | Ø 3 × 8 | 4 de tapa y 4 de la perfboard |

Los cuatro integrantes del circuito (MCU, sensores, actuador, alimentación) deben aparecer en el ensamble. Las sondas DS18B20 salen por cable: modelar la entrada de cable y un tramo de cable.

## 3. Parámetros de Fusion (Modificar → Parámetros de usuario)

Crear los parámetros para que un cambio de medida actualice todo el modelo (esto cubre el criterio *modelo paramétrico*):

| Parámetro | Valor inicial | Descripción |
|---|---|---|
| `pared` | 2.5 mm | Espesor de pared, base y tapa |
| `holgura` | 1.0 mm | Holgura alrededor de cada componente |
| `placa_ancho` / `placa_largo` | 90 / 70 mm | Perfboard |
| `servo_largo` / `servo_ancho` / `servo_alto` | 32.5 / 12.5 / 22.7 mm | SG90 con orejas |
| `int_ancho` | 150 mm | Ancho interior (= placa + holgura + postes + compartimiento servo) |
| `int_largo` | 90 mm | Largo interior |
| `int_alto` | 32 mm | Alto interior (separador 6 + placa 1.6 + zócalo y ESP32 ≈ 18 + margen) |
| `tornillo_d` | 3.0 mm | Diámetro de tornillo M3 |
| `agujero_tapa_d` | 3.4 mm | Agujero pasante con tolerancia de impresión |

**Dimensiones exteriores resultantes:** 155 × 95 × ≈ 37 mm (interior más paredes, base y tapa).

## 4. Decisiones de diseño (justificación para la presentación)

| Decisión | Motivo |
|---|---|
| Caja de dos piezas: base y tapa con 4 tornillos M3 | Acceso a todos los componentes sin destruir el encapsulado (criterio de reparación) |
| Perfboard sobre separadores atornillados | Se retira la placa completa; evita cortocircuitos con el fondo |
| ESP32 en zócalo y sondas/servo con conectores | Reemplazo de piezas sin soldar |
| Compartimiento separado para el servo | Aísla el movimiento y la vibración del resto de la electrónica |
| Perforaciones: USB, jack, cables de sondas, 2 LED | Acceso a puertos y señalización sin abrir la caja |
| Postes de tornillo libres de la perfboard | Evitan interferencias (verificar con el análisis de interferencias de Fusion) |
| Material PETG o PLA | PETG resiste mejor el calor y la intemperie; el PLA basta para pruebas bajo techo |
| Tolerancia de impresión 0.2–0.3 mm en ajustes | Evita piezas que no encajan |

## 5. Pasos sugeridos en Fusion 360
1. Crear el proyecto `TEI201_Grupo6` y un diseño `Controlador_termosifon`.
2. Definir los **parámetros de usuario** de la sección 3.
3. Modelar cada componente como un cuerpo o *componente* separado con sus dimensiones (sección 2). Usar *Boceto → Restricciones → Extrusión* como en la clase 5.
4. Armar el ensamble: separadores, perfboard, ESP32, borneras, jack, LED, compartimiento y servo.
5. Modelar la **base** alrededor del ensamble (extrusión con parámetros) y la **tapa** con 4 agujeros y ventanas para los LED.
6. Ejecutar **Análisis de interferencia** (Inspeccionar → Interferencia): no debe haber choques entre componentes y caja.
7. Probar el parámetro: cambiar `int_ancho` en 10 mm y comprobar que el modelo se actualiza sin errores (evidencia de modelo paramétrico).
8. **Planos:** Crear dibujo desde el diseño con vista superior, frontal, lateral, corte por el eje del ESP32 y una vista isométrica; escala 1:1 o 1:2; cotas funcionales (exterior, interior, perforaciones, distancia a tornillos) y tolerancias (±0.2 mm). Exportar PDF.
9. **Renders:** asignar materiales (PETG, PCB verde, cobre, metal) y exportar una vista exterior y una **explosionada** o con la tapa oculta (espacio de trabajo *Render*).
10. Guardar el archivo (`.f3z`) en esta carpeta y exportar el PDF y las imágenes a `planos/` y `renders/`.

## 6. Lista de verificación de la rúbrica (Diseño 3D, 20 %)
- [ ] El ensamble incluye MCU, sondas (entrada de cable), servo, perfboard, conectores y alimentación con volúmenes reales
- [ ] Modelo paramétrico, sin errores ni interferencias; el archivo abre correctamente
- [ ] Encapsulado con tapa funcional, acceso a USB, jack y cables, y tolerancias consideradas
- [ ] Planos con vistas ortogonales, cotas, tolerancias y escala (PDF)
- [ ] Renders con materiales e iluminación: exterior e interior/explosionado
- [ ] Coincide con el prototipo físico (verificar con una fotografía del montaje)
- [ ] Demostración preparada: mostrar los componentes internos en Fusion durante la presentación
