// Run web/app.js in Node with a tiny DOM shim to catch front-end errors.
//   python src/web.py --port 8011
//   node _refs/js_smoke.mjs http://127.0.0.1:8011
import fs from 'node:fs';

const BASE = process.argv[2] || 'http://127.0.0.1:8011';
const origFetch = globalThis.fetch;
const els = {};

function makeEl(tag = 'div') {
  const el = {
    tag, html: '', textContent: '', value: '', dataset: {}, children: [],
    className: '', attrs: {}, listeners: {}, scrollTop: 0, scrollHeight: 0,
    setAttribute(k, v) { el.attrs[k] = v; },
    appendChild(c) { el.children.push(c); return c; },
    addEventListener(t, fn) { el.listeners[t] = fn; },
    querySelectorAll(sel) {
      if (sel === 'polygon.hex') {
        return [...el.html.matchAll(/data-hex="(\d{4})"/g)].map(m => ({
          dataset: { hex: m[1] }, classList: { toggle: () => {} },
        }));
      }
      return [];
    },
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
  addEventListener: (t, fn) => console.log('listener', t),
};
globalThis.fetch = async (url, opts) => {
  console.log('fetch', BASE + url);
  return origFetch(BASE + url, opts);
};

const src = fs.readFileSync('web/app.js', 'utf8') +
  "\nsetTimeout(async () => {\n" +
  "  try {\n" +
  "    await answer(0);\n" +
  "    console.log('after answer -> day', state.status.day, 'hex', state.status.hex,\n" +
  "              'prompt:', state.prompt && state.prompt.title,\n" +
  "              'highlighted moves:', state.moves.length);\n" +
  "    if (state.moves.length) {\n" +
  "      const i = state.prompt.options.findIndex(o => o.hex === state.moves[0]);\n" +
  "      await answer(i);\n" +
  "      console.log('after move -> hex', state.status.hex, 'moves left', state.status.moves_left);\n" +
  "    }\n" +
  "  } catch (e) { console.log('answer error:', e.message); }\n" +
  "}, 2500);\n";
console.log('app.js tail:', JSON.stringify(src.slice(-30)));

try {
  eval(src);
} catch (err) {
  console.log('SYNTAX/RUN ERROR:', err.stack);
  process.exit(1);
}

setTimeout(() => {
  const svg = els['board'] || makeEl('svg');
  console.log('elements created:', Object.keys(els).join(', ') || '(none)');
  console.log('viewBox:', svg.attrs.viewBox, 'size:', svg.attrs.width, 'x', svg.attrs.height);
  console.log('polygons:', (svg.html.match(/<polygon /g) || []).length,
              'lines:', (svg.html.match(/<line /g) || []).length,
              'texts:', (svg.html.match(/<text /g) || []).length);
  console.log('prompt-title:', (els['prompt-title'] || {}).textContent);
  console.log('option buttons:', (els['prompt-options'] || {}).children.length);
  console.log('status chars:', (els['status'] || {}).html.length);
  console.log('log paragraphs:', (els['log'] || {}).children.length);
  console.log('overlay:', ((els['overlay'] || {}).html || '').slice(0, 160));
  process.exit(0);
}, 6000);
