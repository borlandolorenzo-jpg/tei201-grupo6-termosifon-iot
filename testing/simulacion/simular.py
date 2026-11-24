"""
simular.py — Simulación del colector termosifón con y sin válvula anti-flujo-inverso.


Qué hace
--------
1. Modela un día de noviembre en Santiago: radiación solar G(t) y temperatura ambiente.
2. Modela el sistema con dos masas térmicas (balance de energía, paso de 10 s):
     colector:  C_c dTc/dt = A·τα·G − U_L·A·(Tc − Ta) − Q_flujo − Q_cielo
     tanque:    C_t dTt/dt = Q_flujo − UA_t·(Tt − Ta)
   Q_flujo = h_dir·(Tc − Tt) si Tc > Tt (termosifón de día)
           = h_inv·(Tc − Tt) si Tc < Tt (flujo inverso nocturno: el tanque se enfría)
   y solo existe si la válvula está abierta.
3. Las sondas se simulan con la resolución del DS18B20 (0.0625 °C) y ruido.
4. El controlador es una copia en Python de firmware/main/control.h (misma lógica y umbrales).
5. Corre dos configuraciones con el MISMO clima:
     A = con válvula (controlador activo)   B = sin válvula (siempre abierta)
6. Escribe los CSV en testing/datos/simulacion/ con el formato del dashboard.

Uso:  python testing/simulacion/simular.py
"""
import csv
import math
import os
import random
from datetime import datetime, timedelta, timezone

# ---------------------------------------------------------------- parámetros físicos (supuestos)
A_COL = 0.3          # área del colector [m²]
TAU_ALPHA = 0.70     # transmitancia × absortancia (vidrio + placa negra)
U_L = 10.0           # coef. de pérdidas del colector [W/m²K]
C_COL = 8_000.0      # capacidad térmica colector + agua interna [J/K]
LITROS = 20.0        # volumen del tanque [L] (igual que dashboard/config.js)
C_TANK = LITROS * 4186.0
UA_TANK = 2.5        # pérdidas del tanque al ambiente [W/K]
H_DIR = 15.0         # conductancia del termosifón directo [W/K]
H_INV = 4.0          # conductancia del flujo inverso nocturno [W/K]
Q_CIELO = 15.0       # enfriamiento radiativo nocturno del colector hacia el cielo [W]
DT = 10              # paso [s] = periodo de muestreo del firmware

# Clima de 4 días (pico de radiación [W/m²], T mín y máx [°C]) — noviembre en Santiago
DIAS = [(980, 12.5, 29.0), (900, 14.0, 27.0), (1000, 13.0, 30.5), (950, 13.5, 28.0)]
AMANECER, ATARDECER = 6.6, 20.8   # horas locales


# ---------------------------------------------------------------- controlador = control.h
class DiffController:
    def __init__(self, dt_on=5.0, dt_off=2.0, tank_max=65.0, tank_resume=60.0,
                 min_dwell_s=60, max_failures=3):
        self.dt_on, self.dt_off = dt_on, dt_off
        self.tank_max, self.tank_resume = tank_max, tank_resume
        self.min_dwell, self.max_failures = min_dwell_s, max_failures
        self.open, self.fault, self.over = True, False, False
        self.ever, self.fails, self.last, self.closures = False, 0, 0, 0

    def update(self, tc, ok_c, tt, ok_t, now):
        self.fails = 0 if (ok_c and ok_t) else min(self.fails + 1, 255)
        self.fault = self.fails >= self.max_failures
        desired, safety = self.open, False
        if self.fault:
            desired, safety = True, True                      # fail-open
        elif self.fails == 0:
            if not self.over and tt >= self.tank_max:
                self.over = True
            elif self.over and tt <= self.tank_resume:
                self.over = False
            if self.over:
                desired, safety = False, True
            else:
                d = tc - tt
                if not self.open and d >= self.dt_on:
                    desired = True
                elif self.open and d <= self.dt_off:
                    desired = False
        if desired != self.open and (safety or not self.ever or now - self.last >= self.min_dwell):
            if self.open and not desired:
                self.closures += 1
            self.open, self.last, self.ever = desired, now, True
        return self.open


# ---------------------------------------------------------------- clima
def clima(h, dia):
    gmax, tmin, tmax = DIAS[dia]
    if AMANECER < h < ATARDECER:
        g = gmax * math.sin(math.pi * (h - AMANECER) / (ATARDECER - AMANECER)) ** 1.3
    else:
        g = 0.0
    # mínima a las 06:30, máxima a las 16:30
    if 6.5 <= h < 16.5:
        ta = tmin + (tmax - tmin) * 0.5 * (1 - math.cos(math.pi * (h - 6.5) / 10.0))
    else:
        ta = tmax - (tmax - tmin) * 0.5 * (1 - math.cos(math.pi * ((h - 16.5) % 24) / 14.0))
    return g, ta


def sonda(t, rng):
    return round((t + rng.gauss(0, 0.05)) / 0.0625) * 0.0625


# ---------------------------------------------------------------- simulación
def simular(con_valvula, inicio, seed=7):
    rng = random.Random(seed)            # misma semilla → mismo ruido en A y B
    ctrl = DiffController()
    tc = tt = 16.0
    filas = []
    n = len(DIAS) * 86400 // DT
    t0 = int(inicio.timestamp())
    for k in range(n):
        ts = t0 + k * DT
        local = inicio + timedelta(seconds=k * DT)
        h = local.hour + local.minute / 60 + local.second / 3600
        dia = min(k * DT // 86400, len(DIAS) - 1)
        g, ta = clima(h, dia)

        # lectura de sondas (con una desconexión de 2 min la 2.ª noche para probar el modo seguro)
        desconectada = (dia == 1 and 23 * 3600 <= (ts - t0) % 86400 < 23 * 3600 + 120)
        rc, rt = sonda(tc, rng), sonda(tt, rng)
        ok_c = not desconectada
        abierta = ctrl.update(rc, ok_c, rt, True, ts) if con_valvula else True
        falla = (1 if not ok_c else 0) if con_valvula else 0

        # física
        q = 0.0
        if abierta:
            q = H_DIR * (tc - tt) if tc > tt else H_INV * (tc - tt)
        q_cielo = Q_CIELO if g == 0 else 0.0
        tc += DT * (A_COL * TAU_ALPHA * g - U_L * A_COL * (tc - ta) - q - q_cielo) / C_COL
        tt += DT * (q - UA_TANK * (tt - ta)) / C_TANK

        filas.append({
            "ts_epoch": ts,
            "ts_iso_utc": datetime.fromtimestamp(ts, timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "t_col_c": "" if not ok_c else f"{rc:.4f}",
            "t_tank_c": f"{rt:.4f}",
            "t_amb_c": f"{ta:.2f}",
            "valvula_abierta": int(abierta),
            "falla": falla,
            "rssi_dbm": -58 - rng.randint(0, 8),
            "cierres": ctrl.closures if con_valvula else 0,
        })
    return filas


def guardar(nombre, filas):
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, nombre), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(filas[0]))
        w.writeheader()
        w.writerows(filas)


def tramo(filas, inicio, h_desde, h_hasta):
    a, b = int((inicio + timedelta(hours=h_desde)).timestamp()), int((inicio + timedelta(hours=h_hasta)).timestamp())
    return [r for r in filas if a <= r["ts_epoch"] < b]


OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "datos", "simulacion")

if __name__ == "__main__":
    santiago = timezone(timedelta(hours=-3))                 # horario de verano de Chile
    inicio = datetime(2026, 11, 19, 0, 0, tzinfo=santiago)   # fecha simbólica de la simulación
    A, B = simular(True, inicio), simular(False, inicio)
    guardar("SIM_A_con_valvula_4dias.csv", A)
    guardar("SIM_B_sin_valvula_4dias.csv", B)
    guardar("SIM_P2_P6_registro_24h.csv", tramo(A, inicio, 24, 48))     # día 2 completo
    for i in range(len(DIAS) - 1):                                      # noches 20:30 → 07:30
        guardar(f"SIM_P5_A_noche{i + 1}.csv", tramo(A, inicio, 24 * i + 20.5, 24 * i + 31.5))
        guardar(f"SIM_P5_B_noche{i + 1}.csv", tramo(B, inicio, 24 * i + 20.5, 24 * i + 31.5))
    print("CSV simulados en", os.path.normpath(OUT))
