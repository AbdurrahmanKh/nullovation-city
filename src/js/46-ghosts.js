/* Ghost tasks (Ghost Tasks, Round 1): the tasks you ghosted, creeping round their own blocks. Every overdue task, and
   the next task of each building behind its pace (the same buildings that make garbage through urgency), goes round
   its building's block on the sidewalk as a sheet ghost with glowing eyes and edges, in its building's bubble color.
   The people walk through them: nobody sees them but you. At most 5 to a block, the most overdue first. A ghost comes
   out of its building's front when its task starts to haunt, peeks round corners, lingers by its building's front now
   and then, and rises and fades when its task is ticked. A click opens a small card with the task and its project,
   its due chip, Tick and Enter; resting the mouse on one shows its task by the pointer. Its own switch, in Settings,
   Look; hidden on Still and in Edit City; shown on the postcard and in the project view's picture. */
const Ghosts = (() => {
  const KEY = 'nullovation-city:ghosts';
  let on = (() => { try { return localStorage.getItem(KEY) !== '0'; } catch (e) { return true; } })();
  const MAX = 5, SW = 0.3;
  const SIDE = () => WORLD.S + SW, PER = () => SIDE() * 4;
  const lotA0 = u => WORLD.MARGIN + u * WORLD.PITCH;
  const R = () => Math.random();                         // read at each call, so the tests can steer it
  let ghosts = [], primed = false, lastScan = -1e9, last = 0, lastDraw = 0, cardOf = null, wasShown = false;
  const subs = [];

  /* ---------- which tasks haunt (G1, G2) ---------- */
  /* A building's ghosts, in order: its overdue tasks, the most overdue first, then its next task when it is behind its
     pace (the task the status card puts first), at most 5. A task both overdue and next is one ghost. */
  function hauntOf(p, now = Date.now()) {
    const b = Garbage.breakdown(p, now);
    const list = b.late.slice().sort((x, y) => y.days - x.days || (x.t.due < y.t.due ? -1 : x.t.due > y.t.due ? 1 : 0)).map(l => l.t);
    if (b.sys > 0) { const n = bubbleTodos(p, 1).list[0]; if (n && !list.includes(n)) list.push(n); }
    return list.slice(0, MAX);
  }
  /* Its glow: its building's bubble color. An overdue task makes the bubble red; a building only behind its pace is
     yellow or red with its system. */
  const glowOf = p => urgencyOf(p).color === 'yellow' ? 'yellow' : 'red';

  /* ---------- round the block, on the sidewalk (M1) ---------- */
  function loopPt(u, v, p) {
    const I0 = lotA0(u) - SW / 2, J0 = lotA0(v) - SW / 2, s = SIDE();
    p = ((p % PER()) + PER()) % PER();
    const k = Math.floor(p / s), f = p - k * s;
    return k === 0 ? [I0 + f, J0] : k === 1 ? [I0 + s, J0 + f] : k === 2 ? [I0 + s - f, J0 + s] : [I0, J0 + s - f];
  }
  const wrapP = p => ((p % PER()) + PER()) % PER();
  const sideOf = p => Math.floor(wrapP(p) / SIDE()) % 4;
  const LOOP = [[1, 0], [0, 1], [-1, 0], [0, -1]];
  const headAt = (p, dir) => { const [a, b] = LOOP[sideOf(p)]; return [a * dir, b * dir]; };
  /* Sides 1 and 2 face the camera: the building's front, where people walk in. Looking in, from each. */
  const INWARD = { 1: [-1, 0], 2: [0, -1] };

  function newGhost(p, t, at = null) {
    const g = { pid: p.id, tid: t.id, u: p.plot.u, v: p.plot.v, dir: R() < 0.5 ? 1 : -1, sp: 0.11 + R() * 0.04,
      mode: 'walk', t: 0, alpha: 1, lift: 0, ph: R() * 10, look: null, blocked: 0, color: glowOf(p), pos: null, path: null };
    if (at != null) g.p = at;
    else {                                                  // out of its building's front, fading in
      const s = SIDE(), front = R() < 0.5 ? 1 : 2, f = 1 + R() * (s - 2);
      g.p = front * s + f;
      const pt = loopPt(g.u, g.v, g.p);
      g.path = [front === 1 ? [pt[0] - 0.6, pt[1]] : [pt[0], pt[1] - 0.6], pt];
      g.pos = g.path[0]; g.mode = 'out'; g.alpha = 0; g.k = 0;
    }
    g.look = headAt(g.p, g.dir);
    return g;
  }

  /* Who haunts now: new ghosts come out, ghosts whose task stopped haunting rise and fade like a ticked one (M2). On
     the first look after the city opens, or after the ghosts were hidden, they are already on their rounds. */
  function scan(now = Date.now()) {
    const want = new Map();
    for (const p of DB.projects) {
      if (!p.plot) continue;
      for (const t of hauntOf(p, now)) want.set(p.id + '|' + t.id, { p, t });
    }
    for (const g of ghosts) {
      if (g.mode === 'leave') continue;
      const p = getProject(g.pid);
      if (!p) { g.dead = true; continue; }
      if (!want.has(g.pid + '|' + g.tid)) { leave(g); continue; }
      g.color = glowOf(p);
      if (g.u !== p.plot.u || g.v !== p.plot.v) { g.u = p.plot.u; g.v = p.plot.v; if (g.mode === 'out') { g.mode = 'walk'; g.alpha = 1; } }   // its building moved
      want.delete(g.pid + '|' + g.tid);
    }
    const fresh = new Map();                                // the new ones, by block, so a first look spreads them out
    for (const [k, w] of want) { const b = w.p.id; if (!fresh.has(b)) fresh.set(b, []); fresh.get(b).push(w); }
    for (const list of fresh.values()) {
      const start = R() * PER();
      list.forEach((w, n) => ghosts.push(primed ? newGhost(w.p, w.t) : newGhost(w.p, w.t, start + (n + 0.25 + R() * 0.5) * PER() / list.length)));
    }
    ghosts = ghosts.filter(g => !g.dead);
    primed = true;
    lastScan = performance.now();
  }
  function leave(g) {
    if (g.mode === 'leave') return;
    if (g.mode === 'out') { g.pos = g.pos || g.path[1]; }
    g.mode = 'leave'; g.t = 0; g.alpha0 = g.alpha;
    if (cardOf === g) closeCard();
  }

  /* ---------- moving: creeping, pausing, peeking round corners, lingering by the front ---------- */
  const PEEK = 2.2, LEAN = 0.13;
  function ahead(g) {                                       // another ghost close ahead on the same block
    return ghosts.some(o => o !== g && o.pid === g.pid && o.mode !== 'leave' && o.mode !== 'out' && (() => {
      const d = wrapP((o.p - g.p) * g.dir); return d > 0.01 && d < 0.75;
    })());
  }
  function update(g, dt) {
    if (g.mode === 'leave') {
      g.t += dt;
      const k = Math.min(1, g.t / 1);
      g.lift = Math.round(6 * (1 - (1 - k) * (1 - k)));
      g.alpha = (g.alpha0 == null ? 1 : g.alpha0) * (1 - k);
      if (k >= 1) g.dead = true;
      return;
    }
    if (g.mode === 'card') return;                          // it holds still while you look at its card
    if (g.mode === 'out') {
      const [a, b] = g.path, len = Math.hypot(b[0] - a[0], b[1] - a[1]) || 0.001;
      g.k = Math.min(len, g.k + g.sp * 1.4 * dt);
      const f = g.k / len;
      g.pos = [a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f];
      g.alpha = Math.min(1, g.alpha + dt / 1.2);
      g.look = [(b[0] - a[0]) / len, (b[1] - a[1]) / len];
      if (g.k >= len) { g.mode = 'walk'; g.pos = null; g.alpha = 1; g.look = headAt(g.p, g.dir); }
      return;
    }
    if (g.mode === 'pause' || g.mode === 'linger') {
      g.t -= dt;
      if (g.t <= 0) { if (g.mode === 'pause' && R() < 0.15) g.dir = -g.dir; g.mode = 'walk'; g.look = headAt(g.p, g.dir); }
      return;
    }
    if (g.mode === 'peek') {
      g.t += dt;
      const t = g.t;
      g.lean = t < 0.45 ? 0 : t < 0.7 ? (t - 0.45) / 0.25 : t < 1.6 ? 1 : t < 1.85 ? 1 - (t - 1.6) / 0.25 : 0;
      g.look = t < 0.45 ? g.from : g.to;
      if (t >= PEEK) { g.mode = 'walk'; g.lean = 0; g.look = g.to; }
      return;
    }
    /* walking the block's loop */
    if (ahead(g)) {                                         // two meeting head on: one turns back after a moment
      g.blocked += dt;
      if (g.blocked > 2) { g.dir = -g.dir; g.blocked = 0; g.look = headAt(g.p, g.dir); }
      return;
    }
    g.blocked = 0;
    const s = SIDE(), p0 = g.p, p1 = g.p + g.dir * g.sp * dt;
    const c = g.dir > 0 ? Math.ceil(p0 / s - 1e-9) * s : Math.floor(p0 / s + 1e-9) * s;   // the next corner along
    if (Math.abs(c - p0) > 1e-6 && (g.dir > 0 ? p1 >= c : p1 <= c)) {
      g.p = c;
      if (R() < 0.6) {                                       // stops at the corner, leans round it, then carries on
        g.mode = 'peek'; g.t = 0; g.lean = 0;
        g.from = headAt(c - g.dir * 0.01, g.dir); g.to = headAt(c + g.dir * 0.01, g.dir);
        return;
      }
      g.p = c + g.dir * 0.002;
    } else g.p = p1;
    g.look = headAt(g.p, g.dir);
    const side = sideOf(g.p), f = wrapP(g.p) - side * s;
    if ((side === 1 || side === 2) && f > 1 && f < s - 1 && R() < dt / 16) { g.mode = 'linger'; g.t = 2.5 + R() * 3; g.look = INWARD[side]; return; }
    if (R() < dt / 22) { g.mode = 'pause'; g.t = 1.5 + R() * 2.5; }
  }

  /* ---------- the art: a sheet ghost, 9 by 12 at the map's scale (L1, L3) ---------- */
  const SHAPE = ['...###...', '.#######.', '.#######.', '#########', '#########', '#########', '#########', '#########', '#########', '#########', '#########'];
  const HEMS = [['#.##.##.#'], ['.##.##.##'], ['##.##.##.']];               // the hem ripples, one scallop a frame
  const W = 9, H = SHAPE.length + HEMS[0].length;
  /* see-through inside its glowing edge (L1a); the eyes and edge glow in its building's bubble color (L2), and keep it at night */
  const GLOW = {
    red: { edge: '#FF3D7F', eye: '#E8195A', body: 'rgba(250, 244, 255, 0.62)', dark: '#5A1030' },
    yellow: { edge: '#FFC81E', eye: '#D98A00', body: 'rgba(250, 244, 255, 0.62)', dark: '#6A4A08' },
  };
  const maskOf = hem => SHAPE.concat(HEMS[hem]);
  const inside = (m, x, y) => y >= 0 && y < H && x >= 0 && x < W && m[y][x] === '#';
  const cache = new Map();
  /* One frame on a canvas 2 px wider and taller, the shape at (1, 1): its body, edge and eyes, and the ring round it,
     dark by day for the sidewalk and a soft glow at night. */
  function art(color, hem, ex, ey) {
    const key = color + hem + ':' + ex + ':' + ey;
    if (cache.has(key)) return cache.get(key);
    const m = maskOf(hem), c = GLOW[color];
    const [body, gb] = mkCanvas(W + 2, H + 2), [ringD, gd] = mkCanvas(W + 2, H + 2), [ringG, gg] = mkCanvas(W + 2, H + 2);
    const ey0 = 4 + ey, eyes = new Set([[3 + ex, ey0], [3 + ex, ey0 + 1], [5 + ex, ey0], [5 + ex, ey0 + 1]].map(([x, y]) => x + ',' + y));
    for (let y = -1; y <= H; y++) for (let x = -1; x <= W; x++) {
      const n4 = [[1, 0], [-1, 0], [0, 1], [0, -1]];
      if (inside(m, x, y)) {
        const edge = n4.some(([dx, dy]) => !inside(m, x + dx, y + dy));
        gb.fillStyle = eyes.has(x + ',' + y) ? c.eye : edge ? c.edge : c.body;
        gb.fillRect(x + 1, y + 1, 1, 1);
      } else if (n4.some(([dx, dy]) => inside(m, x + dx, y + dy))) {
        gd.fillStyle = c.dark; gd.fillRect(x + 1, y + 1, 1, 1);
        gg.fillStyle = c.edge; gg.fillRect(x + 1, y + 1, 1, 1);
      }
    }
    const out = { body, ringD, ringG };
    cache.set(key, out);
    return out;
  }
  /* The eyes look the way it goes: to the side it heads on screen, low coming toward you, high going away. */
  function eyesOf(hd) {
    if (!hd) return [0, 0];
    const sx = hd[0] - hd[1], sy = hd[0] + hd[1];
    return [sx > 0.2 ? 1 : sx < -0.2 ? -1 : 0, sy > 0.2 ? 1 : sy < -0.2 ? -1 : 0];
  }

  /* ---------- where each one is, for the map ---------- */
  function placeOf(g) {
    let at = g.pos || loopPt(g.u, g.v, g.p);
    if (g.mode === 'peek' && g.lean) at = [at[0] + g.to[0] * LEAN * g.lean, at[1] + g.to[1] * LEAN * g.lean];
    return at;
  }
  function floatOf(g, now) {
    const bob = Motion.still() ? 0 : Math.round(Math.sin(now / 520 + g.ph));
    return 2 + bob + (g.lift || 0);
  }
  const shownNow = () => on && !Motion.still() && !MapView.editing();
  function items() {
    if (!shownNow()) return [];
    const out = [], toW = MapView.tileToWorld, now = performance.now(), night = Light.t;
    for (const g of ghosts) {
      const [i, j] = placeOf(g), [x, y] = toW(i, j), fl = floatOf(g, now);
      const hem = Math.floor(now / 330 + g.ph) % 3, [ex, ey] = eyesOf(g.look);
      const a = art(g.color, hem, ex, ey), X = Math.round(x) - 5, Y = Math.round(y) - fl - H;
      g.box = { x0: X, x1: X + W + 2, y0: Y, y1: Y + H + 2 };
      out.push({ i, j, key: i + j, box: { x0: X - 1, x1: X + W + 3, y0: Y - 1, y1: Math.round(y) + 2 }, ghost: true, draw: ctx => {
        const al = Math.max(0, Math.min(1, g.alpha));
        ctx.globalAlpha = 0.2 * al;                       // a faint shadow under it
        ctx.fillStyle = '#2B2542'; ctx.fillRect(Math.round(x) - 2, Math.round(y), 5, 1);
        ctx.globalAlpha = 0.45 * (1 - night) * al; ctx.drawImage(a.ringD, X, Y);
        ctx.globalAlpha = 0.3 * night * al; ctx.drawImage(a.ringG, X, Y);
        ctx.globalAlpha = al; ctx.drawImage(a.body, X, Y);
        ctx.globalAlpha = 1;
      } });
    }
    return out;
  }
  /* The ghost under a point on the map, in world pixels; a pixel round it counts too. The one in front wins. */
  function at(wx, wy) {
    if (!shownNow()) return null;
    let best = null;
    for (const g of ghosts) {
      if (g.mode === 'leave' || g.mode === 'out' || !g.box) continue;
      const b = g.box;
      if (wx >= b.x0 - 1 && wx <= b.x1 + 1 && wy >= b.y0 - 1 && wy <= b.y1 + 1) {
        const [i, j] = placeOf(g);
        if (!best || i + j > best.d) best = { g, d: i + j };
      }
    }
    return best ? best.g : null;
  }
  const taskOf = g => { const p = getProject(g.pid); return p ? { p, t: p.todos.find(t => t.id === g.tid) || null } : null; };

  function step(t) {
    const shown = shownNow();
    if (!shown) {                                           // hidden: off, on Still or in Edit City; back on their rounds when shown again
      const was = wasShown;
      if (was) { ghosts = []; primed = false; closeCard(); }
      wasShown = false; last = 0;
      return was;                                           // one more drawing, without them
    }
    if (!wasShown) { wasShown = true; primed = false; ghosts = []; lastScan = -1e9; }
    if (t - lastScan > 1000) scan();
    const dt = last ? Math.min(0.1, (t - last) / 1000) : 0;
    last = t;
    for (const g of ghosts) update(g, dt);
    if (ghosts.some(g => g.dead)) ghosts = ghosts.filter(g => !g.dead);
    if (cardOf) placeCard();
    if (ghosts.length && t - lastDraw >= 50) { lastDraw = t; return true; }
    return false;
  }

  /* ---------- the card (C4): the task and its project, its due chip, Tick and Enter ---------- */
  let card = null;
  function openCard(g) {
    const w = taskOf(g); if (!w || !w.t) return;
    const { p, t } = w;
    if (cardOf && cardOf !== g && cardOf.mode === 'card') cardOf.mode = 'walk';
    cardOf = g;
    if (g.mode !== 'leave' && g.mode !== 'out') { g.mode = 'card'; g.lean = 0; }
    MapView.deselect(); Wheel.close();                     // the status card and the wheel never show with it
    if (!card) { card = h('div', { id: 'ghostCard', class: 'ghost-card', role: 'dialog', 'aria-label': 'Ghost task' }); $('#overlay').append(card); }
    const tick = h('button', { class: 'btn btn-accent btn-small gc-tick', type: 'button', onclick: () => {
      const was = tickTask(p, t);
      if (t.repeat) repeatToast(p, t, was);
      else toast('Ticked off: ' + t.text + '.', '', { label: 'Undo', run: () => { untickTask(p, t, was); changed(p); if (FullView.isOpen()) FullView.render(); } });
      changed(p);
      if (FullView.isOpen()) FullView.render();
      closeCard();
    } }, iconEl('tick', 14), 'Tick');
    const enter = h('button', { class: 'btn btn-small gc-enter', type: 'button', onclick: () => { closeCard(); FullView.openTask(p.id, t.id); } }, iconEl('door', 14, '#FFC2DD'), 'Enter');
    card.replaceChildren(
      h('button', { class: 'icon-btn gc-close', type: 'button', 'aria-label': 'Close', html: iconSvg('close', 14), onclick: () => closeCard() }),
      h('p', { class: 'gc-project', dir: 'auto' }, p.name),
      h('h2', { class: 'gc-task', dir: 'auto' }, t.text),
      dueChip(t) ? h('p', { class: 'gc-due' }, dueChip(t)) : null,
      h('div', { class: 'gc-actions' }, tick, enter),
      h('span', { class: 'gc-tail', 'aria-hidden': 'true', html: iconSvg('tail', 18) }));
    card.dataset.color = g.color;
    card.hidden = false;
    placeCard();
    tick.focus({ preventScroll: true });
    MapView.invalidate();
  }
  function placeCard() {
    if (!card || !cardOf) return;
    if (!cardOf.box) return;
    const b = cardOf.box, [cx, cy] = MapView.worldCss((b.x0 + b.x1) / 2, b.y0);
    const wrap = $('#mapWrap'), Wd = wrap.clientWidth, cw = card.offsetWidth, ch = card.offsetHeight;
    const left = clamp(cx - cw / 2, 8, Math.max(8, Wd - cw - 8)), top = Math.max(8, cy - ch - 12);
    card.style.transform = `translate(${Math.round(left)}px, ${Math.round(top)}px)`;
    const tail = $('.gc-tail', card);
    if (tail) tail.style.left = Math.round(clamp(cx - left, 14, cw - 14) - 6) + 'px';
  }
  function closeCard() {
    if (cardOf && cardOf.mode === 'card') cardOf.mode = 'walk';
    const had = !!cardOf;
    cardOf = null;
    if (card) card.hidden = true;
    return had;
  }

  /* A tick anywhere lays its ghost to rest at once (M2), wherever it is. */
  function ticked(p, t) {
    for (const g of ghosts) if (g.pid === p.id && g.tid === t.id) leave(g);
    lastScan = performance.now();
  }
  function setOn(v) {
    on = !!v;
    try { localStorage.setItem(KEY, on ? '1' : '0'); } catch (e) { /* this visit only */ }
    if (!on) closeCard();
    for (const f of subs) f();
    MapView.invalidate(); MapView.kick();
  }

  return {
    isOn: () => on, setOn, shown: shownNow, items, at, step, ticked, hauntOf, onChange: f => subs.push(f),
    open: openCard, closeCard, cardOpen: () => !!cardOf, cardGhost: () => cardOf, taskOf,
    busy: () => shownNow() && ghosts.length > 0,
    /* for the tests: the ghosts now, a fresh look, and one placed by hand */
    _test: {
      list: () => ghosts.map(g => ({ pid: g.pid, tid: g.tid, u: g.u, v: g.v, p: g.p, mode: g.mode, alpha: g.alpha, lift: g.lift, color: g.color, dir: g.dir, at: placeOf(g), box: g.box ? { ...g.box } : null, look: g.look })),
      scan: () => scan(), reset: () => { ghosts = []; primed = false; lastScan = -1e9; closeCard(); },
      set: (tid, o) => { const g = ghosts.find(x => x.tid === tid); if (g) Object.assign(g, o); return !!g; },
      art: (color, hem = 0, ex = 0, ey = 0) => art(color, hem, ex, ey), shape: hem => maskOf(hem), W, H, MAX,
      glow: (c, o) => { Object.assign(GLOW[c], o); cache.clear(); },
    },
  };
})();
