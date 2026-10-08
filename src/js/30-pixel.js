const PAL = {
  haze: '#120F1F',
  ground1: '#E6E0ED', ground2: '#E1DAE9', speck: '#D6CEE2', speckHi: '#EFEAF5',
  slabL: '#2B2540', slabR: '#221D35', strata: '#342D4C', worldRim: '#4E4670',
  pave: '#F4F1F8', paveDk: '#E6E0EE', plotSideL: '#CBC2DB', plotSideR: '#B6ABCA', rim: '#FFFFFF',
  asphalt: '#908BA5', asphaltHi: '#9D98B1', lines: '#F4F1F8',
  lawn: '#A9E2BE', lawnDk: '#92D5AB', lawnShadow: '#8CCDA4',
  canopy: '#74C997', canopyHi: '#97DDB0', canopyDk: '#58AF80', trunk: '#9C7C6B',
  flowerA: '#F7A6C6', flowerB: '#FFFFFF', flowerC: '#FFE08C',
  pole: '#5F5876', lampOn: '#FFE38A', beacon: '#EE4C93',
  outline: '#5A5073',
  lit: '#FFEBA0',
  ring: '#EE4C93', ringHi: '#FFFFFF', free: '#8E86A8', target: 'rgba(238, 76, 147, 0.22)',
  road: '#26213A', walk: '#383150', curb: '#554C7A', joint: '#302A46', dash: '#E0C35E', stripe: '#433B5F',
  lot: '#1D302C', lotDk: '#26423A', lotHi: '#2F5046',
};
const BUILD_COLORS = ['#F4A3C3', '#7FD6CE', '#B7A5F0', '#A6E3B6', '#FFDF8A', '#9CC7F3', '#FFB797'];

/* The city palette: 32 colors. Generated block art uses at most 16 of them per building.
   The plot colors (pavement, slab sides, outline, lawn, asphalt) are the exact ones the map draws. */
const CITY_PALETTE = [
  ['Ink', '#2B2542'], ['Outline', '#5A5073'], ['Steel', '#7A7394'], ['Asphalt', '#908BA5'],
  ['Slab shade', '#B6ABCA'], ['Slab', '#CBC2DB'], ['Light steel', '#D6CEE2'], ['Ground', '#E1DAE9'],
  ['Pavement', '#F4F1F8'], ['White', '#FFFFFF'],
  ['Deep leaf', '#58AF80'], ['Leaf', '#74C997'], ['Lawn', '#A9E2BE'], ['Pale mint', '#D4F2DE'],
  ['Rose', '#D9799F'], ['Pink', '#F4A3C3'], ['Blush', '#FBD3E3'],
  ['Deep teal', '#3FA79E'], ['Teal', '#7FD6CE'], ['Ice teal', '#C4F0EB'],
  ['Violet', '#8E7BD0'], ['Lavender', '#B7A5F0'], ['Lilac', '#E0D8FB'],
  ['Sky', '#6FA5DE'], ['Pale sky', '#9CC7F3'],
  ['Gold', '#F2C75C'], ['Butter', '#FFE38A'],
  ['Coral', '#F29A74'], ['Peach', '#FFB797'],
  ['Neon pink', '#EE4C93'], ['Neon cyan', '#3FE0F0'],
  ['Wood', '#9C7C6B'],
];
/* Night: the city is drawn in the day palette and swapped to night at draw time, the way SNES games
   swapped palettes. Surfaces darken and cool; window lights, gold, and neon keep glowing. */
const NIGHT = {
  '#2B2542': '#0D0A16', '#5A5073': '#0E0B18', '#7A7394': '#3B3456', '#908BA5': '#2E2942',
  '#B6ABCA': '#2A243E', '#CBC2DB': '#373050', '#D6CEE2': '#4A4268', '#E1DAE9': '#3D3656',
  '#F4F1F8': '#564D7C', '#FFFFFF': '#7C72A8',
  '#58AF80': '#1C4A3B', '#74C997': '#256148', '#A9E2BE': '#2F6B56', '#D4F2DE': '#3B5E55',
  '#D9799F': '#7A3558', '#F4A3C3': '#A24D78', '#FBD3E3': '#B7739A',
  '#3FA79E': '#174744', '#7FD6CE': '#2C6E6B', '#C4F0EB': '#3F8B87',
  '#8E7BD0': '#3E3378', '#B7A5F0': '#5B4BA0', '#E0D8FB': '#7E71C0',
  '#6FA5DE': '#274C80', '#9CC7F3': '#3F6BA3',
  '#F2C75C': '#F2C75C', '#FFE38A': '#FFE38A',
  '#F29A74': '#8E4635', '#FFB797': '#B0664F',
  '#EE4C93': '#FF5FA8', '#3FE0F0': '#4FF0FF',
  '#9C7C6B': '#4F3A31',
};
const nightTable = new Map(Object.entries(NIGHT).map(([d, n]) => [parseInt(d.slice(1), 16), hexToRgb(n)]));
/* Lit windows, lamps, gold, and neon keep glowing at night. */
function isLightColor(r, g, b) {
  return (r > 220 && g > 190 && b < 205) || (r > 220 && g < 110 && b > 120) || (g > 200 && b > 220 && r < 120);
}
/* A color's night version: the hand-picked table for the city palette, and for anything else the same
   hue with the lightness dropped and a cool shift toward blue-violet. */
function nightOf(r, g, b) {
  const key = (r << 16) | (g << 8) | b;
  let v = nightTable.get(key);
  if (v) return v;
  if (isLightColor(r, g, b)) v = [r, g, b];
  else {
    const [hh, ss, ll] = rgbToHsl(r, g, b);
    let dh = 0.694 - hh; if (dh > 0.5) dh -= 1; if (dh < -0.5) dh += 1;
    v = hslToRgb((hh + dh * 0.25 + 1) % 1, Math.min(1, ss * 0.55 + 0.05), 0.05 + ll * 0.36);   // darker, cooler, and quieter
  }
  nightTable.set(key, v);
  return v;
}
function rgbToHsl(r, g, b) {
  r /= 255; g /= 255; b /= 255;
  const mx = Math.max(r, g, b), mn = Math.min(r, g, b), l = (mx + mn) / 2;
  if (mx === mn) return [0, 0, l];
  const d = mx - mn, s = l > 0.5 ? d / (2 - mx - mn) : d / (mx + mn);
  const h = mx === r ? (g - b) / d + (g < b ? 6 : 0) : mx === g ? (b - r) / d + 2 : (r - g) / d + 4;
  return [h / 6, s, l];
}
function hslToRgb(h, s, l) {
  if (!s) { const v = Math.round(l * 255); return [v, v, v]; }
  const q = l < 0.5 ? l * (1 + s) : l + s - l * s, p = 2 * l - q;
  const f = t => { t = (t + 1) % 1; return t < 1 / 6 ? p + (q - p) * 6 * t : t < 0.5 ? q : t < 2 / 3 ? p + (q - p) * (2 / 3 - t) * 6 : p; };
  return [Math.round(f(h + 1 / 3) * 255), Math.round(f(h) * 255), Math.round(f(h - 1 / 3) * 255)];
}
const Light = (() => {
  let mode = 'auto', t = -1;
  const subs = [], cache = new Map();
  try { const m = localStorage.getItem('nullovation-city:light'); if (m === 'day' || m === 'night' || m === 'auto' || m === 'dusk') mode = m; } catch (e) {}
  /* Auto's hours are the city's: night starts at 19:00 and day at 06:30 unless set, with dusk and dawn blending over
     the 90 minutes before each. Times wrap round midnight, so any two hours work. */
  const BLEND = 90;
  const minutes = s => { const m = /^(\d\d):(\d\d)$/.exec(s || ''); return m ? +m[1] * 60 + +m[2] : null; };
  function hours() {
    const c = typeof DB !== 'undefined' && DB.city ? DB.city : {};
    return { night: minutes(c.night) ?? 1140, day: minutes(c.day) ?? 390 };
  }
  const since = (m, from) => ((m - from) % 1440 + 1440) % 1440;     // minutes from `from` forward to m
  function fromClock(d = new Date()) {
    const m = d.getHours() * 60 + d.getMinutes(), { night, day } = hours();
    const dusk = since(m, night - BLEND), dawn = since(m, day - BLEND);
    if (dusk < BLEND) return dusk / BLEND;
    if (dawn < BLEND) return 1 - dawn / BLEND;
    return since(m, day) < since(night - BLEND, day) ? 0 : 1;        // between day's start and dusk: day
  }
  const target = () => mode === 'day' ? 0 : mode === 'night' ? 1 : mode === 'dusk' ? 0.5 : Math.round(fromClock() * 8) / 8;   // dusk: the halfway light
  function update() {
    const n = target();
    if (n === t) return false;
    t = n; cache.clear();
    for (const f of subs) f();
    return true;
  }
  function setMode(m) { mode = m; try { localStorage.setItem('nullovation-city:light', m); } catch (e) {} update(); }
  /* One color at the current light. Returns null when nothing changes (full day). */
  function rgb(r, g, b) {
    if (t <= 0) return null;
    const key = (r << 16) | (g << 8) | b;
    let v = cache.get(key);
    if (!v) {
      const n = nightOf(r, g, b);
      v = t >= 1 ? n : [Math.round(r + (n[0] - r) * t), Math.round(g + (n[1] - g) * t), Math.round(b + (n[2] - b) * t)];
      cache.set(key, v);
    }
    return v;
  }
  function mixHex(day, night) {
    if (t <= 0) return day;
    const a = hexToRgb(day), b = hexToRgb(night);
    return '#' + a.map((c, i) => Math.round(c + (b[i] - c) * t).toString(16).padStart(2, '0')).join('');
  }
  const phase = () => {
    if (mode === 'dusk') return 'dusk';
    if (t <= 0) return 'day';
    if (t >= 1) return 'night';
    const d = new Date(), m = d.getHours() * 60 + d.getMinutes();
    return since(m, hours().day - BLEND) < BLEND ? 'dawn' : 'dusk';
  };
  update();
  return { update, setMode, rgb, mixHex, phase, fromClock, onChange: f => subs.push(f), get t() { return t; }, get mode() { return mode; } };
})();

/* Motion, on this computer: Full, Saver at 30 frames a second, or Still, with nothing moving. Until one is chosen it
   follows the system: Still when the system asks for reduced motion, Full otherwise. */
const Motion = (() => {
  const KEY = 'nullovation-city:motion', MODES = ['full', 'saver', 'still'];
  let chosen = (() => { try { const v = localStorage.getItem(KEY); return MODES.includes(v) ? v : null; } catch (e) { return null; } })();
  const dflt = () => reducedMotion() ? 'still' : 'full';
  const mode = () => chosen || dflt();
  function set(v) {
    chosen = MODES.includes(v) ? v : null;                         // null: follow the system again
    try { if (chosen) localStorage.setItem(KEY, chosen); else localStorage.removeItem(KEY); } catch (e) { /* this visit only */ }
  }
  return { mode, dflt, set, still: () => mode() === 'still', saver: () => mode() === 'saver', MODES };
})();
function shadeData(d) {
  if (Light.t <= 0) return d;
  for (let i = 0; i < d.length; i += 4) {
    if (!d[i + 3]) continue;
    const v = Light.rgb(d[i], d[i + 1], d[i + 2]);
    d[i] = v[0]; d[i + 1] = v[1]; d[i + 2] = v[2];
  }
  return d;
}
function shadeCanvas(c) {
  if (Light.t <= 0) return c;
  const g = c.getContext('2d', { willReadFrequently: true });
  const img = g.getImageData(0, 0, c.width, c.height);
  shadeData(img.data);
  g.putImageData(img, 0, 0);
  return c;
}
/* The ground's colors by day and by night; the map mixes them by the current light. */
const WORLD_DAY = {
  haze: '#2B2F4A', slabL: '#CFC6DF', slabR: '#BBB1CF', strata: '#DCD5E8', rim: '#FFFFFF',
  road: '#908BA5', walk: '#D6CEE2', curb: '#F4F1F8', joint: '#CBC2DB', dash: '#FFE38A', stripe: '#E1DAE9',
  roadDk: '#857F9B', roadLt: '#9D98B1', patch: '#9893AC', patchEdge: '#837D99', crack: '#7A7394',
  manhole: '#7A7394', manholeHi: '#A6A1B8', drain: '#655E7E', paint: '#F4F1F8',
  verge: '#A9E2BE', vergeDk: '#74C997', island: '#A9E2BE',
};
const WORLD_NIGHT = {
  haze: '#120F1F', slabL: '#2B2540', slabR: '#221D35', strata: '#342D4C', rim: '#4E4670',
  road: '#26213A', walk: '#383150', curb: '#554C7A', joint: '#302A46', dash: '#E0C35E', stripe: '#433B5F',
  roadDk: '#211D33', roadLt: '#2D2744', patch: '#2A2440', patchEdge: '#201B31', crack: '#1B1729',
  manhole: '#1E1A2E', manholeHi: '#3A3354', drain: '#17131F', paint: '#4E4670',
  verge: '#26423A', vergeDk: '#1F3A30', island: '#26423A',
};
const worldColor = k => Light.mixHex(WORLD_DAY[k], WORLD_NIGHT[k]);

/* The palette as a PNG strip of 8 px swatches: the file both image tools take as a forced palette. */
function paletteCanvas() {
  const [c, g] = mkCanvas(CITY_PALETTE.length * 8, 8);
  CITY_PALETTE.forEach(([, hex], i) => { g.fillStyle = hex; g.fillRect(i * 8, 0, 8, 8); });
  return c;
}

/* ---------- color ---------- */
function hexToRgb(hex) { const n = parseInt(hex.slice(1), 16); return [(n >> 16) & 255, (n >> 8) & 255, n & 255]; }
function rgbToHex(c) { return '#' + c.map(v => clamp(Math.round(v), 0, 255).toString(16).padStart(2, '0')).join(''); }
function mix(a, b, t) { const A = hexToRgb(a), B = hexToRgb(b); return rgbToHex(A.map((v, i) => v + (B[i] - v) * t)); }
const lighten = (c, t) => mix(c, '#FFFFFF', t);
const darken = (c, t) => mix(c, '#2B2542', t);
function desat(c, t) {
  const [r, g, b] = hexToRgb(c); const l = 0.3 * r + 0.59 * g + 0.11 * b;
  return rgbToHex([r + (l - r) * t, g + (l - g) * t, b + (l - b) * t]);
}

/* ---------- crisp raster helpers (1 unit = 1 art pixel) ---------- */
function mkCanvas(w, hgt) {
  const c = document.createElement('canvas');
  c.width = Math.max(1, Math.ceil(w)); c.height = Math.max(1, Math.ceil(hgt));
  const g = c.getContext('2d', { willReadFrequently: true });
  g.imageSmoothingEnabled = false;
  return [c, g];
}
/* Scanline polygon fill at pixel centers: aliased edges, true 2:1 isometric stairs. */
function fillPoly(g, pts, color) {
  let minY = Infinity, maxY = -Infinity;
  for (const p of pts) { if (p[1] < minY) minY = p[1]; if (p[1] > maxY) maxY = p[1]; }
  g.fillStyle = color;
  for (let y = Math.floor(minY); y < Math.ceil(maxY); y++) {
    const yc = y + 0.5, xs = [];
    for (let i = 0; i < pts.length; i++) {
      const [x1, y1] = pts[i], [x2, y2] = pts[(i + 1) % pts.length];
      if ((y1 <= yc && y2 > yc) || (y2 <= yc && y1 > yc)) xs.push(x1 + ((yc - y1) / (y2 - y1)) * (x2 - x1));
    }
    xs.sort((a, b) => a - b);
    for (let k = 0; k + 1 < xs.length; k += 2) {
      const xa = Math.round(xs[k]), xb = Math.round(xs[k + 1]);
      if (xb > xa) g.fillRect(xa, y, xb - xa, 1);
    }
  }
}
/* Box standing on the floor point (cx, by): square footprint hw wide on each side, hgt tall. */
function isoBox(g, cx, by, hw, hgt, cols) {
  const hh = hw / 2;
  fillPoly(g, [[cx - hw, by - hh], [cx, by], [cx, by - hgt], [cx - hw, by - hh - hgt]], cols.left);
  fillPoly(g, [[cx, by], [cx + hw, by - hh], [cx + hw, by - hh - hgt], [cx, by - hgt]], cols.right);
  fillPoly(g, [[cx, by - 2 * hh - hgt], [cx + hw, by - hh - hgt], [cx, by - hgt], [cx - hw, by - hh - hgt]], cols.top);
}
function diamond(g, cx, cy, hw, hh, color) { fillPoly(g, [[cx, cy - hh], [cx + hw, cy], [cx, cy + hh], [cx - hw, cy]], color); }
function outline(c, color) {
  const g = c.getContext('2d', { willReadFrequently: true });
  const w = c.width, ht = c.height;
  const d = g.getImageData(0, 0, w, ht).data;
  const a = (x, y) => (x < 0 || y < 0 || x >= w || y >= ht) ? 0 : d[(y * w + x) * 4 + 3];
  g.fillStyle = color;
  for (let y = 0; y < ht; y++) for (let x = 0; x < w; x++) {
    if (a(x, y) === 0 && (a(x - 1, y) || a(x + 1, y) || a(x, y - 1) || a(x, y + 1))) g.fillRect(x, y, 1, 1);
  }
}
function alphaMask(c) {
  const d = c.getContext('2d', { willReadFrequently: true }).getImageData(0, 0, c.width, c.height).data;
  const m = new Uint8Array(c.width * c.height);
  for (let i = 0; i < m.length; i++) m[i] = d[i * 4 + 3] > 40 ? 1 : 0;
  return m;
}
function blob(g, cx, cy, r, cols) {
  const r2 = r * r;
  for (let dy = -Math.ceil(r); dy <= Math.ceil(r); dy++) for (let dx = -Math.ceil(r); dx <= Math.ceil(r); dx++) {
    if (dx * dx + dy * dy > r2) continue;
    const s = dx + dy;
    g.fillStyle = s < -r * 0.6 ? cols.hi : s > r * 0.5 ? cols.dk : cols.base;
    g.fillRect(cx + dx, cy + dy, 1, 1);
  }
}

/* ---------- plot: the decorated square every building stands on ---------- */
const PLOT = { W: 128, T: 26, RAISE: 3 };
PLOT.H = PLOT.T + 64 + PLOT.RAISE + 1;

function renderPlotLayers() {
  const { W, T } = PLOT, R = PLOT.RAISE;
  const P = (a, b) => [64 + (a - b) * 16, T + (a + b) * 8];
  const [cu, gu] = mkCanvas(W, PLOT.H);
  const [co, go] = mkCanvas(W, PLOT.H);
  const quad = (g, a0, b0, a1, b1, col) => fillPoly(g, [P(a0, b0), P(a1, b0), P(a1, b1), P(a0, b1)], col);

  const L = P(0, 4), B = P(4, 4), Rt = P(4, 0), Tp = P(0, 0);
  fillPoly(gu, [L, B, [B[0], B[1] + R], [L[0], L[1] + R]], PAL.plotSideL);
  fillPoly(gu, [B, Rt, [Rt[0], Rt[1] + R], [B[0], B[1] + R]], PAL.plotSideR);
  fillPoly(gu, [Tp, Rt, B, L], PAL.pave);

  quad(gu, 0, 3.25, 3.25, 4, PAL.lawn);          // front-left lawn strip
  quad(gu, 0, 0, 0.75, 3.25, PAL.lawn);          // back-left lawn strip
  quad(gu, 3.25, 0.5, 4, 3.25, PAL.asphalt);     // parking stub along the front-right edge
  quad(gu, 3.25, 0.5, 4, 0.75, PAL.asphaltHi);
  gu.fillStyle = PAL.lines;
  for (const b of [1.25, 1.9, 2.55]) {           // parking lines across the stub
    const [x0, y0] = P(3.25, b);
    for (let k = 1; k < 5; k++) gu.fillRect(x0 + 2 * k, y0 + k, 2, 1);
  }
  quad(gu, 0.75, 0.75, 3.25, 3.25, PAL.paveDk);  // plinth ring around the footprint

  const rnd = mulberry32(11);
  gu.fillStyle = PAL.lawnDk;                     // lawn texture
  for (let i = 0; i < 26; i++) {
    const a = rnd() * 3.1, b = 3.35 + rnd() * 0.55; const [x, y] = P(a, b); gu.fillRect(Math.round(x), Math.round(y), 1, 1);
  }
  for (let i = 0; i < 18; i++) {
    const a = 0.1 + rnd() * 0.55, b = 0.2 + rnd() * 2.9; const [x, y] = P(a, b); gu.fillRect(Math.round(x), Math.round(y), 1, 1);
  }
  const flowers = [PAL.flowerA, PAL.flowerB, PAL.flowerC];
  for (let i = 0; i < 9; i++) {
    const a = 0.15 + rnd() * 0.45, b = 0.4 + rnd() * 2.6; const [x, y] = P(a, b);
    gu.fillStyle = flowers[i % 3]; gu.fillRect(Math.round(x), Math.round(y), 1, 1);
  }
  gu.fillStyle = PAL.rim;                        // light catching the two front edges
  for (let k = 0; k < 32; k++) { gu.fillRect(L[0] + 2 * k, L[1] + k - 1, 2, 1); gu.fillRect(B[0] + 2 * k, B[1] - k - 1, 2, 1); }

  const trees = [P(0.95, 3.62), P(2.3, 3.64)];
  for (const [x, y] of trees) diamond(gu, Math.round(x) + 1, Math.round(y) + 1, 6, 3, PAL.lawnShadow);
  const [bx, by] = P(0.38, 1.7);                 // a bush behind the building
  blob(gu, Math.round(bx), Math.round(by) - 2, 3.2, { base: PAL.canopy, hi: PAL.canopyHi, dk: PAL.canopyDk });

  for (const [x0, y0] of trees) {
    const x = Math.round(x0), y = Math.round(y0);
    go.fillStyle = PAL.trunk; go.fillRect(x, y - 5, 2, 5);
    blob(go, x + 1, y - 11, 5.6, { base: PAL.canopy, hi: PAL.canopyHi, dk: PAL.canopyDk });
  }
  const [lx0, ly0] = P(3.62, 0.9);               // street lamp by the parking stub
  const lx = Math.round(lx0), ly = Math.round(ly0);
  go.fillStyle = PAL.pole;
  go.fillRect(lx, ly - 18, 1, 18);
  go.fillRect(lx - 4, ly - 19, 5, 1);
  go.fillRect(lx - 5, ly - 18, 3, 2);
  go.fillStyle = PAL.lampOn;
  go.fillRect(lx - 5, ly - 16, 3, 1);
  outline(co, PAL.outline);
  return { under: shadeCanvas(cu), over: shadeCanvas(co) };
}
/* The standard plot on its own: slab and pavement, no decorations. Real art stands on it. */
function renderBarePlot() {
  const { W, T } = PLOT, R = PLOT.RAISE;
  const P = (a, b) => [64 + (a - b) * 16, T + (a + b) * 8];
  const [c, g] = mkCanvas(W, PLOT.H);
  const L = P(0, 4), B = P(4, 4), Rt = P(4, 0), Tp = P(0, 0);
  fillPoly(g, [L, B, [B[0], B[1] + R], [L[0], L[1] + R]], PAL.plotSideL);
  fillPoly(g, [B, Rt, [Rt[0], Rt[1] + R], [B[0], B[1] + R]], PAL.plotSideR);
  fillPoly(g, [Tp, Rt, B, L], PAL.pave);
  g.fillStyle = PAL.rim;
  for (let k = 0; k < 32; k++) { g.fillRect(L[0] + 2 * k, L[1] + k - 1, 2, 1); g.fillRect(B[0] + 2 * k, B[1] - k - 1, 2, 1); }
  return shadeCanvas(c);
}

/* ---------- placeholder building: generated from the project id, so it never changes ---------- */
const BLD = { PAD: 1, FOOT: 64 };
function renderBuilding(key) {
  const seed = hashStr(key);
  const rnd = mulberry32(seed);
  const base0 = BUILD_COLORS[seed % BUILD_COLORS.length];
  const H = [44, 54, 64, 76][(seed >>> 4) & 3];
  const roof = (seed >>> 7) % 3;
  const extra = roof === 1 ? 14 : roof === 2 ? 10 : 4;
  const PAD = BLD.PAD;
  const CW = 64 + PAD * 2, CH = 32 + H + extra + PAD * 2;
  const [c, g] = mkCanvas(CW, CH);
  const ox = PAD, by = CH - PAD, cx = ox + 32;
  const base = base0;
  const cols = { left: base, right: darken(base, 0.2), top: lighten(base, 0.4) };
  isoBox(g, cx, by, 32, H, cols);

  /* plinth band */
  fillPoly(g, [[ox, by - 16], [cx, by], [cx, by - 4], [ox, by - 20]], darken(cols.left, 0.1));
  fillPoly(g, [[cx, by], [ox + 64, by - 16], [ox + 64, by - 20], [cx, by - 4]], darken(cols.right, 0.1));

  /* windows follow the wall slant */
  const glassL = darken(base, 0.48), glassR = darken(base, 0.55);
  const lit = PAL.lit;
  const topL = x => by - 16 - H + (x - ox) / 2;
  const topR = x => by - H - (x - cx) / 2;
  const winL = (xs, off, w, hgt, col) => { const x0 = ox + xs, y0 = topL(x0) + off; fillPoly(g, [[x0, y0], [x0 + w, y0 + w / 2], [x0 + w, y0 + w / 2 + hgt], [x0, y0 + hgt]], col); };
  const winR = (xs, off, w, hgt, col) => { const x0 = cx + xs, y0 = topR(x0) + off; fillPoly(g, [[x0, y0], [x0 + w, y0 - w / 2], [x0 + w, y0 - w / 2 + hgt], [x0, y0 + hgt]], col); };
  const rows = Math.max(1, Math.floor((H - 26) / 10) + 1);
  for (let r = 0; r < rows; r++) {
    const off = 6 + r * 10;
    for (const xs of [4, 12, 20]) winL(xs, off, 4, 6, rnd() < 0.34 ? lit : glassL);
    for (const xs of [6, 14, 22]) winR(xs, off, 4, 6, rnd() < 0.28 ? lit : glassR);
  }
  /* door with a little awning, on the front-left wall */
  winL(22, H - 12, 6, 11, darken(base, 0.62));
  winL(20, H - 14, 10, 2, lighten(base, 0.55));

  /* roof: a parapet, then one of three roof tops */
  fillPoly(g, [[cx, by - 32 - H + 3], [ox + 58, by - 16 - H], [cx, by - H - 3], [ox + 6, by - 16 - H]], mix(cols.top, cols.right, 0.28));
  const rc = by - H - 16; // floor point at the roof centre
  if (roof === 0) {
    isoBox(g, cx - 6, rc + 6, 8, 6, { left: '#ECE9F2', right: '#CFCADB', top: '#FFFFFF' });
    g.fillStyle = '#CFCADB'; g.fillRect(cx + 10, rc - 6, 2, 6); g.fillStyle = '#FFFFFF'; g.fillRect(cx + 10, rc - 7, 2, 1);
  } else if (roof === 1) {
    const b2 = BUILD_COLORS[(seed >>> 11) % BUILD_COLORS.length];
    const t = b2;
    isoBox(g, cx, rc + 8, 16, 18, { left: lighten(t, 0.1), right: darken(t, 0.16), top: lighten(t, 0.45) });
    const yl = rc - 12, yr = rc - 9; // window tops on the tier's two walls
    fillPoly(g, [[cx - 12, yl], [cx - 8, yl + 2], [cx - 8, yl + 8], [cx - 12, yl + 6]], rnd() < 0.5 ? lit : darken(t, 0.5));
    fillPoly(g, [[cx + 6, yr], [cx + 10, yr - 2], [cx + 10, yr + 4], [cx + 6, yr + 6]], darken(t, 0.58));
  } else {
    g.fillStyle = PAL.pole; g.fillRect(cx, rc - 22, 1, 22); g.fillRect(cx - 2, rc - 10, 5, 1);
    g.fillStyle = PAL.beacon; g.fillRect(cx, rc - 24, 1, 2);
    isoBox(g, cx + 12, rc + 4, 4, 4, { left: '#ECE9F2', right: '#CFCADB', top: '#FFFFFF' });
  }
  outline(c, PAL.outline);
  shadeCanvas(c);
  return { canvas: c, CW, CH, mask: alphaMask(c) };
}

/* ---------- rings and markers drawn on the ground ---------- */
function ringCanvas(hw, hh, thick, color, dashed) {
  const [c, g] = mkCanvas(hw * 2 + 4, hh * 2 + 4);
  const cx = hw + 2, cy = hh + 2;
  diamond(g, cx, cy, hw, hh, color);
  g.globalCompositeOperation = 'destination-out';
  diamond(g, cx, cy, hw - thick * 2, hh - thick, '#000');
  g.globalCompositeOperation = 'source-over';
  if (dashed) {
    const img = g.getImageData(0, 0, c.width, c.height);
    for (let y = 0; y < c.height; y++) for (let x = 0; x < c.width; x++) if (((x >> 3) & 1) === 0) img.data[(y * c.width + x) * 4 + 3] = 0;
    g.putImageData(img, 0, 0);
  }
  return { canvas: c, cx, cy };
}
function fillCanvas(hw, hh, color) {
  const [c, g] = mkCanvas(hw * 2 + 4, hh * 2 + 4);
  diamond(g, hw + 2, hh + 2, hw, hh, color);
  return { canvas: c, cx: hw + 2, cy: hh + 2 };
}

/* ---------- pixel icons for the interface ---------- */
const ICONS = {
  sun: ['...#...', '.#.#.#.', '..###..', '###+###', '..###..', '.#.#.#.', '...#...'],
  moon: ['..###..', '.##....', '##.....', '##.....', '##.....', '.##...#', '..####.'],
  dusk: ['#..#..#', '.#.#.#.', '..+++..', '.+++++.', '#######', '.......', '..###..'],
  doc: ['.#######....', '.#.....##...', '.#.....#.#..', '.#.....####.', '.#........#.', '.#.++++++.#.', '.#........#.', '.#.++++++.#.', '.#........#.', '.#.++++...#.', '.#........#.', '.##########.'],
  task: ['............', '.........+++', '........+++.', '.#######+++.', '.#.....+++#.', '.#+...+++.#.', '.#++.+++..#.', '.#.+++++..#.', '.#..+++...#.', '.#...+....#.', '.#........#.', '.##########.'],
  code: ['............', '############', '#++++++++++#', '############', '#..........#', '#.#........#', '#..#.......#', '#...#......#', '#..#..###..#', '#.#........#', '#..........#', '############'],
  chat: ['............', '.##########.', '#..........#', '#.++++++++.#', '#..........#', '#.++++++...#', '#..........#', '.###..#####.', '...#.#......', '...##.......', '...#........', '............'],
  folder: ['............', '.####.......', '#++++#......', '#++++#######', '#++++++++++#', '#++++++++++#', '#++++++++++#', '#++++++++++#', '#++++++++++#', '############', '............', '............'],
  web: ['....####....', '..##....##..', '.#..####..#.', '.#.#....#.#.', '#..#....#..#', '############', '#..#....#..#', '.#.#....#.#.', '.#..####..#.', '..##....##..', '....####....', '............'],
  claude: ['.....++.....', '.+...++...+.', '..+..++..+..', '...+.++.+...', '....++++....', '++++++++++++', '++++++++++++', '....++++....', '...+.++.+...', '..+..++..+..', '.+...++...+.', '.....++.....'],
  github: ['....####....', '..########..', '.##.####.##.', '.##......##.', '##........##', '##........##', '##........##', '###......###', '.#.##..####.', '.##.#..####.', '..###..###..', '....#..#....'],
  plus: ['..........', '....##....', '....##....', '....##....', '.########.', '.########.', '....##....', '....##....', '....##....', '..........'],
  minus: ['..........', '..........', '..........', '..........', '.########.', '.########.', '..........', '..........', '..........', '..........'],
  close: ['..........', '.##....##.', '..##..##..', '...####...', '....##....', '...####...', '..##..##..', '.##....##.', '..........', '..........'],
  door: ['..######..', '.#++++++#.', '.#+####+#.', '.#+#..#+#.', '.#+#..#+#.', '.#+#.##+#.', '.#+#..#+#.', '.#+#..#+#.', '##########', '..........'],
  grip: ['........', '.##..##.', '.##..##.', '........', '.##..##.', '.##..##.', '........', '.##..##.', '.##..##.', '........'],
  up: ['..........', '..........', '....##....', '...####...', '..##..##..', '.##....##.', '..........', '..........'],
  down: ['..........', '..........', '.##....##.', '..##..##..', '...####...', '....##....', '..........', '..........'],
  flag: ['.#........', '.#######..', '.#+++++++#', '.#++++++#.', '.#+++++++#', '.########.', '.#........', '.#........', '.#........', '###.......'],
  camera: ['....####....', '.##########.', '#++++++++++#', '#+++####+++#', '#++#oooo#++#', '#++#oooo#++#', '#+++####+++#', '#++++++++++#', '.##########.', '............'],
  recap: ['.##########.', '#..........#', '#.##.##.##.#', '#..........#', '#.##.##.##.#', '#..........#', '#.##.++.##.#', '#.....++...#', '.##########.', '............'],
  car: ['..........', '...####...', '..#+..+#..', '.#++..++#.', '##########', '#++++++++#', '##########', '.##....##.', '.##....##.', '..........'],
  alert: ['.########.', '#++++++++#', '#+++##+++#', '#+++##+++#', '#+++##+++#', '#++++++++#', '#+++##+++#', '#++++++++#', '.###..###.', '....##....'],
  caretR: ['#......', '##.....', '###....', '####...', '###....', '##.....', '#......'],
  caretD: ['#######', '.#####.', '..###..', '...#...', '.......', '.......', '.......'],
  pencil: ['.......##.', '......#++#', '.....#++#.', '....#++#..', '...#++#...', '..#++#....', '.#++#.....', '.##.......', '#.........', '..........'],
  more: ['....##....', '....##....', '..........', '..........', '....##....', '....##....', '..........', '..........', '....##....', '....##....'],
  flip: ['.....#.....', '.#.......+.', '.##..#..++.', '.###...+++.', '.####.++++.', '.###...+++.', '.##..#..++.', '.#.......+.', '.....#.....', '...........'],
  download: ['....##....', '....##....', '....##....', '.#..##..#.', '.##.##.##.', '..######..', '...####...', '....##....', '#........#', '##########'],
  clock: ['...####...', '.##....##.', '.#..#...#.', '#...#....#', '#...###..#', '#........#', '.#......#.', '.##....##.', '...####...', '..........'],
  copy: ['...######.', '...#....#.', '######..#.', '#....#..#.', '#....#..#.', '#....####.', '#....#....', '#....#....', '######....', '..........'],
  gear: ['....##....', '.#.####.#.', '..######..', '.###..###.', '####..####', '####..####', '.###..###.', '..######..', '.#.####.#.', '....##....'],
  back: ['..........', '....#.....', '...##.....', '..########', '.#########', '..########', '...##.....', '....#.....', '..........', '..........'],
  help: ['..####..', '.##..##.', '.....##.', '....##..', '...##...', '...##...', '........', '...##...', '...##...', '........'],
  walker: ['....##....', '....##....', '..........', '...####...', '..#.##.#..', '..#.##.#..', '....##....', '...#..#...', '...#..#...', '..##..##..'],
  disk: ['#########.', '#+#....#+#', '#+#....#+#', '#+######+#', '#++++++++#', '#+######+#', '#+#....#+#', '#+#....#+#', '#+######+#', '##########'],
  arrow: ['######....', '######....', '####......', '##.##.....', '##..##....', '##...##...', '......##..', '.......##.', '........##', '..........'],
  brand: ['.......#........', '......###.......', '......#+#.......', '......#o#.......', '......#+#.......', '..###.#o#.####..', '..#+#.#+#.#++#..', '..#o#.#o#.#oo#..', '..#+#.#+#.#++#..', '..#o#.#o#.#oo#..', '..#+#.#+#.#++#..', '################'],
};
const ICON_NAMES = { doc: 'Doc', code: 'Code', github: 'GitHub', claude: 'Claude', chat: 'Chat', folder: 'Folder', web: 'Web' };
const ICON_ACCENT = { claude: '#D97757' };             // Claude's spark keeps its own orange
function iconSvg(name, size = 24, accent = ICON_ACCENT[name] || 'var(--accent)') {
  const rows = ICONS[name]; if (!rows) return '';
  const w = rows[0].length, ht = rows.length;
  let out = '';
  rows.forEach((r, y) => {
    let x = 0;
    while (x < w) {
      const ch = r[x];
      if (ch === '.') { x++; continue; }
      let x2 = x; while (x2 < w && r[x2] === ch) x2++;
      const fill = ch === '#' ? 'currentColor' : ch === '+' ? accent : 'var(--ic-o, #FFFFFF)';
      out += `<rect x="${x}" y="${y}" width="${x2 - x}" height="1" style="fill:${fill}"/>`;
      x = x2;
    }
  });
  return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${w} ${ht}" width="${size}" height="${Math.round(size * ht / w)}" shape-rendering="crispEdges" aria-hidden="true" focusable="false">${out}</svg>`;
}
function iconEl(name, size, accent) { const s = h('span', { class: 'ic', 'aria-hidden': 'true' }); s.style.display = 'inline-flex'; s.innerHTML = iconSvg(name, size, accent); return s; }

/* ---------- block art supplied by the user: PNG or GIF, still or animated ---------- */
const Art = (() => {
  const cache = new Map();
  const MAX_W = 512;
  function dataUrlBytes(url) {
    const bin = atob(url.slice(url.indexOf(',') + 1));
    const out = new Uint8Array(bin.length);
    for (let i = 0; i < bin.length; i++) out[i] = bin.charCodeAt(i);
    return out;
  }
  /* Every frame as full RGBA, plus delays. GIFs are decoded here so every frame is available. */
  async function readFrames(url) {
    if (/^data:image\/gif/i.test(url)) {
      const g = decodeGif(dataUrlBytes(url));
      if (!g.frames.length) throw new Error('This GIF has no frames.');
      return { w: g.width, h: g.height, frames: g.frames.map(f => ({ rgba: f.rgba, delay: f.delay < 20 ? 100 : f.delay })) };
    }
    const img = await loadImage(url);
    const [c, g] = mkCanvas(img.naturalWidth, img.naturalHeight);
    g.drawImage(img, 0, 0);
    return { w: c.width, h: c.height, frames: [{ rgba: g.getImageData(0, 0, c.width, c.height).data, delay: 0 }] };
  }
  /* The box around everything that is ever visible, across all frames. */
  function contentBox(src) {
    const { w, h } = src;
    let x0 = w, y0 = h, x1 = -1, y1 = -1;
    for (const f of src.frames) {
      const d = f.rgba;
      for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) {
        if (d[(y * w + x) * 4 + 3] === 0) continue;
        if (x < x0) x0 = x; if (x > x1) x1 = x; if (y < y0) y0 = y; if (y > y1) y1 = y;
      }
    }
    return x1 < 0 ? null : { x: 0, y: y0, w, h: y1 - y0 + 1 };   // full width kept on purpose: see the art contract
  }
  /* Reads a file's image data without storing anything, for checks before upload. */
  async function probe(url) {
    const src = await readFrames(url);
    const box = contentBox(src);
    if (!box) throw new Error('The image is fully transparent.');
    return { srcW: src.w, srcH: src.h, w: box.w, h: box.h, frames: src.frames.length,
      trimmed: { left: box.x, top: box.y, right: src.w - box.x - box.w, bottom: src.h - box.y - box.h } };
  }
  const TILE = 32;
  /* Day colors are kept; canvases are rebuilt from them whenever the light changes. */
  function paint(entry) {
    const toCanvas = (rgba, w, h) => {
      const [c, g] = mkCanvas(w, h);
      const img = g.createImageData(w, h);
      img.data.set(rgba);
      shadeData(img.data);
      g.putImageData(img, 0, 0);
      return c;
    };
    entry.base = toCanvas(entry.src.base, entry.w, entry.h);
    entry.frames = entry.src.patches.map(list => list.map(q => ({ x: q.x, y: q.y, w: q.w, h: q.h, c: toCanvas(q.rgba, q.w, q.h) })));
  }
  async function set(id, url) {
    const src = await readFrames(url);
    const box = contentBox(src);
    if (!box) throw new Error('The image is fully transparent.');
    const W = box.w, H = box.h;
    const crop = rgba => {
      const out = new Uint8ClampedArray(W * H * 4);
      for (let y = 0; y < H; y++) {
        const from = ((box.y + y) * src.w + box.x) * 4;
        out.set(rgba.subarray(from, from + W * 4), y * W * 4);
      }
      return out;
    };
    const full = src.frames.map(f => crop(f.rgba));
    const base = full[0];
    const mask = new Uint8Array(W * H);                    // clickable wherever any frame is visible
    for (const fr of full) for (let i = 0; i < mask.length; i++) if (fr[i * 4 + 3] > 40) mask[i] = 1;
    // each later frame keeps only the tiles that differ from the first one
    const patches = full.map((fr, fi) => {
      if (fi === 0) return [];
      const list = [];
      for (let ty = 0; ty < H; ty += TILE) for (let tx = 0; tx < W; tx += TILE) {
        const tw = Math.min(TILE, W - tx), th = Math.min(TILE, H - ty);
        let differs = false;
        for (let y = ty; y < ty + th && !differs; y++) {
          const o = (y * W + tx) * 4;
          for (let k = 0; k < tw * 4; k++) if (fr[o + k] !== base[o + k]) { differs = true; break; }
        }
        if (!differs) continue;
        const rgba = new Uint8ClampedArray(tw * th * 4);
        for (let y = 0; y < th; y++) rgba.set(fr.subarray(((ty + y) * W + tx) * 4, ((ty + y) * W + tx + tw) * 4), y * tw * 4);
        list.push({ x: tx, y: ty, w: tw, h: th, rgba });
      }
      return list;
    });
    const delays = src.frames.map(f => f.delay);
    const total = delays.reduce((x, y) => x + y, 0);
    const entry = { url, w: W, h: H, src: { base, patches }, delays, total, count: full.length,
      animated: full.length > 1 && total > 0, mask,
      trimmed: { left: box.x, top: box.y, right: src.w - box.x - box.w, bottom: src.h - box.y - box.h } };
    paint(entry);
    cache.set(id, entry);
    MapView.dropCache(id);
    MapView.invalidate();
    return entry;
  }
  /* Draws frame i at (x, y) scaled to (w, h). */
  function draw(g, a, i, x, y, w, h) {
    const s = w / a.w;
    g.drawImage(a.base, x, y, w, h);
    const list = a.frames[i] || [];
    for (const q of list) g.drawImage(q.c, x + q.x * s, y + q.y * s, q.w * s, q.h * s);
  }
  function indexAt(a, t) {
    if (!a.animated || Motion.still()) return 0;           // Still: every building and park on its first frame
    let m = t % a.total;
    for (let i = 0; i < a.delays.length; i++) { m -= a.delays[i]; if (m < 0) return i; }
    return a.count - 1;
  }
  Light.onChange(() => { for (const e of cache.values()) paint(e); });
  async function load(id) {
    const url = await Store.getArt(id);
    if (!url) return null;   // keep the flag: storage may only be busy, and the next load retries
    try { return await set(id, url); } catch (e) { return null; }
  }
  return { set, load, probe, indexAt, draw, get: id => cache.get(id) || null, drop: id => { cache.delete(id); MapView.dropCache(id); }, MAX_W };
})();
