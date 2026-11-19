"""Genera planos/plano_referencia.svg (A3, escala 1:1, proyección ISO 1er diedro) del encapsulado.
Usa los mismos parámetros que generar_modelo.py. Convertir a PDF con un navegador (Imprimir -> PDF) o Inkscape."""
P = dict(pared=2.5, ix=150.0, iy=90.0, iz=32.0)
pared, ix, iy, iz = P["pared"], P["ix"], P["iy"], P["iz"]
EX, EY, EZ = ix + 2*pared, iy + 2*pared, iz + 2*pared
ZT = pared + iz            # cara inferior de la tapa
ZP = pared + 6 + 1.6       # cara superior de la perfboard
o = []
a = o.append
def line(x1,y1,x2,y2,w=0.35,c="#111",dash=None):
    d = f' stroke-dasharray="{dash}"' if dash else ""
    a(f'<line x1="{x1:.2f}" y1="{y1:.2f}" x2="{x2:.2f}" y2="{y2:.2f}" stroke="{c}" stroke-width="{w}"{d}/>')
def rect(x,y,w,h,fill="none",sw=0.35,c="#111",dash=None):
    d = f' stroke-dasharray="{dash}"' if dash else ""
    a(f'<rect x="{x:.2f}" y="{y:.2f}" width="{w:.2f}" height="{h:.2f}" fill="{fill}" stroke="{c}" stroke-width="{sw}"{d}/>')
def circ(x,y,r,fill="none",sw=0.35,dash=None):
    d = f' stroke-dasharray="{dash}"' if dash else ""
    a(f'<circle cx="{x:.2f}" cy="{y:.2f}" r="{r:.2f}" fill="{fill}" stroke="#111" stroke-width="{sw}"{d}/>')
def txt(x,y,s,size=3.2,anchor="start",w="400",c="#111",rot=None):
    t = f' transform="rotate({rot} {x} {y})"' if rot else ""
    a(f'<text x="{x:.2f}" y="{y:.2f}" font-size="{size}" text-anchor="{anchor}" font-weight="{w}" fill="{c}"{t}>{s}</text>')
def dimh(x1,x2,y,label,off=0,ext=None):
    yy = y + off
    for x in (x1,x2): line(x,y,x,yy+ (1.5 if off>=0 else -1.5),0.18,"#444")
    line(x1,yy,x2,yy,0.25,"#222"); a(f'<path d="M{x1},{yy} l3,-0.9 v1.8z M{x2},{yy} l-3,-0.9 v1.8z" fill="#222"/>')
    txt((x1+x2)/2, yy-1.2, label, 3.2, "middle")
def dimv(y1,y2,x,label,off=0):
    xx = x + off
    for y in (y1,y2): line(x,y,xx+(1.5 if off>=0 else -1.5),y,0.18,"#444")
    line(xx,y1,xx,y2,0.25,"#222"); a(f'<path d="M{xx},{y1} l-0.9,3 h1.8z M{xx},{y2} l-0.9,-3 h1.8z" fill="#222"/>')
    txt(xx-1.2,(y1+y2)/2,label,3.2,"middle",rot=-90)
def hatch(x,y,w,h):
    a(f'<rect x="{x:.2f}" y="{y:.2f}" width="{w:.2f}" height="{h:.2f}" fill="url(#h)" stroke="#111" stroke-width="0.5"/>')

W, H = 420, 297
a(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}mm" height="{H}mm" viewBox="0 0 {W} {H}" font-family="Helvetica, Arial, sans-serif">')
a('<defs><pattern id="h" width="2" height="2" patternUnits="userSpaceOnUse" patternTransform="rotate(45)"><line x1="0" y1="0" x2="0" y2="2" stroke="#555" stroke-width="0.3"/></pattern></defs>')
a(f'<rect width="{W}" height="{H}" fill="#fff"/>'); rect(8,8,W-16,H-16,sw=0.7)

# ---------------- VISTA FRONTAL (desde y=0), origen exterior x0=28, suelo en y=72 ----------------
fx0, fz0 = 28, 72
X = lambda x: fx0 + x + pared            # x interior -> mm en hoja
Zf = lambda z: fz0 - z
txt(fx0, 18, "VISTA FRONTAL", 4, w="700")
rect(fx0, Zf(EZ), EX, EZ, "#f2f2f2", 0.6)
line(fx0, Zf(ZT), fx0+EX, Zf(ZT), 0.35)                       # unión base/tapa
circ(X(77), Zf(ZP+5.5), 4.2, "#fff", 0.5)                      # jack DC Ø8.4
txt(X(77)+6, Zf(ZP+5.5)+1, "Ø8.4 (jack DC)", 2.8)
dimh(fx0, fx0+EX, Zf(0), "155", off=7); dimv(Zf(EZ), Zf(0), fx0, "37", off=-7)
txt(fx0+EX/2, Zf(ZT)-1.3, "tapa", 2.6, "middle", c="#555")
# ---------------- PLANTA (tapa retirada) ----------------
px0, py0 = 28, 112                                          # esquina superior izquierda de la planta
Xp = lambda x: px0 + x + pared
Yp = lambda y: py0 + EY - (y + pared)                       # y interior: frente (y=0) abajo
txt(px0, 105, "PLANTA (tapa retirada)", 4, w="700")
rect(px0, py0, EX, EY, "#f2f2f2", 0.6); rect(Xp(0), Yp(iy), ix, iy, "#fff", 0.4)
for (cx, cy) in [(5,5),(ix-5,5),(5,iy-5),(ix-5,iy-5)]:
    circ(Xp(cx), Yp(cy), 4, "#e6e6e6", 0.35); circ(Xp(cx), Yp(cy), 1.25, "#fff", 0.3)
rect(Xp(102), Yp(iy), 2, iy, "#e6e6e6", 0.35)                  # pared divisoria
rect(Xp(9), Yp(80), 90, 70, "none", 0.35, "#1a7f4b", "3 1.5")  # perfboard
for (sx, sy) in [(13,14),(95,14),(13,76),(95,76)]: circ(Xp(sx), Yp(sy), 3, "none", 0.3)
rect(Xp(12), Yp(58), 52, 28, "#d9dbe3", 0.35)
txt(Xp(38), Yp(44)+1, "ESP32 DevKit V1", 2.8, "middle")
for cx in (15,35,55): rect(Xp(cx-8), Yp(76), 16, 8, "#cfe0f2", 0.3)
rect(Xp(70), Yp(22), 14, 12, "#ddd", 0.3); txt(Xp(77), Yp(16)+1, "jack", 2.4, "middle")
rect(Xp(90), Yp(54), 8, 16, "#cfe0f2", 0.3); circ(Xp(93), Yp(24), 4, "#cdd7ef", 0.3)
circ(Xp(80), Yp(55), 2.5, "#bfe8c9", 0.3); circ(Xp(90), Yp(55), 2.5, "#f2bdbd", 0.3)
rect(Xp(110), Yp(50.5), 23, 12.5, "#ccd5f0", 0.4); rect(Xp(105.25), Yp(50.5), 32.5, 12.5, "none", 0.3, "#111", "2 1")
txt(Xp(121.5), Yp(44)+1, "servo SG90", 2.6, "middle")
rect(Xp(-pared-0.5), Yp(50), pared+0.5, 12, "#fff", 0.4)       # ranura USB
txt(Xp(-pared)+0.5, Yp(32)+4.5, "USB", 2.6, "start", c="#555")
for cx in (15,35,55): rect(Xp(cx)-3.2, Yp(iy+pared)+0.0, 6.4, pared, "#fff", 0.3)
txt(Xp(35), Yp(iy+pared)-1.5, "salida cables sondas Ø6.4 (×3)", 2.6, "middle")
dimh(px0, px0+EX, py0+EY, "155", off=7); dimv(py0, py0+EY, px0, "95", off=-7)
dimh(Xp(0), Xp(ix), py0, "150 (interior)", off=-6)
dimh(Xp(9), Xp(99), Yp(80), "90", off=-4); dimv(Yp(80), Yp(10), Xp(9), "70", off=-5)
dimh(Xp(0), Xp(102), py0+EY, "102", off=14)
line(px0-4, Yp(44), px0+EX+4, Yp(44), 0.2, "#c00", "6 1.5 1 1.5"); txt(px0+EX+5, Yp(44)+1.2, "A", 3.5, w="700", c="#c00")
txt(px0-6.5, Yp(44)+1.2, "A", 3.5, w="700", c="#c00")
# ---------------- VISTA LATERAL IZQUIERDA ----------------
lx0 = 235
Xl = lambda y: lx0 + EY - (y + pared)
txt(lx0, 18, "VISTA LATERAL IZQUIERDA", 4, w="700")
rect(lx0, Zf(EZ), EY, EZ, "#f2f2f2", 0.6); line(lx0, Zf(ZT), lx0+EY, Zf(ZT), 0.35)
rect(Xl(50), Zf(ZP+4+3.5), 12, 7, "#fff", 0.5); txt(Xl(50)-14, Zf(ZP+4)+1, "USB 12×7", 2.8)
dimh(lx0, lx0+EY, Zf(0), "95", off=7)
# ---------------- CORTE A-A ----------------
cx0, cy_base = 235, 215
Xc = lambda x: cx0 + x + pared
Zc = lambda z: cy_base - z
txt(cx0, 135, "CORTE A-A (y = 44 mm)", 4, w="700")
cy_base = 188; Zc = lambda z: cy_base - z
hatch(cx0, Zc(pared), EX, pared)                                 # piso
hatch(cx0, Zc(ZT), pared, ZT-pared+0)                            # pared izq (con ranura USB)
a(f'<rect x="{cx0}" y="{Zc(17.6):.2f}" width="{pared}" height="7" fill="#fff"/>')
hatch(Xc(ix), Zc(ZT), pared, ZT)                                 # pared der
hatch(Xc(102), Zc(ZT), 2, ZT-pared)
a(f'<rect x="{Xc(102)-0.1:.2f}" y="{Zc(16.5):.2f}" width="2.2" height="6" fill="#fff"/>')
hatch(cx0, Zc(EZ), EX, pared)                                    # tapa
hatch(Xc(0.2), Zc(ZT), 2, 2); hatch(Xc(ix-2.2), Zc(ZT), 2, 2)    # labio
hatch(Xc(9), Zc(ZP), 90, 1.6)                                    # perfboard
rect(Xc(12), Zc(ZP+12), 52, 12, "#d9dbe3", 0.4); rect(Xc(90), Zc(ZP+8), 8, 8, "#cfe0f2", 0.4)
rect(Xc(110), Zc(pared+22.7), 23, 22.7, "#ccd5f0", 0.4); rect(Xc(105.25), Zc(pared+17), 32.5, 2, "#ccd5f0", 0.4)
txt(Xc(38), Zc(ZP+6)+1, "ESP32", 2.6, "middle"); txt(Xc(121.5), Zc(pared+11), "servo", 2.6, "middle")
dimv(Zc(EZ), Zc(0), cx0+EX, "37", off=7); dimv(Zc(ZT), Zc(pared), Xc(ix)+pared, "32 (int.)", off=14)
dimv(Zc(ZP), Zc(pared), Xc(0), "8.1", off=-5)
# ---------------- NOTAS Y CAJETÍN ----------------
nx, ny = 28, 238
txt(nx, ny, "NOTAS", 3.6, w="700")
for i, t in enumerate(["1. Unidades: milímetros. Escala 1:1. Proyección ISO (1er diedro).",
                       "2. Tolerancia general ±0.2 mm; holguras de impresión 0.2–0.3 mm.",
                       "3. Material: PETG (o PLA para pruebas bajo techo). Espesor de pared 2.5 mm.",
                       "4. Tapa: 4 tornillos M3×8 en postes Ø8 con agujero guía Ø2.5; agujeros pasantes Ø3.4.",
                       "5. Perfboard 90×70×1.6 sobre 4 separadores M3 de 6 mm (retirable).",
                       "6. Plano de REFERENCIA generado de generar_modelo.py con medidas nominales:",
                       "   verificar con pie de metro y reemplazar por el dibujo exportado de Fusion 360."]):
    txt(nx, ny+7+i*5.2, t, 3)
bx, by = 255, 236
rect(bx, by, 150, 52, "none", 0.6)
for yy in (by+13, by+26, by+39): line(bx, yy, bx+150, yy, 0.3)
line(bx+75, by+13, bx+75, by+52, 0.3)
txt(bx+3, by+9, "Controlador termosifón IoT — Encapsulado (base y tapa)", 4.2, w="700")
txt(bx+3, by+21, "TEI 201 · Grupo 6 · UAI", 3.2); txt(bx+78, by+21, "Escala 1:1 · Rev. A", 3.2)
txt(bx+3, by+34, "Dibujó: Lorenzo Borlando", 3.2); txt(bx+78, by+34, "Fecha: 19-11-2026", 3.2)
txt(bx+3, by+47, "Estado: REFERENCIA (nominal)", 3.2, w="700", c="#b3261e"); txt(bx+78, by+47, "Unidades: mm · Hoja 1/1 (A3)", 3.2)
a('</svg>')
open("../planos/plano_referencia.svg", "w", encoding="utf-8").write("\n".join(o))
print("ok")
