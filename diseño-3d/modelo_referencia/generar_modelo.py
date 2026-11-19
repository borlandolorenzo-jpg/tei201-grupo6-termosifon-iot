"""
Modelo 3D de REFERENCIA del encapsulado del controlador (CadQuery).

Genera, a partir de los parámetros de diseño-3d/README.md (sección 3):
  - base.step / tapa.step / ensamble_completo.step (importables en Fusion 360)
  - base.stl / tapa.stl (impresión 3D de prueba)
  - componentes.csv (posiciones y volúmenes de cada componente)

IMPORTANTE: es un punto de partida para el gemelo digital. Las medidas son nominales
(hojas de datos / tabla del README). Hay que medir cada pieza real con pie de metro,
corregir los parámetros y rehacer el modelo paramétrico en Fusion 360 (.f3z).

Uso:  python3 generar_modelo.py        (requiere:  pip install cadquery)
Ejes: X = ancho, Y = largo, Z = alto. Origen: esquina interior inferior (sobre el piso = z 2.5).
"""
import csv
import cadquery as cq

# ------------------------- Parámetros (mm) -------------------------
pared = 2.5            # espesor de pared, piso y tapa
holgura = 1.0
int_x, int_y, int_z = 150.0, 90.0, 32.0     # cavidad interior
tornillo_d, agujero_tapa_d = 3.0, 3.4
poste_d, poste_pre_d = 8.0, 2.5             # poste de tornillo de la tapa / agujero guía
placa_x, placa_y, placa_z = 90.0, 70.0, 1.6 # perfboard
sep_h, sep_d = 6.0, 6.0                     # separadores M3
placa_x0, placa_y0 = 9.0, 10.0              # esquina de la perfboard (coords interiores)
div_x = 102.0                               # pared divisoria del compartimiento del servo
div_t = 2.0
EXT_X, EXT_Y = int_x + 2 * pared, int_y + 2 * pared
EXT_Z = int_z + 2 * pared

# z de referencia (z = 0 es la cara inferior de la base)
Z_PISO = pared
Z_PLACA_TOP = Z_PISO + sep_h + placa_z      # 10.1
Z_TAPA = Z_PISO + int_z                     # cara inferior de la tapa (34.5)

def box(x0, y0, z0, dx, dy, dz):
    """Caja con esquina mínima (x0,y0,z0) en coordenadas interiores (x,y) y z absoluta."""
    return cq.Workplane("XY").box(dx, dy, dz, centered=False).translate((x0, y0, z0))

def cyl(cx, cy, z0, d, h):
    return cq.Workplane("XY").circle(d / 2).extrude(h).translate((cx, cy, z0))

# ------------------------- Base -------------------------
base = box(-pared, -pared, 0, EXT_X, EXT_Y, Z_TAPA)                      # bloque exterior
base = base.cut(box(0, 0, Z_PISO, int_x, int_y, int_z + 1))               # cavidad
# postes de tornillo de la tapa (4 esquinas) con agujero guía
poste_pos = [(5, 5), (int_x - 5, 5), (5, int_y - 5), (int_x - 5, int_y - 5)]
for (px, py) in poste_pos:
    base = base.union(cyl(px, py, Z_PISO, poste_d, int_z))
    base = base.cut(cyl(px, py, Z_TAPA - 14, poste_pre_d, 14.1))
# separadores de la perfboard (a 4 mm de los bordes)
sep_pos = [(placa_x0 + 4, placa_y0 + 4), (placa_x0 + placa_x - 4, placa_y0 + 4),
           (placa_x0 + 4, placa_y0 + placa_y - 4), (placa_x0 + placa_x - 4, placa_y0 + placa_y - 4)]
for (sx, sy) in sep_pos:
    base = base.union(cyl(sx, sy, Z_PISO, sep_d, sep_h))
    base = base.cut(cyl(sx, sy, Z_PISO + 0.5, 2.5, sep_h))                # agujero para tornillo M3
# pared divisoria del compartimiento del servo, con paso para el cable
base = base.union(box(div_x, 0, Z_PISO, div_t, int_y, int_z))
base = base.cut(box(div_x - 1, 41, Z_PISO + 8, div_t + 2, 8, 6))
# perforaciones
usb_z = Z_PLACA_TOP + 4
base = base.cut(box(-pared - 1, 44 - 6, usb_z - 3.5, pared + 2, 12, 7))   # USB (pared izquierda)
base = base.cut(cq.Workplane("XZ").center(77, Z_PLACA_TOP + 5.5).circle(4.2).extrude(pared + 2)
                .translate((0, 1, 0)))                                     # jack DC (pared frontal y=0)
for cx in (15, 35, 55):                                                    # cables de sondas (pared y=90)
    base = base.cut(cq.Workplane("XZ").center(cx, Z_PLACA_TOP + 4).circle(3.2).extrude(-(pared + 2))
                    .translate((0, int_y - 1, 0)))

# ------------------------- Tapa -------------------------
tapa = box(-pared, -pared, Z_TAPA, EXT_X, EXT_Y, pared)
for (px, py) in poste_pos:
    tapa = tapa.cut(cyl(px, py, Z_TAPA - 1, agujero_tapa_d, pared + 2))
led_pos = [(80, 55), (90, 55)]
for (lx, ly) in led_pos:
    tapa = tapa.cut(cyl(lx, ly, Z_TAPA - 1, 5.2, pared + 2))
# labio interior que centra la tapa en la caja
lip = box(0.2, 0.2, Z_TAPA - 2, int_x - 0.4, int_y - 0.4, 2).cut(box(2.2, 2.2, Z_TAPA - 3, int_x - 4.4, int_y - 4.4, 5))
for (px, py) in poste_pos:
    lip = lip.cut(cyl(px, py, Z_TAPA - 3, poste_d + 0.6, 5))
tapa = tapa.union(lip)
for (px, py) in poste_pos:
    tapa = tapa.cut(cyl(px, py, Z_TAPA - 3, agujero_tapa_d, pared + 4))

# ------------------------- Componentes (gemelo) -------------------------
comp = {}   # nombre -> (solid, color rgb, dimensiones)
def add(name, solid, color, dims):
    comp[name] = (solid, color, dims)

add("Perfboard 90x70x1.6", box(placa_x0, placa_y0, Z_PISO + sep_h, placa_x, placa_y, placa_z), (0.1, 0.5, 0.25), (placa_x, placa_y, placa_z))
add("ESP32 DevKit V1 (con zocalos)", box(12, 30, Z_PLACA_TOP, 52, 28, 12), (0.15, 0.15, 0.2), (52, 28, 12))
for i, cx in enumerate((15, 35, 55)):
    add(f"Bornera sonda J{i+2}", box(cx - 8, 68, Z_PLACA_TOP, 16, 8, 10), (0.2, 0.45, 0.8), (16, 8, 10))
add("Jack DC 5.5x2.1", box(70, 10, Z_PLACA_TOP, 14, 12, 11), (0.1, 0.1, 0.1), (14, 12, 11))
add("Bornera servo J5", box(90, 38, Z_PLACA_TOP, 8, 16, 8), (0.2, 0.45, 0.8), (8, 16, 8))
add("Condensador 470uF", cyl(93, 24, Z_PLACA_TOP, 8, 12), (0.1, 0.2, 0.6), (8, 8, 12))
add("LED verde 5 mm", cyl(80, 55, Z_PLACA_TOP + 14, 5, 9), (0.1, 0.8, 0.2), (5, 5, 9))
add("LED rojo 5 mm", cyl(90, 55, Z_PLACA_TOP + 14, 5, 9), (0.9, 0.1, 0.1), (5, 5, 9))
add("Servo SG90 (cuerpo)", box(110, 38, Z_PISO, 23, 12.5, 22.7), (0.2, 0.3, 0.7), (23, 12.5, 22.7))
add("Servo SG90 (orejas)", box(105.25, 38, Z_PISO + 15, 32.5, 12.5, 2), (0.2, 0.3, 0.7), (32.5, 12.5, 2))
for k, (px, py) in enumerate(poste_pos):
    add(f"Tornillo M3x8 tapa {k+1}", cyl(px, py, Z_TAPA - 8, tornillo_d, 8 + pared).union(cyl(px, py, Z_TAPA + pared, 5.5, 1.5)), (0.7, 0.7, 0.75), (tornillo_d, tornillo_d, 8 + pared))
for k, (sx, sy) in enumerate(sep_pos):
    add(f"Tornillo M3x8 perfboard {k+1}", cyl(sx, sy, Z_PLACA_TOP, 5.5, 1.5).union(cyl(sx, sy, Z_PISO + 0.5, tornillo_d, 7.1 + 1.5 + 0.0)), (0.7, 0.7, 0.75), (tornillo_d, tornillo_d, 8))

# ------------------------- Verificación de interferencias -------------------------
def inter(a, b):
    try:
        v = a.intersect(b).val().Volume()
    except Exception:
        v = 0.0
    return v
fixed = {"base": base, "tapa": tapa}
problemas = []
names = list(comp)
for n in names:
    s = comp[n][0]
    for fn, fs in fixed.items():
        v = inter(s, fs)
        if v > 0.5 and not n.startswith("Tornillo") and not n.startswith("LED"):
            problemas.append((n, fn, round(v, 1)))
for i in range(len(names)):
    for j in range(i + 1, len(names)):
        a, b = names[i], names[j]
        if a.startswith("Tornillo") or b.startswith("Tornillo"):
            continue
        if a.startswith("Perfboard") or b.startswith("Perfboard"):
            continue
        if a.startswith("Servo SG90") and b.startswith("Servo SG90"):
            continue                      # cuerpo y orejas son la misma pieza
        v = inter(comp[a][0], comp[b][0])
        if v > 0.5:
            problemas.append((a, b, round(v, 1)))
print("Interferencias detectadas:", problemas if problemas else "ninguna")

# ------------------------- Exportación -------------------------
cq.exporters.export(base, "base.step"); cq.exporters.export(tapa, "tapa.step")
cq.exporters.export(base, "base.stl", tolerance=0.05); cq.exporters.export(tapa, "tapa.stl", tolerance=0.05)
asm = cq.Assembly(name="controlador_termosifon")
asm.add(base, name="base", color=cq.Color(0.85, 0.85, 0.85))
asm.add(tapa, name="tapa", color=cq.Color(0.75, 0.82, 0.85))
for n, (s, c, d) in comp.items():
    asm.add(s, name=n.replace(" ", "_"), color=cq.Color(*c))
asm.save("ensamble_completo.step")

with open("componentes.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["componente", "ancho_x_mm", "largo_y_mm", "alto_z_mm", "volumen_mm3"])
    w.writerow(["Base (caja)", EXT_X, EXT_Y, Z_TAPA, round(base.val().Volume(), 1)])
    w.writerow(["Tapa", EXT_X, EXT_Y, pared + 2, round(tapa.val().Volume(), 1)])
    for n, (s, c, d) in comp.items():
        w.writerow([n, *d, round(s.val().Volume(), 1)])
for nm, sol in (("base", base), ("tapa", tapa)):
    print(nm, "válida:", sol.val().isValid(), "· sólidos:", len(sol.solids().vals()))
print("Exterior: %.1f x %.1f x %.1f mm" % (EXT_X, EXT_Y, EXT_Z))
print("Volumen base: %.0f mm3 · tapa: %.0f mm3" % (base.val().Volume(), tapa.val().Volume()))
