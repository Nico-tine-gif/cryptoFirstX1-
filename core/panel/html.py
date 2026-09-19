"""Embedded HTML/CSS/JS for the control panel. No external assets."""

INDEX_HTML = """<!doctype html>
<html><head>
<meta charset="utf-8">
<title>cryptoFirstX1 admin</title>
<style>
  * { box-sizing: border-box; }
  body {
    margin: 0; padding: 20px;
    background: #0d1117; color: #c9d1d9;
    font-family: ui-monospace, Menlo, Consolas, monospace;
    font-size: 13px;
  }
  h1 { font-size: 16px; margin: 0 0 4px; color: #58a6ff; }
  .sub { color: #8b949e; font-size: 11px; margin-bottom: 16px; }
  .grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
    gap: 12px;
  }
  .card {
    background: #161b22; border: 1px solid #30363d;
    border-radius: 6px; padding: 12px;
  }
  .card h2 {
    font-size: 12px; margin: 0 0 10px;
    color: #58a6ff; text-transform: uppercase;
    letter-spacing: 1px;
  }
  .row { display: flex; justify-content: space-between; padding: 2px 0; }
  .k { color: #8b949e; }
  .v { color: #c9d1d9; }
  .ok { color: #3fb950; }
  .bad { color: #f85149; }
  .warn { color: #d29922; }
  table { width: 100%; border-collapse: collapse; font-size: 11px; }
  th { text-align: left; color: #8b949e; padding: 3px 6px;
       border-bottom: 1px solid #30363d; font-weight: normal; }
  td { padding: 3px 6px; border-bottom: 1px solid #21262d; }
  button {
    background: #21262d; color: #c9d1d9;
    border: 1px solid #30363d; border-radius: 4px;
    padding: 5px 10px; cursor: pointer; font-family: inherit;
    font-size: 12px;
  }
  button:hover { background: #30363d; }
  button.danger { color: #f85149; border-color: #f85149; }
  input {
    background: #0d1117; color: #c9d1d9;
    border: 1px solid #30363d; border-radius: 4px;
    padding: 4px 8px; font-family: inherit; font-size: 12px;
    width: 100%;
  }
  #status { position: fixed; top: 8px; right: 12px; font-size: 11px; color: #8b949e; }
</style>
</head><body>
<h1>cryptoFirstX1 — admin control panel</h1>
<div class="sub">P1–P9 stack &nbsp;·&nbsp; auto-refresh <span id="refresh">5</span>s &nbsp;·&nbsp; <span id="last">—</span></div>
<div id="status">connecting…</div>

<div class="grid">
  <div class="card"><h2>Dashboard</h2><div id="dash"></div></div>
  <div class="card"><h2>Security</h2><div id="sec"></div>
    <div style="margin-top:8px">
      <button onclick="act('lock')">Lock</button>
      <button onclick="act('unlock')">Unlock</button>
    </div>
  </div>
  <div class="card"><h2>Reconcile</h2><div id="rec"></div></div>
  <div class="card"><h2>Policy gates</h2><div id="pol"></div></div>
  <div class="card"><h2>Allowlist</h2><div id="al"></div>
    <div style="margin-top:8px; display:flex; gap:6px">
      <input id="alAddr" placeholder="bc1q...">
      <button onclick="addAl()">Add</button>
    </div>
  </div>
  <div class="card"><h2>Recent ledger</h2><div id="led"></div></div>
</div>

<script>
async function j(u, opts) {
  const r = await fetch(u, opts || {});
  const t = await r.text();
  try { return JSON.parse(t); } catch { return { error: t }; }
}
function row(k, v, cls) {
  return `<div class="row"><span class="k">${k}</span>
          <span class="v ${cls||''}">${v}</span></div>`;
}
function num(v) { return v === null || v === undefined ? '—' : v; }

async function tick() {
  const t0 = Date.now();
  document.getElementById('status').textContent = 'loading…';
  try {
    const [dash, sec, rec, pol, al, led] = await Promise.all([
      j('/api/dashboard'), j('/api/security'),
      j('/api/reconcile'), j('/api/policy'),
      j('/api/allowlist'), j('/api/ledger?limit=8'),
    ]);

    document.getElementById('dash').innerHTML =
      row('available',  num(dash.available_units)) +
      row('reserved',   num(dash.reserved_units)) +
      row('total',      num(dash.total_units)) +
      row('deposit-backed', num(dash.deposit_backed_units)) +
      row('system-earned',  num(dash.system_earned_units));

    const authCls = sec.admin_authenticated ? 'ok' : 'bad';
    document.getElementById('sec').innerHTML =
      row('authenticated', sec.admin_authenticated, authCls) +
      row('p6 signing',    sec.p6_signing) +
      row('p6 broadcast',  sec.p6_broadcast) +
      row('keys stored',   sec.private_keys_stored) +
      row('auto-withdraw', sec.automatic_withdrawals);

    const balCls = rec.balanced ? 'ok' : 'bad';
    document.getElementById('rec').innerHTML =
      row('chain deposits', rec.chain_deposits) +
      row('ledger credits', rec.ledger_credits) +
      row('matched',        rec.matched) +
      row('orphans',        (rec.orphan_credits||[]).length,
          (rec.orphan_credits||[]).length ? 'bad' : 'ok') +
      row('balanced', rec.balanced, balCls);

    document.getElementById('pol').innerHTML =
      Object.entries(pol).map(([k,v]) => {
        const cls = (v === false || v === 0) ? 'warn' : '';
        return row(k, String(v), cls);
      }).join('');

    document.getElementById('al').innerHTML =
      (al.entries||[]).map(e =>
        `<div class="row"><span class="k">${e[1]||'—'}</span>
         <span class="v">${e[0]}</span></div>`).join('') ||
      '<div class="k">empty</div>';

    const rows = (led.entries||[]).map(e =>
      `<tr><td>${e.entry_type}</td><td>${e.amount_cents}</td>
       <td>${e.reference_id||''}</td></tr>`).join('');
    document.getElementById('led').innerHTML =
      `<table><tr><th>type</th><th>cents</th><th>ref</th></tr>${rows}</table>`;

    document.getElementById('last').textContent =
      new Date().toLocaleTimeString() + ' (' + (Date.now()-t0) + 'ms)';
    document.getElementById('status').textContent = 'live';
  } catch (e) {
    document.getElementById('status').textContent = 'error: ' + e.message;
  }
}

async function act(a) {
  await j('/api/' + a, { method: 'POST' });
  tick();
}

async function addAl() {
  const addr = document.getElementById('alAddr').value.trim();
  if (!addr) return;
  await j('/api/allowlist/add?address=' + encodeURIComponent(addr),
          { method: 'POST' });
  document.getElementById('alAddr').value = '';
  tick();
}

let t = 5;
setInterval(() => { t--; if (t <= 0) { t = 5; tick(); }
                    document.getElementById('refresh').textContent = t; }, 1000);
tick();
</script>
</body></html>
"""
