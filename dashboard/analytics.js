/*
 * analytics.js — Convierte lecturas crudas en información útil (indicadores y alertas).
 * Sin dependencias del navegador: se puede probar con Node (testing/unit/test_analytics.js).
 *
 * Una "fila" es: { ts (epoch s), tc, tt, ta (°C o null), v (1 abierta / 0 cerrada), f (bits de falla) }
 */
(function (root, factory) {
  if (typeof module === 'object' && module.exports) module.exports = factory();
  else root.Analytics = factory();
})(typeof self !== 'undefined' ? self : this, function () {
  'use strict';

  const CP_WATER_WH_PER_L_K = 1.163; // calor específico del agua: 4186 J/(kg·K) = 1.163 Wh/(kg·K) ≈ por litro
  const MAX_GAP_S = 60;              // intervalos más largos se consideran "sin datos" y no se integran

  const isNum = (x) => typeof x === 'number' && isFinite(x);

  /**
   * opts: { tankLiters, hotTargetC, tankMaxC, offlineAfterS, nowS, dtOn }
   */
  function computeKPIs(rows, opts) {
    const o = Object.assign(
      { tankLiters: 20, hotTargetC: 45, tankMaxC: 65, offlineAfterS: 60, nowS: Math.floor(Date.now() / 1000), dtOn: 5 },
      opts || {}
    );
    const r = { n: rows.length, alerts: [] };
    if (!rows.length) {
      r.alerts.push({ level: 'warn', text: 'Sin datos en el periodo seleccionado.' });
      return r;
    }

    const last = rows[rows.length - 1];
    r.last = last;
    r.ageS = o.nowS - last.ts;
    r.online = r.ageS <= o.offlineAfterS;
    r.deltaT = isNum(last.tc) && isNum(last.tt) ? last.tc - last.tt : null;

    let closures = 0;
    let secProtected = 0;   // válvula cerrada con tanque más caliente que el colector: flujo inverso evitado
    let secLeak = 0;        // válvula abierta con flujo inverso (tanque > colector + 1 K): pérdida pese al control
    let secCollect = 0;     // válvula abierta captando calor (colector > tanque + 2 K)
    let secTotal = 0;
    let tankMax = -Infinity, tankMaxTs = null;
    let firstTank = null, lastTank = null;

    for (let i = 0; i < rows.length; i++) {
      const p = rows[i];
      if (isNum(p.tt)) {
        if (firstTank === null) firstTank = p.tt;
        lastTank = p.tt;
        if (p.tt > tankMax) { tankMax = p.tt; tankMaxTs = p.ts; }
      }
      if (i === 0) continue;
      const q = rows[i - 1];
      const dt = p.ts - q.ts;
      if (dt <= 0 || dt > MAX_GAP_S) continue;   // hueco: no se integra
      secTotal += dt;
      if (q.v === 1 && p.v === 0) closures++;
      if (isNum(q.tc) && isNum(q.tt)) {
        const d = q.tc - q.tt;
        if (q.v === 0 && d < 0) secProtected += dt;
        if (q.v === 1 && d < -1) secLeak += dt;
        if (q.v === 1 && d >= 2) secCollect += dt;
      }
    }

    r.closures = closures;
    r.hoursProtected = secProtected / 3600;
    r.hoursLeak = secLeak / 3600;
    r.hoursCollecting = secCollect / 3600;
    r.hoursTotal = secTotal / 3600;
    r.tankMax = isFinite(tankMax) ? tankMax : null;
    r.tankMaxTs = tankMaxTs;
    // Calor almacenado neto en el tanque durante la ventana (referencial: depende del volumen informado).
    r.storedWh = firstTank !== null ? o.tankLiters * CP_WATER_WH_PER_L_K * (lastTank - firstTank) : null;

    // ---- Alertas ----
    if (!r.online) r.alerts.push({ level: 'bad', text: `Dispositivo sin reportar hace ${Math.round(r.ageS)} s.` });
    if (last.f & 1) r.alerts.push({ level: 'bad', text: 'Falla del sensor del colector. Válvula en modo seguro (abierta).' });
    if (last.f & 2) r.alerts.push({ level: 'bad', text: 'Falla del sensor del tanque. Válvula en modo seguro (abierta).' });
    if (last.f & 4) r.alerts.push({ level: 'warn', text: 'Falla del sensor ambiente (no afecta el control).' });
    if (isNum(last.tt) && last.tt >= o.tankMaxC) r.alerts.push({ level: 'bad', text: `Sobretemperatura en el tanque (${last.tt.toFixed(1)} °C).` });
    else if (isNum(last.tt) && last.tt >= o.hotTargetC) r.alerts.push({ level: 'good', text: `Agua lista para uso: tanque en ${last.tt.toFixed(1)} °C (objetivo ${o.hotTargetC} °C).` });
    if (r.hoursLeak > 0.25) r.alerts.push({ level: 'warn', text: `Flujo inverso con válvula abierta durante ${(r.hoursLeak * 60).toFixed(0)} min: revisar umbrales de control.` });
    return r;
  }

  /** Reduce la cantidad de puntos para graficar (toma 1 de cada k). */
  function downsample(rows, maxPoints) {
    if (rows.length <= maxPoints) return rows;
    const k = Math.ceil(rows.length / maxPoints);
    const out = [];
    for (let i = 0; i < rows.length; i += k) out.push(rows[i]);
    if (out[out.length - 1] !== rows[rows.length - 1]) out.push(rows[rows.length - 1]);
    return out;
  }

  /** CSV compatible con testing/analisis.py (separador coma, hora UTC en epoch y ISO). */
  function toCSV(rows) {
    const head = 'ts_epoch,ts_iso_utc,t_col_c,t_tank_c,t_amb_c,valvula_abierta,falla,rssi_dbm,cierres';
    const fmt = (x) => (isNum(x) ? x.toFixed(2) : '');
    const lines = rows.map((r) =>
      [r.ts, new Date(r.ts * 1000).toISOString(), fmt(r.tc), fmt(r.tt), fmt(r.ta), r.v, r.f || 0, isNum(r.rssi) ? r.rssi : '', isNum(r.cl) ? r.cl : ''].join(',')
    );
    return [head].concat(lines).join('\n');
  }

  /** Datos simulados SOLO para ver el dashboard sin hardware. Nunca usar como evidencia. */
  function demoRows(nowS, hours) {
    const rows = [];
    const step = 10;
    const start = nowS - hours * 3600;
    let tank = 22, valve = 1, lastChange = -1e9;
    for (let t = start; t <= nowS; t += step) {
      const h = ((t % 86400) / 3600 - 3 + 24) % 24;            // hora local aproximada (UTC-3)
      const sun = Math.max(0, Math.sin(((h - 7) / 11) * Math.PI)); // sol entre 7 y 18 h
      const amb = 12 + 10 * Math.max(0, Math.sin(((h - 6) / 16) * Math.PI));
      const col = amb + 45 * sun + (Math.random() - 0.5) * 0.4;
      const d = col - tank;
      if (valve === 0 && d >= 5 && t - lastChange > 60) { valve = 1; lastChange = t; }
      if (valve === 1 && d <= 2 && t - lastChange > 60) { valve = 0; lastChange = t; }
      if (valve === 1) tank += Math.max(-0.02, 0.0008 * d);
      tank -= 0.00005 * (tank - amb);
      rows.push({ ts: t, tc: col, tt: tank + (Math.random() - 0.5) * 0.1, ta: amb, v: valve, f: 0 });
    }
    return rows;
  }

  return { computeKPIs, downsample, toCSV, demoRows, MAX_GAP_S };
});
