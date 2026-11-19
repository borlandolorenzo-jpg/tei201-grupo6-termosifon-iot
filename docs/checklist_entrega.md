# Checklist de entrega — Avance 3 (23-11-2026)

**Leyenda:** ✅ listo en este repositorio · 🔧 lo hace el equipo con el hardware real · 📝 completar con datos propios

## Requisito habilitante
- ✅ `FUENTES.md` en la raíz del repo → 📝 completar versiones de librerías, cambios hechos al probar y la sección 4
  *(sin FUENTES.md o vacío, Software queda con 1.0)*

## Software (30 %)
| Ítem | Estado |
|---|---|
| Captura continua de datos reales | 🔧 cargar `main.ino` al ESP32, configurar `config.h` y las direcciones de las sondas |
| Repositorio de datos persistente (Firebase) | 🔧 crear el proyecto y pegar las reglas (README, paso 1) |
| Dashboard con gráficos, tendencias y alertas | ✅ `dashboard/` · 🔧 poner la URL en `config.js` y verificar con datos reales |
| Información útil que responde al problema | ✅ indicadores y alertas definidos en `analytics.js` |
| Código comentado y modular | ✅ |
| Explicación de las funciones principales | ✅ `docs/guion_presentacion.md` (repaso de funciones) |

## Hardware (30 %)
| Ítem | Estado |
|---|---|
| Justificación técnica de cada componente | ✅ columna "Justificación" de `hardware/BOM.xlsx` |
| Esquemático completo | ✅ `hardware/esquematico.pdf` *(si el profesor exige Fritzing/KiCad, redibujar con la tabla de conexiones)* |
| BOM con cantidades, especificación y costo | ✅ · 📝 reemplazar costos estimados por los de las boletas y completar la hoja del colector |
| Montaje ordenado, conexiones seguras y etiquetadas | 🔧 soldar en perfboard (guía en `hardware/montaje_perfboard.md`) |
| Fotografías desde al menos 3 ángulos | 🔧 guardar en `hardware/fotos/` |
| Diseño para la reparación (abrir el encapsulado en la demo) | 🔧 imprimir y ensayar |

## Diseño 3D (20 %)
| Ítem | Estado |
|---|---|
| Archivo `.f3d`/`.f3z` con el ensamble completo (todos los componentes) | 🔧 modelar en Fusion con la guía de `diseño-3d/README.md`; hay un ensamble de referencia importable en `diseño-3d/modelo_referencia/ensamble_completo.step` |
| Modelo paramétrico sin interferencias | 🔧 |
| Planos con vistas, cotas, tolerancias y escala (PDF) | ✅ referencia en `diseño-3d/planos/plano_referencia.pdf` · 🔧 reemplazar por el exportado de Fusion |
| Renders exterior e interior o explosionado | ✅ referencia en `diseño-3d/renders/` · 🔧 rehacer en Fusion con materiales |
| Consistencia con el prototipo físico | 🔧 medir con pie de metro |

## Testing y validación (10 %)
| Ítem | Estado |
|---|---|
| Protocolo completo con las 7 secciones (a–g) | ✅ `testing/protocolo_pruebas.pdf` |
| Pruebas unitarias en PC | ✅ `testing/unit/` |
| Script de análisis listo | ✅ `testing/analisis.py` |
| Resultados experimentales (P1–P6) | Pendiente permitido en el Avance 3 |
| Al menos una falla encontrada y su solución | 📝 `docs/notas_iteracion.md` |

## GitHub (5 %)
- ✅ Estructura de carpetas `firmware/ hardware/ diseño-3d/ testing/ docs/` y README completo
- 🔧 Crear el repositorio (público o accesible al evaluador) y subir **todo** antes de la presentación
- 🔧 Verificar que `config.h` **no** se sube (está en `.gitignore`) y que el repo se puede clonar
- 🔧 Commits con mensajes descriptivos (por ejemplo: «Agrega controlador con histéresis», «Corrige dirección de sonda del tanque»)
- 🔧 Incluir la URL del repo en las diapositivas

## Presentación (5 %)
- ✅ Diapositivas base: `docs/Presentacion_Avance3.pptx` → 📝 agregar fotos, capturas del dashboard y renders
- ✅ Guion y preguntas probables: `docs/guion_presentacion.md`
- 🔧 Demo probada **3 veces el día anterior**; roles asignados; 8–10 min

## Excepciones permitidas (no obligatorias en el Avance 3)
Informe final · datos experimentales de las pruebas definitivas · análisis de resultados y conclusiones.
