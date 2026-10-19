/* Barbarian Prince - browser front-end for src/engine.py */

let board = null;
let sid = null;
let state = null;
let zoom = 0.24;
let showIds = true;
let showScan = false;
let hexById = {};

const PLACE_SYMBOL = {
  town: 'o', village: 'o', city: 'O', castle: '*', fort: '*', tower: '*',
  temple: '+', shrine: '+', ruins: 'x', mine: '#', farm: 'f', hollow: 'o',
  pool: '~', inn: 'i', cave: 'c', camp: 'c', pass: '^', marsh: '~'
};

async function api(path, opts) {
  const res = await fetch(path, opts);
  if (!res.ok) {
    let detail = res.statusText;
    try { detail = (await res.json()).detail || detail; } catch (e) { /* ignore */ }
    throw new Error(detail);
  }
  return res.json();
}

function esc(s) {
  return String(s).replace(/[&<>]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;' }[c]));
}

function linkRefs(text) {
  return esc(text).replace(/\b([re]\d{3})\b/g, '<a class="ref" data-ref="$1">$1</a>');
}

function sharedEdge(a, b) {
  const ha = hexById[a], hb = hexById[b];
  const vx = hb.cx - ha.cx, vy = hb.cy - ha.cy;
  const n = Math.hypot(vx, vy) || 1;
  const nx = -vy / n * (board.radius / 2);
  const ny = vx / n * (board.radius / 2);
  const mx = (ha.cx + hb.cx) / 2, my = (ha.cy + hb.cy) / 2;
  return [mx + nx, my + ny, mx - nx, my - ny];
}

function renderBoard() {
  const svg = document.getElementById('board');
  const W = board.maxx - board.minx, H = board.maxy - board.miny;
  const fs = px => (px / zoom).toFixed(1);          // screen px -> board units
  svg.setAttribute('viewBox', `${board.minx} ${board.miny} ${W} ${H}`);
  svg.setAttribute('width', Math.round(W * zoom));
  svg.setAttribute('height', Math.round(H * zoom));

  const parts = [];

  if (showScan && board.scan) {
    const [sx, sy, sw, sh] = board.scan;
    parts.push(`<image href="/scan/board.png" x="${sx}" y="${sy}" width="${sw}" height="${sh}" opacity="0.5"/>`);
  }

  for (const h of board.hexes) {
    const pts = h.points.map(p => p.join(',')).join(' ');
    const fill = board.terrain_colors[h.terrain] || '#d8d8d8';
    const tip = `${h.id} - ${h.travel_terrain}` +
                (h.place ? ` - ${h.place.name}` : '') +
                (h.region ? ` (${h.region})` : '');
    parts.push(`<polygon class="hex" data-hex="${h.id}" points="${pts}" fill="${fill}"><title>${esc(tip)}</title></polygon>`);
  }

  for (const [a, b] of board.rivers) {
    if (!hexById[a] || !hexById[b]) continue;
    const [x1, y1, x2, y2] = sharedEdge(a, b);
    parts.push(`<line class="river" x1="${x1}" y1="${y1}" x2="${x2}" y2="${y2}"/>`);
  }
  for (const [a, b] of board.roads) {
    if (!hexById[a] || !hexById[b]) continue;
    const [x1, y1, x2, y2] = sharedEdge(a, b);
    parts.push(`<line class="road" x1="${x1}" y1="${y1}" x2="${x2}" y2="${y2}"/>`);
  }

  for (const h of board.hexes) {
    if (h.region) {
      parts.push(`<text class="region" x="${h.cx}" y="${h.cy - 26}" font-size="${fs(11)}" text-anchor="middle">${esc(h.region)}</text>`);
    }
    if (h.place) {
      parts.push(`<text class="place" x="${h.cx}" y="${h.cy - 8}" font-size="${fs(14)}" text-anchor="middle">${PLACE_SYMBOL[h.place.kind] || '*'}</text>`);
      parts.push(`<text class="label" x="${h.cx}" y="${h.cy + 24}" font-size="${fs(8)}" text-anchor="middle">${esc(h.place.name)}</text>`);
    }
  }

  if (showIds) {
    for (const h of board.hexes) {
      parts.push(`<text class="label" x="${h.cx}" y="${h.cy + 40}" font-size="${fs(7)}" text-anchor="middle">${h.id}</text>`);
    }
  }

  parts.push('<g id="overlay"></g>');
  svg.innerHTML = parts.join('\n');
}


function renderOverlay() {
  const svg = document.getElementById('board');
  if (!svg) return;
  const moves = state && state.moves ? state.moves : [];
  const cur = state ? state.status.hex : null;
  const visited = state ? state.status.visited : [];

  svg.querySelectorAll('polygon.hex').forEach(p => {
    const hid = p.dataset.hex;
    p.classList.toggle('move', moves.includes(hid));
    p.classList.toggle('current', hid === cur);
    p.classList.toggle('visited', visited.includes(hid) && hid !== cur);
  });

  const g = document.getElementById('overlay');
  const parts = [];
  if (cur && hexById[cur]) {
    const h = hexById[cur];
    const r = board.radius * 0.2;
    parts.push(`<circle class="token-ring" cx="${h.cx}" cy="${h.cy}" r="${r + 12}"/>`);
    parts.push(`<circle class="token" cx="${h.cx}" cy="${h.cy}" r="${r}"/>`);
    parts.push(`<text x="${h.cx}" y="${h.cy + 6}" font-size="${(14 / zoom).toFixed(1)}" text-anchor="middle" fill="#fff">&#9733;</text>`);
  }
  g.innerHTML = parts.join('\n');
}

function renderStatus(st) {
  const rows = st.party_detail.map(([name, skill, endurance, wounds, mount]) =>
    `<tr><td>${esc(name)}</td><td>${skill}</td><td>${endurance - wounds}/${endurance}</td><td>${mount}</td></tr>`
  ).join('');
  const caches = Object.keys(st.caches || {}).length
    ? '<div class="party"><b>Caches:</b> ' +
      Object.entries(st.caches).map(([k, v]) => `${k} (${v[1]}g)`).join(', ') + '</div>'
    : '';
  const items = (st.items || []).length
    ? '<div class="party"><b>Items:</b> ' + st.items.map(esc).join(', ') + '</div>'
    : '';

  document.getElementById('status').innerHTML = `
    <div class="stat-grid">
      <div class="stat"><b>${st.day}</b><span>day of 70</span></div>
      <div class="stat"><b>${st.hex}</b><span>${esc(st.place || st.travel_terrain)}</span></div>
      <div class="stat"><b>${st.gold}</b><span>gold</span></div>
      <div class="stat"><b>${st.food}</b><span>food</span></div>
      <div class="stat"><b>${st.wit}</b><span>wit &amp; wiles</span></div>
      <div class="stat"><b>${st.moves_left}</b><span>moves left (${st.speed}/day)</span></div>
    </div>
    <div class="party">
      <table>
        <thead><tr><th>Party</th><th>skill</th><th>endurance</th><th>mount</th></tr></thead>
        <tbody>${rows}</tbody>
      </table>
    </div>
    ${caches}${items}`;

function renderPrompt(p) {
  const title = document.getElementById('prompt-title');
  const text = document.getElementById('prompt-text');
  const opts = document.getElementById('prompt-options');
  opts.innerHTML = '';

  if (state.status.game_over) {
    title.textContent = state.status.won ? 'Victory' : 'Game over';
    text.innerHTML = esc(state.status.reason || 'The adventure is finished.');
    const b = document.createElement('button');
    b.textContent = 'Start a new game';
    b.onclick = newGame;
    opts.appendChild(b);
    return;
  }
  if (!p) {
    title.textContent = 'Nothing to do';
    text.textContent = '';
    return;
  }
  title.textContent = p.title;
  text.innerHTML = linkRefs(p.text);
  p.options.forEach((o, i) => {
    const b = document.createElement('button');
    b.textContent = `${i + 1}. ${o.label}`;
    b.onclick = () => answer(i);
    opts.appendChild(b);
  });
}

function appendLog(lines) {
  const log = document.getElementById('log');
  for (const line of lines) {
    const p = document.createElement('p');
    if (line.startsWith('***')) p.className = 'over';
    else if (/Combat|Battle|encounter/i.test(line)) p.className = 'event';
    else if (/rolled|check/i.test(line)) p.className = 'roll';
    p.textContent = line;
    log.appendChild(p);
  }
  log.scrollTop = log.scrollHeight;
}

async function answer(index) {
  if (!sid) return;
  try {
    state = await api(`/api/game/${sid}/answer`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ index })
    });
  } catch (err) {
    appendLog('(error: ' + err.message + ')');
    return;
  }
  appendLog(state.log);
  renderStatus(state.status);
  renderPrompt(state.prompt);
  renderOverlay();
}

async function newGame() {
  const raw = document.getElementById('seed').value.trim();
  const seed = raw === '' ? null : parseInt(raw, 10);
  document.getElementById('log').innerHTML = '';
  try {
    state = await api('/api/game', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ seed })
    });
  } catch (err) {
    appendLog('(could not start a game: ' + err.message + ')');
    return;
  }
  sid = state.session;
  appendLog(state.log);
  renderStatus(state.status);
  renderPrompt(state.prompt);
  renderOverlay();
}

async function autoPlay() {
  if (!sid) return;
  state = await api(`/api/game/${sid}/auto`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ steps: 400 })
  });
  appendLog(state.log);
  renderStatus(state.status);
  renderPrompt(state.prompt);
  renderOverlay();
}


/* ---------------------------------------------------------------- wiring */
async function init() {
  board = await api('/api/board');
  hexById = Object.fromEntries(board.hexes.map(h => [h.id, h]));
  renderBoard();

  document.getElementById('btn-new').onclick = newGame;
  document.getElementById('btn-auto').onclick = autoPlay;
  document.getElementById('btn-quit').onclick = () => {
    sid = null;
    state = null;
    document.getElementById('log').innerHTML = '';
    document.getElementById('status').innerHTML = '';
    document.getElementById('prompt-title').textContent = 'Waiting for a game to start...';
    document.getElementById('prompt-text').textContent = '';
    document.getElementById('prompt-options').innerHTML = '';
    renderOverlay();
  };

  document.querySelectorAll('.zoom button').forEach(b => {
    b.onclick = () => {
      zoom = parseFloat(b.dataset.zoom);
      document.querySelectorAll('.zoom button').forEach(x => x.classList.remove('on'));
      b.classList.add('on');
      renderBoard();
      renderOverlay();
    };
  });

  document.getElementById('show-ids').onchange = e => {
    showIds = e.target.checked;
    renderBoard();
    renderOverlay();
  };
  document.getElementById('show-scan').onchange = e => {
    showScan = e.target.checked;
    renderBoard();
    renderOverlay();
  };

  document.getElementById('board').addEventListener('click', e => {
    const hid = e.target && e.target.dataset && e.target.dataset.hex;
    if (!hid) return;
    if (!state || !state.moves || !state.moves.includes(hid)) return;
    const i = state.prompt.options.findIndex(o => o.hex === hid);
    if (i >= 0) answer(i);
  });

  document.addEventListener('click', e => {
    if (e.target.classList && e.target.classList.contains('ref')) {
      showRef(e.target.dataset.ref);
    }
  });
  document.getElementById('ref-close').onclick = () =>
    document.getElementById('ref-modal').classList.add('hidden');
  document.getElementById('ref-modal').onclick = e => {
    if (e.target.id === 'ref-modal') e.target.classList.add('hidden');
  };

  document.addEventListener('keydown', e => {
    if (!state || !state.prompt || state.status.game_over) return;
    if (document.getElementById('ref-modal').classList.contains('hidden') === false) return;
    const n = parseInt(e.key, 10);
    if (n >= 1 && n <= state.prompt.options.length) answer(n - 1);
  });

  newGame();
}

init();

async function showRef(ref) {
  try {
    const r = await api('/api/ref/' + ref);
    document.getElementById('ref-title').textContent = `${r.id} - ${r.title}`;
    document.getElementById('ref-body').textContent = r.text.trim();
    document.getElementById('ref-modal').classList.remove('hidden');
  } catch (err) {
    appendLog('(no entry for ' + ref + ')');
  }
}

}
