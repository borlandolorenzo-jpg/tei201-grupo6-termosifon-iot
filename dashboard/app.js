/* app.js — lógica de la interfaz: descarga de Firebase, gráficos y tarjetas. */
(function () {
  'use strict';
  const params = new URLSearchParams(location.search);
  const DEMO = params.get('demo') === '1';   // ?demo=1 muestra datos SIMULADOS (solo para ver el diseño)
  const $ = (id) => document.getElementById(id);

  // ---------- Configuración (config.js + localStorage) ----------
  const cfg = Object.assign({}, window.DASH_CONFIG);
  try {
    const saved = JSON.parse(localStorage.getItem('dashCfg') || '{}');
    Object.assign(cfg, saved);
  } catch (e) { /* sin almacenamiento: se usan los valores de config.js */ }

  let rows = [];
  let timer = null;
  let chTemp = null, chDt = null;

  // ---------- Descarga ----------
  async function fetchRows(hours) {
    if (DEMO) return Analytics.demoRows(Math.floor(Date.now() / 1000), hours);
    const n = Math.round((hours * 3600) / 10) + 20;
    let url = cfg.FIREBASE_URL.replace(/\/$/, '') + '/lecturas.json?orderBy=' +
      encodeURIComponent('"$key"') + '&limitToLast=' + n;
    if (cfg.FIREBASE_AUTH) url += '&auth=' + encodeURIComponent(cfg.FIREBASE_AUTH);
    const res = await fetch(url, { cache: 'no-store' });
    if (!res.ok) throw new Error('HTTP ' + res.status + (res.status === 401 ? ' (reglas de Firebase)' : ''));
    const data = await res.json();
    if (!data) return [];
    return Object.keys(data).sort().map((k) => data[k]).filter((r) => r && r.ts > 0);
  }

  // ---------- Utilidades de formato ----------
  const f1 = (x) => (typeof x === 'number' && isFinite(x) ? x.toFixed(1) : '–');
  function timeLabel(ts, hours) {
    const d = new Date(ts * 1000);
    const t = d.toLocaleTimeString('es-CL', { hour: '2-digit', minute: '2-digit' });
    return hours > 24 ? d.toLocaleDateString('es-CL', { day: '2-digit', month: '2-digit' }) + ' ' + t : t;
  }
  const css = (name) => getComputedStyle(document.documentElement).getPropertyValue(name).trim();

  // ---------- Gráficos ----------
  function makeCharts() {
    Chart.defaults.font.family = 'system-ui, sans-serif';
    Chart.defaults.color = css('--muted');
    const base = {
      responsive: true, maintainAspectRatio: false, animation: false, spanGaps: false,
      interaction: { mode: 'index', intersect: false },
      plugins: { legend: { position: 'bottom', labels: { usePointStyle: true, boxWidth: 8 } } },
      elements: { point: { radius: 0 }, line: { borderWidth: 2 } },
      scales: { x: { ticks: { maxTicksLimit: 8, maxRotation: 0 }, grid: { display: false } } }
    };
    chTemp = new Chart($('chTemp'), {
      type: 'line',
      data: { labels: [], datasets: [
        { label: 'Colector', data: [], borderColor: css('--col'), backgroundColor: css('--col') },
        { label: 'Tanque', data: [], borderColor: css('--tank'), backgroundColor: css('--tank') },
        { label: 'Ambiente', data: [], borderColor: css('--amb'), backgroundColor: css('--amb'), borderDash: [5, 4] }
      ] },
      options: Object.assign({}, base, { scales: Object.assign({}, base.scales, { y: { title: { display: true, text: '°C' }, grid: { color: css('--line') } } }) })
    });
    chDt = new Chart($('chDt'), {
      type: 'line',
      data: { labels: [], datasets: [
        { label: 'ΔT (colector − tanque) [K]', data: [], borderColor: css('--col'), backgroundColor: css('--col'), yAxisID: 'y' },
        { label: 'Umbral apertura', data: [], borderColor: css('--good'), backgroundColor: css('--good'), borderDash: [6, 4], borderWidth: 1, yAxisID: 'y' },
        { label: 'Umbral cierre', data: [], borderColor: css('--warn'), backgroundColor: css('--warn'), borderDash: [6, 4], borderWidth: 1, yAxisID: 'y' },
        { label: 'Válvula (1 = abierta)', data: [], borderColor: css('--teal'), backgroundColor: css('--teal'), stepped: true, yAxisID: 'y2' }
      ] },
      options: Object.assign({}, base, { scales: Object.assign({}, base.scales, {
        y: { title: { display: true, text: 'K' }, grid: { color: css('--line') } },
        y2: { position: 'right', min: -0.1, max: 1.1, ticks: { stepSize: 1, callback: (v) => (v === 1 ? 'abierta' : v === 0 ? 'cerrada' : '') }, grid: { display: false } }
      }) })
    });
  }

  function updateCharts(hours) {
    const pts = Analytics.downsample(rows, 1200);
    const labels = pts.map((r) => timeLabel(r.ts, hours));
    chTemp.data.labels = labels;
    chTemp.data.datasets[0].data = pts.map((r) => r.tc);
    chTemp.data.datasets[1].data = pts.map((r) => r.tt);
    chTemp.data.datasets[2].data = pts.map((r) => r.ta);
    chTemp.update();
    chDt.data.labels = labels;
    chDt.data.datasets[0].data = pts.map((r) => (r.tc != null && r.tt != null ? r.tc - r.tt : null));
    chDt.data.datasets[1].data = pts.map(() => cfg.DT_ON);
    chDt.data.datasets[2].data = pts.map(() => cfg.DT_OFF);
    chDt.data.datasets[3].data = pts.map((r) => r.v);
    chDt.update();
  }

  // ---------- Tarjetas, alertas, indicadores ----------
  function render(hours) {
    const k = Analytics.computeKPIs(rows, {
      tankLiters: Number(cfg.TANK_LITERS), hotTargetC: Number(cfg.HOT_TARGET_C), tankMaxC: Number(cfg.TANK_MAX_C), dtOn: Number(cfg.DT_ON)
    });
    const badge = $('badge');
    if (DEMO) { badge.className = 'badge demo'; badge.textContent = 'DATOS SIMULADOS (demo)'; }
    else if (k.last && k.online) { badge.className = 'badge on'; badge.textContent = 'En línea'; }
    else { badge.className = 'badge off'; badge.textContent = 'Sin conexión'; }

    if (k.last) {
      $('vCol').textContent = f1(k.last.tc);
      $('vTank').textContent = f1(k.last.tt);
      $('vAmb').textContent = f1(k.last.ta);
      $('vDt').textContent = f1(k.deltaT);
      const v = $('vValve');
      v.textContent = k.last.v === 1 ? 'ABIERTA' : 'CERRADA';
      v.className = 'chip ' + (k.last.v === 1 ? 'open' : 'closed');
      $('tankSub').textContent = 'Objetivo agua caliente: ' + cfg.HOT_TARGET_C + ' °C';
    }

    const ul = $('alerts');
    ul.textContent = '';
    const list = k.alerts.length ? k.alerts : [{ level: 'info', text: 'Sin alertas activas.' }];
    list.forEach((a) => { const li = document.createElement('li'); li.className = a.level; li.textContent = a.text; ul.appendChild(li); });

    const kp = $('kpis');
    kp.textContent = '';
    const items = k.last ? [
      ['Cierres de válvula', String(k.closures)],
      ['Flujo inverso evitado', k.hoursProtected.toFixed(2) + ' h'],
      ['Captando calor (válvula abierta, ΔT ≥ 2 K)', k.hoursCollecting.toFixed(2) + ' h'],
      ['Flujo inverso con válvula abierta', k.hoursLeak.toFixed(2) + ' h'],
      ['Temperatura máxima del tanque', k.tankMax != null ? k.tankMax.toFixed(1) + ' °C' : '–'],
      ['Calor almacenado neto (ref.)', k.storedWh != null ? (k.storedWh / 1000).toFixed(2) + ' kWh' : '–']
    ] : [];
    items.forEach(([l, v]) => {
      const d = document.createElement('div');
      d.className = 'card';
      const a = document.createElement('div'); a.className = 'v'; a.textContent = v;
      const b = document.createElement('div'); b.className = 'l'; b.textContent = l;
      d.appendChild(a); d.appendChild(b); kp.appendChild(d);
    });
    $('status').textContent = k.last
      ? 'Muestras: ' + k.n + ' · Última lectura: ' + new Date(k.last.ts * 1000).toLocaleString('es-CL') + ' · Actualiza cada ' + cfg.REFRESH_S + ' s'
      : '';
    updateCharts(hours);
  }

  async function refresh() {
    const hours = Number($('range').value);
    try {
      rows = await fetchRows(hours);
      render(hours);
    } catch (e) {
      $('status').textContent = 'No se pudo leer Firebase: ' + e.message + '. Revisar URL, reglas y conexión (Configuración).';
      $('badge').className = 'badge off'; $('badge').textContent = 'Sin conexión';
    }
  }

  // ---------- Eventos ----------
  $('range').addEventListener('change', refresh);
  $('btnCsv').addEventListener('click', () => {
    const blob = new Blob([Analytics.toCSV(rows)], { type: 'text/csv' });
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = 'registro_' + new Date().toISOString().slice(0, 16).replace(/[:T]/g, '-') + (DEMO ? '_DEMO' : '') + '.csv';
    a.click();
    URL.revokeObjectURL(a.href);
  });
  $('btnCfg').addEventListener('click', () => {
    $('cUrl').value = cfg.FIREBASE_URL; $('cAuth').value = cfg.FIREBASE_AUTH || '';
    $('cLit').value = cfg.TANK_LITERS; $('cHot').value = cfg.HOT_TARGET_C;
    $('cOn').value = cfg.DT_ON; $('cOff').value = cfg.DT_OFF;
    $('dlg').showModal();
  });
  $('cSave').addEventListener('click', () => {
    cfg.FIREBASE_URL = $('cUrl').value.trim(); cfg.FIREBASE_AUTH = $('cAuth').value.trim();
    cfg.TANK_LITERS = Number($('cLit').value) || cfg.TANK_LITERS; cfg.HOT_TARGET_C = Number($('cHot').value) || cfg.HOT_TARGET_C;
    cfg.DT_ON = Number($('cOn').value) || cfg.DT_ON; cfg.DT_OFF = Number($('cOff').value) || cfg.DT_OFF;
    try { localStorage.setItem('dashCfg', JSON.stringify(cfg)); } catch (e) { /* ignorar */ }
    refresh();
  });

  makeCharts();
  refresh();
  timer = setInterval(refresh, Math.max(5, Number(cfg.REFRESH_S) || 10) * 1000);
})();
