/* Traffic: cars, a small bus, and delivery drones on the streets, and people on the sidewalks.
   Everything steps in whole map pixels, calmly. The city is busiest around the buildings you
   worked on recently, and a building left alone goes quiet around it. */
const Traffic = (() => {
  const KEY = 'nullovation-city:traffic';
  let on = (() => { try { return localStorage.getItem(KEY) !== '0'; } catch (e) { return true; } })();
  const SW = 0.3, LANE = 0.35, CAR_GAP = 0.9;
  const HEADS = { 'i+': [1, 0], 'i-': [-1, 0], 'j+': [0, 1], 'j-': [0, -1] };
  const rightOf = h => { const [a, b] = HEADS[h]; return [-b, a]; };
  const keyOf = v => Object.keys(HEADS).find(k => HEADS[k][0] === v[0] && HEADS[k][1] === v[1]);
  const R = Math.random;
  const pickW = list => { let s = 0; for (const x of list) s += x[1]; let r = R() * s; for (const x of list) if ((r -= x[1]) < 0) return x[0]; return list.length ? list[list.length - 1][0] : null; };
  let N = 0, ready = false, cars = [], people = [], riders = [], drones = [], busy = new Map(), weights = new Map(), seats = new Map();
  let last = 0, lastDraw = 0, lastW = 0;
  const S = () => WORLD.S, PITCH = () => WORLD.PITCH;
  const roadC = r => r * WORLD.PITCH + WORLD.GAP / 2;          // a road's centre line, in tiles
  const lotA0 = u => WORLD.MARGIN + u * WORLD.PITCH;           // a lot's first tile
  const SIDE = () => WORLD.S + SW, PER = () => SIDE() * 4;     // a block's sidewalk loop

  /* ---------- how busy each plot is: recent work draws people and cars ---------- */
  /* How busy a building is: everything that happened to it this week, each thing fading over seven days,
     plus a little for being touched today. 0 is idle, near 1 is a busy week. */
  function busyness(p, now = Date.now()) {
    const WEEK = 7 * 864e5;
    let score = 0;
    for (const e of p.activity || []) { const age = now - e.at; if (age >= 0 && age < WEEK) score += 1 - age / WEEK; }
    const t = Math.max(p.updatedAt || 0, (p.urgency && p.urgency.lastWorked) || 0);
    if (now - t < 864e5) score += 1.5;
    return 1 - Math.exp(-score / 5);
  }
  function refreshWeights(now = Date.now()) {
    weights = new Map();
    const lay = MapView.layout();
    for (let u = 0; u < N; u++) for (let v = 0; v < N; v++) {
      const p = lay.get(u + ',' + v);
      weights.set(u + ',' + v, p ? 0.03 + 0.97 * busyness(p, now) : 0.1);   // parks: a few people pass through and sit
    }
  }
  const BUSY = 0.3;                                             // at or above this, a building draws its own crowd
  const CROWD_KEY = 'nullovation-city:crowds', CROWD_PER = { none: 0, small: 8, medium: 14, large: 20 }, CEILING = 150;
  let crowd = (() => { try { const v = localStorage.getItem(CROWD_KEY); return v in CROWD_PER ? v : 'medium'; } catch (e) { return 'medium'; } })();
  const wAt = (u, v) => (u < 0 || v < 0 || u >= N || v >= N) ? 0 : (weights.get(u + ',' + v) ?? 0);
  const projectAt = (u, v) => MapView.layout().get(u + ',' + v) || null;

  /* ---------- cars and the bus ---------- */
  const edgeLots = (ri, rj, h) => {                            // the two lots a street segment runs between
    if (h === 'i+') return [[ri, rj - 1], [ri, rj]];
    if (h === 'i-') return [[ri - 1, rj - 1], [ri - 1, rj]];
    if (h === 'j+') return [[ri - 1, rj], [ri, rj]];
    return [[ri - 1, rj - 1], [ri, rj - 1]];
  };
  const edgeW = (ri, rj, h) => 0.08 + 2 * edgeLots(ri, rj, h).reduce((s, [u, v]) => s + wAt(u, v), 0);
  const validEdge = (ri, rj, h) => { const [a, b] = HEADS[h]; const ti = ri + a, tj = rj + b; return ti >= 0 && tj >= 0 && ti <= N && tj <= N; };
  function carPos(c) {
    const [a, b] = HEADS[c.h], [ra, rb] = rightOf(c.h);
    return [roadC(c.ri) + a * c.t + ra * LANE, roadC(c.rj) + b * c.t + rb * LANE];
  }
  /* The end a car drives toward: the street segment's key, its end, and where its marks sit along the way. */
  function approach(c) {
    const along = c.h[0] === 'i', plus = c.h[1] === '+';
    const road = along ? c.rj : c.ri, from = along ? c.ri : c.rj;
    const li = plus ? from : from - 1;
    if (li < 0 || li >= N) return null;
    const e = plus ? 1 : 0, E = plus ? lotA0(li) + S() : lotA0(li);
    const sign = plus ? 1 : -1, half = c.len / 2, base = roadC(from);
    const tAt = front => (front - sign * half - base) * sign;
    return { key: li + ',' + road + ',' + (along ? 1 : 2) + ',' + e, mark: MapView.crossMark(li, road, along, e),
      tStop: tAt(plus ? E - 0.12 : E + 0.13), tZebra: tAt(plus ? E - 0.45 : E + 0.45) };
  }
  function spawnCar(type) {
    const edges = [];
    for (let ri = 0; ri <= N; ri++) for (let rj = 0; rj <= N; rj++) for (const h of Object.keys(HEADS)) if (validEdge(ri, rj, h)) edges.push([[ri, rj, h], edgeW(ri, rj, h)]);
    for (let tries = 0; tries < 30; tries++) {
      const [ri, rj, h] = pickW(edges);
      const c = { type, ri, rj, h, t: 0.6 + R() * (PITCH() - 2), next: null, wait: 0, stopped: false,
        v: type === 'bus' ? 0.32 + R() * 0.1 : 0.42 + R() * 0.36, len: type === 'bus' ? 1.1 : 0.56,
        color: Math.floor(R() * CAR_COLORS.length) };
      const [i, j] = carPos(c);
      if (cars.every(o => { const [a, b] = carPos(o); return Math.hypot(a - i, b - j) > 1.4; })) return c;
    }
    return null;
  }
  function chooseNext(c) {
    const [a, b] = HEADS[c.h], ti = c.ri + a, tj = c.rj + b;
    const r = rightOf(c.h), l = [-r[0], -r[1]];
    const opts = [[c.h, 1.6], [keyOf(r), 1], [keyOf(l), 1]]
      .filter(([h]) => validEdge(ti, tj, h)).map(([h, bias]) => [h, bias * edgeW(ti, tj, h)]);
    return opts.length ? pickW(opts) : keyOf([-a, -b]);        // a dead end at the map's edge: turn back
  }
  function updateCars(dt, now) {
    for (const c of cars) {
      if (c.wait > 0) { c.wait -= dt; continue; }
      if (!c.next && c.t > PITCH() - 1.3) c.next = chooseNext(c);
      let step = c.v * dt;
      const ap = approach(c);
      if (ap) {
        if (ap.mark === 'stop' && !c.stopped && c.t < ap.tStop && c.t + step >= ap.tStop) { c.t = ap.tStop; c.stopped = true; c.wait = 0.8 + R() * 1.1; continue; }
        if (ap.mark === 'zebra' && (busy.get(ap.key) || 0) > now && c.t <= ap.tZebra + 0.02 && c.t + step > ap.tZebra) { c.t = Math.max(c.t, Math.min(ap.tZebra, c.t + step)); continue; }
      }
      const [ci, cj] = carPos(c), [ha, hb] = HEADS[c.h];
      const blocked = cars.some(o => {                           // someone close ahead in the same lane: hold back
        if (o === c || o.h !== c.h) return false;
        const [oi, oj] = carPos(o);
        const ahead = (oi - ci) * ha + (oj - cj) * hb, side = Math.abs((oi - ci) * hb - (oj - cj) * ha);
        return ahead > 0 && ahead < (c.len + o.len) / 2 + CAR_GAP * 0.6 && side < 0.2;
      });
      if (blocked) continue;
      c.t += step;
      const turn = c.next;
      if (!turn) continue;
      const r = rightOf(c.h), isRight = turn === keyOf(r), isStraight = turn === c.h, isBack = !isRight && !isStraight && turn === keyOf([-ha, -hb]);
      const at = isStraight ? PITCH() : isRight ? PITCH() - LANE : isBack ? PITCH() : PITCH() + LANE;
      if (c.t >= at) {
        const over = c.t - at;
        c.ri += ha; c.rj += hb; c.h = turn; c.next = null; c.stopped = false;
        c.t = (isStraight || isBack ? 0 : isRight ? LANE : -LANE) + over;
      }
    }
  }

  /* ---------- people ---------- */
  function loopPt(u, v, p) {
    const I0 = lotA0(u) - SW / 2, J0 = lotA0(v) - SW / 2, s = SIDE();
    p = ((p % PER()) + PER()) % PER();
    const k = Math.floor(p / s), f = p - k * s;
    return k === 0 ? [I0 + f, J0] : k === 1 ? [I0 + s, J0 + f] : k === 2 ? [I0 + s - f, J0 + s] : [I0, J0 + s - f];
  }
  const sideOf = p => Math.floor((((p % PER()) + PER()) % PER()) / SIDE());
  /* Where people can cross from a block: only at zebra crossings, to the block across the street. */
  function crossingsOf(u, v) {
    const out = [], s = SIDE(), a0 = lotA0(u), a1 = a0 + S(), b0 = lotA0(v), b1 = b0 + S();
    const I0 = a0 - SW / 2, I1 = a1 + SW / 2, J0 = b0 - SW / 2, J1 = b1 + SW / 2;
    const add = (li, road, along, e, from, to, u2, v2, p, p2) => {
      if (MapView.crossMark(li, road, along, e) === 'zebra') out.push({ p, u2, v2, p2, key: li + ',' + road + ',' + (along ? 1 : 2) + ',' + e, from, to });
    };
    if (v > 0) { const J = lotA0(v - 1) + S() + SW / 2; for (const [e, iz] of [[0, a0 + 0.23], [1, a1 - 0.23]]) add(u, v, true, e, [iz, J0], [iz, J], u, v - 1, iz - I0, 2 * s + (I1 - iz)); }
    if (v < N - 1) { const J = lotA0(v + 1) - SW / 2; for (const [e, iz] of [[0, a0 + 0.23], [1, a1 - 0.23]]) add(u, v + 1, true, e, [iz, J1], [iz, J], u, v + 1, 2 * s + (I1 - iz), iz - I0); }
    if (u > 0) { const I = lotA0(u - 1) + S() + SW / 2; for (const [e, jz] of [[0, b0 + 0.23], [1, b1 - 0.23]]) add(v, u, false, e, [I0, jz], [I, jz], u - 1, v, 3 * s + (J1 - jz), s + (jz - J0)); }
    if (u < N - 1) { const I = lotA0(u + 1) - SW / 2; for (const [e, jz] of [[0, b0 + 0.23], [1, b1 - 0.23]]) add(v, u + 1, false, e, [I1, jz], [I, jz], u + 1, v, s + (jz - J0), 3 * s + (J1 - jz)); }
    return out;
  }
  const crossCache = new Map();
  const crossings = (u, v) => { const k = u + ',' + v; if (!crossCache.has(k)) crossCache.set(k, crossingsOf(u, v)); return crossCache.get(k); };
  /* Park benches on empty plots, in the park scenes' own coordinates; a mirrored park swaps them. */
  const BENCHES = { park: [[2.0, 2.45]], pond: [[3.0, 3.35]], plaza: [[1.95, 3.45], [3.45, 1.95]], garden: [] };
  function benchSeats(u, v) {
    if (projectAt(u, v)) return [];
    const info = MapView.lotInfo(u, v);
    if (!info) return [];
    const out = [];
    for (const [a, b] of BENCHES[info.id] || []) {
      const [la, lb] = info.flip ? [b, a] : [a, b];
      for (const off of [0.1, 0.27]) out.push({ key: u + ',' + v + ',' + la + ',' + off, at: info.flip ? [lotA0(u) + la, lotA0(v) + lb + off] : [lotA0(u) + la + off, lotA0(v) + lb] });
    }
    return out;
  }
  const pickI = list => Math.floor(R() * list.length);
  /* A look: about half have long hair, and half of those wear a dress; at most one item each. */
  function newLook() {
    const look = { hair: pickI(HAIR), skin: pickI(SKIN), shirt: pickI(SHIRTS), pants: pickI(PANTS), long: R() < 0.5, dress: false, item: null, cap: 0 };
    look.dress = look.long && R() < 0.5;
    const r = R();
    look.item = r < 0.06 ? 'pack' : r < 0.18 ? 'tote' : r < 0.33 ? 'cap' : r < 0.43 ? 'phone' : null;
    if (look.item === 'cap') look.cap = pickI(CAPS);
    return look;
  }
  /* A few run, twice as fast, and never stop; some walk with a kid or a dog beside them. */
  function newPerson(u, v, p, mode = 'walk') {
    const q = { u, v, p, dir: R() < 0.5 ? 1 : -1, sp: 0.2 + R() * 0.14, mode, t: 0, alpha: 1, walked: R(), lat: (R() - 0.5) * 0.1, talk: 0, talkT: 0,
      look: newLook(), run: R() < 0.03, buddy: null };
    if (q.run) { q.sp *= 2; q.look.dress = false; q.look.item = null; }
    else {
      const b = R();
      if (b < 0.06) q.buddy = { kind: 'kid', look: Object.assign(newLook(), { long: false, dress: false, item: null }) };
      else if (b < 0.11) q.buddy = { kind: 'dog', color: pickI(DOGS) };
    }
    return q;
  }
  /* Cyclists ride the sidewalk loops three times as fast as walking, and cross at zebras; they never stop. */
  function newRider(u, v, p) {
    return { u, v, p, dir: R() < 0.5 ? 1 : -1, sp: 0.6 + R() * 0.3, mode: 'walk', alpha: 1, walked: R(),
      look: Object.assign(newLook(), { frame: pickI(BIKES) }) };
  }
  const riderCount = () => Math.round(2 * N * N / 25);
  function blockPick() {
    const list = [];
    for (let u = 0; u < N; u++) for (let v = 0; v < N; v++) list.push([[u, v], wAt(u, v) + 0.03]);
    return pickW(list);
  }
  function spawnPerson() { const [u, v] = blockPick(); return newPerson(u, v, R() * PER()); }
  /* Someone steps out of a building you worked on recently, or out of a park when there are none. */
  function personFromBuilding(at = null) {
    const list = [];
    if (!at) for (let u = 0; u < N; u++) for (let v = 0; v < N; v++) if (projectAt(u, v)) list.push([[u, v], wAt(u, v) + 0.02]);
    if (!at && !list.length) return spawnPerson();
    const [u, v] = at || pickW(list), s = SIDE();
    const front = R() < 0.5 ? 1 : 2, f = 0.6 + R() * (s - 1.2), p = front * s + f;
    const pt = loopPt(u, v, p), inside = front === 1 ? [pt[0] - 0.6, pt[1]] : [pt[0], pt[1] - 0.6];
    const q = newPerson(u, v, p, 'path');
    Object.assign(q, { path: [inside, pt], pos: inside, k: 0, then: 'walk', alpha: 0, fadeIn: true });
    return q;
  }
  const here = q => q.mode === 'walk' || q.mode === 'pause' ? loopPt(q.u, q.v, q.p) : q.pos;
  function startPath(q, from, to, then) { Object.assign(q, { mode: 'path', path: [from, to], pos: from, k: 0, then }); }
  /* The extras each busy building should have, in proportion to how busy it is. */
  function extraTargets() {
    const busyOnes = [];
    for (let u = 0; u < N; u++) for (let v = 0; v < N; v++) if (projectAt(u, v) && wAt(u, v) >= BUSY) busyOnes.push([u + ',' + v, wAt(u, v)]);
    const out = new Map(), per = CROWD_PER[crowd];
    const room = Math.max(0, CEILING - baseCount()), scale = busyOnes.length * per > room ? room / (busyOnes.length * per) : 1;
    for (const [k] of busyOnes) out.set(k, Math.floor(per * scale));
    return out;
  }
  const baseCount = () => Math.round(20 * N * N / 25);
  let lastBalance = 0;
  function balanceExtras(now) {
    const want = extraTargets(), have = new Map();
    for (const q of people) if (q.home && !q.leaving) have.set(q.home, (have.get(q.home) || 0) + 1);
    for (const [k, n] of want) for (let m = have.get(k) || 0; m < n; m++) {           // step out of the building to join the crowd
      const [u, v] = k.split(',').map(Number), q = personFromBuilding([u, v]);
      q.home = k; q.p = q.p; people.push(q);
    }
    for (const q of people) {                                                            // a building gone quiet: its crowd goes inside
      if (!q.home || q.leaving) continue;
      const n = want.get(q.home) || 0, c = have.get(q.home) || 0;
      if (c > n && (q.mode === 'walk' || q.mode === 'pause')) { q.leaving = true; have.set(q.home, c - 1); }
    }
  }
  function updatePeople(dt, now) {
    const target = baseCount();
    if (now - lastBalance > 1500) { lastBalance = now; balanceExtras(now); }
    for (const q of people) {
      if (q.mode === 'pause') {                                  // standing: hands move now and then, as if talking
        q.talkT -= dt;
        if (q.talkT <= 0) { q.talk = q.talk ? 0 : 1 + Math.floor(R() * 2); q.talkT = q.talk ? 0.25 + R() * 0.5 : 0.3 + R() * 1.2; }
      } else q.talk = 0;
      if (q.mode === 'pause' || q.mode === 'sit') {
        q.t -= dt;
        if (q.t <= 0) {
          if (q.mode === 'sit') { seats.delete(q.seat); startPath(q, q.pos, q.back, 'walk'); }
          else q.mode = 'walk';
        }
        continue;
      }
      if (q.mode === 'path') {
        const [a, b] = q.path, len = Math.hypot(b[0] - a[0], b[1] - a[1]) || 0.001;
        q.k = Math.min(len, q.k + q.sp * dt); q.walked += q.sp * dt;
        const f = q.k / len;
        q.pos = [a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f];
        if (q.fadeIn) q.alpha = Math.min(1, q.alpha + dt / 0.8);
        if (q.cross) busy.set(q.cross, now + 700);               // cars wait while someone is on the zebra
        if (q.k >= len) {
          q.cross = null; q.fadeIn = false;
          if (q.then === 'walk') { q.mode = 'walk'; if (q.nextBlock) { [q.u, q.v, q.p] = q.nextBlock; q.nextBlock = null; } }
          else if (q.then === 'sit') { q.mode = 'sit'; q.t = 10 + R() * 20; }
          else if (q.then === 'gone') q.mode = 'fade';
        }
        continue;
      }
      if (q.mode === 'fade') { q.alpha -= dt / 0.8; if (q.alpha <= 0) q.dead = true; continue; }
      /* walking the block's loop */
      const p0 = q.p, p1 = q.p + q.dir * q.sp * dt;
      q.p = p1; q.walked += q.sp * dt;
      const passed = x => { const P = PER(); const A = ((p0 % P) + P) % P, B = A + (p1 - p0); return q.dir > 0 ? (x > A && x <= B) || (x + P > A && x + P <= B) : (x < A && x >= B) || (x - P < A && x - P >= B); };
      const cross = q.home ? null : crossings(q.u, q.v).find(c => passed(c.p));
      if (cross && R() < 0.3 * (0.3 + wAt(cross.u2, cross.v2))) {
        startPath(q, cross.from, cross.to, 'walk'); q.cross = cross.key; q.nextBlock = [cross.u2, cross.v2, cross.p2];
        continue;
      }
      const side = sideOf(q.p);
      const rate = q.leaving ? 1 : q.home ? 0.05 : 0.025 * wAt(q.u, q.v);
      if (projectAt(q.u, q.v) && (side === 1 || side === 2) && R() < dt * rate) {   // into a building
        const pt = loopPt(q.u, q.v, q.p);
        startPath(q, pt, side === 1 ? [pt[0] - 0.6, pt[1]] : [pt[0], pt[1] - 0.6], 'gone');
        continue;
      }
      if (!q.run && !q.buddy && R() < dt * 0.03) {               // a free bench in this park
        const seat = benchSeats(q.u, q.v).find(s => !seats.has(s.key));
        if (seat) { const pt = loopPt(q.u, q.v, q.p); seats.set(seat.key, q); q.seat = seat.key; q.back = pt; startPath(q, pt, seat.at, 'sit'); continue; }
      }
      const onBlock = people.filter(o => o.u === q.u && o.v === q.v && (o.mode === 'walk' || o.mode === 'pause'));
      const standing = onBlock.filter(o => o.mode === 'pause').length;
      if (standing >= Math.max(2, onBlock.length * 0.34)) continue;           // most of a crowd keeps moving
      if (q.run) continue;                                        // runners keep running
      if (R() < dt / (q.home ? 35 : 50)) { q.mode = 'pause'; q.t = 4 + R() * 8; }  // stop for a while; others nearby may join
      else if (R() < dt * 0.3) {
        const [i, j] = loopPt(q.u, q.v, q.p);
        const group = onBlock.filter(o => o !== q && o.mode === 'pause');
        const near = group.find(o => { const [a, b] = loopPt(o.u, o.v, o.p); return Math.hypot(a - i, b - j) < 0.45; });
        if (near && group.filter(o => { const [a, b] = loopPt(o.u, o.v, o.p); return Math.hypot(a - i, b - j) < 0.6; }).length < (q.home ? 5 : 4)) { q.mode = 'pause'; q.t = near.t + R() * 3; }
      }
    }
    people = people.filter(q => !q.dead);
    const base = people.filter(q => !q.home).length;
    for (let k = base; k < target; k++) people.push(personFromBuilding());
  }
  function updateRiders(dt, now) {
    for (const q of riders) {
      if (q.mode === 'path') {                                   // across a zebra; cars wait for them too
        const [a, b] = q.path, len = Math.hypot(b[0] - a[0], b[1] - a[1]) || 0.001;
        q.k = Math.min(len, q.k + q.sp * dt); q.walked += q.sp * dt;
        const f = q.k / len;
        q.pos = [a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f];
        busy.set(q.cross, now + 700);
        if (q.k >= len) { q.cross = null; q.mode = 'walk'; [q.u, q.v, q.p] = q.nextBlock; q.nextBlock = null; }
        continue;
      }
      const p0 = q.p, p1 = q.p + q.dir * q.sp * dt;
      q.p = p1; q.walked += q.sp * dt;
      const P = PER(), A = ((p0 % P) + P) % P, B = A + (p1 - p0);
      const passed = x => q.dir > 0 ? (x > A && x <= B) || (x + P > A && x + P <= B) : (x < A && x >= B) || (x - P < A && x - P >= B);
      const cross = crossings(q.u, q.v).find(c => passed(c.p));
      if (cross && R() < 0.3) { startPath(q, cross.from, cross.to, 'walk'); q.cross = cross.key; q.nextBlock = [cross.u2, cross.v2, cross.p2]; }
    }
  }

  /* ---------- delivery drones: hops between the buildings you are busy with ---------- */
  function droneTarget() {
    const list = [];
    for (let u = 0; u < N; u++) for (let v = 0; v < N; v++) list.push([[u, v], (projectAt(u, v) ? wAt(u, v) : 0.02) + 0.01]);
    const [u, v] = pickW(list);
    return [lotA0(u) + S() / 2 + (R() - 0.5), lotA0(v) + S() / 2 + (R() - 0.5)];
  }
  function updateDrones(dt) {
    for (const d of drones) {
      d.spin += dt;
      if (d.hold > 0) { d.hold -= dt; continue; }
      const [ti, tj] = d.to, di = ti - d.i, dj = tj - d.j, dist = Math.hypot(di, dj);
      const step = d.sp * dt;
      if (dist <= step) { d.i = ti; d.j = tj; d.hold = 2 + R() * 3; d.to = droneTarget(); continue; }
      d.i += di / dist * step; d.j += dj / dist * step;
    }
  }

  /* ---------- the art: drawn in code, in the city palette, by day and by night ---------- */
  const CAR_COLORS = ['#F4A3C3', '#7FD6CE', '#B7A5F0', '#FFE38A', '#9CC7F3', '#FFFFFF', '#F29A74'];
  const HAIR = ['#2B2542', '#6E5446', '#FFE38A', '#9C7C6B'], SKIN = ['#FFB797', '#9C7C6B', '#F4D2B8'];
  const SHIRTS = ['#F4A3C3', '#7FD6CE', '#B7A5F0', '#FFE38A', '#9CC7F3', '#F29A74', '#FFFFFF', '#D9799F', '#74C997'];
  const PANTS = ['#2B2542', '#7A7394', '#8E7BD0', '#3FA79E'];
  const CAPS = ['#B7A5F0', '#F29A74', '#FFE38A', '#7FD6CE', '#FFFFFF'], DOGS = ['#9C7C6B', '#FFFFFF', '#2B2542', '#FFE38A'];
  const BIKES = ['#8E7BD0', '#F29A74', '#3FA79E', '#D9799F'];
  const PACK = '#F29A74', TOTE = '#FFE38A', GLOW = '#3FE0F0', WHEEL = '#2B2542';
  const night = hex => mix(hex, '#141024', 0.58);
  const tone = hex => Light.mixHex(hex, night(hex));
  const shade = (hex, k) => mix(hex, '#2B2542', k), lite = (hex, k) => mix(hex, '#FFFFFF', k);
  let artKey = '', art = null;
  function inPoly(x, y, pts) { let c = false; for (let a = 0, b = pts.length - 1; a < pts.length; b = a++) { const [xa, ya] = pts[a], [xb, yb] = pts[b]; if ((ya > y) !== (yb > y) && x < (xb - xa) * (y - ya) / (yb - ya) + xa) c = !c; } return c; }
  function rasterBox(g, P, i0, i1, j0, j1, z0, z1, cols) {
    const faces = [[[P(i0, j1, z0), P(i1, j1, z0), P(i1, j1, z1), P(i0, j1, z1)], cols.left], [[P(i1, j0, z0), P(i1, j1, z0), P(i1, j1, z1), P(i1, j0, z1)], cols.right],
      [[P(i0, j0, z1), P(i1, j0, z1), P(i1, j1, z1), P(i0, j1, z1)], cols.top]];
    for (const [pts, col] of faces) {
      const xs = pts.map(p => p[0]), ys = pts.map(p => p[1]);
      g.fillStyle = col;
      for (let y = Math.floor(Math.min(...ys)); y <= Math.ceil(Math.max(...ys)); y++) for (let x = Math.floor(Math.min(...xs)); x <= Math.ceil(Math.max(...xs)); x++) if (inPoly(x + 0.5, y + 0.5, pts)) g.fillRect(x, y, 1, 1);
    }
  }
  /* A 1 px outline round whatever is on the canvas. */
  function outline(c, col) {
    const g = c.getContext('2d'), w = c.width, h = c.height, src = g.getImageData(0, 0, w, h), d = src.data, out = g.createImageData(w, h);
    const [r, gg, b] = hexToRgb(col);
    for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) {
      const k = (y * w + x) * 4;
      if (d[k + 3]) { out.data.set(d.subarray(k, k + 4), k); continue; }
      const nb = [[1, 0], [-1, 0], [0, 1], [0, -1]].some(([dx, dy]) => { const X = x + dx, Y = y + dy; return X >= 0 && Y >= 0 && X < w && Y < h && d[(Y * w + X) * 4 + 3]; });
      if (nb) { out.data[k] = r; out.data[k + 1] = gg; out.data[k + 2] = b; out.data[k + 3] = 255; }
    }
    g.putImageData(out, 0, 0);
    return c;
  }
  function vehicle(type, color, h) {
    const along = h[0] === 'i', plus = h[1] === '+';
    const [c, g] = mkCanvas(30, 26), ox = 15, oy = 17, HW = WORLD.TW / 2, HH = WORLD.TH / 2;
    const P = (i, j, z) => [ox + (i - j) * HW, oy + (i + j) * HH - z];
    const box = (l0, l1, w0, w1, z0, z1, cols) => along ? rasterBox(g, P, l0, l1, w0, w1, z0, z1, cols) : rasterBox(g, P, w0, w1, l0, l1, z0, z1, cols);
    const body = tone(color), cols = { left: body, right: tone(shade(color, 0.22)), top: tone(lite(color, 0.28)) };
    const glass = { left: tone('#9CC7F3'), right: tone('#6FA5DE'), top: tone(lite(color, 0.4)) };
    if (type === 'bus') {
      const L = 0.55, W = 0.17;
      box(-L, L, -W, W, 1, 9, cols);
      box(-L + 0.06, L - 0.06, -W - 0.001, W + 0.001, 5, 7, { left: glass.left, right: glass.right, top: cols.top });
      box(-L, L, -W, W, 9, 9.5, { left: tone('#FFFFFF'), right: tone('#E1DAE9'), top: tone('#FFFFFF') });
    } else {
      const L = 0.28, W = 0.15, cab = plus ? [-0.2, 0.07] : [-0.07, 0.2];
      box(-L, L, -W, W, 1, 4, cols);
      box(cab[0], cab[1], -0.12, 0.12, 4, 7, glass);
    }
    g.fillStyle = tone('#2B2542');                                // wheels
    for (const t of type === 'bus' ? [-0.4, 0.4] : [-0.17, 0.17]) { const [x, y] = along ? P(t, 0.17, 0) : P(0.17, t, 0); g.fillRect(Math.round(x), Math.round(y) - 1, 1, 1); }
    return { c: outline(c, tone('#5A5073')), ox, oy };
  }
  /* People are 5 px wide and 6 tall (kids 5), drawn facing right; walking left mirrors them. Walking toward you the face
     shows under the hair; walking away the head is all hair. A look adds at most one item. */
  const BODY = {
    0: ['..H..', '..k..', '.sss.', '.sss.', '..p..', '..p..'],
    1: ['..H..', '..k..', '.sss.', '.sss.', '.p.p.', '.p.p.'],
    sit: ['..H..', '..k..', '.sss.', '.sss.', '.pp..'],
    talkL: ['..H..', '..k..', 'ksss.', '.sss.', '..p..', '..p..'],
    talkR: ['..H..', '..k..', '.sssk', '.sss.', '..p..', '..p..'],
    run0: ['..H..', '..k..', '.sssk', 'ksss.', '.p..p', 'p....'],
    run1: ['..H..', '..k..', 'ksss.', '.sssk', 'p..p.', '....p'],
    kid0: ['..H..', '..k..', '.sss.', '..p..', '..p..'],
    kid1: ['..H..', '..k..', '.sss.', '.p.p.', '.p.p.'],
  };
  const DOG = [['...g', 'gggg', 'g..g'], ['...g', 'gggg', '.gg.']];
  const BIKE = [['..H....', '..k....', '.sssb..', '.ss.b..', '..pbb..', 'ww.b.ww', 'ww...ww'],
                ['..H....', '..k....', '.sssb..', '.ss.b..', '..bbp..', 'ww.b.ww', 'ww...ww']];
  function personRows(look, frame, back) {
    const r = BODY[frame].map(row => row.split('')), kid = String(frame).startsWith('kid'), sit = frame === 'sit';
    const set = (y, x, ch) => { if (r[y]) r[y][x] = ch; };
    if (back) set(1, 2, 'H');
    if (look.long && !kid) {
      set(1, 1, 'H'); set(1, 3, 'H');
      if (back) for (const x of [1, 2, 3]) set(2, x, 'H');                   // falling down the back
    }
    if (look.dress && !kid && !String(frame).startsWith('run')) {
      if (sit) { r[3] = 'sssss'.split(''); r[4] = r[4].map(ch => ch === 'p' ? 'k' : ch); }
      else { r[4] = 'sssss'.split(''); r[5] = r[5].map(ch => ch === 'p' ? 'k' : ch); }
    }
    if (look.item === 'pack') {
      if (back) { set(2, 1, 'f'); set(2, 2, 'c'); set(3, 1, 'c'); set(3, 2, 'c'); }      // its screen glows at night
      else { set(2, 0, 'c'); set(3, 0, 'c'); }
    }
    if (look.item === 'tote') { set(3, 4, 't'); set(4, 4, 't'); }
    if (look.item === 'cap') { set(0, 2, 'C'); set(0, 3, 'C'); }                            // the brim points the way they walk
    if (look.item === 'phone') set(3, 4, 'f');
    return r.map(row => row.join(''));
  }
  function paint(rows, col, w, h, top) {
    const [c, g] = mkCanvas(w, h);
    rows.forEach((row, y) => [...row].forEach((ch, x) => { if (col[ch]) { g.fillStyle = col[ch]; g.fillRect(x, y + top, 1, 1); } }));
    return c;
  }
  const flipRows = rows => rows.map(row => [...row].reverse().join(''));
  function person(look, frame, back, flip) {
    const col = { H: tone(HAIR[look.hair]), k: tone(SKIN[look.skin]), s: tone(SHIRTS[look.shirt]), p: tone(PANTS[look.pants]),
      C: tone(CAPS[look.cap || 0]), c: tone(PACK), t: tone(TOTE), f: GLOW };                 // the glow keeps its color by night
    const rows = personRows(look, frame, back);
    return paint(flip ? flipRows(rows) : rows, col, 5, 8, frame === 'sit' ? 1 : 7 - rows.length);
  }
  function dog(color, frame, flip) {
    const rows = DOG[frame];
    return paint(flip ? flipRows(rows) : rows, { g: tone(DOGS[color]) }, 4, 3, 0);
  }
  function bike(look, frame, back, flip) {
    const rows = BIKE[frame].map((row, y) => back && y === 1 ? '..H....' : row);
    const col = { H: tone(HAIR[look.hair]), k: tone(SKIN[look.skin]), s: tone(SHIRTS[look.shirt]), p: tone(PANTS[look.pants]),
      b: tone(BIKES[look.frame]), w: tone(WHEEL) };
    return paint(flip ? flipRows(rows) : rows, col, 7, 8, 1);
  }
  function drone(frame) {
    const [c, g] = mkCanvas(9, 8);
    const col = { '#': tone('#7A7394'), '+': tone('#D6CEE2'), r: tone('#FFFFFF'), l: '#EE4C93', w: tone('#9C7C6B') };
    const rows = [frame ? 'r.....r' : '.r...r.', '.#####.', '#+++++#', '.##l##.', '...w...', '..www..'];
    rows.forEach((row, y) => [...row].forEach((ch, x) => { if (col[ch]) { g.fillStyle = col[ch]; g.fillRect(x + 1, y + 1, 1, 1); } }));
    return c;
  }
  function artSet() {
    const k = Math.round(Light.t * 20) + '';
    if (k === artKey && art) return art;
    artKey = k;
    const veh = {};
    for (const h of Object.keys(HEADS)) {
      veh['bus' + h] = vehicle('bus', '#FFE38A', h);
      CAR_COLORS.forEach((col, n) => { veh['car' + n + h] = vehicle('car', col, h); });
    }
    art = { veh, people: new Map(), drones: [drone(0), drone(1)] };
    return art;
  }
  const cached = (key, make) => { const A = artSet(); if (!A.people.has(key)) A.people.set(key, make()); return A.people.get(key); };
  const lookKey = l => [l.hair, l.skin, l.shirt, l.pants, +l.long, +l.dress, l.item || '', l.cap || 0, l.frame || 0].join('.');
  const personArt = (look, frame, back, flip) => cached('p' + lookKey(look) + '.' + frame + '.' + (+back) + (+flip), () => person(look, frame, back, flip));
  const dogArt = (color, frame, flip) => cached('d' + color + '.' + frame + '.' + (+flip), () => dog(color, frame, flip));
  const bikeArt = (look, frame, back, flip) => cached('b' + lookKey(look) + '.' + frame + '.' + (+back) + (+flip), () => bike(look, frame, back, flip));
  /* Which way someone moves, in tiles: round the loop, or along a path. Toward you is +i or +j; to the right is +i or -j. */
  const LOOP = [[1, 0], [0, 1], [-1, 0], [0, -1]];
  function heading(q) {
    if (q.path && (q.mode === 'path' || q.mode === 'fade')) {
      const [a, b] = q.path, di = b[0] - a[0], dj = b[1] - a[1], n = Math.hypot(di, dj);
      if (n > 1e-6) return [di / n, dj / n];
    }
    const [a, b] = LOOP[sideOf(q.p)];
    return [a * q.dir, b * q.dir];
  }
  const facing = hd => ({ back: !!hd && hd[0] + hd[1] < 0, flip: !!hd && hd[0] - hd[1] < 0 });

  /* ---------- the map asks for these ---------- */
  function items() {
    const out = [], A = artSet(), toW = MapView.tileToWorld;
    const dark = Light.t;                                          // 0 by day, 1 at night
    for (const c of cars) {
      const [i, j] = carPos(c), [x, y] = toW(i, j), a = A.veh[(c.type === 'bus' ? 'bus' : 'car' + c.color) + c.h];
      const [ha, hb] = HEADS[c.h], half = c.len / 2, toward = ha > 0 || hb > 0;
      out.push({ i, j, key: i + j, box: { x0: x - 26, x1: x + 26, y0: y - 17, y1: y + 18 }, draw: g => {
        if (dark > 0.3) {                                          // the beam on the road ahead
          const [rx, ry] = [-hb, ha], k = Math.min(1, (dark - 0.3) / 0.4);
          const p0 = toW(i + ha * half, j + hb * half), pl = toW(i + ha * (half + 0.9) + rx * 0.28, j + hb * (half + 0.9) + ry * 0.28), pr = toW(i + ha * (half + 0.9) - rx * 0.28, j + hb * (half + 0.9) - ry * 0.28);
          g.fillStyle = `rgba(255, 236, 170, ${0.28 * k})`;
          g.beginPath(); g.moveTo(p0[0], p0[1]); g.lineTo(pl[0], pl[1]); g.lineTo(pr[0], pr[1]); g.closePath(); g.fill();
        }
        g.drawImage(a.c, Math.round(x) - a.ox, Math.round(y) - a.oy);
        if (dark > 0.3) {
          const [rx, ry] = [-hb, ha], w = c.type === 'bus' ? 0.1 : 0.08;
          const end = toward ? half : -half, col = toward ? '#FFF2B8' : '#EE4C93';
          g.fillStyle = col;
          for (const sgn of (toward ? [1, -1] : [1, -1])) {
            const [lx, ly] = toW(i + ha * end + rx * w * sgn, j + hb * end + ry * w * sgn);
            g.fillRect(Math.round(lx), Math.round(ly) - 2, 1, 1);
          }
        }
      } });
    }
    const shadow = (g, x, y, w) => { g.fillStyle = 'rgba(43, 37, 66, 0.28)'; g.fillRect(Math.round(x) - (w >> 1), Math.round(y), w, 1); };
    for (const q of people) {
      const at = here(q);
      if (!at) continue;
      const moving = q.mode === 'walk' || q.mode === 'path', n = Math.floor(q.walked / 0.16) % 2;
      const [bi, bj] = at, frame = q.mode === 'sit' ? 'sit' : moving ? (q.run ? 'run' + n : n) : q.talk === 1 ? 'talkL' : q.talk === 2 ? 'talkR' : 0;
      const hd = q.mode === 'sit' ? null : heading(q), { back, flip } = facing(hd);
      const [i, j] = q.mode === 'sit' ? [bi, bj] : [bi + q.lat, bj - q.lat];
      const [x, y] = toW(i, j), img = personArt(q.look, frame, back, flip), lift = q.mode === 'sit' ? 3 : 0;
      const alpha = () => Math.max(0, Math.min(1, q.alpha));
      out.push({ i, j, key: i + j, box: { x0: x - 3, x1: x + 3, y0: y - 9, y1: y + 2 }, draw: g => {
        g.globalAlpha = alpha();
        if (q.mode !== 'sit') shadow(g, x, y, 3);
        g.drawImage(img, Math.round(x) - 2, Math.round(y) - 7 - lift);
        g.globalAlpha = 1;
      } });
      if (q.buddy && hd) {                                         // a kid or a dog, a step to the walker's right
        const bi2 = i - hd[1] * 0.12, bj2 = j + hd[0] * 0.12, [x2, y2] = toW(bi2, bj2);
        const kid = q.buddy.kind === 'kid';
        const bimg = kid ? personArt(q.buddy.look, moving ? 'kid' + n : 'kid0', back, flip) : dogArt(q.buddy.color, moving ? n : 0, flip);
        out.push({ i: bi2, j: bj2, key: bi2 + bj2, box: { x0: x2 - 3, x1: x2 + 3, y0: y2 - 8, y1: y2 + 2 }, draw: g => {
          g.globalAlpha = alpha();
          shadow(g, x2, y2, kid ? 3 : 4);
          g.drawImage(bimg, Math.round(x2) - 2, Math.round(y2) - (kid ? 7 : 3));
          g.globalAlpha = 1;
        } });
      }
    }
    for (const q of riders) {
      const at = here(q);
      if (!at) continue;
      const [i, j] = at, [x, y] = toW(i, j), { back, flip } = facing(heading(q));
      const img = bikeArt(q.look, Math.floor(q.walked / 0.25) % 2, back, flip);
      out.push({ i, j, key: i + j, box: { x0: x - 4, x1: x + 4, y0: y - 9, y1: y + 2 }, draw: g => {
        shadow(g, x, y, 5);
        g.drawImage(img, Math.round(x) - 3, Math.round(y) - 7);
      } });
    }
    return out;
  }
  function drawGround(g) {                                      // drone shadows, under everything else
    const toW = MapView.tileToWorld;
    g.fillStyle = 'rgba(43, 37, 66, 0.22)';
    for (const d of drones) { const [x, y] = toW(d.i, d.j); g.fillRect(Math.round(x) - 2, Math.round(y), 5, 1); g.fillRect(Math.round(x) - 1, Math.round(y) + 1, 3, 1); }
  }
  function drawAir(g) {                                         // drones, over everything
    const A = artSet(), toW = MapView.tileToWorld;
    for (const d of drones) {
      const [x, y] = toW(d.i, d.j), bob = d.hold > 0 ? Math.round(Math.sin(d.spin * 1.7)) : 0;
      g.drawImage(A.drones[Math.floor(d.spin * 8) % 2], Math.round(x) - 4, Math.round(y) - d.alt - 4 + bob);
    }
  }
  function reset() {
    N = WORLD.N; crossCache.clear(); busy.clear(); seats.clear();
    refreshWeights();
    const total = Math.round(16 * N * N / 25), nDrones = Math.max(1, Math.round(12 * N * N / 25 / 6)), nBus = Math.max(1, Math.round(2 * N * N / 25));
    cars = [];
    for (let k = 0; k < total - nDrones - nBus; k++) { const c = spawnCar('car'); if (c) cars.push(c); }
    for (let k = 0; k < nBus; k++) { const c = spawnCar('bus'); if (c) cars.push(c); }
    drones = Array.from({ length: nDrones }, () => { const [i, j] = droneTarget(); return { i, j, to: droneTarget(), alt: 64 + Math.round(R() * 16), sp: 0.7 + R() * 0.3, hold: 0, spin: R() * 5 }; });
    people = [];
    while (people.length < baseCount()) people.push(spawnPerson());
    for (const [k, n] of extraTargets()) {                         // the crowds round busy buildings, already out
      const [u, v] = k.split(',').map(Number);
      for (let m = 0; m < n; m++) { const q = newPerson(u, v, R() * PER()); q.home = k; people.push(q); }
    }
    riders = [];
    while (riders.length < riderCount()) { const [u, v] = blockPick(); riders.push(newRider(u, v, R() * PER())); }
    ready = true;
  }
  function step(t) {
    if (!ready || N !== WORLD.N) reset();
    const dt = last ? Math.min(0.1, (t - last) / 1000) : 0;
    last = t;
    if (t - lastW > 5000) { refreshWeights(); lastW = t; }
    updateCars(dt, t); updatePeople(dt, t); updateRiders(dt, t); updateDrones(dt);
    if (t - lastDraw >= 50) { lastDraw = t; return true; }
    return false;
  }
  return {
    active: () => on, isOn: () => on, step, items, drawGround, drawAir, reset,
    setOn: v => { on = !!v; try { localStorage.setItem(KEY, on ? '1' : '0'); } catch (e) { /* this visit only */ } last = 0; },
    stats: () => ({ cars: cars.filter(c => c.type === 'car').length, buses: cars.filter(c => c.type === 'bus').length, drones: drones.length, people: people.length, extras: people.filter(q => q.home).length, bikes: riders.length }),
    busyness: p => busyness(p),
    crowd: () => crowd,
    setCrowd: v => { if (!(v in CROWD_PER)) return; crowd = v; try { localStorage.setItem(CROWD_KEY, v); } catch (e) { /* this visit only */ } lastBalance = 0; },
    _state: () => ({ cars, people, riders, drones, busy }),
    /* for the tests: a look, and the sprite rows and canvases the map draws */
    _look: () => newLook(), _rows: (look, frame, back) => personRows(look, frame, back),
    _sprite: (look, frame, back, flip) => personArt(look, frame, back, flip),
  };
})();
