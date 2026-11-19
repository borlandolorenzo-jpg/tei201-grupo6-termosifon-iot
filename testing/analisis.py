#!/usr/bin/env python3
"""
analisis.py — Tratamiento de datos del protocolo experimental (testing/protocolo_pruebas.md).

Uso (desde la raíz del repositorio):
  python testing/analisis.py calibracion testing/datos/P1_calibracion.csv
  python testing/analisis.py control     testing/datos/P2_registro.csv [--dt-on 5 --dt-off 2]
  python testing/analisis.py entrega     testing/datos/P3_registro.csv [--periodo 10]
  python testing/analisis.py ab --a A1.csv A2.csv A3.csv --b B1.csv B2.csv B3.csv
  python testing/analisis.py diurno      testing/datos/P6_registro.csv [--objetivo 45]

Los CSV de registro son los que exporta el dashboard (botón "Exportar CSV"):
  ts_epoch,ts_iso_utc,t_col_c,t_tank_c,t_amb_c,valvula_abierta,falla,rssi_dbm,cierres
El CSV de calibración se llena a mano con la plantilla testing/datos/plantilla_P1_calibracion.csv:
  punto,t_ref_c,sensor,t_medida_c

Los resultados (tablas y gráficos PNG) quedan en testing/resultados/.
Requiere: pandas, numpy, matplotlib.
"""
import argparse
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "resultados")
WH_PER_L_K = 1.163          # calor específico del agua [Wh/(L·K)]
MAX_GAP_S = 60              # huecos mayores no se integran (igual que el dashboard)


def _out(name):
    os.makedirs(OUT, exist_ok=True)
    return os.path.join(OUT, name)


def _read_registro(path):
    df = pd.read_csv(path)
    need = {"ts_epoch", "t_col_c", "t_tank_c", "t_amb_c", "valvula_abierta"}
    if not need.issubset(df.columns):
        sys.exit(f"{path}: faltan columnas {sorted(need - set(df.columns))}")
    df = df.sort_values("ts_epoch").drop_duplicates("ts_epoch").reset_index(drop=True)
    df["t"] = pd.to_datetime(df["ts_epoch"], unit="s", utc=True).dt.tz_convert("America/Santiago")
    df["dT"] = df["t_col_c"] - df["t_tank_c"]
    df["dt_s"] = df["ts_epoch"].diff().shift(-1)    # duración del intervalo que parte en cada muestra
    return df


# ------------------------------------------------------------------ P1
def cmd_calibracion(a):
    df = pd.read_csv(a.csv)
    df["error"] = df["t_medida_c"] - df["t_ref_c"]
    g = df.groupby(["sensor", "punto"]).agg(
        t_ref=("t_ref_c", "mean"), n=("error", "size"), error_medio=("error", "mean"),
        desv_est=("error", "std"), error_max_abs=("error", lambda x: x.abs().max()))
    g["u_tipoA"] = g["desv_est"] / np.sqrt(g["n"])
    g["cumple_0.5C"] = g["error_medio"].abs() <= 0.5
    print("\n== P1 · Error de cada sonda por punto de temperatura ==")
    print(g.round(3).to_string())

    off = df.groupby("sensor")["error"].mean()
    print("\n== Offset sugerido por sonda (restar a la lectura) ==")
    print(off.round(3).to_string())

    # error de ΔT entre sondas del mismo baño (peor caso): máx. diferencia entre errores medios por punto
    piv = g["error_medio"].unstack("sensor")
    spread = (piv.max(axis=1) - piv.min(axis=1)).max()
    print(f"\nMáx. diferencia de error entre sondas en el mismo punto: {spread:.3f} K (criterio ≤ 0.5 K)")

    df["error_corr"] = df["error"] - df["sensor"].map(off)
    resid = df.groupby("sensor")["error_corr"].apply(lambda x: x.abs().max())
    print("\nError máx. absoluto tras corregir offset:")
    print(resid.round(3).to_string())

    g.round(4).to_csv(_out("P1_error_por_punto.csv"))
    fig, ax = plt.subplots(figsize=(7, 4))
    for s, d in g.reset_index().groupby("sensor"):
        ax.errorbar(d["t_ref"], d["error_medio"], yerr=d["desv_est"], marker="o", capsize=3, label=s)
    ax.axhspan(-0.5, 0.5, color="green", alpha=0.08, label="±0.5 °C (fabricante)")
    ax.axhline(0, color="k", lw=0.8)
    ax.set_xlabel("Temperatura de referencia [°C]"); ax.set_ylabel("Error medio (sonda − referencia) [K]")
    ax.set_title("P1 · Error de las sondas DS18B20"); ax.legend(); fig.tight_layout()
    fig.savefig(_out("P1_error_vs_referencia.png"), dpi=150)
    ok = bool((g["error_medio"].abs() <= 0.5).all() and spread <= 0.5)
    print("\nRESULTADO P1:", "CUMPLE" if ok else "NO CUMPLE (ver tablas)")


# ------------------------------------------------------------------ P2
def cmd_control(a):
    df = _read_registro(a.csv)
    v = df["valvula_abierta"].astype(int)
    falla = df["falla"].fillna(0).astype(int) if "falla" in df else pd.Series(0, index=df.index)
    chg = v.diff().fillna(0) != 0
    tr = df[chg].copy()
    tr["evento"] = np.where(v[chg] == 1, "ABRE", "CIERRA")
    # La decisión se toma con las temperaturas de la misma muestra
    def coherente(r):
        if r["evento"] == "ABRE":
            return (r["dT"] >= a.dt_on) or (int(r.get("falla", 0)) & 3 != 0)
        return r["dT"] <= a.dt_off
    tr["falla"] = falla[chg]
    tr["coherente"] = tr.apply(coherente, axis=1) if len(tr) else []
    print("\n== P2 · Transiciones de la válvula ==")
    cols = ["t", "evento", "t_col_c", "t_tank_c", "dT", "falla", "coherente"]
    print(tr[cols].round({"t_col_c": 2, "t_tank_c": 2, "dT": 2}).to_string(index=False) if len(tr) else "(sin transiciones)")
    n = len(tr)
    pct = 100 * tr["coherente"].mean() if n else float("nan")
    # chattering: más de 2 transiciones en 10 min
    t_s = tr["ts_epoch"].to_numpy()
    chatter = sum(1 for i in range(len(t_s) - 2) if t_s[i + 2] - t_s[i] < 600)
    print(f"\nTransiciones: {n} · coherentes con las reglas: {pct:.0f} % (criterio 100 %)")
    print(f"Ventanas con >2 transiciones en 10 min (chattering): {chatter} (criterio 0)")
    in_band = df[(df["dT"] > a.dt_off) & (df["dT"] < a.dt_on)]
    print(f"Muestras dentro de la banda muerta ({a.dt_off}–{a.dt_on} K): {len(in_band)}")
    fig, ax = plt.subplots(2, 1, figsize=(8, 5), sharex=True)
    ax[0].plot(df["t"], df["dT"], label="ΔT"); ax[0].axhline(a.dt_on, ls="--", c="g", label="apertura")
    ax[0].axhline(a.dt_off, ls="--", c="orange", label="cierre"); ax[0].set_ylabel("ΔT [K]"); ax[0].legend()
    ax[1].step(df["t"], v, where="post"); ax[1].set_ylabel("Válvula (1=abierta)"); ax[1].set_xlabel("Hora local")
    fig.suptitle("P2 · Decisión del controlador"); fig.tight_layout(); fig.savefig(_out("P2_control.png"), dpi=150)
    tr.to_csv(_out("P2_transiciones.csv"), index=False)
    print("RESULTADO P2:", "CUMPLE" if (n == 0 or (pct == 100 and chatter == 0)) else "NO CUMPLE")


# ------------------------------------------------------------------ P3
def cmd_entrega(a):
    df = _read_registro(a.csv)
    dur = df["ts_epoch"].iloc[-1] - df["ts_epoch"].iloc[0]
    esperadas = int(dur // a.periodo) + 1
    gaps = df["ts_epoch"].diff().dropna()
    tasa = 100 * len(df) / esperadas
    print("\n== P3 · Entrega de datos ==")
    print(f"Duración: {dur/60:.1f} min · muestras esperadas: {esperadas} · recibidas: {len(df)} · tasa: {tasa:.1f} %")
    print(f"Mayor hueco entre muestras: {gaps.max():.0f} s · huecos > {2*a.periodo} s: {(gaps > 2*a.periodo).sum()}")
    sin_dato = df[["t_col_c", "t_tank_c", "t_amb_c"]].isna().sum()
    print("Lecturas inválidas (vacías) por sonda:\n" + sin_dato.to_string())
    print("RESULTADO P3 (criterio tasa ≥ 98 %):", "CUMPLE" if tasa >= 98 else "NO CUMPLE")


# ------------------------------------------------------------------ P5
def _perdida(path):
    df = _read_registro(path)
    t0, tf = df["t_tank_c"].dropna().iloc[0], df["t_tank_c"].dropna().iloc[-1]
    amb = df["t_amb_c"].mean()
    horas = (df["ts_epoch"].iloc[-1] - df["ts_epoch"].iloc[0]) / 3600
    perdida = t0 - tf
    norm = perdida / (t0 - amb) if t0 - amb > 1 else float("nan")   # fracción del salto inicial perdida
    return dict(archivo=os.path.basename(path), horas=horas, T0=t0, Tf=tf, T_amb_media=amb,
                perdida_K=perdida, perdida_norm=norm)


def cmd_ab(a):
    A = pd.DataFrame([_perdida(p) for p in a.a]); B = pd.DataFrame([_perdida(p) for p in a.b])
    print("\n== P5 · Ensayo nocturno A (con válvula) ==\n" + A.round(3).to_string(index=False))
    print("\n== P5 · Ensayo nocturno B (sin válvula) ==\n" + B.round(3).to_string(index=False))
    ma, mb = A["perdida_norm"].mean(), B["perdida_norm"].mean()
    red = 100 * (1 - ma / mb)
    print(f"\nPérdida normalizada media: A = {ma:.3f}  B = {mb:.3f}")
    print(f"Reducción de la pérdida nocturna con válvula: {red:.1f} %  (criterio propuesto ≥ 25 %)")
    sa, sb = A["perdida_norm"].std(ddof=1), B["perdida_norm"].std(ddof=1)
    print(f"Dispersión entre noches: s_A = {sa:.3f}, s_B = {sb:.3f} (n_A={len(A)}, n_B={len(B)})")
    # energía perdida de referencia
    if a.litros:
        eA = a.litros * WH_PER_L_K * A["perdida_K"].mean(); eB = a.litros * WH_PER_L_K * B["perdida_K"].mean()
        print(f"Energía perdida media ({a.litros:g} L): A = {eA:.0f} Wh · B = {eB:.0f} Wh")
    fig, ax = plt.subplots(figsize=(5.5, 4))
    ax.bar(["A: con válvula", "B: sin válvula"], [ma, mb], yerr=[sa, sb], capsize=5, color=["#0b6e6e", "#d9531e"])
    ax.set_ylabel("Pérdida normalizada (T0−Tf)/(T0−T_amb)"); ax.set_title(f"P5 · Reducción: {red:.0f} %")
    fig.tight_layout(); fig.savefig(_out("P5_AB.png"), dpi=150)
    pd.concat([A.assign(config="A"), B.assign(config="B")]).to_csv(_out("P5_resumen.csv"), index=False)
    print("RESULTADO P5:", "CUMPLE" if red >= 25 else "NO CUMPLE")


# ------------------------------------------------------------------ P6
def cmd_diurno(a):
    df = _read_registro(a.csv)
    ok = df["dt_s"].between(0, MAX_GAP_S)
    collecting = df.loc[ok & (df["valvula_abierta"] == 1) & (df["dT"] >= 2), "dt_s"].sum() / 3600
    leak = df.loc[ok & (df["valvula_abierta"] == 1) & (df["dT"] < -1), "dt_s"].sum() / 3600
    closures = int(((df["valvula_abierta"].shift(1) == 1) & (df["valvula_abierta"] == 0)).sum())
    tmax = df["t_tank_c"].max()
    idx = df.index[df["t_tank_c"] >= a.objetivo]
    t_obj = df.loc[idx[0], "t"] if len(idx) else None
    print("\n== P6 · Desempeño diurno ==")
    print(f"T máx. tanque: {tmax:.1f} °C · objetivo {a.objetivo:g} °C alcanzado: {'sí, a las ' + t_obj.strftime('%H:%M') if t_obj is not None else 'NO'}")
    print(f"Horas captando calor: {collecting:.2f} h · flujo inverso con válvula abierta: {leak:.2f} h · cierres: {closures}")
    fig, ax = plt.subplots(figsize=(8, 4))
    for c, l in [("t_col_c", "Colector"), ("t_tank_c", "Tanque"), ("t_amb_c", "Ambiente")]:
        ax.plot(df["t"], df[c], label=l)
    ax.axhline(a.objetivo, ls="--", c="k", lw=0.8, label="objetivo"); ax.legend(); ax.set_ylabel("°C"); ax.set_xlabel("Hora local")
    fig.tight_layout(); fig.savefig(_out("P6_diurno.png"), dpi=150)
    print("RESULTADO P6:", "CUMPLE" if tmax >= a.objetivo else "NO CUMPLE")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = ap.add_subparsers(dest="cmd", required=True)
    p = sp.add_parser("calibracion"); p.add_argument("csv"); p.set_defaults(f=cmd_calibracion)
    p = sp.add_parser("control"); p.add_argument("csv"); p.add_argument("--dt-on", type=float, default=5.0)
    p.add_argument("--dt-off", type=float, default=2.0); p.set_defaults(f=cmd_control)
    p = sp.add_parser("entrega"); p.add_argument("csv"); p.add_argument("--periodo", type=float, default=10.0); p.set_defaults(f=cmd_entrega)
    p = sp.add_parser("ab"); p.add_argument("--a", nargs="+", required=True); p.add_argument("--b", nargs="+", required=True)
    p.add_argument("--litros", type=float, default=None); p.set_defaults(f=cmd_ab)
    p = sp.add_parser("diurno"); p.add_argument("csv"); p.add_argument("--objetivo", type=float, default=45.0); p.set_defaults(f=cmd_diurno)
    a = ap.parse_args()
    a.f(a)


if __name__ == "__main__":
    main()
