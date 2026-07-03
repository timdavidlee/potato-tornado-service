"""The dataset browser UI — a single self-contained HTML page served at ``/``.

The page is plain HTML/CSS/JS with no external assets (no CDN), so it works inside the container
with no network egress. It drives the existing JSON API (``/collections`` …) entirely from the
browser via ``fetch``, so the UI adds no new server-side query paths or dependencies.
"""

from __future__ import annotations

INDEX_HTML = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>potato-tornado · dataset browser</title>
<style>
  :root {
    --bg: #0f1117; --panel: #171a23; --panel-2: #1e222d; --border: #2a2f3c;
    --text: #e6e8ee; --muted: #9aa1b1; --accent: #7c9cff; --accent-dim: #2a3350;
  }
  * { box-sizing: border-box; }
  html, body { margin: 0; height: 100%; }
  body {
    background: var(--bg); color: var(--text); display: flex; height: 100vh;
    font: 14px/1.5 ui-sans-serif, system-ui, -apple-system, "Segoe UI", Roboto, sans-serif;
  }
  aside {
    width: 260px; flex: none; background: var(--panel); border-right: 1px solid var(--border);
    display: flex; flex-direction: column; overflow: hidden;
  }
  aside header { padding: 16px; border-bottom: 1px solid var(--border); }
  aside header h1 { font-size: 14px; margin: 0; letter-spacing: .3px; }
  aside header p { margin: 4px 0 0; color: var(--muted); font-size: 12px; }
  #tree { overflow-y: auto; padding: 8px 0; flex: 1; }
  .collection > button {
    width: 100%; text-align: left; background: none; border: 0; color: var(--text);
    padding: 8px 16px; cursor: pointer; font-size: 13px; font-weight: 600;
    display: flex; align-items: center; gap: 8px;
  }
  .collection > button:hover { background: var(--panel-2); }
  .collection > button .chev { color: var(--muted); transition: transform .12s; font-size: 10px; }
  .collection.open > button .chev { transform: rotate(90deg); }
  .tables { display: none; }
  .collection.open .tables { display: block; }
  .tables button {
    width: 100%; text-align: left; background: none; border: 0; color: var(--muted);
    padding: 5px 16px 5px 36px; cursor: pointer; font-size: 13px;
  }
  .tables button:hover { background: var(--panel-2); color: var(--text); }
  .tables button.active { background: var(--accent-dim); color: var(--text); }
  main { flex: 1; display: flex; flex-direction: column; overflow: hidden; }
  main header {
    padding: 14px 20px; border-bottom: 1px solid var(--border);
    display: flex; align-items: center; gap: 12px; flex: none;
  }
  main header h2 { font-size: 15px; margin: 0; font-variant-ligatures: none; }
  main header h2 .sep { color: var(--muted); margin: 0 6px; }
  main header .spacer { flex: 1; }
  .pager { display: flex; align-items: center; gap: 8px; color: var(--muted); font-size: 13px; }
  .pager button {
    background: var(--panel-2); color: var(--text); border: 1px solid var(--border);
    border-radius: 6px; padding: 4px 10px; cursor: pointer; font-size: 13px;
  }
  .pager button:disabled { opacity: .4; cursor: default; }
  .tablewrap { overflow: auto; flex: 1; }
  table { border-collapse: collapse; width: 100%; font-variant-numeric: tabular-nums; }
  th, td {
    text-align: left; padding: 7px 12px; border-bottom: 1px solid var(--border);
    white-space: nowrap; max-width: 420px; overflow: hidden; text-overflow: ellipsis;
  }
  th {
    position: sticky; top: 0; background: var(--panel-2); color: var(--muted);
    font-weight: 600; font-size: 12px; text-transform: uppercase; letter-spacing: .4px;
  }
  tbody tr:hover { background: var(--panel); }
  td.null { color: var(--muted); font-style: italic; }
  .placeholder { margin: auto; color: var(--muted); text-align: center; padding: 40px; }
  .error { color: #ff8a8a; }
</style>
</head>
<body>
<aside>
  <header>
    <h1>potato-tornado</h1>
    <p>dataset browser</p>
  </header>
  <div id="tree"><div class="placeholder">Loading…</div></div>
</aside>
<main>
  <header>
    <h2 id="title"><span class="placeholder-inline">Select a table</span></h2>
    <div class="spacer"></div>
    <div class="pager" id="pager" hidden>
      <button id="prev">‹ Prev</button>
      <span id="range"></span>
      <button id="next">Next ›</button>
    </div>
  </header>
  <div class="tablewrap" id="content">
    <div class="placeholder">Pick a collection on the left to browse its tables.</div>
  </div>
</main>
<script>
const LIMIT = 100;
const state = { schema: null, table: null, offset: 0, count: 0 };

async function api(path) {
  const res = await fetch(path);
  if (!res.ok) {
    let detail = res.statusText;
    try { detail = (await res.json()).detail ?? detail; } catch (_) {}
    throw new Error(detail);
  }
  return res.json();
}

async function loadTree() {
  const tree = document.getElementById("tree");
  let collections;
  try {
    collections = await api("collections");
  } catch (e) {
    tree.innerHTML = '<div class="placeholder error">' + e.message + "</div>";
    return;
  }
  if (!collections.length) {
    tree.innerHTML = '<div class="placeholder">No collections seeded yet.</div>';
    return;
  }
  tree.innerHTML = "";
  for (const schema of collections) {
    const wrap = document.createElement("div");
    wrap.className = "collection";
    const btn = document.createElement("button");
    btn.innerHTML = '<span class="chev">▶</span>' + schema;
    const tables = document.createElement("div");
    tables.className = "tables";
    let loaded = false;
    btn.onclick = async () => {
      wrap.classList.toggle("open");
      if (wrap.classList.contains("open") && !loaded) {
        loaded = true;
        tables.innerHTML = '<button disabled>Loading…</button>';
        try {
          const names = await api("collections/" + schema + "/tables");
          tables.innerHTML = "";
          for (const t of names) {
            const tb = document.createElement("button");
            tb.textContent = t;
            tb.dataset.key = schema + "." + t;
            tb.onclick = () => selectTable(schema, t, tb);
            tables.appendChild(tb);
          }
        } catch (e) {
          tables.innerHTML = '<button disabled class="error">' + e.message + "</button>";
          loaded = false;
        }
      }
    };
    wrap.append(btn, tables);
    tree.appendChild(wrap);
  }
}

function selectTable(schema, table, el) {
  document.querySelectorAll(".tables button").forEach((b) => b.classList.remove("active"));
  if (el) el.classList.add("active");
  state.schema = schema;
  state.table = table;
  state.offset = 0;
  loadRows();
}

async function loadRows() {
  const { schema, table, offset } = state;
  const content = document.getElementById("content");
  document.getElementById("title").innerHTML =
    schema + '<span class="sep">/</span>' + table;
  content.innerHTML = '<div class="placeholder">Loading rows…</div>';
  let data;
  try {
    data = await api(
      "collections/" + schema + "/tables/" + table + "?limit=" + LIMIT + "&offset=" + offset
    );
  } catch (e) {
    content.innerHTML = '<div class="placeholder error">' + e.message + "</div>";
    return;
  }
  state.count = data.rows.length;
  renderRows(data.rows);
  updatePager();
}

function renderRows(rows) {
  const content = document.getElementById("content");
  if (!rows.length) {
    content.innerHTML = '<div class="placeholder">No rows on this page.</div>';
    return;
  }
  const cols = Object.keys(rows[0]);
  const table = document.createElement("table");
  const thead = document.createElement("thead");
  const htr = document.createElement("tr");
  for (const c of cols) {
    const th = document.createElement("th");
    th.textContent = c;
    htr.appendChild(th);
  }
  thead.appendChild(htr);
  const tbody = document.createElement("tbody");
  for (const row of rows) {
    const tr = document.createElement("tr");
    for (const c of cols) {
      const td = document.createElement("td");
      const v = row[c];
      if (v === null || v === undefined) {
        td.textContent = "NULL";
        td.className = "null";
      } else if (typeof v === "object") {
        td.textContent = JSON.stringify(v);
      } else {
        td.textContent = String(v);
      }
      td.title = td.textContent;
      tr.appendChild(td);
    }
    tbody.appendChild(tr);
  }
  table.append(thead, tbody);
  content.innerHTML = "";
  content.appendChild(table);
  content.scrollTop = 0;
}

function updatePager() {
  const pager = document.getElementById("pager");
  pager.hidden = false;
  const start = state.offset + 1;
  const end = state.offset + state.count;
  document.getElementById("range").textContent =
    state.count ? "rows " + start + "–" + end : "no rows";
  document.getElementById("prev").disabled = state.offset === 0;
  // We only know there is a next page if this page came back full.
  document.getElementById("next").disabled = state.count < LIMIT;
}

document.getElementById("prev").onclick = () => {
  state.offset = Math.max(0, state.offset - LIMIT);
  loadRows();
};
document.getElementById("next").onclick = () => {
  state.offset += LIMIT;
  loadRows();
};

loadTree();
</script>
</body>
</html>
"""
