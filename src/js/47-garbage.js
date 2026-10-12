/* Garbage: what a neglected city looks like. Every point of neglect is one piece of street trash by its building:
   first on the building's own front strip and sidewalks, then in the gutters of the streets beside it, then in the
   nearest park, then on the sidewalks across the street. Each piece has a fixed spot and kind, dealt by the
   building's place in the city, so garbage stays put between visits. When its cause is fixed, a hover garbage truck
   drives in from one end of the street, three of its crew spread round the block and sweep, the building's garbage
   goes with a sparkle, and the truck leaves by the other end.
   The points, one piece each: a pace building missing one period 5, and red 10 for its second period and 10 more for
   each period after; a work-until-finished building with no task finished for a day 10, and 10 more each day after;
   each overdue task 5 a day late. Rest days pause the urgency points, not the late ones; away pauses both, the late
   tasks keeping what they have. One ceiling for the whole city; over it, every building's share shrinks in proportion. */
const Garbage = (() => {
  const KEY = 'nullovation-city:garbage';                     // the switch, on this computer
  let on = (() => { try { return localStorage.getItem(KEY) !== '0'; } catch (e) { return true; } })();
  const CEILING = 500, spacing = 1;
  const LIFT = 3;                                             // a building's plot stands this many pixels above the street
  const MAX_SPOTS = 640;
  const subs = [], forced = new Map();                        // forced: counts the tests set, by project id

  /* ---------- the points ---------- */
  /* The urgency system's own: nothing until a period is missed. A pace building is yellow after one period (5) and red
     after two (10), 10 more for each period after; a work-until-finished building is red when no task was finished for
     a day (10), 10 more for each day after. Its yellow means a task was finished today, so it is not neglect. */
  function systemPoints(p, now) {
    const u = p.urgency || {}, urg = urgencyOf(p, now);
    if (!urg.system) return 0;
    if (u.system === 'pace') {
      const N = Math.max(1, u.days || 1) * DAY, start = u.pickedAt || now, worked = u.lastWorked && u.lastWorked >= start;
      const gone = worked ? countedMs(u.lastWorked, now) : countedMs(start, now) + N, m = Math.floor(gone / N);
      return urg.system === 'yellow' ? 5 : 10 * Math.max(1, isFinite(m) ? m - 1 : 1);
    }
    if (u.system === 'finish' && urg.system === 'red') {
      const gone = countedMs(u.lastWorked || u.pickedAt || p.createdAt || now, now);
      return 10 * Math.max(1, isFinite(gone) ? Math.floor(gone / DAY) : 1);
    }
    return 0;
  }
  /* A task's: 5 for each day it is late, rest days included. Away, it stops growing and keeps what it has: the days
     after the one you set away, up to the day you are back, do not count. */
  const dayN = s => { const m = /^(\d{4})-(\d\d)-(\d\d)$/.exec(s || ''); return m ? Math.round(Date.UTC(+m[1], +m[2] - 1, +m[3]) / DAY) : null; };
  function lateDays(t, now) {
    const due = dayN(t.due), today = dayN(ymd(now));
    if (due == null || today <= due) return 0;
    let days = today - due;
    for (const [f, e] of (DB.city && DB.city.awaySpans) || []) {
      const a = Math.max(due + 1, dayN(f) + 1), b = Math.min(today + 1, dayN(e));
      if (b > a) days -= b - a;
    }
    return Math.max(0, days);
  }
  function rulesOf(p, now = Date.now()) {
    const sys = systemPoints(p, now), parts = [];
    if (sys) parts.push((urgencyOf(p, now).system === 'red' ? 'red ' : 'yellow ') + sys);
    let late = 0, lateN = 0;
    for (const t of p.todos) { if (t.done) continue; const d = lateDays(t, now); if (d) { late += 5 * d; lateN++; } }
    if (lateN) parts.push(plural(lateN, 'late task', 'late tasks') + ' ' + late);
    return { n: sys + late, why: parts.join(', ') };
  }
  const wanted = p => Math.max(0, Math.round(forced.has(p.id) ? forced.get(p.id) : rulesOf(p).n));
  /* Every building's pieces after the ceiling: shares shrink in proportion, the leftovers going to the largest remainders. */
  function targets() {
    const raw = DB.projects.map(p => [p.id, wanted(p)]), total = raw.reduce((s, [, n]) => s + n, 0);
    const out = new Map();
    if (total <= CEILING) { for (const [id, n] of raw) out.set(id, n); return { map: out, total, shown: total }; }
    const k = CEILING / total, rest = [];
    let used = 0;
    for (const [id, n] of raw) { const f = n * k, w = Math.floor(f); out.set(id, w); used += w; rest.push([id, f - w]); }
    rest.sort((a, b) => b[1] - a[1] || (a[0] < b[0] ? -1 : 1));
    for (let i = 0; i < CEILING - used && i < rest.length; i++) out.set(rest[i][0], out.get(rest[i][0]) + 1);
    return { map: out, total, shown: CEILING };
  }

  /* ---------- the spots: dealt by the building's place in the city ---------- */
  const hash = (...k) => k.reduce((h, v) => (Math.imul(h ^ (v + 0x9e37), 0x85ebca6b) + 0x27d4eb2f) >>> 0, 23);
  const rng = (...k) => mulberry32(hash(...k));
  const KINDS = [['paper', 34], ['note', 20], ['can', 26], ['bag', 20]];
  const pickW = (r, list) => { let x = r() * list.reduce((s, w) => s + w[1], 0); for (const [v, w] of list) if ((x -= w) < 0) return v; return list[0][0]; };
  const spotCache = new Map();
  const occupied = () => new Set(DB.projects.map(p => p.plot.u + ',' + p.plot.v));
  function nearestPark(u, v) {
    const taken = occupied(), { NU, NV } = WORLD;
    const order = [[1, 0], [0, 1], [1, 1], [-1, 0], [0, -1], [1, -1], [-1, 1], [-1, -1], [2, 0], [0, 2], [2, 1], [1, 2], [-2, 0], [0, -2], [2, 2]];
    for (const [du, dv] of order) {
      const a = u + du, b = v + dv;
      if (a >= 0 && b >= 0 && a < NU && b < NV && !taken.has(a + ',' + b)) return [a, b];
    }
    return null;
  }
  function spotsFor(p) {
    const { S, MARGIN, PITCH, NU, NV, OU, OV } = WORLD, u = p.plot.u, v = p.plot.v;
    const park = nearestPark(u, v);
    const key = [u, v, NU, NV, OU, OV, spacing, park ? park.join('.') : '-'].join(':');
    const hit = spotCache.get(p.id);
    if (hit && hit.key === key) return hit.list;
    const a0 = MARGIN + u * PITCH, a1 = a0 + S, b0 = MARGIN + v * PITCH, b1 = b0 + S;
    const TI = MARGIN * 2 + NU * PITCH - WORLD.GAP, TJ = MARGIN * 2 + NV * PITCH - WORLD.GAP;
    const R = (i0, i1, j0, j1, lift = 0) => ({ i0: Math.max(0.15, i0), i1: Math.min(TI - 0.15, i1), j0: Math.max(0.15, j0), j1: Math.min(TJ - 0.15, j1), lift });
    const groups = [
      { dens: 0.075, rects: [R(a1 - 0.55, a1 - 0.12, b0 + 0.4, b1 - 0.12, LIFT), R(a0 + 0.4, a1 - 0.55, b1 - 0.55, b1 - 0.12, LIFT),   // the plot's front strip
        R(a1 + 0.05, a1 + 0.25, b0 - 0.05, b1 + 0.25), R(a0 - 0.05, a1 + 0.05, b1 + 0.05, b1 + 0.25)] },                                 // the front sidewalks
      { dens: 0.075, rects: [R(a0 - 0.25, a0 - 0.05, b0 - 0.05, b1 + 0.05), R(a0 - 0.05, a1 + 0.05, b0 - 0.25, b0 - 0.05)] },           // the back sidewalks
      { dens: 0.07, rects: [R(a1 + 0.35, a1 + 0.55, b0, b1), R(a0, a1, b1 + 0.35, b1 + 0.55), R(a0 - 0.55, a0 - 0.35, b0, b1), R(a0, a1, b0 - 0.55, b0 - 0.35)] },  // the gutters
      park ? { dens: 0.085, rects: [(() => { const c0 = MARGIN + park[0] * PITCH, d0 = MARGIN + park[1] * PITCH; return R(c0 + 0.35, c0 + S - 0.35, d0 + 0.35, d0 + S - 0.35); })()] } : null,
      { dens: 0.08, rects: [R(a1 + 1.75, a1 + 1.95, b0, b1), R(a0, a1, b1 + 1.75, b1 + 1.95), R(a0 - 1.95, a0 - 1.75, b0, b1), R(a0, a1, b0 - 1.95, b0 - 1.75),
        R(a1 + 1.45, a1 + 1.65, b0, b1), R(a0, a1, b1 + 1.45, b1 + 1.65), R(a0 - 1.65, a0 - 1.45, b0, b1), R(a0, a1, b0 - 1.65, b0 - 1.45)] },
    ].filter(Boolean);
    const r = rng(u + OU, v + OV, 41), list = [], minD = 2.6 * spacing;
    const toW = MapView.tileToWorld;
    const place = (rect, check) => {
      if (rect.i1 < rect.i0 || rect.j1 < rect.j0) return false;
      const i = rect.i0 + r() * (rect.i1 - rect.i0), j = rect.j0 + r() * (rect.j1 - rect.j0);
      const [x, y] = toW(i, j);
      if (check && list.some(s => Math.abs(s.x - x) < minD * 1.6 && Math.abs(s.y - y) < minD)) return false;
      const kind = pickW(r, KINDS), variant = Math.floor(r() * 8), flip = r() < 0.5;
      list.push({ i, j, x, y, lift: rect.lift, kind, variant, flip, n: list.length });
      return true;
    };
    /* Litter gathers: most pieces fall near a few spots in each stretch (a corner, the curb by a door), the rest anywhere. */
    const gauss = () => (r() + r() + r() - 1.5) / 1.5;
    for (const g of groups) {
      const areas = g.rects.map(q => Math.max(0, q.i1 - q.i0) * Math.max(0, q.j1 - q.j0)), area = areas.reduce((s, a) => s + a, 0);
      if (!area) continue;
      const pickRect = () => { let x = r() * area, q = 0; while (q < areas.length - 1 && (x -= areas[q]) > 0) q++; return g.rects[q]; };
      const centers = Array.from({ length: Math.max(2, Math.round(area / 1.1)) }, () => { const q = pickRect(); return { q, i: q.i0 + r() * (q.i1 - q.i0), j: q.j0 + r() * (q.j1 - q.j0) }; });
      const want = Math.floor(area / (g.dens * spacing * spacing));
      let made = 0, tries = 0;
      while (made < want && tries < want * 14 && list.length < MAX_SPOTS) {
        tries++;
        if (r() < 0.7) {
          const c = centers[Math.floor(r() * centers.length)], q = c.q, rad = 0.32 * spacing;
          const i = clamp(c.i + gauss() * rad, q.i0, q.i1), j = clamp(c.j + gauss() * rad, q.j0, q.j1);
          if (place({ i0: i, i1: i, j0: j, j1: j, lift: q.lift }, true)) made++;
        } else if (place(pickRect(), true)) made++;
      }
    }
    /* Past every spot the buildings' own ground piles up: more pieces on the strip, the sidewalks and the gutters. */
    const pile = groups.slice(0, 3).flatMap(g => g.rects);
    let guard = 0;
    while (list.length < MAX_SPOTS && guard++ < MAX_SPOTS * 4) place(pile[Math.floor(r() * pile.length)], false);
    spotCache.set(p.id, { key, list });
    return list;
  }

  /* ---------- the art: drawn in code at double detail, like the props, in the city palette by day and by night ---------- */
  const SPR = {
    paper: [
      { rows: ['.ooo.', 'oWWwo', 'oWsso', 'oswso', '.ooo.'], c: { o: '#5A5073', W: '#FFFFFF', w: '#F4F1F8', s: '#CBC2DB' } },
      { rows: ['..oooo..', '.oWWWWoo', 'oWWwwso.', '.oooo...'], c: { o: '#5A5073', W: '#FFFFFF', w: '#F4F1F8', s: '#CBC2DB' } },
      { rows: ['.oooo.', 'oCWCCo', 'oCCsso', '.oooo.'], c: { o: '#5A5073', C: '#F29A74', W: '#FFE38A', s: '#D9799F' } },
      { rows: ['.oooo.', 'oCWCCo', 'oCCsso', '.oooo.'], c: { o: '#5A5073', C: '#9CC7F3', W: '#FFFFFF', s: '#6FA5DE' } },
    ],
    note: [
      { rows: ['.ooo.', 'oFFFo', 'oFFso', 'oFsso', '.ooo.'], c: { o: '#5A5073', F: '#FFE38A', s: '#F2C75C' } },
      { rows: ['...o...', '..oFo..', '.oFFFo.', 'oFFFsso', '.osssoo', '..ooo..'], c: { o: '#5A5073', F: '#FBD3E3', s: '#F4A3C3' } },
      { rows: ['.ooo.', 'oFFFo', 'oFFso', 'oFsso', '.ooo.'], c: { o: '#5A5073', F: '#C4F0EB', s: '#7FD6CE' } },
      { rows: ['...o...', '..oFo..', '.oFFFo.', 'oFFFsso', '.osssoo', '..ooo..'], c: { o: '#5A5073', F: '#E0D8FB', s: '#B7A5F0' } },
    ],
    can: [
      { rows: ['.oo....', 'oCCoo..', 'oCCCCoo', '.ooCgSo', '...ooo.'], c: { o: '#2B2542', C: '#F29A74', g: '#3FE0F0', S: '#D6CEE2' } },
      { rows: ['.oo....', 'oCCoo..', 'oCCCCoo', '.ooCgSo', '...ooo.'], c: { o: '#2B2542', C: '#EE4C93', g: '#3FE0F0', S: '#D6CEE2' } },
      { rows: ['.oo....', 'oCCoo..', 'oCCCCoo', '.ooCgSo', '...ooo.'], c: { o: '#2B2542', C: '#6FA5DE', g: '#3FE0F0', S: '#D6CEE2' } },
      { rows: ['.oo......', 'oTToo....', 'oTTTToo..', '.ooTTTgoo', '...ooTKKo', '.....ooo.'], c: { o: '#2B2542', T: '#3FA79E', g: '#3FE0F0', K: '#F2C75C' } },
    ],
    bag: [
      { rows: ['....oo....', '...oKKo...', '..oVLLVo..', '.oVLLVVVo.', 'oVLLVVVVDo', 'oVLVVVVVDo', 'oVVVVVVDDo', '.oVVVVDDo.', '..ooooooo.'], c: { o: '#2B2542', K: '#FFE38A', L: '#8E7BD0', V: '#5A5073', D: '#433A5E' }, stand: true },
      { rows: ['....oo....', '...oKKo...', '..oVLLVo..', '.oVLLVVVo.', 'oVLLVVVVDo', 'oVLVVVVVDo', 'oVVVVVVDDo', '.oVVVVDDo.', '..ooooooo.'], c: { o: '#5A5073', K: '#F29A74', L: '#FFFFFF', V: '#E0D8FB', D: '#B7A5F0' }, stand: true },
      { rows: ['..oo........', '.oKKoooooo..', 'oLLVVVVVVVo.', 'oLVVVVVVVDDo', '.oDDDDDDDDo.', '..oooooooo..'], c: { o: '#2B2542', K: '#FFE38A', L: '#8E7BD0', V: '#5A5073', D: '#433A5E' }, stand: true },
    ],
  };
  const tone = hex => { const v = Light.rgb(...hexToRgb(hex)); return v ? rgbToHex(v) : hex; };
  let artKey = '', art = null;
  function artSet() {
    const k = String(Math.round(Light.t * 20));
    if (k === artKey && art) return art;
    artKey = k; art = {};
    for (const [kind, list] of Object.entries(SPR)) art[kind] = list.map(s => {
      const w = Math.max(...s.rows.map(r => r.length)), hgt = s.rows.length;
      const make = flip => {
        const [c, g] = mkCanvas(w, hgt);
        s.rows.forEach((row, y) => [...row].forEach((ch, x) => { if (s.c[ch]) { g.fillStyle = tone(s.c[ch]); g.fillRect(flip ? w - 1 - x : x, y, 1, 1); } }));
        return c;
      };
      return { w, h: hgt, plain: make(false), flipped: make(true), stand: !!s.stand };
    });
    art.truck = {};
    return art;
  }

  /* ---------- what is drawn: per building, the live pieces and those waiting for the crew ---------- */
  const shown = new Map(), doomed = new Map(), lastTargets = { map: new Map(), total: 0, shown: 0 };
  let primed = false;
  function refresh() {
    const t = targets();
    lastTargets.map = t.map; lastTargets.total = t.total; lastTargets.shown = t.shown;
    for (const p of DB.projects) {
      const want = Math.min(t.map.get(p.id) || 0, spotsFor(p).length);
      const was = shown.has(p.id) ? shown.get(p.id) : (primed ? 0 : want);
      const set = doomed.get(p.id) || new Set();
      if (want >= was) { for (const k of [...set]) if (k < want) set.delete(k); }
      else { for (let k = want; k < was; k++) set.add(k); queueClean(p.id); }
      if (set.size) doomed.set(p.id, set); else doomed.delete(p.id);
      shown.set(p.id, want);
    }
    for (const id of [...shown.keys()]) if (!getProject(id)) { shown.delete(id); doomed.delete(id); }
    primed = true;
    for (const f of subs) f();
    MapView.invalidate();
  }

  /* ---------- wind: now and then a loose paper hops a few pixels along ---------- */
  const drift = new Map();                                    // "id:n" -> [dx, dy] in world pixels, for this visit
  let hops = [], nextGust = 0, visible = [];
  function gust(t) {
    const light = visible.filter(s => s.spot.kind === 'paper' || s.spot.kind === 'note');
    if (!light.length) return;
    const s = light[Math.floor(Math.random() * light.length)], key = s.id + ':' + s.spot.n;
    if (hops.some(h => h.key === key)) return;
    const from = drift.get(key) || [0, 0], dir = Math.random() < 0.5 ? [2, 1] : [-2, 1], len = (1 + Math.random() * 2) * (Math.random() < 0.5 ? 1 : -1);
    let to = [from[0] + dir[0] * len, from[1] + dir[1] * len];
    if (Math.hypot(to[0], to[1]) > 7) to = [from[0] * 0.3, from[1] * 0.3];   // never wanders far from its spot
    hops.push({ key, from, to, t0: t, dur: 700 + Math.random() * 500 });
  }
  function offsetOf(key, t) {
    const h = hops.find(q => q.key === key);
    if (!h) return drift.get(key) || [0, 0];
    const k = clamp((t - h.t0) / h.dur, 0, 1), e = easeOut(k);
    return [lerp(h.from[0], h.to[0], e), lerp(h.from[1], h.to[1], e) - Math.sin(k * Math.PI) * 2.5];
  }

  /* ---------- the cleanup: a hover truck, three of its crew, and a sparkle where each piece was ---------- */
  const queue = [], jobs = [], sparkles = [];
  const MAX_TRUCKS = 3, LANE = 0.35;
  function queueClean(id) { if (!queue.includes(id) && !jobs.some(j => j.id === id && (j.phase === 'in' || (j.phase === 'crew' && j.crew.some(c => c.state !== 'back' && c.state !== 'home'))))) queue.push(id); }
  /* A block's sidewalk loop, as the people walk it: from its top corner round by the south-east and south-west sides. */
  const SWK = 0.3, SIDE = () => WORLD.S + SWK, PER = () => SIDE() * 4;
  function loopPt(u, v, q) {
    const { MARGIN, PITCH } = WORLD, I0 = MARGIN + u * PITCH - SWK / 2, J0 = MARGIN + v * PITCH - SWK / 2, sd = SIDE();
    q = ((q % PER()) + PER()) % PER();
    const k = Math.floor(q / sd), f = q - k * sd;
    return k === 0 ? [I0 + f, J0] : k === 1 ? [I0 + sd, J0 + f] : k === 2 ? [I0 + sd - f, J0 + sd] : [I0, J0 + sd - f];
  }
  /* The truck runs the whole street, from one end of the map to the other: in from the far end, a stop by the block,
     out by the near end. The street on the block's south-east or south-west side, dealt by its place. */
  function routeFor(p) {
    const { S, MARGIN, PITCH, OU, OV, NU, NV, GAP } = WORLD, u = p.plot.u, v = p.plot.v;
    const a0 = MARGIN + u * PITCH, a1 = a0 + S, b0 = MARGIN + v * PITCH, b1 = b0 + S;
    const TI = MARGIN * 2 + NU * PITCH - GAP, TJ = MARGIN * 2 + NV * PITCH - GAP;
    if ((hash(u + OU, v + OV, 7) & 1) === 0) {                 // the south-east street, driving toward you
      const i = a1 + 1 - LANE, stop = b0 + 2;
      return { h: 'j+', at: s => [i, s], s0: -0.8, stop, s1: TJ + 0.8, door: [a1 + 0.44, stop], q0: SIDE() + (stop - (b0 - SWK / 2)), u, v };
    }
    const j = b1 + 1 - LANE, stop = a0 + 2;                  // the south-west street, driving away
    return { h: 'i-', at: s => [s, j], s0: TI + 0.8, stop, s1: -0.8, door: [stop, b1 + 0.44], q0: 2 * SIDE() + ((a0 - SWK / 2 + SIDE()) - stop), u, v };
  }
  const truckActive = () => Traffic.isOn() && !Motion.still() && on;
  function startJobs(t) {
    while (queue.length && jobs.filter(j => j.phase !== 'gone').length < MAX_TRUCKS) {
      const id = queue.shift(), p = getProject(id);
      if (!p || !doomed.get(id)) continue;
      const r = routeFor(p);
      jobs.push({ id, r, phase: 'in', s: r.s0, t0: t, phaseT: t, crew: crewFor(r) });
    }
  }
  function vanish(id, n, t, withSparkle = true) {
    const p = getProject(id), set = doomed.get(id);
    if (!p || !set || !set.has(n)) return;
    set.delete(n);
    if (!set.size) doomed.delete(id);
    const s = spotsFor(p)[n], off = drift.get(id + ':' + n) || [0, 0];
    if (withSparkle && s) sparkles.push({ x: s.x + off[0], y: s.y - s.lift + off[1], i: s.i, j: s.j, t0: t + Math.random() * 120 });
  }
  function clearAll(t, withSparkle) {
    for (const [id, set] of [...doomed.entries()]) for (const n of [...set]) vanish(id, n, t, withSparkle);
    queue.length = 0;
  }
  /* Three of the crew, each to a spot of its own round the block, reached along the sidewalk loop from the curb by the
     truck, at least a block side's third apart. */
  const CREW = 3, WALK = 1.35, WORK = 3400, REACH = 4.6;
  function crewFor(r) {
    const R = Math.random, spots = [];
    for (let tries = 0; spots.length < CREW && tries < 200; tries++) {
      const d = (R() * 2 - 1) * REACH;
      if (spots.every(x => Math.abs(x - d) > 1.4)) spots.push(d);
    }
    while (spots.length < CREW) spots.push((spots.length - 1) * 1.5);
    return spots.map((d, k) => {
      const path = [r.door], n = Math.max(1, Math.ceil(Math.abs(d) / 0.2));
      for (let x = 0; x <= n; x++) path.push(loopPt(r.u, r.v, r.q0 + d * x / n));
      const len = []; let total = 0;
      for (let x = 1; x < path.length; x++) { total += Math.hypot(path[x][0] - path[x - 1][0], path[x][1] - path[x - 1][1]); len.push(total); }
      return { k, path, len, total, state: 'in', t0: 0, at: r.door, hd: null, delay: k * 260, plan: [] };
    });
  }
  function along(c, dist) {                                   // a point on the crew member's path, and the way it heads
    const { path, len } = c;
    if (dist <= 0) return [path[0], [path[1][0] - path[0][0], path[1][1] - path[0][1]]];
    for (let x = 0; x < len.length; x++) if (dist <= len[x]) {
      const a = path[x], b = path[x + 1], prev = x ? len[x - 1] : 0, k = (dist - prev) / Math.max(1e-6, len[x] - prev);
      return [[lerp(a[0], b[0], k), lerp(a[1], b[1], k)], [b[0] - a[0], b[1] - a[1]]];
    }
    const a = path[path.length - 2], b = path[path.length - 1];
    return [b, [b[0] - a[0], b[1] - a[1]]];
  }
  const cruise = d => clamp(Math.abs(d) / 4.5, 3, 7);           // tiles a second: a far start is driven faster
  function stepJob(j, t, dt) {
    const r = j.r, dir = Math.sign(r.s1 - r.s0);
    if (j.phase === 'in') {
      const left = (r.stop - j.s) * dir, sp = cruise(r.stop - r.s0) * clamp(left / 1.8, 0.1, 1);
      j.s += dir * Math.min(left, sp * dt);
      if (left <= 0.004) {
        j.s = r.stop; j.phase = 'crew'; j.phaseT = t;
        /* every piece waiting goes to the crew member nearest it, cleared nearest first while they sweep */
        const p = getProject(j.id), spots = p ? spotsFor(p) : [], ends = j.crew.map(c => c.path[c.path.length - 1]);
        for (const n of doomed.get(j.id) || []) {
          const q = spots[n]; if (!q) continue;
          let best = 0, bd = Infinity;
          ends.forEach((e, k) => { const d = Math.hypot(q.i - e[0], q.j - e[1]); if (d < bd) { bd = d; best = k; } });
          j.crew[best].plan.push({ n, d: bd });
        }
        for (const c of j.crew) { c.plan.sort((a, b) => a.d - b.d); c.state = 'wait'; c.t0 = t + c.delay; }
      }
    } else if (j.phase === 'crew') {
      for (const c of j.crew) {
        if (c.state === 'wait' && t >= c.t0) { c.state = 'out'; c.t0 = t; }
        if (c.state === 'out') {
          const dist = (t - c.t0) / 1000 * WALK, [at, hd] = along(c, dist);
          c.at = at; c.hd = hd;
          if (dist >= c.total) { c.state = 'work'; c.t0 = t; c.plan.forEach((q, x) => { q.at = t + 200 + (WORK - 500) * (x + 1) / (c.plan.length + 1); }); }
        } else if (c.state === 'work') {
          for (const q of c.plan) if (!q.done && t >= q.at) { q.done = true; vanish(j.id, q.n, t); }
          const end = c.path[c.path.length - 1], wob = Math.sin((t - c.t0) / 520 + c.k) * 0.12;
          c.at = [end[0] + (r.h === 'j+' ? 0 : wob), end[1] + (r.h === 'j+' ? wob : 0)]; c.hd = null;
          if (t - c.t0 >= WORK) { c.state = 'back'; c.t0 = t; }
        } else if (c.state === 'back') {
          const dist = c.total - (t - c.t0) / 1000 * WALK, [at, hd] = along(c, dist);
          c.at = at; c.hd = [-hd[0], -hd[1]];
          if (dist <= 0) c.state = 'home';
        }
      }
      if (j.crew.every(c => c.state === 'back' || c.state === 'home')) for (const n of [...(doomed.get(j.id) || [])]) vanish(j.id, n, t);   // the far ones go too
      if (j.crew.every(c => c.state === 'home')) { j.phase = 'leave'; j.phaseT = t; }
    } else if (j.phase === 'leave') {
      const gone = (j.s - r.stop) * dir;
      j.s += dir * cruise(r.s1 - r.stop) * clamp(0.12 + gone / 1.8, 0.12, 1) * dt;
      if ((j.s - r.s1) * dir >= 0) j.phase = 'gone';
    }
  }
  function step(t) {
    if (!on || MapView.editing()) { if (jobs.length || doomed.size) { jobs.length = 0; clearAll(t, false); } hops = []; return false; }
    const dt = lastStep ? Math.min(0.1, (t - lastStep) / 1000) : 0;
    lastStep = t;
    if (Motion.still()) { if (doomed.size || jobs.length) { jobs.length = 0; clearAll(t, false); return true; } return false; }
    if (!truckActive()) { jobs.length = 0; if (doomed.size) clearAll(t, true); }
    else { startJobs(t); for (const j of jobs) stepJob(j, t, dt); }
    for (let x = jobs.length - 1; x >= 0; x--) if (jobs[x].phase === 'gone') jobs.splice(x, 1);
    if (t >= nextGust) { if (nextGust) gust(t); nextGust = t + 1800 + Math.random() * 3800; }
    for (let x = hops.length - 1; x >= 0; x--) { const h = hops[x]; if (t - h.t0 >= h.dur) { drift.set(h.key, h.to); hops.splice(x, 1); } }
    for (let x = sparkles.length - 1; x >= 0; x--) if (t - sparkles[x].t0 > 560) sparkles.splice(x, 1);
    const moving = jobs.length || hops.length || sparkles.length;
    if (moving && t - lastDraw >= 40) { lastDraw = t; return true; }
    return false;
  }
  let lastStep = 0, lastDraw = 0;
  const busy = () => on && (jobs.length > 0 || hops.length > 0 || sparkles.length > 0 || doomed.size > 0 || [...shown.values()].some(n => n > 0));

  /* ---------- the truck: a hover garbage truck, drawn like the cars, in deep teal with a gold band ---------- */
  function inPoly(x, y, pts) { let c = false; for (let a = 0, b = pts.length - 1; a < pts.length; b = a++) { const [xa, ya] = pts[a], [xb, yb] = pts[b]; if ((ya > y) !== (yb > y) && x < (xb - xa) * (y - ya) / (yb - ya) + xa) c = !c; } return c; }
  function rasterBox(g, P, i0, i1, j0, j1, z0, z1, cols) {
    const faces = [[[P(i0, j1, z0), P(i1, j1, z0), P(i1, j1, z1), P(i0, j1, z1)], cols.left], [[P(i1, j0, z0), P(i1, j1, z0), P(i1, j1, z1), P(i1, j0, z1)], cols.right],
      [[P(i0, j0, z1), P(i1, j0, z1), P(i1, j1, z1), P(i0, j1, z1)], cols.top]];
    for (const [pts, col] of faces) {
      if (!col) continue;
      const xs = pts.map(p => p[0]), ys = pts.map(p => p[1]);
      g.fillStyle = col;
      for (let y = Math.floor(Math.min(...ys)); y <= Math.ceil(Math.max(...ys)); y++) for (let x = Math.floor(Math.min(...xs)); x <= Math.ceil(Math.max(...xs)); x++) if (inPoly(x + 0.5, y + 0.5, pts)) g.fillRect(x, y, 1, 1);
    }
  }
  function outline(c, col) {
    const g = c.getContext('2d'), w = c.width, hh = c.height, src = g.getImageData(0, 0, w, hh), d = src.data, out = g.createImageData(w, hh);
    const [r, gg, b] = hexToRgb(col);
    for (let y = 0; y < hh; y++) for (let x = 0; x < w; x++) {
      const k = (y * w + x) * 4;
      if (d[k + 3]) { out.data.set(d.subarray(k, k + 4), k); continue; }
      const nb = [[1, 0], [-1, 0], [0, 1], [0, -1]].some(([dx, dy]) => { const X = x + dx, Y = y + dy; return X >= 0 && Y >= 0 && X < w && Y < hh && d[(Y * w + X) * 4 + 3]; });
      if (nb) { out.data[k] = r; out.data[k + 1] = gg; out.data[k + 2] = b; out.data[k + 3] = 255; }
    }
    g.putImageData(out, 0, 0);
    return c;
  }
  const shade = (hex, k) => mix(hex, '#2B2542', k), lite = (hex, k) => mix(hex, '#FFFFFF', k);
  function truck(h) {
    const A = artSet();
    if (A.truck[h]) return A.truck[h];
    const along = h[0] === 'i', plus = h[1] === '+';
    const [c, g] = mkCanvas(40, 36), ox = 20, oy = 26, HW = WORLD.TW / 2, HH = WORLD.TH / 2;
    const P = (i, j, z) => [ox + (i - j) * HW, oy + (i + j) * HH - z];
    const box = (l0, l1, w0, w1, z0, z1, cols) => along ? rasterBox(g, P, l0, l1, w0, w1, z0, z1, cols) : rasterBox(g, P, w0, w1, l0, l1, z0, z1, cols);
    const L = 0.46, W = 0.18, cab = plus ? [0.18, L] : [-L, -0.18], bin = plus ? [-L + 0.07, 0.15] : [-0.15, L - 0.07], hop = plus ? [-L, -L + 0.07] : [L - 0.07, L];
    const set = col => ({ left: tone(col), right: tone(shade(col, 0.24)), top: tone(lite(col, 0.3)) });
    box(hop[0], hop[1], -W + 0.02, W - 0.02, 3, 10, { left: tone('#433A5E'), right: tone('#2B2542'), top: tone('#5A5073') });   // the hopper at the back
    box(bin[0], bin[1], -W, W, 3, 13, set('#3FA79E'));                                                                     // the body
    box(bin[0], bin[1], -W - 0.001, W + 0.001, 6, 8, { left: tone('#F2C75C'), right: tone(shade('#F2C75C', 0.2)), top: null });   // a gold band
    box(cab[0], cab[1], -W + 0.01, W - 0.01, 3, 9.5, set('#7FD6CE'));                                                       // the cab
    box(cab[0] + (plus ? 0.04 : 0), cab[1] - (plus ? 0 : 0.04), -W + 0.005, W - 0.005, 6.5, 9, { left: tone('#9CC7F3'), right: tone('#6FA5DE'), top: null });
    const out = { c: outline(c, tone('#5A5073')), ox, oy };
    g.fillStyle = '#3FE0F0';                                         // the hover pads glow under it, by day and by night
    for (const t of [-0.3, 0.3]) for (const s of [-0.12, 0.12]) { const [x, y] = along ? P(t, s, 1) : P(s, t, 1); g.fillRect(Math.round(x), Math.round(y), 1, 1); }
    A.truck[h] = out;
    return out;
  }

  /* ---------- the crew: three of the city's people in coral overalls and yellow caps ---------- */
  const LOOKS = [{ hair: 0, skin: 0, shirt: 5, pants: 1, long: false, dress: false, item: 'cap', cap: 2 },
    { hair: 1, skin: 1, shirt: 5, pants: 1, long: true, dress: false, item: 'cap', cap: 2 },
    { hair: 3, skin: 2, shirt: 5, pants: 1, long: false, dress: false, item: 'cap', cap: 2 }];

  /* ---------- the map asks for these ---------- */
  /* Pieces lie flat on the ground, so they skip the depth sort: those on sidewalks and streets are drawn with the ground,
     under everything standing, and those on a plot (a building's front strip, or a park) right after that plot. */
  const ground = [], onPlots = new Map();
  const plotOf = (i, j) => {
    const { S, MARGIN, PITCH } = WORLD, u = Math.floor((i - MARGIN) / PITCH), v = Math.floor((j - MARGIN) / PITCH);
    const di = i - (MARGIN + u * PITCH), dj = j - (MARGIN + v * PITCH);
    return di >= 0 && di <= S && dj >= 0 && dj <= S ? u + ',' + v : null;
  };
  function prepare(view) {
    visible = []; ground.length = 0; onPlots.clear();
    if (!on || MapView.editing()) return;
    const A = artSet(), t = performance.now();
    const inView = (x, y, pad = 8) => !view || (x > view.x0 - pad && x < view.x1 + pad && y > view.y0 - pad && y < view.y1 + pad);
    const put = (i, j, f) => { const k = plotOf(i, j); if (!k) { ground.push(f); return; } if (!onPlots.has(k)) onPlots.set(k, []); onPlots.get(k).push(f); };
    for (const p of DB.projects) {
      const n = shown.get(p.id) || 0, dset = doomed.get(p.id);
      if (!n && !dset) continue;
      const spots = spotsFor(p);
      const draw = s => {
        if (!s) return;
        const off = offsetOf(p.id + ':' + s.n, t), x = s.x + off[0], y = s.y - s.lift + off[1];
        if (!inView(x, y)) return;
        const list = A[s.kind], spr = list[s.variant % list.length], w = spr.w / 2, hh = spr.h / 2;
        const left = Math.round((x - w / 2) * 2) / 2, top = Math.round((spr.stand ? y - hh + 0.5 : y - hh / 2) * 2) / 2;
        visible.push({ id: p.id, spot: s });
        put(s.i, s.j, g => {
          if (spr.stand) { g.fillStyle = 'rgba(43, 37, 66, 0.25)'; g.fillRect(Math.round(x - w / 2), Math.round(y), Math.ceil(w), 1); }
          MapView.drawHalf(s.flip ? spr.flipped : spr.plain, left, top);
        });
      };
      for (let k = 0; k < n && k < spots.length; k++) draw(spots[k]);
      if (dset) for (const k of dset) if (k >= n) draw(spots[k]);
    }
    for (const sp of sparkles) {
      const age = t - sp.t0;
      if (age >= 0 && inView(sp.x, sp.y)) put(sp.i, sp.j, g => sparkle(g, sp.x, sp.y - 2, age));
    }
  }
  const drawGround = g => { for (const f of ground) f(g); };
  const drawOnPlot = (g, u, v) => { const l = onPlots.get(u + ',' + v); if (l) for (const f of l) f(g); };
  /* The truck and its crew stand up, so they join the depth sort like the cars and the people. */
  function items() {
    if (!on || MapView.editing() || typeof Traffic === 'undefined') return [];
    const out = [], t = performance.now(), toW = MapView.tileToWorld;
    if (truckActive()) for (const j of jobs) {
      if (j.phase === 'gone') continue;
      const [i, jj] = j.r.at(j.s), [x, y] = toW(i, jj), tk = truck(j.r.h);
      const dir = Math.sign(j.r.s1 - j.r.s0), fadeIn = clamp((j.s - j.r.s0) * dir / 1.2, 0, 1), fadeOut = clamp((j.r.s1 - j.s) * dir / 1.2, 0, 1);
      const alpha = Math.min(fadeIn, fadeOut), bob = Math.round(Math.sin(t / 380 + j.t0));
      out.push({ i, j: jj, key: i + jj, box: { x0: x - 26, x1: x + 26, y0: y - 26, y1: y + 18 }, draw: g => {
        g.globalAlpha = alpha;
        g.fillStyle = 'rgba(43, 37, 66, 0.26)';                          // its shadow on the road, two pixels below it
        const sh = j.r.h[0] === 'i' ? [[-0.4, -0.12], [0.4, -0.12], [0.4, 0.12], [-0.4, 0.12]] : [[-0.12, -0.4], [0.12, -0.4], [0.12, 0.4], [-0.12, 0.4]];
        g.beginPath(); sh.forEach(([a, b], k) => { const [px, py] = toW(i + a, jj + b); k ? g.lineTo(px, py) : g.moveTo(px, py); }); g.closePath(); g.fill();
        g.drawImage(tk.c, Math.round(x) - tk.ox, Math.round(y) - tk.oy - 1 + bob);
        if (Light.t > 0.3) lamps(g, j, i, jj);
        g.globalAlpha = 1;
      } });
      if (j.phase === 'crew') for (const c of j.crew) {
        if (c.state === 'wait' || c.state === 'home') continue;
        const [ci, cj] = c.at, [cx, cy] = toW(ci, cj), look = LOOKS[c.k % LOOKS.length], working = c.state === 'work';
        let frame = 0, back = false, flip = false;
        if (c.hd) { back = c.hd[0] + c.hd[1] < 0; flip = c.hd[0] - c.hd[1] < 0; frame = Math.floor(t / 150 + c.k) % 2; }
        else { frame = Math.floor(t / 220 + c.k * 2) % 2 ? 'talkL' : 'talkR'; back = c.k === 1; flip = Math.floor(t / 900 + c.k) % 2 === 1; }
        const img = Traffic._sprite(look, frame, back, flip);
        out.push({ i: ci, j: cj, key: ci + cj, box: { x0: cx - 4, x1: cx + 4, y0: cy - 9, y1: cy + 2 }, draw: g => {
          g.fillStyle = 'rgba(43, 37, 66, 0.28)'; g.fillRect(Math.round(cx) - 1, Math.round(cy), 3, 1);
          g.drawImage(img, Math.round(cx) - 2, Math.round(cy) - 7);
          if (working) broom(g, Math.round(cx), Math.round(cy), t, c.k);
        } });
      }
    }
    return out;
  }
  function lamps(g, j, i, jj) {
    const toW = MapView.tileToWorld, [ha, hb] = { 'j+': [0, 1], 'i-': [-1, 0] }[j.r.h], toward = ha > 0 || hb > 0, half = 0.46;
    const [rx, ry] = [-hb, ha], end = toward ? half : -half;
    g.fillStyle = toward ? '#FFF2B8' : '#EE4C93';
    for (const sgn of [1, -1]) { const [lx, ly] = toW(i + ha * end + rx * 0.1 * sgn, jj + hb * end + ry * 0.1 * sgn); g.fillRect(Math.round(lx), Math.round(ly) - 3, 1, 1); }
  }
  function broom(g, x, y, t, k) {
    const swing = Math.floor(t / 220 + k * 2) % 2 ? 1 : -1;
    g.fillStyle = tone('#9C7C6B');
    g.fillRect(x + 2, y - 4, 1, 1); g.fillRect(x + 2 + (swing > 0 ? 1 : 0), y - 3, 1, 1); g.fillRect(x + 2 + (swing > 0 ? 1 : 0), y - 2, 1, 1);
    g.fillStyle = tone('#F2C75C');
    g.fillRect(x + 1 + (swing > 0 ? 2 : 0), y - 1, 3, 1);
  }
  function sparkle(g, x, y, age) {
    const X = Math.round(x), Y = Math.round(y), f = Math.floor(age / 140);
    const W = '#FFF6D6', Y2 = '#FFE38A';
    if (f === 0) { g.fillStyle = W; g.fillRect(X, Y, 1, 1); }
    else if (f === 1) { g.fillStyle = Y2; g.fillRect(X - 1, Y, 3, 1); g.fillRect(X, Y - 1, 1, 3); g.fillStyle = W; g.fillRect(X, Y, 1, 1); }
    else if (f === 2) { g.fillStyle = Y2; g.fillRect(X - 2, Y, 1, 1); g.fillRect(X + 2, Y, 1, 1); g.fillRect(X, Y - 2, 1, 1); g.fillRect(X, Y + 2, 1, 1); g.fillStyle = W; g.fillRect(X, Y, 1, 1); }
    else { g.fillStyle = Y2; g.fillRect(X - 1, Y - 1, 1, 1); g.fillRect(X + 1, Y + 1, 1, 1); g.fillRect(X + 1, Y - 1, 1, 1); g.fillRect(X - 1, Y + 1, 1, 1); }
  }

  /* ---------- the switch, and what the panel sets ---------- */
  function setOn(v) {
    on = !!v;
    try { localStorage.setItem(KEY, on ? '1' : '0'); } catch (e) { /* this visit only */ }
    if (!on) { jobs.length = 0; clearAll(performance.now(), false); }
    for (const f of subs) f();
    MapView.invalidate(); MapView.kick();
  }
  /* A ticked task, a moved building or a new day shows within a second. */
  let lastSig = '';
  setInterval(() => {
    if (typeof DB === 'undefined' || !primed) return;
    const sig = DB.projects.map(p => p.id + ':' + p.plot.u + '.' + p.plot.v + ':' + wanted(p)).join();
    if (sig !== lastSig) { lastSig = sig; refresh(); }
  }, 1000);
  return {
    isOn: () => on, setOn, items, prepare, drawGround, drawOnPlot, step, busy, refresh, rulesOf, CEILING,
    shownOf: id => shown.get(id) || 0, waitingOf: id => (doomed.get(id) || new Set()).size, totals: () => ({ ...lastTargets }),
    trucks: () => jobs.filter(j => j.phase !== 'gone').length, queued: () => queue.length, onChange: f => subs.push(f),
    /* for the tests: counts set by hand, the spots, the drawn art, and what is on the map now */
    _test: { force: (id, n) => { if (n == null) forced.delete(id); else forced.set(id, n); refresh(); }, spots: id => spotsFor(getProject(id)),
      truck: h => truck(h).c, art: () => artSet(), visible: () => visible.length, jobs: () => jobs.map(j => ({ id: j.id, phase: j.phase, s: j.s, r: j.r, crew: j.crew.map(c => ({ state: c.state, at: c.at })) })),
      sparkles: () => sparkles.length },
  };
})();
