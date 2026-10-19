/* Celebrations (the sixth task idea, Celebrations, Rounds 1 and 2). Every tick sets off small particles round its
   building (T1), never a firework: a burst like the gold stars his decision rounds tool throws when its name is
   typed. 16 fly out of the building's middle, drift down and twinkle out over 1.5 seconds. Each building picks its
   kind in the project view's Building panel (T2), and starts on stars (T3). Particles are pixel art at the map's
   scale, about the size of the people, with the city's 1 px dark outline, and keep their colors at night, like the
   neon.
   Finishing a milestone of 2 tasks or more (S1) throws a 30 second street party round its building (S2): the building's
   particles burst every 2 seconds or so, party lights hang over its four streets, and, with the traffic on, a crowd
   dances round the block, six party drones loop over it and a bus pulls up to watch (those three live in Traffic).
   Proxima Pace announces it, with Go to it. A milestone throws its party once a day. Motion on Still shows none of it. */
const Celebrate = (() => {
  const KEY = 'nullovation-city:celebrate';
  const BURST_MS = 1500, BURST_N = 16, PARTY_EVERY = 2000, MIN_TASKS = 2;
  let PARTY_MS = 30000;
  const R = Math.random;

  /* ---------- the kinds: rows of letters in the city palette, drawn with a 1 px dark outline ---------- */
  const C = { K: '#2B2542', W: '#FFFFFF', g: '#F2C75C', y: '#FFE38A', G: '#58AF80', L: '#74C997', l: '#A9E2BE', P: '#EE4C93',
    p: '#F4A3C3', c: '#3FE0F0', t: '#7FD6CE', v: '#8E7BD0', a: '#B7A5F0', i: '#E0D8FB', s: '#6FA5DE', S: '#9CC7F3', o: '#F29A74' };
  const ZERO = ['.x.', 'x.x', 'x.x', 'x.x', '.x.'], ONE = ['.x.', 'xx.', '.x.', '.x.', 'xxx'];
  const tint = (rows, k) => ({ rows, sub: { x: k } });
  const DEFS = {
    stars: { colors: ['g'], frames: [{ rows: ['..y..', '.yyg.', 'yyggg', '.ggg.', '.g.g.'] }] },
    binary: { colors: ['c'], frames: [tint(ZERO, 'c'), tint(ONE, 'c')] },
    'gold-binary': { colors: ['g'], frames: [tint(ZERO, 'g'), tint(ONE, 'g')] },
    dollars: { colors: ['L'], frames: [{ rows: ['..G..', '.LLL.', 'L.G..', '.LLL.', '..G.L', '.LLL.', '..G..'] }] },
    lightning: { colors: ['y'], frames: [{ rows: ['...y', '..yy', '.yy.', 'yyyy', '.yy.', 'yy..', 'y...'] }] },
    sparkles: { colors: ['g'], frames: [{ rows: ['..y..', '..y..', 'yyWgg', '..g..', '..g..'] }] },
    hearts: { colors: ['P'], frames: [{ rows: ['pP.PP', 'PPPPP', '.PPP.', '..P..'] }] },
    leaves: { colors: ['L'], frames: [{ rows: ['...LL', '..LlL', '.LlL.', 'LLL..', 'G....'] }] },
    buttons: { colors: ['P', 't', 'g', 's'], frames: ['P', 't', 'g', 's'].map(k => tint(['.x.', 'xWx', '.x.'], k)).concat([{ rows: ['.i.', 'iii', '.i.'] }]) },
    bubbles: { colors: ['W'], frames: [{ rows: ['.WWWWW.', 'WWWWWWW', 'WvWvWvW', '.WWWWW.', '.W.....'] }] },
    coins: { colors: ['g'], turns: true, frames: [{ rows: ['.yy.', 'yWyg', 'yygg', 'yggg', '.gg.'] }, { rows: ['yg', 'Wg', 'yg', 'yg', 'gg'] }, { rows: ['g', 'g', 'g', 'g', 'g'] }] },
    confetti: { colors: ['P', 'c', 'g', 's', 'L', 'a', 'o'],
      frames: [['xx', 'xx'], ['xxx'], ['x', 'x', 'x']].flatMap(rows => ['P', 'c', 'g', 's', 'L', 'a', 'o'].map(k => tint(rows, k))) },
  };
  const defOf = id => DEFS[id] || DEFS.stars;
  const kindOf = p => (p && PARTICLE_IDS.includes(p.particles) ? p.particles : 'stars');
  /* The colors a kind shows, for the party drones. */
  const colorsOf = id => defOf(id).colors.map(k => C[k]);
  const sprites = new Map();
  function sprite(id, n) {
    const key = id + ':' + n;
    if (sprites.has(key)) return sprites.get(key);
    const f = defOf(id).frames[n], w = f.rows[0].length + 2, hgt = f.rows.length + 2;
    const [c, g] = mkCanvas(w, hgt), on = new Set();
    f.rows.forEach((row, y) => [...row].forEach((ch, x) => {
      const k = (f.sub && f.sub[ch]) || ch;
      if (ch !== '.' && C[k]) { g.fillStyle = C[k]; g.fillRect(x + 1, y + 1, 1, 1); on.add((x + 1) + ',' + (y + 1)); }
    }));
    g.fillStyle = C.K;                                               // the city's 1 px dark outline
    for (let y = 0; y < hgt; y++) for (let x = 0; x < w; x++) {
      if (on.has(x + ',' + y)) continue;
      if ([[1, 0], [-1, 0], [0, 1], [0, -1]].some(([dx, dy]) => on.has((x + dx) + ',' + (y + dy)))) g.fillRect(x, y, 1, 1);
    }
    const s = { c, w, h: hgt };
    sprites.set(key, s);
    return s;
  }
  /* The frame a particle shows: coins turn as they fly (full, half, edge, half); the rest keep their own. */
  function frameOf(id, q, now) {
    const d = defOf(id);
    if (d.turns) return [0, 1, 2, 1][Math.floor(now / 125 + q.ph * 4) % 4];
    return q.f % d.frames.length;
  }

  /* ---------- a burst: out from the building's middle, a little fall, then a twinkle ---------- */
  let bursts = [];
  function parts(n = BURST_N) {
    return Array.from({ length: n }, (_, k) => {
      const a = R() * Math.PI * 2, d = 24 + R() * 26;
      return { dx: Math.cos(a) * d, dy: Math.sin(a) * d * 0.75 - 10, delay: R() * 100, f: k, ph: R() };
    });
  }
  function burst(p, at = performance.now()) {
    if (!p || Motion.still()) return;
    bursts.push({ pid: p.id, t0: at, parts: parts() });
    MapView.kick();
  }
  const ease = u => 1 - Math.pow(1 - u, 3);                       // close to that burst's cubic-bezier(.2, .7, .3, 1)
  /* One burst at time now, round the point ox, oy, in map pixels; scale shrinks it for the picker's tiles. */
  function drawBurst(g, id, b, ox, oy, now, scale = 1) {
    const d = defOf(id);
    for (const q of b.parts) {
      const u = (now - b.t0 - q.delay) / BURST_MS;
      if (u <= 0 || u >= 1) continue;
      const e = ease(u), x = ox + q.dx * e * scale, y = oy + (q.dy + 14 * u) * e * scale;
      if (u > 0.8) {                                               // it twinkles out as a dot of its own color
        g.fillStyle = C[d.colors[q.f % d.colors.length]];
        const s = u > 0.9 ? 1 : 2;
        g.fillRect(Math.round(x - s / 2), Math.round(y - s / 2), s, s);
        continue;
      }
      const s = sprite(id, frameOf(id, q, now));
      g.drawImage(s.c, Math.round(x - s.w / 2), Math.round(y - s.h / 2));
    }
  }

  /* ---------- the street party ---------- */
  let parties = new Map();                                          // project id -> { pid, mid, t0, until, next }
  let state = (() => { try { const v = JSON.parse(localStorage.getItem(KEY) || 'null'); return v && typeof v === 'object' && v.ms ? v : { ms: {} }; } catch (e) { return { ms: {} }; } })();
  const save = () => { try { localStorage.setItem(KEY, JSON.stringify(state)); } catch (e) { /* this visit only */ } };
  /* A tick anywhere: its particles, and a party when it finished its milestone. */
  function ticked(p, t) {
    if (!p || !t) return;
    burst(p);
    if (!t.milestoneId) return;
    const m = (p.milestones || []).find(x => x.id === t.milestoneId);
    const ts = p.todos.filter(x => x.milestoneId === t.milestoneId);
    if (!m || ts.length < MIN_TASKS || !ts.every(x => x.done)) return;      // a repeat is never done, so its milestone never finishes
    const today = ymd(Date.now());
    if (state.ms[m.id] === today) return;                         // once a day: unticking and ticking again throws no second one
    state.ms[m.id] = today;
    for (const k of Object.keys(state.ms)) if (state.ms[k] !== today) delete state.ms[k];
    save();
    party(p, m, ts.length);
  }
  function party(p, m, n) {
    const now = performance.now();
    if (!Motion.still()) {
      parties.set(p.id, { pid: p.id, mid: m.id, t0: now, until: now + PARTY_MS, next: now + PARTY_EVERY });
      if (typeof Traffic !== 'undefined' && Traffic.active() && p.plot) Traffic.party(p.plot.u, p.plot.v, now + PARTY_MS, colorsOf(kindOf(p)));
      MapView.kick();
    }
    if (typeof Proxima !== 'undefined') Proxima.announce(p, m, n);
  }
  /* Each frame: the bursts that are done go, a party bursts every 2 seconds or so, and ends after 30. True while
     anything is moving. */
  function step(now) {
    if (Motion.still()) { if (bursts.length || parties.size) { bursts = []; parties.clear(); return true; } return false; }
    bursts = bursts.filter(b => now - b.t0 < BURST_MS + 120 && getProject(b.pid));
    for (const [id, pt] of [...parties]) {
      const p = getProject(id);
      if (!p || now >= pt.until) { parties.delete(id); continue; }
      if (now >= pt.next) { bursts.push({ pid: id, t0: now, parts: parts() }); pt.next = now + PARTY_EVERY - 250 + R() * 500; }
    }
    return bursts.length > 0 || parties.size > 0;
  }

  /* ---------- the party lights: strings across the four streets round the block, glowing at night ---------- */
  const BULBS = ['#EE4C93', '#FFE38A', '#3FE0F0', '#B7A5F0', '#74C997'];
  const POLE = 11, SAG = 3;
  const tone = hex => Light.mixHex(hex, mix(hex, '#141024', 0.58));
  function strings(u, v) {
    const { MARGIN, PITCH, S } = WORLD, a0 = MARGIN + u * PITCH, a1 = a0 + S, b0 = MARGIN + v * PITCH, b1 = b0 + S;
    const out = [];
    for (const f of [0.2, 0.5, 0.8]) {
      const i = a0 + S * f, j = b0 + S * f;
      out.push([[a0 - 0.15, j], [a0 - 1.85, j]], [[a1 + 0.15, j], [a1 + 1.85, j]], [[i, b0 - 0.15], [i, b0 - 1.85]], [[i, b1 + 0.15], [i, b1 + 1.85]]);
    }
    return out;
  }
  function drawString(g, A, B, now, n) {
    const toW = MapView.tileToWorld, [xa, ya] = toW(...A), [xb, yb] = toW(...B);
    g.fillStyle = tone('#5A5073');
    for (const [x, y] of [[xa, ya], [xb, yb]]) g.fillRect(Math.round(x), Math.round(y) - POLE, 1, POLE);
    g.fillStyle = tone('#D6CEE2');
    for (const [x, y] of [[xa, ya], [xb, yb]]) g.fillRect(Math.round(x), Math.round(y) - POLE - 1, 1, 1);
    const steps = Math.max(2, Math.round(Math.max(Math.abs(xb - xa), Math.abs(yb - ya))));
    const beat = Math.floor(now / 450);
    for (let k = 0; k <= steps; k++) {
      const s = k / steps, x = Math.round(xa + (xb - xa) * s), y = Math.round(ya + (yb - ya) * s - POLE - SAG * 4 * s * (1 - s));
      g.fillStyle = tone('#7A7394'); g.fillRect(x, y, 1, 1);
      if (k % 2 === 1 && k < steps) { g.fillStyle = BULBS[((k - 1) / 2 + beat + n) % BULBS.length]; g.fillRect(x, y + 1, 1, 1); }   // the lights chase along
    }
  }
  /* The strings, as figures the map sorts by depth, so a building in front hides the ones behind it. */
  function items() {
    if (!parties.size) return [];
    const out = [], toW = MapView.tileToWorld, now = performance.now();
    for (const pt of parties.values()) {
      const p = getProject(pt.pid);
      if (!p || !p.plot) continue;
      strings(p.plot.u, p.plot.v).forEach(([A, B], n) => {
        const [xa, ya] = toW(...A), [xb, yb] = toW(...B), i = (A[0] + B[0]) / 2, j = (A[1] + B[1]) / 2;
        out.push({ i, j, key: i + j, light: true, box: { x0: Math.min(xa, xb) - 2, x1: Math.max(xa, xb) + 2, y0: Math.min(ya, yb) - POLE - SAG - 2, y1: Math.max(ya, yb) + 2 },
          draw: g => drawString(g, A, B, now, n) });
      });
    }
    return out;
  }
  /* The particles, over everything but the bubbles. geomOf gives a building's place on the map, or null. */
  function drawAir(g, geomOf) {
    if (!bursts.length) return;
    const now = performance.now();
    for (const b of bursts) {
      const p = getProject(b.pid), geo = p && geomOf(b.pid);
      if (!geo) continue;
      drawBurst(g, kindOf(p), b, geo.X, geo.top + 0.42 * (geo.base - geo.top), now);
    }
  }

  /* ---------- the picker in the Building panel: a tile per kind, which plays its burst while pointed at ---------- */
  function tile(id) {
    const W = 40, H = 30, sc = Math.max(2, Math.round(2 * (window.devicePixelRatio || 1)));
    const [c, g] = mkCanvas(W * sc, H * sc);
    c.style.width = W * 2 + 'px'; c.style.height = H * 2 + 'px';
    let b = null, timer = 0;
    const still = () => {                                          // at rest: three of them, as if mid-burst
      g.setTransform(sc, 0, 0, sc, 0, 0); g.imageSmoothingEnabled = false; g.clearRect(0, 0, W, H);
      const d = defOf(id);
      [[12, 13, 0], [27, 10, 1], [20, 21, 2]].forEach(([x, y, k]) => { const s = sprite(id, k % d.frames.length); g.drawImage(s.c, Math.round(x - s.w / 2), Math.round(y - s.h / 2)); });
    };
    const paint = () => {
      if (!c.isConnected) { stop(); return; }
      const now = performance.now();
      if (!b || now - b.t0 > BURST_MS + 200) b = { t0: now, parts: parts() };
      g.setTransform(sc, 0, 0, sc, 0, 0); g.imageSmoothingEnabled = false; g.clearRect(0, 0, W, H);
      drawBurst(g, id, b, W / 2, H / 2 + 2, now, 0.42);
    };
    const play = () => { if (timer || Motion.still()) return; b = null; paint(); timer = setInterval(paint, 40); };
    const stop = () => { clearInterval(timer); timer = 0; still(); };
    still();
    return { canvas: c, play, stop };
  }
  /* The Building panel's section: Stars pressed until another kind is picked. */
  function picker(p, onPick) {
    const grid = h('div', { class: 'pv-particles', role: 'group', 'aria-label': 'Particles' });
    for (const [id, name] of PARTICLE_KINDS) {
      const t = tile(id), on = kindOf(p) === id;
      const btn = h('button', { class: 'pick-particle' + (on ? ' on' : ''), type: 'button', 'aria-pressed': String(on), 'data-kind': id, title: name,
        onclick: () => { if (kindOf(p) !== id) { p.particles = id; changed(p, { touch: false }); } burst(p); onPick && onPick(id); },
        onmouseenter: t.play, onmouseleave: t.stop, onfocus: t.play, onblur: t.stop },
        h('span', { class: 'pick-particle-art' }, t.canvas), h('span', { class: 'pick-particle-name' }, name));
      grid.append(btn);
    }
    return grid;
  }

  return {
    ticked, burst, step, items, drawAir, picker, kindOf, colorsOf, sprite,
    busy: () => bursts.length > 0 || parties.size > 0,
    partyOf: id => { const pt = parties.get(id); return pt ? { mid: pt.mid, left: Math.max(0, pt.until - performance.now()) } : null; },
    _test: { partyMs: ms => { PARTY_MS = ms; },
      end: () => {                                                // every party ends now, as at its 30 seconds
        const now = performance.now();
        for (const pt of parties.values()) pt.until = now;
        if (typeof Traffic !== 'undefined') for (const pt of Traffic._state().parties.values()) pt.until = now;
      }, bursts: () => bursts.map(b => ({ pid: b.pid, t0: b.t0, n: b.parts.length })), parties: () => [...parties.keys()],
      state: () => JSON.parse(JSON.stringify(state)), forget: () => { state = { ms: {} }; save(); }, strings, BURST_MS, MIN_TASKS, defs: () => Object.keys(DEFS) },
  };
})();
