// Pruebas de dashboard/analytics.js. Ejecutar:  node testing/unit/test_analytics.js
const assert = require('assert');
const A = require('../../dashboard/analytics.js');

let n = 0;
function t(name, fn) { fn(); n++; console.log('  ok: ' + name); }

const NOW = 1_800_000_000;
const row = (i, tc, tt, v, f = 0) => ({ ts: NOW - 1000 + i * 10, tc, tt, ta: 15, v, f });

t('sin datos genera alerta', () => {
  const k = A.computeKPIs([], { nowS: NOW });
  assert.strictEqual(k.n, 0); assert.ok(k.alerts.length === 1);
});

t('cierres y horas de flujo inverso evitado', () => {
  // 6 muestras abiertas con sol, luego 12 cerradas con tanque más caliente (dT<0), cada 10 s
  const rows = [];
  for (let i = 0; i < 6; i++) rows.push(row(i, 50, 30, 1));
  for (let i = 6; i < 18; i++) rows.push(row(i, 20, 30, 0));
  const k = A.computeKPIs(rows, { nowS: rows[rows.length - 1].ts + 5 });
  assert.strictEqual(k.closures, 1);
  // intervalos con v=0 (muestra previa): i=6..16 => 11 intervalos x 10 s
  assert.ok(Math.abs(k.hoursProtected - (11 * 10) / 3600) < 1e-9);
  // intervalos con v=1 (muestra previa): i=0..5 => 6 intervalos x 10 s
  assert.ok(Math.abs(k.hoursCollecting - (6 * 10) / 3600) < 1e-9);
  assert.strictEqual(k.hoursLeak, 0);
  assert.ok(k.online);
});

t('huecos mayores a 60 s no se integran', () => {
  const rows = [row(0, 20, 30, 0), { ts: NOW + 5000, tc: 20, tt: 30, ta: 15, v: 0, f: 0 }];
  const k = A.computeKPIs(rows, { nowS: rows[1].ts });
  assert.strictEqual(k.hoursProtected, 0);
});

t('alerta de dispositivo sin reportar', () => {
  const k = A.computeKPIs([row(0, 30, 30, 1)], { nowS: NOW + 5000 });
  assert.ok(!k.online);
  assert.ok(k.alerts.some((a) => /sin reportar/.test(a.text)));
});

t('alertas de falla, sobretemperatura y agua lista', () => {
  let k = A.computeKPIs([row(0, 30, 30, 1, 2)], { nowS: row(0).ts });
  assert.ok(k.alerts.some((a) => a.level === 'bad' && /tanque/.test(a.text)));
  k = A.computeKPIs([row(0, 80, 66, 0)], { nowS: row(0).ts });
  assert.ok(k.alerts.some((a) => /Sobretemperatura/.test(a.text)));
  k = A.computeKPIs([row(0, 60, 47, 1)], { nowS: row(0).ts });
  assert.ok(k.alerts.some((a) => a.level === 'good' && /lista/.test(a.text)));
});

t('calor almacenado: 20 L y +10 K = 0.2326 kWh', () => {
  const rows = [row(0, 50, 30, 1), row(1, 50, 40, 1)];
  const k = A.computeKPIs(rows, { nowS: rows[1].ts, tankLiters: 20 });
  assert.ok(Math.abs(k.storedWh - 232.6) < 1e-6);
});

t('downsample respeta el máximo y conserva el último punto', () => {
  const rows = Array.from({ length: 5000 }, (_, i) => row(i, 20, 20, 1));
  const out = A.downsample(rows, 1200);
  assert.ok(out.length <= 1201 + 1);
  assert.strictEqual(out[out.length - 1], rows[rows.length - 1]);
});

t('CSV tiene encabezado y una línea por fila', () => {
  const csv = A.toCSV([row(0, 30.123, 25, 1), row(1, null, 25, 0, 1)]);
  const lines = csv.split('\n');
  assert.strictEqual(lines.length, 3);
  assert.ok(lines[0].startsWith('ts_epoch,'));
  assert.ok(lines[1].includes('30.12'));
});

t('datos demo: se generan y el controlador cierra de noche', () => {
  const rows = A.demoRows(NOW, 24);
  assert.ok(rows.length > 8000);
  const k = A.computeKPIs(rows, { nowS: NOW });
  assert.ok(k.closures >= 1, 'debería haber al menos un cierre');
});

console.log(`\n${n} pruebas pasaron`);
