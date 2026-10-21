// Check the "original map scan" rendering path of web/app.js.
//   python src/web.py --port 8011
//   node _refs/scan_smoke.mjs http://127.0.0.1:8011
import fs from 'node:fs';

const BASE = process.argv[2] || 'http://127.0.0.1:8011';
const origFetch = globalThis.fetch;
const els = {};

function makeEl(tag = 'div') {
  const el = {
    tag, html: '', textContent: '', value: '', checked: true, dataset: {},
    children: [], className: '', attrs: {}, listeners: {},
    setAttribute(k, v) { el.attrs[k] = v; },
    appendChild(c) { el.children.push(c); return c; },
    addEventListener(t, fn) { el.listeners[t] = fn; },
    querySelectorAll() { return []; },
  };
  el.classList = {
    contains: c => el.className.split(' ').includes(c),
    add: c => { if (!el.classList.contains(c)) el.className = (el.className + ' ' + c).trim(); },
    remove: c => { el.className = el.className.split(' ').filter(x => x !== c).join(' '); },
    toggle: (c, on) => on ? el.classList.add(c) : el.classList.remove(c),
  };
  Object.defineProperty(el, 'innerHTML', { get: () => el.html, set: v => { el.html = v; } });
  return el;
}

globalThis.document = {
  getElementById: id => (els[id] ||= makeEl(id)),
  querySelectorAll: () => [],
  createElement: t => makeEl(t),
  addEventListener: () => {},
};
globalThis.fetch = async (url, opts) => origFetch(BASE + url, opts);

eval(fs.readFileSync('web/app.js', 'utf8'));

setTimeout(async () => {
  const svg = els['board'];
  const style = els['map-style'];
  const count = () => ({
    images: (svg.html.match(/<image /g) || []).length,
    fills: (svg.html.match(/fill="none"/g) || []).length,
    lines: (svg.html.match(/<line /g) || []).length,
    scanMode: (svg.html.match(/class="hex scan-(mode|blend)/g) || []).length,
  });

  console.log('vector  ->', count());
  for (const mode of ['scan', 'blend', 'vector']) {
    style.value = mode;
    style.onchange({ target: style });
    console.log(mode.padEnd(8), '->', count());
  }

  const grid = els['show-grid'];
  grid.checked = false;
  grid.onchange({ target: grid });
  console.log('grid off ->', (svg.html.match(/nogrid/g) || []).length, 'hexes without grid');

  const traces = els['show-traces'];
  traces.checked = false;
  traces.onchange({ target: traces });
  console.log('traces off ->', (svg.html.match(/<line /g) || []).length, 'lines');

  const res = await fetch('/scan/board.jpg');
  console.log('/scan/board.jpg ->', res.status, res.headers.get('content-type'),
              (await res.arrayBuffer()).byteLength, 'bytes');
  process.exit(0);
}, 4000);
