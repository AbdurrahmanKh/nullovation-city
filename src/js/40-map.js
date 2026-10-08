const MapView = (() => {
  const { S, MARGIN, TW, TH, PITCH } = WORLD;
  const HW = TW / 2, HH = TH / 2;
  const SLAB = 14;
  let NU = 0, NV = 0, OU = 0, OV = 0, TI = 0, TJ = 0, WX0 = 0, WX1 = 0, WY0 = 0, WY1 = 0;   // set by applyWorld() from WORLD

  let canvas, ctx, wrap;
  let dpr = 1, vw = 1, vh = 1;               // canvas size in device pixels
  const cam = { x: 0, y: 220, z: 2 };         // z: device pixels per art pixel; whole numbers are crisp
  let worldCanvas = null, layers = null, barePlot = null, rings = null;
  const animIdx = new Map();   // last drawn frame per animated block
  Light.onChange(() => {
    if (!layers) return;
    bcache.clear(); flat.clear();
    layers = renderPlotLayers(); barePlot = renderBarePlot(); worldCanvas = buildWorld();
    invalidate();
  });
  const bcache = new Map();
  let ghost = null;            // the project being aimed while planting
  let planting = null;         // { id, t0, dur, then }: a freshly planted block solidifying
  let dirty = true, raf = 0, lastT = 0, clean = false;
  const anim = { glide: null, zoom: null };
  const keys = new Set();
  let hoverId = null;
  let mode = { name: 'idle' };               // idle | place {pendingName, pendingId, target} | move {id, target, gx, gy}
  let gesture = null;
  const pointers = new Map();
  let settleTimer = null, lastAnchor = null;

  /* ---------- geometry ---------- */
  const tileToWorld = (i, j) => [(i - j) * HW, (i + j) * HH];
  const worldToTile = (x, y) => [(y / HH + x / HW) / 2, (y / HH - x / HW) / 2];
  const plotTop = (u, v) => tileToWorld(MARGIN + u * PITCH, MARGIN + v * PITCH);
  const zMin = () => 1;
  const zMax = () => Math.max(4, Math.round(8 * dpr));
  function xf() { const z = cam.z; return { z, tx: Math.round(vw / 2 - cam.x * z), ty: Math.round(vh / 2 - cam.y * z) }; }
  function worldToCss(x, y) { const { z, tx, ty } = xf(); return [(x * z + tx) / dpr, (y * z + ty) / dpr]; }
  function cssToWorld(cx, cy) { const { z, tx, ty } = xf(); return [(cx * dpr - tx) / z, (cy * dpr - ty) / z]; }
  function clampCam() { cam.x = clamp(cam.x, WX0, WX1); cam.y = clamp(cam.y, WY0, WY1); }

  /* ---------- the streets' fixed choices, shared by the ground and the traffic on it ---------- */
  const seed = (...k) => mulberry32(k.reduce((h, v) => (Math.imul(h ^ (v + 0x9e37), 0x85ebca6b) + 0x27d4eb2f) >>> 0, 17));
  const pick = (r, weights) => { let x = r() * weights.reduce((s, w) => s + w[1], 0); for (const [v, w] of weights) { if ((x -= w) < 0) return v; } return weights[0][0]; };
  /* At each end of a street segment: a zebra crossing, a stop line, or nothing. A segment along i runs beside lot li
     on the u axis, across road ri on the v axis; along j the other way round. Dealt by the city's plot, so a mark
     stays where it is when the map grows. */
  const crossMark = (li, ri, along, e) => pick(seed(li + (along ? OU : OV), ri + (along ? OV : OU), along ? 1 : 2, e, 7), [['zebra', 55], ['stop', 30], ['none', 15]]);

  /* ---------- street props: fixed per block side, like the street details ---------- */
  /* A block's four sides, each measured from its own corner going round clockwise: the north-east side from the top
     corner, the south-east from the right, the south-west from the bottom, the north-west from the left. A prop faces
     its street: its front shows on the south-east and south-west sides, its back on the north-east and north-west.
     Its foot stands on the sidewalk; on the front sides it stands near the curb, so it reaches back over the plot's rim,
     and on the back sides near the plot, so it stays out of the street. */
  const PROP_SIDES = [
    { name: 'ne', back: true, off: 0.06, at: (a0, b0, a1, b1, a, o) => [a0 + a, b0 - o] },
    { name: 'se', back: false, off: 0.22, at: (a0, b0, a1, b1, a, o) => [a1 + o, b0 + a] },
    { name: 'sw', back: false, off: 0.22, at: (a0, b0, a1, b1, a, o) => [a1 - a, b1 + o] },
    { name: 'nw', back: true, off: 0.06, at: (a0, b0, a1, b1, a, o) => [a0 - o, b1 - a] },
  ];
  /* Which street a view faces as drawn: a front the one named in props.json (PROPS' faces), south-east or south-west;
     its back the opposite one, the same diagonal turned around. Mirrored, a view turns to the other street on the same
     side of the camera (south-east and south-west, or north-east and north-west), so each view serves two sides and is
     mirrored on the one it does not face. */
  const TURNED = { se: 'nw', sw: 'ne', ne: 'sw', nw: 'se' };
  function propFaces(kind, back) {
    const pr = typeof PROPS === 'undefined' ? null : PROPS.find(p => p.id === kind);
    const front = pr ? pr.faces : 'sw';
    return back ? TURNED[front] : front;
  }
  let propCache = { key: '', list: [] };
  const mod = (x, m) => ((x % m) + m) % m;
  /* Bus stops follow a fixed pattern; a vending machine stands mid-block; a holo billboard by the corner, just past
     where a zebra lands; a bin on a building's two front sides, where people walk in. At most two to a side, kept
     apart. Every draw is taken whatever the block holds, so planting a building only adds or takes away its bins.
     Each side is dealt by the city's plot, so the props stay with their blocks when the map grows.
     The amount scales how many: each prop has its own draw, so a higher amount only adds props and a lower one only
     takes some away, and none moves. Bus stops keep the pattern up to today's amount, and above it some stand off the
     pattern too. Deal again lays them out anew by the same rules. A kind turned off is only taken away. */
  function propPlan() {
    const c = DB.city, built = new Set(DB.projects.map(p => p.plot.u + ',' + p.plot.v));
    const key = [NU, NV, OU, OV, c.props, c.busstop, c.vending, c.billboard, c.bin, c.amount, c.deal].join(':') + ':' + [...built].sort().join(';');
    if (propCache.key === key) return propCache.list;
    const list = [], amt = c.amount, deal = c.deal;
    const pat = deal ? (r => [1 + Math.floor(r() * 4), 1 + Math.floor(r() * 4), 1 + Math.floor(r() * 4), Math.floor(r() * 5)])(mulberry32(deal * 7919 + 13)) : [3, 5, 7, 0];
    if (c.props) for (let u = 0; u < NU; u++) for (let v = 0; v < NV; v++) {
      const U = u + OU, V = v + OV;
      const a0 = MARGIN + u * PITCH, b0 = MARGIN + v * PITCH, a1 = a0 + S, b1 = b0 + S;
      PROP_SIDES.forEach((sd, k) => {
        const r = deal ? seed(U, V, k, 61, deal) : seed(U, V, k, 61), d = Array.from({ length: 6 }, () => r());
        const e = (deal ? seed(U, V, k, 62, deal) : seed(U, V, k, 62))();
        const want = [];
        if (mod(U * pat[0] + V * pat[1] + k * pat[2] + pat[3], 5) === 0 ? e < Math.min(1, amt) : e < (amt - 1) * 0.25) want.push(['busstop', 1.2 + d[0] * 1.6]);
        if (built.has(u + ',' + v) && !sd.back && d[1] < 0.6 * amt) want.push(['bin', 0.9 + d[2] * 2.2]);
        if (d[3] < 0.2 * amt) want.push(['vending', 1.5 + d[4]]);
        if (d[5] < 0.15 * amt) want.push(['billboard', 0.62]);
        const placed = [];
        for (const [kind, a] of want) {
          if (placed.length >= 2) break;
          if (placed.some(o => Math.abs(o.a - a) < (kind === 'busstop' || o.kind === 'busstop' ? 1.1 : 0.8))) continue;
          placed.push({ kind, a });
        }
        for (const { kind, a } of placed) {
          if (!c[kind]) continue;
          const [i, j] = sd.at(a0, b0, a1, b1, a, sd.off);
          list.push({ kind, u, v, side: sd.name, a, i, j, back: sd.back, mirror: propFaces(kind, sd.back) !== sd.name });
        }
      });
    }
    propCache = { key, list };
    return list;
  }

  /* ---------- static art ---------- */
  /* The ground: a street grid. Every lot is a block wrapped in sidewalks, the gaps between lots
     are two-lane streets, a ring road runs round the city, and empty lots are grass. Every detail is dealt by the
     city's plot or tile, never by its place on the grid, so it stays put when a line or a ring is added. */
  function buildWorld() {
    const w = WX1 - WX0, hgt = WY1 - WY0 + 2;
    const [c, g] = mkCanvas(w, hgt);
    const ox = -WX0;
    const pt = (i, j) => { const [x, y] = tileToWorld(i, j); return [ox + x, y]; };
    const Q = (i0, j0, i1, j1, col) => fillPoly(g, [pt(i0, j0), pt(i1, j0), pt(i1, j1), pt(i0, j1)], col);
    const left = [0, TJ * HH], bottom = [ox + (TI - TJ) * HW, (TI + TJ) * HH], right = [w, TI * HH];
    fillPoly(g, [left, bottom, [bottom[0], bottom[1] + SLAB], [left[0], left[1] + SLAB]], worldColor('slabL'));
    fillPoly(g, [bottom, right, [right[0], right[1] + SLAB], [bottom[0], bottom[1] + SLAB]], worldColor('slabR'));
    g.fillStyle = worldColor('strata');
    const stepsL = (TI * HW) / 2, stepsR = (TJ * HW) / 2;
    for (let k = 0; k < stepsL; k++) g.fillRect(2 * k, left[1] + 6 + k, 2, 1);
    for (let k = 0; k < stepsR; k++) g.fillRect(bottom[0] + 2 * k, bottom[1] + 5 - k, 2, 1);

    /* lots and roads along each axis: i runs over u, j over v */
    const axis = (n, span) => {
      const lots = [], roads = [[0, MARGIN]];
      for (let k = 0; k < n; k++) {
        const l0 = MARGIN + k * PITCH;
        lots.push([l0, l0 + S]);
        roads.push(k < n - 1 ? [l0 + S, l0 + PITCH] : [l0 + S, span]);
      }
      return { lots, roads };
    };
    const I = axis(NU, TI), J = axis(NV, TJ);
    const SW = 0.3, PX = 1 / 16;               // sidewalk width, and one pixel in tile units
    const C = k => worldColor(k);
    Q(0, 0, TI, TJ, C('road'));                           // asphalt everywhere, then everything on top of it
    const px = (i, j, col) => { const [x, y] = pt(i, j); g.fillStyle = col; g.fillRect(Math.round(x), Math.round(y), 1, 1); };
    const ellipse = (ci, cj, r, col, n = 20) => fillPoly(g, Array.from({ length: n }, (_, k) => pt(ci + r * Math.cos(k / n * 2 * Math.PI), cj + r * Math.sin(k / n * 2 * Math.PI))), col);
    for (let i = 0; i < TI; i++) for (let j = 0; j < TJ; j++) {        // a faint grain, dealt by the city's tile
      const r = seed(i + OU * PITCH, j + OV * PITCH, 5);
      for (let n = 0; n < 9; n++) px(i + r(), j + r(), r() < 0.6 ? C('roadDk') : C('roadLt'));
    }
    for (const along of [true, false]) {        // a street segment: along i (j across the road) or along j
      const lotsA = along ? I.lots : J.lots, roadsA = along ? J.roads : I.roads;
      const oL = along ? OU : OV, oR = along ? OV : OU;
      for (let li = 0; li < lotsA.length; li++) {
        const [l0, l1] = lotsA[li];
        for (let ri = 0; ri < roadsA.length; ri++) {
          const [r0, r1] = roadsA[ri];
          const outer = ri === 0 || ri === roadsA.length - 1;
          const q = (a0, a1, c0, c1, col) => along ? Q(a0, c0, a1, c1, col) : Q(c0, a0, c1, a1, col);
          const P = (a, c) => along ? [a, c] : [c, a];
          const r = seed(li + oL, ri + oR, along ? 1 : 2);
          const in0 = r0 + SW, in1 = r1 - SW, mid = (r0 + r1) / 2;
          /* wear: a repaired patch, a crack, a manhole, a drain at the curb */
          if (r() < 0.4) {
            const len = 0.35 + r() * 0.5, w = 0.14 + r() * 0.16, a = l0 + 0.5 + r() * (l1 - l0 - 1 - len), c = in0 + 0.04 + r() * (in1 - in0 - w - 0.08);
            q(a, a + len, c, c + w, C('patchEdge')); q(a + PX, a + len - PX, c + PX, c + w - PX, C('patch'));
          }
          if (r() < 0.35) {
            let [ci, cj] = P(l0 + 0.6 + r() * (l1 - l0 - 1.2), in0 + 0.1 + r() * (in1 - in0 - 0.2));
            const [x0, y0] = pt(ci, cj); let x = Math.round(x0), y = Math.round(y0);
            g.fillStyle = C('crack');
            for (let k = 0; k < 7 + r() * 8; k++) { g.fillRect(x, y, 1, 1); x += r() < 0.5 ? 1 : -1; y += r() < 0.35 ? 1 : 0; }
          }
          if (r() < 0.3) {
            const [ci, cj] = P(l0 + 0.7 + r() * (l1 - l0 - 1.4), r() < 0.5 ? (in0 + mid) / 2 : (mid + in1) / 2);
            ellipse(ci, cj, 0.11, C('manhole')); ellipse(ci, cj, 0.075, C('manholeHi')); ellipse(ci, cj, 0.05, C('manhole'));
          }
          if (r() < 0.45) {
            const a = l0 + 0.5 + r() * (l1 - l0 - 1), side = r() < 0.5;
            const c0 = side ? in0 : in1 - 0.07;
            q(a, a + 0.16, c0, c0 + 0.07, C('drain'));
            for (let k = 1; k < 4; k++) q(a + k * 0.04, a + k * 0.04 + PX, c0 + PX, c0 + 0.07 - PX, C('roadLt'));
          }
          /* markings: each street its own; the ring road is always the avenue with a double line. The ring road deals
             its own marking too, unused, so a street that stops or starts being the ring keeps its sidewalks. */
          const own = pick(r, [['dash', 45], ['double', 18], ['none', 17], ['arrows', 20]]);
          const dashes = own === 'dash' || own === 'arrows' ? (() => { const step = 0.55 + r() * 0.35; return { step, len: step * (0.4 + r() * 0.2), phase: r() * step }; })() : null;
          const kind = outer ? 'double' : own;
          if (kind === 'dash' || kind === 'arrows') {
            const { step, len, phase } = dashes;
            for (let k = l0 + 0.62 + phase; k < l1 - 0.62; k += step) q(k, Math.min(k + len, l1 - 0.62), mid - PX / 2, mid + PX / 2, C('dash'));
          } else if (kind === 'double') {
            q(l0 + 0.5, l1 - 0.5, mid - PX * 1.5, mid - PX / 2, C('dash'));
            q(l0 + 0.5, l1 - 0.5, mid + PX / 2, mid + PX * 1.5, C('dash'));
          }
          if (kind === 'arrows') {                                  // turn arrows in each lane, pointing at the next crossing
            for (const [end, dir] of [[l0 + 0.62, -1], [l1 - 0.62, 1]]) {
              const lane = dir > 0 ? (mid + in1) / 2 : (in0 + mid) / 2;
              const tip = end, back = end - dir * 0.34;
              fillPoly(g, [pt(...P(tip, lane)), pt(...P(tip - dir * 0.12, lane - 0.09)), pt(...P(tip - dir * 0.12, lane + 0.09))], C('paint'));
              q(Math.min(back, tip - dir * 0.12), Math.max(back, tip - dir * 0.12), lane - PX, lane + PX, C('paint'));
            }
          }
          /* sidewalks: each side its own paving, and some with a grass verge */
          for (const [s0, s1, roadSide] of [[r0, r0 + SW, r0 + SW], [r1 - SW, r1, r1 - SW]]) {
            q(l0, l1, s0, s1, C('walk'));
            const pave = pick(r, [['tiles', 45], ['brick', 30], ['plain', 25]]);
            if (pave === 'tiles') for (let k = l0 + 0.5; k < l1; k += 0.5) q(k, k + PX, s0, s1, C('joint'));
            else if (pave === 'plain') for (let k = l0 + 1; k < l1; k += 1) q(k, k + PX, s0, s1, C('joint'));
            else {
              const m1 = (s0 + s1) / 2;
              q(l0, l1, m1 - PX / 2, m1 + PX / 2, C('joint'));
              for (let k = l0 + 0.25; k < l1; k += 0.25) { q(k, k + PX, s0, m1, C('joint')); q(k + 0.125, k + 0.125 + PX, m1, s1, C('joint')); }
            }
            if (r() < 0.28) {                                      // a grass verge along the curb, with a few shrubs
              const v0 = roadSide === s1 ? s1 - 0.11 : s0, v1 = v0 + 0.11;
              q(l0 + 0.4, l1 - 0.4, v0, v1, C('verge'));
              for (let k = l0 + 0.5 + r() * 0.3; k < l1 - 0.5; k += 0.35 + r() * 0.4) px(...P(k, (v0 + v1) / 2), C('vergeDk'));
            }
            q(l0, l1, roadSide === s1 ? s1 - PX : s0, roadSide === s1 ? s1 : s0 + PX, C('curb'));   // the curb edge facing the road
          }
          /* each end: a crosswalk, a stop line, or nothing */
          for (const [end, e] of [[l0 + 0.06, 0], [l1 - 0.4, 1]]) {
            const how = crossMark(li, ri, along, e);
            if (how === 'zebra') for (let s0 = in0 + 0.1; s0 + 0.12 <= in1 - 0.05; s0 += 0.24) q(end, end + 0.34, s0, s0 + 0.12, C('stripe'));
            else if (how === 'stop') {                            // across the lane that drives toward this end, on the right
              const at = e ? end + 0.3 : end, far = along ? e : !e;
              q(at, at + 0.05, far ? mid : in0 + 0.05, far ? in1 - 0.05 : mid, C('paint'));
            }
          }
        }
      }
    }
    for (let ai = 0; ai < I.roads.length; ai++) for (let bi = 0; bi < J.roads.length; bi++) {   // crossings: corners, and each its own middle
      const [a0, a1] = I.roads[ai], [b0, b1] = J.roads[bi];
      for (const [i0, i1] of [[a0, a0 + SW], [a1 - SW, a1]]) for (const [j0, j1] of [[b0, b0 + SW], [b1 - SW, b1]]) Q(i0, j0, i1, j1, C('walk'));
      const ci = (a0 + a1) / 2, cj = (b0 + b1) / 2, rr = Math.min(a1 - a0, b1 - b0) / 2 - SW;
      const r = seed(ai + OU, bi + OV, 91);
      const ring = ai === 0 || ai === I.roads.length - 1 || bi === 0 || bi === J.roads.length - 1;
      const kind = ring ? pick(r, [['plain', 70], ['manhole', 30]]) : pick(r, [['plain', 50], ['manhole', 22], ['island', 12], ['box', 16]]);
      if (kind === 'manhole') { ellipse(ci + 0.15, cj - 0.1, 0.11, C('manhole')); ellipse(ci + 0.15, cj - 0.1, 0.075, C('manholeHi')); ellipse(ci + 0.15, cj - 0.1, 0.05, C('manhole')); }
      else if (kind === 'island') {                                // a small roundabout: a curb ring, grass, and a painted circle round it
        ellipse(ci, cj, rr * 0.72, C('paint'), 28); ellipse(ci, cj, rr * 0.72 - PX, C('road'), 28);
        ellipse(ci, cj, rr * 0.42, C('curb'), 24); ellipse(ci, cj, rr * 0.42 - PX, C('island'), 24);
        const rs = seed(ai + OU, bi + OV, 92);
        for (let n = 0; n < 6; n++) { const t = rs() * Math.PI * 2, d = rs() * rr * 0.28; px(ci + d * Math.cos(t), cj + d * Math.sin(t), C('vergeDk')); }
      } else if (kind === 'box') {                                 // a yellow box junction: keep clear
        const d = rr * 0.62, col = C('dash');
        Q(ci - d, cj - d, ci + d, cj - d + PX, col); Q(ci - d, cj + d - PX, ci + d, cj + d, col);
        Q(ci - d, cj - d, ci - d + PX, cj + d, col); Q(ci + d - PX, cj - d, ci + d, cj + d, col);
        for (let s = 0; s <= 1; s += PX / (4 * d)) { px(ci - d + 2 * d * s, cj - d + 2 * d * s, col); px(ci - d + 2 * d * s, cj + d - 2 * d * s, col); }
      }
    }
    I.lots.forEach(([a0, a1], u) => J.lots.forEach(([b0, b1], v) => {   // empty lots are grass until a building is planted
      const rnd = seed(u + OU, v + OV, 99);
      Q(a0, b0, a1, b1, Light.mixHex('#D4F2DE', '#1D302C'));
      for (let n = 0; n < 70; n++) {
        const [x, y] = pt(a0 + 0.1 + rnd() * (a1 - a0 - 0.2), b0 + 0.1 + rnd() * (b1 - b0 - 0.2));
        g.fillStyle = rnd() < 0.8 ? Light.mixHex('#A9E2BE', '#26423A') : Light.mixHex('#FFFFFF', '#2F5046');
        g.fillRect(Math.round(x), Math.round(y), 1, 1);
      }
    }));
    g.fillStyle = worldColor('rim');
    for (let k = 0; k < stepsL; k++) g.fillRect(2 * k, left[1] + k - 1, 2, 1);
    for (let k = 0; k < stepsR; k++) g.fillRect(bottom[0] + 2 * k, bottom[1] - k - 1, 2, 1);
    return c;
  }
  function buildRings() {
    return {
      sel: ringCanvas(70, 35, 2, PAL.ring),
      selHi: ringCanvas(72, 36, 1, PAL.ringHi),
      hover: ringCanvas(70, 35, 1, PAL.ringHi),
      free: fillCanvas(64, 32, 'rgba(183, 165, 240, 0.16)'),
      freeRing: ringCanvas(64, 32, 1, '#6B6388'),
      target: fillCanvas(64, 32, PAL.target),
      targetRing: ringCanvas(66, 33, 1, PAL.ring),
    };
  }
  function bld(p) {
    let b = bcache.get(p.id);
    if (!b) { b = renderBuilding(p.id); bcache.set(p.id, b); }
    return b;
  }

  /* Where every part of a block lands in world space. lift raises it while it is carried.
     Art either brings its own plot (bottom edge on the ground at the plot's front corner) or
     stands on the standard plot the tool draws (bottom edge on the plot surface's front corner).
     Both are fit to the plot width. */
  /* Uploaded art wins, then the chosen generic building, then the code-drawn placeholder.
     Generic buildings bring the city's standard plot with them. */
  function artFor(p) {
    const custom = p && p.art && p.art.has ? Art.get(p.id) : null;
    if (custom) return { art: custom, ownPlot: !!p.art.includesPlot };
    const gen = p && p.generic ? Art.get('g:' + p.generic) : null;
    return gen ? { art: gen, ownPlot: true } : { art: null, ownPlot: false };
  }
  function blockGeom(p, u, v, lift = 0) {
    const [X, Y] = plotTop(u, v);
    const { art, ownPlot } = artFor(p);
    const plotX = X - 64, plotY = Y - PLOT.RAISE - PLOT.T - lift;
    if (art) {
      const s = PLOT.W / art.w, dh = art.h * s;
      const bottom = (ownPlot ? Y + 64 : Y - PLOT.RAISE + 64) - lift;
      return { kind: ownPlot ? 'artWhole' : 'artOnPlot', X, Y, art, s, plotX, plotY, flip: !!(p && p.flip),
        dx: X - 64, dy: bottom - dh, dw: PLOT.W, dh, top: Math.min(bottom - dh, plotY + PLOT.T), base: Y + 64 - lift };
    }
    const b = bld(p);
    const fy = Y - PLOT.RAISE + 48 - lift;     // floor point of the placeholder's footprint
    const dy = fy - (b.CH - BLD.PAD);
    return { kind: 'placeholder', X, Y, b, plotX, plotY, flip: !!(p && p.flip), dx: X - 32 - BLD.PAD, dy, top: dy + BLD.PAD, base: Y + 64 - lift };
  }
  /* In-between scales above 1 (like 1.5 device pixels per art pixel at 3x) are drawn sharp: the art is first
     enlarged crisply to the next whole scale, then scaled down smoothly, so pixels stay square and even. */
  let sharpCanvas = null, sharpCtx = null;
  function drawArt(art, x, y, w, hgt, frame = null) {
    const eff = cam.z * (w / art.w);          // device pixels per source pixel
    const idx = frame == null ? Art.indexAt(art, performance.now()) : frame;
    const between = Math.abs(eff - Math.round(eff)) > 0.02;
    if (between && eff > 1) {
      const k = Math.ceil(eff), sw = art.w * k, sh = Math.ceil(art.h * k);
      if (!sharpCanvas) { sharpCanvas = document.createElement('canvas'); sharpCtx = sharpCanvas.getContext('2d'); }
      if (sharpCanvas.width < sw || sharpCanvas.height < sh) { sharpCanvas.width = Math.max(sharpCanvas.width, sw); sharpCanvas.height = Math.max(sharpCanvas.height, sh); }
      sharpCtx.clearRect(0, 0, sw, sh);
      sharpCtx.imageSmoothingEnabled = false;
      Art.draw(sharpCtx, art, idx, 0, 0, sw, sh);
      ctx.imageSmoothingEnabled = true; ctx.imageSmoothingQuality = 'medium';
      ctx.drawImage(sharpCanvas, 0, 0, sw, sh, x, y, w, hgt);
      ctx.imageSmoothingEnabled = false;
      return;
    }
    ctx.imageSmoothingEnabled = between || eff < 1;   // sharp at whole scales; smooth only when shrinking
    if (eff < 1) ctx.imageSmoothingQuality = 'high';
    Art.draw(ctx, art, idx, x, y, w, hgt);
    ctx.imageSmoothingEnabled = false;
  }
  function drawBlock(g, frame = null) {
    if (g.flip) { ctx.save(); ctx.translate(2 * g.X, 0); ctx.scale(-1, 1); }
    if (g.kind === 'artWhole') drawArt(g.art, g.dx, g.dy, g.dw, g.dh, frame);
    else if (g.kind === 'artOnPlot') { ctx.drawImage(barePlot, g.plotX, g.plotY); drawArt(g.art, g.dx, g.dy, g.dw, g.dh, frame); }
    else {
      ctx.drawImage(layers.under, g.plotX, g.plotY);
      ctx.drawImage(g.b.canvas, g.dx, g.dy);
      ctx.drawImage(layers.over, g.plotX, g.plotY);
    }
    if (g.flip) ctx.restore();
  }
  /* Empty lots are little parks, one of a few scenes picked by the city's plot (U, V). */
  const lotPlan = new Map();
  function mixHash(u, v) {
    let h = (Math.imul(u + 1, 374761393) + Math.imul(v + 1, 668265263)) | 0;
    h = Math.imul(h ^ (h >>> 13), 1274126177);
    return (h ^ (h >>> 16)) >>> 0;
  }
  /* Scenes are shuffled by a hash, then nudged so no park repeats a neighbour. Round the city's origin each plot checks
     the neighbours nearer the origin: from (0, 0) outward the one above and the one to the left, as before, and in the
     other three quarters the mirror of that. So every two neighbours are checked once, and a plot's scene depends only
     on its place in the city, never on where the map's edge is. */
  function lotVariant(U, V) {
    const key = U + ',' + V;
    if (lotPlan.has(key)) return lotPlan.get(key);
    const n = LOTS.length, near = [];
    if (U >= 0 && V >= 0) { if (V > 0) near.push(lotVariant(U, V - 1)); if (U > 0) near.push(lotVariant(U - 1, V)); }
    else if (U < 0 && V >= 0) { near.push(lotVariant(U + 1, V)); if (V > 0) near.push(lotVariant(U, V - 1)); }
    else if (U < 0) near.push(lotVariant(U + 1, V), lotVariant(U, V + 1));
    else { near.push(lotVariant(U, V + 1)); if (U > 0) near.push(lotVariant(U - 1, V)); }
    let k = mixHash(U, V) % n;
    for (let tries = 0; tries < n && near.includes(k); tries++) k = (k + 1) % n;
    lotPlan.set(key, k);
    return k;
  }
  /* A park's scene: the one picked for it in Edit City, or else the one dealt by its place. */
  function lotIndex(u, v) {
    const U = u + OU, V = v + OV, pick = DB.city.parks[U + ',' + V], at = pick ? LOTS.findIndex(l => l.id === pick) : -1;
    return at >= 0 ? at : lotVariant(U, V);
  }
  const lotFlip = (u, v) => mod((u + OU) * 7 + (v + OV) * 13, 3) === 1;   // mirror some of them, for variety
  function lotScene(u, v) {
    if (typeof LOTS === 'undefined' || !LOTS.length) return null;
    return Art.get('lot:' + LOTS[lotIndex(u, v)].id);
  }
  function drawLot(u, v) {
    const art = lotScene(u, v);
    if (!art) return;
    const [X, Y] = plotTop(u, v);
    const s = PLOT.W / art.w, dh = art.h * s;
    const flip = lotFlip(u, v);
    if (flip) { ctx.save(); ctx.translate(2 * X, 0); ctx.scale(-1, 1); }
    drawArt(art, X - 64, Y + 64 - dh, PLOT.W, dh);
    if (flip) ctx.restore();
  }
  function drawRing(r, X, Y) { ctx.drawImage(r.canvas, X - r.cx, Y + 32 - r.cy); }
  /* The props on screen, as figures for the depth sort: each stands on the middle of its bottom row, at half size like
     the buildings, and a mirrored one turns round that point. People walk through them, in front or behind by depth. */
  function propItems() {
    if (typeof PROPS === 'undefined') return [];
    const out = [], z = cam.z, hx = vw / (2 * z), hy = vh / (2 * z);
    for (const pr of propPlan()) {
      const art = Art.get('prop:' + pr.kind + ':' + (pr.back ? 'back' : 'front'));
      if (!art) continue;
      const [x, y] = tileToWorld(pr.i, pr.j), X = Math.round(x), Y = Math.round(y), w = art.w / 2, hgt = art.h / 2;
      const left = X - Math.round(art.w / 2) / 2, top = Y + 1 - hgt;
      const box = { x0: X - w / 2 - 1, x1: X + w / 2 + 1, y0: top, y1: Y + 1 };
      if (box.x1 < cam.x - hx || box.x0 > cam.x + hx || box.y1 < cam.y - hy || box.y0 > cam.y + hy) continue;
      out.push({ i: pr.i, j: pr.j, key: pr.i + pr.j, box, prop: pr, draw: () => {
        if (pr.mirror) { ctx.save(); ctx.translate(2 * X, 0); ctx.scale(-1, 1); }
        drawArt(art, left, top, w, hgt, 0);
        if (pr.mirror) ctx.restore();
      } });
    }
    lastProps = out.length;
    return out;
  }
  let lastProps = 0;

  /* A block as one flat image at 1x: used to fade it as a unit, for previews, and for PNG export. */
  function flatBlock(p, frame = 0, scale = 2) {
    const g0 = blockGeom(p, 0, 0), [X0, Y0] = plotTop(0, 0);
    const minX = g0.X - 64, minY = Math.floor(Math.min(g0.top, g0.plotY)), maxY = Math.ceil(g0.base) + 1;
    const [cv, gc] = mkCanvas(PLOT.W * scale, (maxY - minY) * scale);
    const saved = ctx, zs = cam.z;
    ctx = gc; cam.z = scale;
    ctx.scale(scale, scale);
    ctx.translate(-minX, -minY);
    drawBlock(g0, g0.art ? frame : null);
    gc.setTransform(1, 0, 0, 1, 0, 0);          // leave the canvas clean for anyone who draws on it next
    ctx = saved; cam.z = zs;
    return { canvas: cv, ox: minX - X0, oy: minY - Y0, scale };
  }
  /* Draws a flattened block back onto the map at world size. */
  function drawFlat(c, x, y) {
    const w = c.canvas.width / c.scale, hh = c.canvas.height / c.scale, eff = cam.z / c.scale;
    ctx.imageSmoothingEnabled = Math.abs(eff - Math.round(eff)) > 0.02 || eff < 1;
    ctx.drawImage(c.canvas, x, y, w, hh);
    ctx.imageSmoothingEnabled = false;
  }
  const flat = new Map();
  function composed(p) {
    const id = p.id;
    const { art, ownPlot } = artFor(p);
    const key = (art ? art.url.length + ':' + art.w + ':' + ownPlot + ':' + (p.generic || '') : 'p') + ':' + (p.flip ? 'f' : '') + ':' + Light.t;
    const hit = flat.get(id);
    if (hit && hit.key === key) return hit;
    const out = Object.assign({ key }, flatBlock(p, 0));
    flat.set(id, out);
    return out;
  }
  /* Canvas pixels per map pixel for previews: two screen pixels per map pixel, sharp on any screen. */
  const previewScale = () => Math.max(2, Math.round(2 * (window.devicePixelRatio || 1)));
  /* A preview canvas that keeps playing, and follows day and night, while it is on the page. */
  function livePreview(p, scale = 2) {
    const first = flatBlock(p, 0, scale).canvas;
    let last = '';
    const tick = () => {
      if (!first.isConnected) { clearInterval(timer); return; }
      const { art } = artFor(p);
      const i = art && art.animated ? Art.indexAt(art, performance.now()) : 0;
      const key = i + ':' + Light.t;
      if (key === last) return;
      last = key;
      const g = first.getContext('2d');
      g.setTransform(1, 0, 0, 1, 0, 0);
      g.clearRect(0, 0, first.width, first.height);
      g.drawImage(flatBlock(p, i, scale).canvas, 0, 0);
    };
    const timer = setInterval(tick, 40);
    tick();
    return first;
  }
  /* The project view's header: a live banner of the building's own block of the city, its neighbours,
     parks, and streets included, in the city's current light. It is the map's own drawing, pointed at
     a small canvas for a moment, with no selection marks. */
  function profileScene(p, cssW = 420, minCssH = 0) {
    const sc = previewScale();
    const u = p.plot ? p.plot.u : 0, v = p.plot ? p.plot.v : 0;
    const g0 = blockGeom(p, u, v);
    const worldW = Math.max(180, Math.round(cssW / 2));
    let minY = Math.floor(Math.min(g0.top, g0.plotY)) - 16, maxY = Math.ceil(g0.base) + 22;
    const need = Math.ceil(minCssH / 2) - (maxY - minY);           // a short building gets more street around it
    if (need > 0) { minY -= Math.ceil(need / 2); maxY += Math.floor(need / 2); }
    const worldH = maxY - minY;
    const [cv, gc] = mkCanvas(worldW * sc, worldH * sc);
    cv.style.width = worldW * 2 + 'px'; cv.style.height = worldH * 2 + 'px';
    const cx = g0.X, cy = (minY + maxY) / 2;
    const paint = () => {
      const saved = { ctx, vw, vh, x: cam.x, y: cam.y, z: cam.z, clean, noBubbles };
      ctx = gc; vw = cv.width; vh = cv.height; cam.x = cx; cam.y = cy; cam.z = sc; clean = true; noBubbles = true;
      try { draw(); } finally {
        ctx = saved.ctx; vw = saved.vw; vh = saved.vh; cam.x = saved.x; cam.y = saved.y; cam.z = saved.z; clean = saved.clean; noBubbles = saved.noBubbles;
        ctx.setTransform(1, 0, 0, 1, 0, 0);
      }
    };
    paint();
    const timer = setInterval(() => { if (!cv.isConnected) { clearInterval(timer); return; } paint(); }, 110);
    return cv;
  }
  function blockPng(p) {
    const c = composed(p).canvas;
    c.toBlob(blob => {
      if (!blob) { toast('The block could not be saved. Try again.', 'error'); return; }
      downloadBlob(blob, slug(p.name) + '-block.png');
      toast('Block saved as a PNG at 1x.');
    }, 'image/png');
  }

  /* Which project shows on which plot right now, including the preview while carrying one. */
  function displayLayout() {
    const m = new Map();
    for (const p of DB.projects) m.set(p.plot.u + ',' + p.plot.v, p);
    if (mode.name === 'move') {
      const M = getProject(mode.id), T = mode.target;
      if (M && T && !(T.u === M.plot.u && T.v === M.plot.v)) {
        const A = M.plot.u + ',' + M.plot.v, K = T.u + ',' + T.v;
        const O = m.get(K);
        m.delete(A);
        if (O) m.set(A, O);
        m.set(K, M);
      }
    }
    return m;
  }

  function draw() {
    const { z, tx, ty } = xf();
    ctx.setTransform(1, 0, 0, 1, 0, 0);
    ctx.fillStyle = worldColor('haze');
    ctx.fillRect(0, 0, vw, vh);
    ctx.setTransform(z, 0, 0, z, tx, ty);
    ctx.imageSmoothingEnabled = false;
    ctx.drawImage(worldCanvas, WX0, WY0);
    const lay = displayLayout();
    const slots = mode.name === 'place' || mode.name === 'move';
    const T = mode.target;
    const moving = typeof Traffic !== 'undefined' && Traffic.active();
    if (moving) Traffic.drawGround(ctx);
    const plots = [];
    for (let d = 0; d <= NU + NV - 2; d++) for (let u = 0; u < NU; u++) {
      const v = d - u;
      if (v < 0 || v >= NV) continue;
      const [X, Y] = plotTop(u, v), p = lay.get(u + ',' + v);
      const a0 = MARGIN + u * PITCH, b0 = MARGIN + v * PITCH;
      plots.push({ plot: true, u, v, a0, a1: a0 + S, b0, b1: b0 + S, key: a0 + b0 + S,
        box: { x0: X - 64, x1: X + 64, y0: p ? blockGeom(p, u, v).top : Y - 30, y1: Y + 66 } });
    }
    const items = (moving ? Traffic.items() : []).concat(propItems());
    for (const it of items.length ? depthSort(plots, items) : plots) {
      if (it.plot) drawPlot(it.u, it.v, lay, slots, T); else it.draw(ctx);
    }
    if (moving) Traffic.drawAir(ctx);
    if (!noBubbles) drawUrgency();
  }

  /* One plot: its park or its building, with its ring. */
  function drawPlot(u, v, lay, slots, T) {
    const [X, Y] = plotTop(u, v);
    const p = lay.get(u + ',' + v);
    const isTarget = slots && T && T.u === u && T.v === v;
    if (!p) {
      drawLot(u, v);
      if (editing && editHover && editHover.u === u && editHover.v === v && !clean) { drawRing(rings.free, X, Y); drawRing(rings.freeRing, X, Y); }
      if (!slots) return;
      if (isTarget && mode.name === 'place') {
        drawRing(rings.target, X, Y); drawRing(rings.targetRing, X, Y);
        const c = composed(ghost);
        ctx.globalAlpha = 0.42; drawFlat(c, X + c.ox, Y + c.oy); ctx.globalAlpha = 1;
      } else { drawRing(rings.free, X, Y); drawRing(rings.freeRing, X, Y); }
      return;
    }
    const carried = mode.name === 'move' && p.id === mode.id;
    if (clean) { /* postcard: no selection marks */ }
    else if (carried) { drawRing(rings.target, X, Y); drawRing(rings.targetRing, X, Y); }
    else if (p.id === App.selectedId && mode.name !== 'move') { drawRing(rings.selHi, X, Y); drawRing(rings.sel, X, Y); }
    else if (p.id === hoverId && !slots) drawRing(rings.hover, X, Y);
    const lift = carried ? 6 : 0;
    if (planting && planting.id === p.id && !clean) {
      const e = easeOut(clamp((performance.now() - planting.t0) / planting.dur, 0, 1));
      const c = composed(p);
      ctx.globalAlpha = 0.42 + 0.58 * e; drawFlat(c, X + c.ox, Y + c.oy - Math.round((1 - e) * 7)); ctx.globalAlpha = 1;
    } else if (clean || matchesFilter(p)) drawBlock(blockGeom(p, u, v, lift));
    else {
      const c = composed(p);
      ctx.globalAlpha = 0.3; drawFlat(c, X + c.ox, Y + c.oy - lift); ctx.globalAlpha = 1;
    }

  }
  /* Back to front: a figure is drawn after a plot when it is past that plot along either axis, or inside it;
     figures among themselves by depth. Only things that overlap on screen get an order. */
  function depthSort(plots, sprites) {
    const all = plots.concat(sprites), n = all.length;
    const after = Array.from({ length: n }, () => []), indeg = new Array(n).fill(0);
    const ov = (a, b) => a.x0 < b.x1 && b.x0 < a.x1 && a.y0 < b.y1 && b.y0 < a.y1;
    const edge = (x, y) => { after[x].push(y); indeg[y]++; };
    for (let x = 0; x < n; x++) for (let y = x + 1; y < n; y++) {
      const A = all[x], B = all[y];
      if (!ov(A.box, B.box)) continue;
      if (A.plot && B.plot) { if (A.key !== B.key) A.key < B.key ? edge(x, y) : edge(y, x); continue; }
      if (A.plot || B.plot) {
        const [pi, si] = A.plot ? [x, y] : [y, x], P = all[pi], f = all[si];
        const inside = f.i >= P.a0 && f.i <= P.a1 && f.j >= P.b0 && f.j <= P.b1;
        (inside || P.a1 <= f.i || P.b1 <= f.j) ? edge(pi, si) : edge(si, pi);
        continue;
      }
      A.key <= B.key ? edge(x, y) : edge(y, x);
    }
    const out = [], done = new Array(n).fill(false);
    for (let k = 0; k < n; k++) {
      let best = -1;
      for (let x = 0; x < n; x++) if (!done[x] && indeg[x] === 0 && (best < 0 || all[x].key < all[best].key)) best = x;
      if (best < 0) for (let x = 0; x < n; x++) if (!done[x] && (best < 0 || all[x].key < all[best].key)) best = x;   // never expected: fall back to depth
      done[best] = true; out.push(all[best]);
      for (const y of after[best]) indeg[y]--;
    }
    return out;
  }

  /* A menu that opens upward from a button at the bottom of the map: every option, the current one ticked.
     Arrow keys move, Enter picks, Esc or a click outside closes. Clicking the button again closes it too. */
  let openDrop = null;
  /* A drop-up: the options as the same buttons as the map's bar, stacked above the one clicked. Each option
     has its own icon, so the bar's button wears the chosen one. Arrow keys move, Esc or a click outside closes. */
  function dropUp(btn, options, current, onPick) {
    if (openDrop) { const was = openDrop.btn; closeDrop(); if (was === btn) return; }
    const host = btn.closest('.map-tools') || document.body;
    const menu = h('div', { class: 'dropup', role: 'group', 'aria-label': btn.title || 'Options' },
      options.map(o => h('button', { class: 'btn dropup-btn', type: 'button', 'data-value': o.value, title: o.hint || o.label, 'aria-pressed': String(o.value === current),
        onclick: () => { closeDrop(); onPick(o.value); btn.focus(); } },
        h('span', { 'aria-hidden': 'true', html: iconSvg(o.icon, 14) }), h('span', null, o.label))));
    host.appendChild(menu);
    menu.style.left = btn.offsetLeft + 'px';
    menu.style.minWidth = btn.offsetWidth + 'px';
    btn.setAttribute('aria-expanded', 'true');
    const items = [...menu.querySelectorAll('.dropup-btn')];
    (items.find(i => i.getAttribute('aria-pressed') === 'true') || items[0]).focus();
    const onKey = e => {
      const k = items.indexOf(document.activeElement);
      if (e.key === 'Escape') { e.preventDefault(); e.stopPropagation(); closeDrop(); btn.focus(); }
      else if (e.key === 'ArrowDown') { e.preventDefault(); items[(k + 1) % items.length].focus(); }
      else if (e.key === 'ArrowUp') { e.preventDefault(); items[(k - 1 + items.length) % items.length].focus(); }
    };
    const onDown = e => { if (!menu.contains(e.target) && !btn.contains(e.target)) closeDrop(); };
    menu.addEventListener('keydown', onKey);
    setTimeout(() => document.addEventListener('pointerdown', onDown, true), 0);
    openDrop = { menu, btn, onDown };
  }
  function closeDrop() {
    if (!openDrop) return;
    document.removeEventListener('pointerdown', openDrop.onDown, true);
    openDrop.btn.setAttribute('aria-expanded', 'false');
    openDrop.menu.remove(); openDrop = null;
  }

  /* ---------- urgency bubbles: drawn over everything, in their own colors by day and by night ---------- */
  const BUB_KEY = 'nullovation-city:bubbles';
  let bubbleMode = (() => { try { const v = localStorage.getItem(BUB_KEY); return ['all', 'red', 'tasks', 'none'].includes(v) ? v : 'all'; } catch (e) { return 'all'; } })();
  let noBubbles = false, lastBobKey = '', lastBobCheck = 0;
  const BUB = {
    red: { edge: '#5A1030', fill: '#E0356F', hi: '#FF7FA6', ink: '#FFFFFF' },
    yellow: { edge: '#6A4A08', fill: '#FFD23F', hi: '#FFF0A0', ink: '#3A2A06' },
    grey: { edge: '#7A7394', fill: '#F4F1F8', hi: '#FFFFFF', ink: '#2B2542' },        // the tasks view: near white
  };
  const GLYPH = {
    '0': ['111', '101', '101', '101', '111'], '1': ['010', '110', '010', '010', '111'], '2': ['111', '001', '111', '100', '111'],
    '3': ['111', '001', '111', '001', '111'], '4': ['101', '101', '111', '001', '001'], '5': ['111', '100', '111', '001', '111'],
    '6': ['111', '100', '111', '101', '111'], '7': ['111', '001', '010', '010', '010'], '8': ['111', '101', '111', '101', '111'],
    '9': ['111', '101', '111', '001', '111'], '!': ['1', '1', '1', '0', '1'],
  };
  const idHash = id => { let x = 0; for (const c of id) x = (x * 31 + c.charCodeAt(0)) | 0; return Math.abs(x); };
  /* One building's bubble: just above its top, bobbing a pixel, slowly, out of step with its neighbours. */
  function bubbleFor(p, u, v, wall, t) {
    let color, count, text;
    if (bubbleMode === 'tasks') {                                   // every project: how many tasks are still open
      count = p.todos.filter(x => !x.done).length; color = 'grey'; text = String(Math.min(count, 99));
    } else {
      const urg = urgencyOf(p, wall);
      if (!urg.color || bubbleMode === 'none' || (bubbleMode === 'red' && urg.color !== 'red')) return null;
      color = urg.color; count = urg.count; text = urg.count <= 1 ? '!' : String(Math.min(urg.count, 99));
    }
    const g = blockGeom(p, u, v);
    const tw = [...text].reduce((w, ch) => w + GLYPH[ch][0].length, 0) + text.length - 1;
    const w = Math.max(9, tw + 6), hh = 11, k = idHash(p.id);
    const bob = Motion.still() ? 0 : Math.round(Math.sin(t / (1500 + (k % 420)) + (k % 628) / 100));
    return { p, color, count, text, tw, x: Math.round(g.X - w / 2), y: Math.round(g.top) - 6 - hh + bob, w, h: hh, bob };
  }
  function eachBubble(fn) {
    const wall = Date.now(), t = performance.now();
    for (const [key, p] of displayLayout().entries()) {
      const [u, v] = key.split(',').map(Number);
      const b = bubbleFor(p, u, v, wall, t);
      if (b && fn(b) === true) return b;
    }
    return null;
  }
  function drawUrgency() { ctx.imageSmoothingEnabled = false; eachBubble(drawBubble); }
  function drawBubble(b) {
    const c = BUB[b.color], { x, y, w } = b, hh = b.h, tx = x + Math.floor(w / 2);
    ctx.fillStyle = c.edge;
    ctx.fillRect(x + 1, y, w - 2, hh); ctx.fillRect(x, y + 1, w, hh - 2);      // the outline, corners rounded off
    ctx.fillRect(tx - 2, y + hh, 4, 1); ctx.fillRect(tx - 1, y + hh + 1, 2, 1); // the tail
    ctx.fillStyle = c.fill;
    ctx.fillRect(x + 1, y + 1, w - 2, hh - 2);
    ctx.fillRect(tx - 1, y + hh - 1, 2, 2);
    ctx.fillStyle = c.hi;
    ctx.fillRect(x + 2, y + 1, w - 4, 1);
    ctx.fillStyle = c.ink;
    let cx = x + Math.floor((w - b.tw) / 2);
    for (const ch of b.text) {
      const gl = GLYPH[ch];
      for (let r = 0; r < 5; r++) for (let q = 0; q < gl[r].length; q++) if (gl[r][q] === '1') ctx.fillRect(cx + q, y + 3 + r, 1, 1);
      cx += gl[0].length + 1;
    }
  }
  /* A cheap signature of every visible bubble, so the map redraws only when one bobs or changes. */
  function bubbleKey() {
    let key = '';
    eachBubble(b => { key += b.p.id + b.color + b.count + b.bob + ';'; });
    return key;
  }
  function setBubbleMode(mode) {
    bubbleMode = mode;
    try { localStorage.setItem(BUB_KEY, mode); } catch (e) { /* the choice lasts for this visit */ }
    invalidate();
  }

  /* ---------- frame loop ---------- */
  function kick() { if (!raf) raf = requestAnimationFrame(frame); }
  function invalidate() { dirty = true; kick(); }
  function frame(t) {
    raf = 0;
    const dt = lastT ? Math.min(50, t - lastT) : 16;
    lastT = t;
    let more = false;
    if (keys.size) {
      const dx = (keys.has('r') ? 1 : 0) - (keys.has('l') ? 1 : 0);
      const dy = (keys.has('d') ? 1 : 0) - (keys.has('u') ? 1 : 0);
      if (dx || dy) {
        const len = Math.hypot(dx, dy), sp = ((720 * dpr) / cam.z) * (dt / 1000);
        cam.x += (dx / len) * sp; cam.y += (dy / len) * sp;
        clampCam(); dirty = true; saveUiSoon();
      }
      more = true;
    }
    if (anim.glide) {
      const a = anim.glide, k = clamp((t - a.t0) / a.dur, 0, 1), e = easeOut(k);
      cam.x = lerp(a.fx, a.tx, e); cam.y = lerp(a.fy, a.ty, e);
      clampCam(); dirty = true;
      if (k >= 1) { anim.glide = null; saveUiSoon(); } else more = true;
    }
    if (anim.zoom) {
      const a = anim.zoom, k = clamp((t - a.t0) / a.dur, 0, 1);
      zoomAt(a.ax, a.ay, lerp(a.from, a.to, easeOut(k)));
      if (k >= 1) anim.zoom = null; else more = true;
      dirty = true;
    }
    let animating = false;
    const still = Motion.still();
    if (t - lastBobCheck > 90) {
      lastBobCheck = t;
      const key = bubbleKey();
      if (key !== lastBobKey) { lastBobKey = key; dirty = true; }
    }
    if (lastBobKey && !still) more = true;
    if (typeof Traffic !== 'undefined' && Traffic.active()) { if (Traffic.step(t)) dirty = true; more = true; }
    if (planting) {
      dirty = true; more = true;
      if (t - planting.t0 >= planting.dur) { const done = planting.then; planting = null; if (done) setTimeout(done, 0); }
    }
    if (typeof LOTS !== 'undefined' && !still) for (const l of LOTS) {
      const a = Art.get('lot:' + l.id);
      if (!a || !a.animated) continue;
      animating = true;
      const i = Art.indexAt(a, t);
      if (animIdx.get('lot:' + l.id) !== i) { animIdx.set('lot:' + l.id, i); dirty = true; }
    }
    if (!still) for (const p of DB.projects) {
      const a = artFor(p).art;
      if (!a || !a.animated) continue;
      animating = true;
      const i = Art.indexAt(a, t);
      if (animIdx.get(p.id) !== i) { animIdx.set(p.id, i); dirty = true; }
    }
    if (animating) more = true;
    if (dirty && Motion.saver() && t - lastPaint < 32) more = true;   // Saver: the next frame draws it
    else if (dirty) { draw(); dirty = false; lastPaint = t; paints++; Bubble.position(); if (editing) placeArrows(); }
    if (more) kick(); else lastT = 0;
  }
  let lastPaint = 0, paints = 0;

  /* ---------- camera ---------- */
  function updateZoomLabel() {
    const v = Math.round((cam.z / dpr) * 10) / 10;
    $('#zoomLevel').textContent = (Number.isInteger(v) ? v : v.toFixed(1)) + 'x';
  }
  function zoomAt(cssX, cssY, z) {
    z = clamp(z, zMin(), zMax());
    const px = cssX * dpr, py = cssY * dpr;
    const wx = (px - vw / 2) / cam.z + cam.x, wy = (py - vh / 2) / cam.z + cam.y;
    cam.z = z;
    cam.x = wx - (px - vw / 2) / z; cam.y = wy - (py - vh / 2) / z;
    clampCam(); invalidate(); updateZoomLabel(); saveUiSoon();
  }
  function scheduleSettle() { clearTimeout(settleTimer); settleTimer = setTimeout(settle, 170); }
  /* After scrolling stops, ease onto the nearest whole-number zoom, where pixels are sharp. */
  function settle() {
    if (gesture && gesture.type === 'pinch') return;
    const target = snapZ(cam.z);
    const [ax, ay] = lastAnchor || [vw / dpr / 2, vh / dpr / 2];
    if (Math.abs(target - cam.z) < 0.001) { cam.z = target; invalidate(); updateZoomLabel(); return; }
    if (reducedMotion()) { zoomAt(ax, ay, target); return; }
    anim.zoom = { from: cam.z, to: target, t0: performance.now(), dur: 200, ax, ay };
    kick();
  }
  /* Whole even steps keep the 256 px buildings pixel-exact; 3x is added too, drawn sharp by drawArt. */
  function zoomLevels() {
    const L = [1];
    for (let z = 2; z <= zMax(); z += 2) L.push(z);
    const three = Math.round(3 * dpr);
    if (!L.includes(three) && three <= zMax()) L.push(three);
    return L.sort((a, b) => a - b);
  }
  function snapZ(z) {
    const L = zoomLevels();
    return L.reduce((best, x) => Math.abs(x - z) < Math.abs(best - z) ? x : best, L[0]);
  }
  function zoomStep(dir) {
    const cur = snapZ(anim.zoom ? anim.zoom.to : cam.z), L = zoomLevels();
    const target = L[clamp(L.indexOf(cur) + dir, 0, L.length - 1)];
    const ax = vw / dpr / 2, ay = vh / dpr / 2;
    if (reducedMotion()) { zoomAt(ax, ay, target); return; }
    anim.zoom = { from: cam.z, to: target, t0: performance.now(), dur: 200, ax, ay };
    kick();
  }
  function cancelGlide() { anim.glide = null; }
  /* Glides so the building sits in the open part of the map, right of a panel that covers leftCss pixels. */
  function glideBeside(id, leftCss) {
    const p = getProject(id); if (!p || !p.plot) return;
    const g = blockGeom(p, p.plot.u, p.plot.v);
    const Wc = vw / dpr, off = Math.min(leftCss, Wc * 0.75) / 2;
    const tx = g.X - (off * dpr) / cam.z, ty = (g.top + g.base) / 2;
    if (reducedMotion()) { cam.x = tx; cam.y = ty; clampCam(); invalidate(); return; }
    anim.glide = { fx: cam.x, fy: cam.y, tx, ty, t0: performance.now(), dur: 380 };
    kick();
  }
  function glideTo(id) {
    const p = getProject(id); if (!p) return;
    const g = blockGeom(p, p.plot.u, p.plot.v);
    const z = cam.z, Hc = vh / dpr;
    const bubbleH = Bubble.height() || 240;
    const blockH = ((g.base - g.top) * z) / dpr;
    const need = blockH + bubbleH + 22 + 58;   // bubble and its tail above, Enter below
    const baseY = need + 32 <= Hc ? (Hc - need) / 2 + bubbleH + 22 + blockH : 16 + bubbleH + 22 + blockH;
    const tx = g.X, ty = g.base - (baseY * dpr - vh / 2) / z;
    if (reducedMotion()) { cam.x = tx; cam.y = ty; clampCam(); invalidate(); return; }
    anim.glide = { fx: cam.x, fy: cam.y, tx, ty, t0: performance.now(), dur: 380 };
    kick();
  }
  function frameAll() {
    const ps = DB.projects;
    let minX = Infinity, maxX = -Infinity, minY = Infinity, maxY = -Infinity;
    if (!ps.length) { minX = WX0; maxX = WX1; minY = WY0; maxY = WY1; }
    for (const p of ps) {
      const [X, Y] = plotTop(p.plot.u, p.plot.v);
      minX = Math.min(minX, X - 72); maxX = Math.max(maxX, X + 72);
      minY = Math.min(minY, Y - 100); maxY = Math.max(maxY, Y + 72);
    }
    const z = Math.floor(Math.min((vw * 0.85) / (maxX - minX), (vh * 0.85) / (maxY - minY)));
    cam.z = snapZ(clamp(z, Math.max(zMin(), Math.round(dpr)), Math.min(zMax(), Math.round(4 * dpr))));
    cam.x = (minX + maxX) / 2; cam.y = (minY + maxY) / 2;
    clampCam(); updateZoomLabel(); invalidate();
  }
  function setCam(c) {
    cam.x = c.x; cam.y = c.y;
    cam.z = clamp(Math.round(c.z * dpr), zMin(), zMax());
    clampCam(); updateZoomLabel(); invalidate();
  }
  const saveUiSoon = debounce(() => Store.saveUi({ cam: { x: cam.x, y: cam.y, z: cam.z / dpr } }), 500);

  function resize() {
    const r = wrap.getBoundingClientRect();
    const nd = window.devicePixelRatio || 1;
    if (nd !== dpr) { cam.z = clamp(Math.round((cam.z * nd) / dpr), 1, Math.max(4, Math.round(8 * nd))); dpr = nd; }
    vw = Math.max(1, Math.round(r.width * dpr)); vh = Math.max(1, Math.round(r.height * dpr));
    canvas.width = vw; canvas.height = vh;
    ctx.imageSmoothingEnabled = false;
    updateZoomLabel(); invalidate();
  }

  /* ---------- hit testing ---------- */
  function hitGeom(g, wx, wy) {
    if (g.flip) wx = 2 * g.X - wx;
    const cy = g.Y + 32 - PLOT.RAISE;
    if (Math.abs(wx - g.X) / 64 + Math.abs(wy - cy) / 32 <= 1) return true;
    if (g.kind === 'placeholder') {
      const b = g.b, lx = Math.floor(wx - g.dx), ly = Math.floor(wy - g.dy);
      return lx >= 0 && ly >= 0 && lx < b.CW && ly < b.CH && b.mask[ly * b.CW + lx] === 1;
    }
    const a = g.art, lx = Math.floor((wx - g.dx) / g.s), ly = Math.floor((wy - g.dy) / g.s);
    return lx >= 0 && ly >= 0 && lx < a.w && ly < a.h && a.mask[ly * a.w + lx] === 1;
  }
  function hitProject(cx, cy) {
    const [wx, wy] = cssToWorld(cx, cy);
    const onBubble = eachBubble(b => wx >= b.x - 1 && wx <= b.x + b.w + 1 && wy >= b.y - 1 && wy <= b.y + b.h + 3);
    if (onBubble) return onBubble.p;
    const list = [...displayLayout().entries()].map(([k, p]) => { const [u, v] = k.split(',').map(Number); return { p, u, v }; });
    list.sort((a, b) => (b.u + b.v) - (a.u + a.v));
    for (const { p, u, v } of list) if (hitGeom(blockGeom(p, u, v), wx, wy)) return p;
    return null;
  }
  /* Forgiving: the gap around a plot still counts as that plot. */
  function plotNear(cx, cy) {
    const [wx, wy] = cssToWorld(cx, cy);
    const [i, j] = worldToTile(wx, wy + PLOT.RAISE);
    const u = Math.round((i - MARGIN - S / 2) / PITCH), v = Math.round((j - MARGIN - S / 2) / PITCH);
    if (u < 0 || v < 0 || u >= NU || v >= NV) return null;
    const ci = MARGIN + u * PITCH + S / 2, cj = MARGIN + v * PITCH + S / 2;
    if (Math.abs(i - ci) > PITCH / 2 + 0.5 || Math.abs(j - cj) > PITCH / 2 + 0.5) return null;
    return { u, v };
  }
  const same = (a, b) => (!a && !b) || (a && b && a.u === b.u && a.v === b.v);

  /* ---------- selection, placing, moving ---------- */
  function select(id, { glide = true } = {}) {
    Wheel.close();                                           // the wheel closes for the status bubble
    App.selectedId = id; hideTip();
    Bubble.open(id);
    if (glide) { if (FullView.isOpen()) glideBeside(id, FullView.rightEdge()); else glideTo(id); }   // with the view open, into the open strip
    invalidate();
  }
  function deselect() {
    if (!App.selectedId) return false;
    App.selectedId = null; Bubble.close(); invalidate();
    return true;
  }
  async function startPlace(name, generic) {
    setEditing(false);
    if (!freePlots().length) {
      if (!canResize(1)) {
        if (WORLD.NU < WORLD.MAX_N || WORLD.NV < WORLD.MAX_N) toast('Every plot is taken. Add a line of plots in Edit City, under Settings, then plant it.', 'error');
        else toast('Every plot is taken, and the map is at its largest. Delete a project to free one up.', 'error');
        return false;
      }
      const ok = await Confirm.ask({ title: 'Every plot is taken', body: 'Add a ring of plots around the city? The map grows from ' + WORLD.NU + ' by ' + WORLD.NV + ' to ' + (WORLD.NU + 2) + ' by ' + (WORLD.NV + 2) + ' plots.', confirm: 'Add a ring' });
      if (!ok || !resizeWorld(1)) return false;
    }
    deselect();
    const pendingId = uid('p');
    ghost = { id: '__ghost', art: { has: false, includesPlot: false }, generic: generic || null };
    flat.delete('__ghost');
    mode = { name: 'place', pendingName: name, pendingId, generic: generic || null, target: null };
    $('#bannerName').textContent = name;
    $('#banner').hidden = false;
    canvas.classList.add('placing');
    invalidate();
    return true;
  }
  function placeAt(t) {
    const { pendingName, pendingId, generic } = mode;
    endPlace();
    const p = createProject(pendingName, t, pendingId, generic);
    Menu.refresh();
    const plan = () => { select(p.id, { glide: false }); FullView.open(p.id, { section: 'about' }); };
    if (reducedMotion()) { plan(); return; }
    planting = { id: p.id, t0: performance.now(), dur: 450, then: plan };
    kick();
  }
  function endPlace() {
    mode = { name: 'idle' }; ghost = null;
    $('#banner').hidden = true;
    canvas.classList.remove('placing', 'over-building');
    invalidate();
  }
  function beginMove(p, x, y) {
    if (!gesture || gesture.hit !== p || gesture.type !== 'maybe') return;
    gesture.type = 'move';
    const [X, Y] = plotTop(p.plot.u, p.plot.v);
    const [cx, cy] = worldToCss(X, Y + 32);
    mode = { name: 'move', id: p.id, target: { u: p.plot.u, v: p.plot.v }, gx: cx - x, gy: cy - y };
    canvas.classList.add('moving'); hideTip();
    Bubble.position();
    invalidate();
  }
  function finishMove(commit = true) {
    const M = getProject(mode.id), T = mode.target;
    mode = { name: 'idle' };
    canvas.classList.remove('moving');
    if (commit && M && T && !(T.u === M.plot.u && T.v === M.plot.v)) {
      const O = projectAt(T.u, T.v);
      if (O) O.plot = { u: M.plot.u, v: M.plot.v };
      M.plot = { u: T.u, v: T.v };
      changed(null, { touch: false });       // moving a building is not work on the project
    }
    invalidate(); Bubble.position();
    if (editing) editUi();
  }
  function cancelMode() {
    if (mode.name === 'place') { endPlace(); return true; }
    if (mode.name === 'move') { if (gesture) { clearTimeout(gesture.hold); gesture = null; } finishMove(false); return true; }
    return false;
  }

  /* ---------- hover label ---------- */
  function showTip(text, x, y) {
    const t = $('#tip');
    t.textContent = text; t.setAttribute('dir', 'auto'); t.hidden = false;
    const W = wrap.clientWidth, Hh = wrap.clientHeight;
    const w = t.offsetWidth, hh = t.offsetHeight;
    t.style.transform = `translate(${Math.round(clamp(x + 14, 8, W - w - 8))}px, ${Math.round(clamp(y + 18, 8, Hh - hh - 8))}px)`;
  }
  function hideTip() { const t = $('#tip'); if (t) t.hidden = true; }
  function hover(x, y) {
    if (mode.name === 'place') {
      const t = plotNear(x, y);
      const free = t && !projectAt(t.u, t.v) ? t : null;
      if (!same(free, mode.target)) { mode.target = free; invalidate(); }
      canvas.classList.toggle('over-building', !!free);
      return;
    }
    if (mode.name === 'move') return;
    if (editing) {
      const hit = hitProject(x, y), t = hit ? null : plotNear(x, y), park = t && !projectAt(t.u, t.v) ? t : null;
      if (!same(park, editHover)) { editHover = park; invalidate(); }
      canvas.classList.toggle('over-building', !!park);
      canvas.classList.toggle('edit-grab', !!hit);
      if (park) showTip(parkName(LOTS[lotIndex(park.u, park.v)].id) + ': click for the next kind', x, y);
      else if (hit) showTip(hit.name + ': drag to move', x, y);
      else hideTip();
      return;
    }
    const hit = hitProject(x, y);
    const id = hit ? hit.id : null;
    if (id !== hoverId) { hoverId = id; invalidate(); }
    canvas.classList.toggle('over-building', !!hit);
    if (hit && hit.id !== App.selectedId) showTip(hit.name, x, y); else hideTip();
  }

  /* ---------- input ---------- */
  function local(e) { const r = canvas.getBoundingClientRect(); return [e.clientX - r.left, e.clientY - r.top]; }
  function onDown(e) {
    if (e.pointerType === 'mouse' && e.button !== 0) return;
    Menu.closeDrawer();
    const [x, y] = local(e);
    try { canvas.setPointerCapture(e.pointerId); } catch (_) { /* ignore */ }
    pointers.set(e.pointerId, { x, y });
    cancelGlide();
    if (pointers.size === 2) { beginPinch(); return; }
    if (pointers.size > 2) return;
    const hit = mode.name === 'place' ? null : hitProject(x, y);
    gesture = { type: 'maybe', id: e.pointerId, sx: x, sy: y, lx: x, ly: y, hit, hold: null };
    if (hit && mode.name === 'idle' && !editing) gesture.hold = setTimeout(() => beginMove(hit, x, y), 380);
  }
  function onMove(e) {
    const [x, y] = local(e);
    if (pointers.has(e.pointerId)) pointers.set(e.pointerId, { x, y });
    if (gesture && gesture.type === 'pinch') { updatePinch(); return; }
    if (!gesture || gesture.id !== e.pointerId) { if (e.pointerType === 'mouse') hover(x, y); return; }
    const dx = x - gesture.lx, dy = y - gesture.ly;
    gesture.lx = x; gesture.ly = y;
    if (gesture.type === 'maybe' && Math.hypot(x - gesture.sx, y - gesture.sy) > 5) {
      clearTimeout(gesture.hold);
      if (editing && gesture.hit && mode.name === 'idle') beginMove(gesture.hit, gesture.sx, gesture.sy);
      else { gesture.type = 'pan'; canvas.classList.add('panning'); hideTip(); }
    }
    if (gesture.type === 'pan') {
      cam.x -= (dx * dpr) / cam.z; cam.y -= (dy * dpr) / cam.z;
      clampCam(); invalidate(); saveUiSoon();
      if (mode.name === 'place') hover(x, y);
    } else if (gesture.type === 'move') {
      const t = plotNear(x + mode.gx, y + mode.gy);
      if (t && !same(t, mode.target)) { mode.target = t; invalidate(); }
    }
  }
  function onUp(e) {
    const [x, y] = local(e);
    pointers.delete(e.pointerId);
    try { canvas.releasePointerCapture(e.pointerId); } catch (_) { /* ignore */ }
    if (gesture && gesture.type === 'pinch') { if (pointers.size < 2) { gesture = null; scheduleSettle(); } return; }
    if (!gesture || gesture.id !== e.pointerId) return;
    clearTimeout(gesture.hold);
    const g = gesture; gesture = null;
    canvas.classList.remove('panning');
    if (e.type === 'pointercancel') { if (g.type === 'move') finishMove(false); return; }
    if (g.type === 'maybe') click(x, y, g.hit);
    else if (g.type === 'move') finishMove(true);
  }
  function click(x, y, hit) {
    if (editing) {
      const t = hit ? null : plotNear(x, y);
      if (t && !projectAt(t.u, t.v)) cyclePark(t.u, t.v);
      return;
    }
    if (mode.name === 'place') {
      const t = plotNear(x, y);
      if (t && !projectAt(t.u, t.v)) placeAt(t);
      return;
    }
    if (hit) { if (hit.id !== App.selectedId) select(hit.id); else glideTo(hit.id); }
    else deselect();
  }
  function beginPinch() {
    if (gesture) clearTimeout(gesture.hold);
    if (mode.name === 'move') finishMove(false);
    const [a, b] = [...pointers.values()];
    gesture = { type: 'pinch', d0: Math.hypot(a.x - b.x, a.y - b.y) || 1, z0: cam.z, mx: (a.x + b.x) / 2, my: (a.y + b.y) / 2 };
    canvas.classList.remove('panning');
  }
  function updatePinch() {
    const [a, b] = [...pointers.values()];
    if (!a || !b) return;
    const d = Math.hypot(a.x - b.x, a.y - b.y) || 1, mx = (a.x + b.x) / 2, my = (a.y + b.y) / 2;
    cam.x -= ((mx - gesture.mx) * dpr) / cam.z; cam.y -= ((my - gesture.my) * dpr) / cam.z;
    gesture.mx = mx; gesture.my = my;
    zoomAt(mx, my, (gesture.z0 * d) / gesture.d0);
    lastAnchor = [mx, my];
  }
  function onWheel(e) {
    if (FullView.isOpen()) {
      if (e.target.closest && e.target.closest('#pv, #pvSide')) return;   // the panels scroll themselves
      e.preventDefault();
      FullView.scrollBy(e.deltaY * (e.deltaMode === 1 ? 16 : e.deltaMode === 2 ? 400 : 1));
      return;
    }
    e.preventDefault();
    const [x, y] = local(e);
    const unit = e.deltaMode === 1 ? 16 : e.deltaMode === 2 ? 400 : 1;
    const k = e.ctrlKey ? 0.01 : 0.0022;       // ctrl + wheel is a trackpad pinch
    cancelGlide(); anim.zoom = null;
    zoomAt(x, y, cam.z * Math.exp(-e.deltaY * unit * k));
    lastAnchor = [x, y];
    scheduleSettle();
  }
  function keyDir(e) {
    switch (e.key) { case 'ArrowLeft': return 'l'; case 'ArrowRight': return 'r'; case 'ArrowUp': return 'u'; case 'ArrowDown': return 'd'; default: break; }
    switch (e.code) { case 'KeyA': return 'l'; case 'KeyD': return 'r'; case 'KeyW': return 'u'; case 'KeyS': return 'd'; default: return null; }
  }
  const typing = e => { const t = e.target; return !!t && (t.isContentEditable || /^(INPUT|TEXTAREA|SELECT)$/.test(t.tagName)); };

  function applyWorld() {
    NU = WORLD.NU; NV = WORLD.NV; OU = WORLD.OU; OV = WORLD.OV; TI = WORLD.TI; TJ = WORLD.TJ;
    WX0 = -TJ * HW; WX1 = TI * HW; WY0 = 0; WY1 = (TI + TJ) * HH + SLAB;
    worldCanvas = buildWorld();
  }
  /* The map's four sides, named like a block's: the north-east side is the line v = 0 (top right on screen), the
     south-east u = NU - 1, the south-west v = NV - 1, and the north-west u = 0. A line added on the north-west or
     north-east side moves the grid's start, so the plots there shift by one and the city's origin by one back. */
  const SIDES = ['ne', 'se', 'sw', 'nw'];
  const lineOf = side => side === 'nw' ? (p => p.u === 0) : side === 'se' ? (p => p.u === WORLD.NU - 1) : side === 'ne' ? (p => p.v === 0) : (p => p.v === WORLD.NV - 1);
  const lineEmpty = side => !DB.projects.some(p => lineOf(side)(p.plot));
  const outerRingEmpty = () => SIDES.every(lineEmpty);
  const fits = n => n >= WORLD.MIN_N && n <= WORLD.MAX_N;
  /* A ring fits when both sides stay within 5 to 11; taking one off also needs the ring empty. */
  const canResize = dir => fits(WORLD.NU + 2 * dir) && fits(WORLD.NV + 2 * dir) && (dir > 0 || outerRingEmpty());
  const canLine = (side, dir) => fits((side === 'nw' || side === 'se' ? WORLD.NU : WORLD.NV) + dir) && (dir > 0 || lineEmpty(side));
  /* Moves the grid: du and dv plots added before it on each axis, and the new size. The view stays on the same
     buildings, and everything dealt by place stays with them. */
  function reshape(du, dv, nu, nv) {
    cancelMode();
    for (const p of DB.projects) p.plot = { u: p.plot.u + du, v: p.plot.v + dv };
    setWorld({ nu, nv, ou: WORLD.OU - du, ov: WORLD.OV - dv }); DB.world = worldState();
    cam.x += (du - dv) * PITCH * HW; cam.y += (du + dv) * PITCH * HH;
    applyWorld(); clampCam();
    persistNow(); invalidate(); Menu.refresh(); Bubble.position();
    if (typeof Settings !== 'undefined') Settings.refresh();
    if (editing) editUi();
    return true;
  }
  /* Adds (dir 1) or removes (dir -1) one ring of plots around the city. */
  function resizeWorld(dir) {
    if (!canResize(dir)) return false;
    return reshape(dir, dir, WORLD.NU + 2 * dir, WORLD.NV + 2 * dir);
  }
  /* Adds (dir 1) or takes off (dir -1) one line of plots on one side of the city. */
  function addLine(side, dir) {
    if (!SIDES.includes(side) || !canLine(side, dir)) return false;
    const du = side === 'nw' ? dir : 0, dv = side === 'ne' ? dir : 0;
    return reshape(du, dv, WORLD.NU + (side === 'nw' || side === 'se' ? dir : 0), WORLD.NV + (side === 'ne' || side === 'sw' ? dir : 0));
  }
  /* ---------- Edit City: lines, rings, parks and buildings, from the City tab of Settings ---------- */
  let editing = false, editHover = null;
  const SIDE_NAMES = { ne: 'north-east', se: 'south-east', sw: 'south-west', nw: 'north-west' };
  const SIDE_TURN = { nw: 0, ne: 90, se: 180, sw: 270 };            // the arrow icon points north-west
  const parkName = id => (id.charAt(0).toUpperCase() + id.slice(1)).replace(/-/g, ' ');
  function setEditing(on) {
    on = !!on;
    if (on === editing) return false;
    if (on) { cancelMode(); deselect(); hideTip(); }
    else { if (mode.name === 'move') { if (gesture) { clearTimeout(gesture.hold); gesture = null; } finishMove(false); } editHover = null; hideTip(); }
    editing = on;
    $('#editBar').hidden = !on; $('#editArrows').hidden = !on;
    canvas.classList.toggle('editing', on);
    canvas.classList.remove('edit-grab', 'over-building');
    if (on) { buildArrows(); frameCity(); editUi(); }
    invalidate();
    if (typeof Settings !== 'undefined') Settings.refresh();
    return true;
  }
  /* Opening Edit City frames the whole map, its four arrow pairs included, between its bar and the map's buttons. */
  function frameCity() {
    const pad = 3 * PITCH * HW, top = 130 * dpr, bottom = 80 * dpr;
    const w = WX1 - WX0 + 2 * pad, hh = WY1 - WY0 + 2 * pad;
    const fit = Math.min(vw * 0.94 / w, (vh - top - bottom) * 0.94 / hh);
    const L = zoomLevels(), z = L.filter(x => x <= fit).pop() || L[0];
    cam.z = z;
    cam.x = (WX0 + WX1) / 2;
    cam.y = (WY0 + WY1) / 2 + (vh / 2 - (top + (vh - top - bottom) / 2)) / z;
    anim.glide = null; anim.zoom = null;
    clampCam(); updateZoomLabel(); saveUiSoon();
  }
  /* Each side: an arrow out that adds a line, and an arrow in that takes off the outer line; the arrow in shows only
     when that line is empty and the city is longer than 5 plots that way, and the arrow out while it is under 11. */
  function buildArrows() {
    const box = $('#editArrows');
    box.replaceChildren(...SIDES.map(side => h('div', { class: 'edit-side', 'data-side': side },
      [1, -1].map(dir => h('button', { class: 'btn edit-arrow', type: 'button', 'data-dir': dir > 0 ? 'out' : 'in',
        'aria-label': dir > 0 ? 'Add a line on the ' + SIDE_NAMES[side] + ' side' : 'Take off the ' + SIDE_NAMES[side] + ' line',
        title: dir > 0 ? 'Add a line on the ' + SIDE_NAMES[side] + ' side' : 'Take off the ' + SIDE_NAMES[side] + ' line',
        onclick: () => { addLine(side, dir); },
      }, h('span', { class: 'edit-arrow-ic', style: 'transform: rotate(' + ((SIDE_TURN[side] + (dir > 0 ? 0 : 180)) % 360) + 'deg)', html: iconSvg('arrow', 16) }))))));
  }
  function editUi() {
    if (!editing) return;
    $('#editSize').textContent = WORLD.NU + ' by ' + WORLD.NV + ' plots';
    $('#btnGrow').disabled = !canResize(1);
    $('#btnShrink').disabled = !fits(WORLD.NU - 2) || !fits(WORLD.NV - 2);
    for (const el of $$('#editArrows .edit-side')) {
      const side = el.dataset.side;
      el.querySelector('[data-dir="out"]').hidden = !canLine(side, 1);
      el.querySelector('[data-dir="in"]').hidden = !canLine(side, -1);
    }
    placeArrows();
  }
  /* The arrows sit just outside the middle of each side, and follow the map as it pans and zooms. A city bigger than
     the view keeps them at its edge, between the bar and the map's buttons, so every side stays in reach. */
  function placeArrows() {
    if (!editing) return;
    const at = { nw: [-1.6, TJ / 2], ne: [TI / 2, -1.6], se: [TI + 2.2, TJ / 2], sw: [TI / 2, TJ + 2.2] };
    const bar = $('#editBar'), W = wrap.clientWidth, H = wrap.clientHeight;
    const top = bar.offsetTop + bar.offsetHeight + 34, bottom = H - 84;
    for (const el of $$('#editArrows .edit-side')) {
      let [cx, cy] = worldToCss(...tileToWorld(...at[el.dataset.side]));
      const half = el.offsetWidth / 2 + 8;
      cx = clamp(cx, half, W - half); cy = clamp(cy, top, Math.max(top, bottom));
      el.style.transform = `translate(${Math.round(cx)}px, ${Math.round(cy)}px) translate(-50%, -50%)`;
    }
  }
  /* A click on a park deals its next kind. Back at the kind its place deals, the pick is dropped. */
  function cyclePark(u, v) {
    const U = u + OU, V = v + OV, next = LOTS[(lotIndex(u, v) + 1) % LOTS.length].id;
    if (next === LOTS[lotVariant(U, V)].id) delete DB.city.parks[U + ',' + V]; else DB.city.parks[U + ',' + V] = next;
    persistSoon(); invalidate();
    const t = $('#tip'); if (t && !t.hidden) t.textContent = parkName(next) + ': click for the next kind';
  }

  /* Q and E (or [ and ]) step through buildings in map order: top to bottom, then left to right. */
  function hop(dir) {
    const list = DB.projects.filter(matchesFilter).sort((a, b) =>
      (a.plot.u + a.plot.v) - (b.plot.u + b.plot.v) || (a.plot.u - a.plot.v) - (b.plot.u - b.plot.v));
    if (!list.length) return;
    const from = App.selectedId || Wheel.owner();           // from the building whose wheel is open, too
    let i = list.findIndex(p => p.id === from);
    i = i < 0 ? (dir > 0 ? 0 : list.length - 1) : (i + dir + list.length) % list.length;
    select(list[i].id);
  }
  /* The postcard's options, on this computer: the caption with the date, and the size, as on screen or doubled. */
  const CARD_KEY = 'nullovation-city:postcard', CARD_DEFAULT = { caption: true, size: 'screen' };
  let card = (() => { try { const v = JSON.parse(localStorage.getItem(CARD_KEY) || 'null'); return v && typeof v === 'object' ? { caption: v.caption !== false, size: v.size === 'double' ? 'double' : 'screen' } : { ...CARD_DEFAULT }; } catch (e) { return { ...CARD_DEFAULT }; } })();
  function setCard(o) {
    card = Object.assign({}, card, o);
    try { if (card.caption === CARD_DEFAULT.caption && card.size === CARD_DEFAULT.size) localStorage.removeItem(CARD_KEY); else localStorage.setItem(CARD_KEY, JSON.stringify(card)); } catch (e) { /* this visit only */ }
  }
  /* Saves the current view as a PNG, without selection marks, with a small caption. Doubled, the same view is drawn
     at twice the scale on a canvas twice the size. */
  async function postcard() {
    try { await document.fonts.load('600 16px "Readex Pro"'); } catch (e) { /* fall back to any font */ }
    const k = card.size === 'double' ? 2 : 1;
    const out = document.createElement('canvas');
    out.width = vw * k; out.height = vh * k;
    const g = out.getContext('2d');
    const saved = { ctx, vw, vh, z: cam.z };
    ctx = g; vw = out.width; vh = out.height; cam.z = saved.z * k; clean = true;
    try { draw(); } finally {
      ctx = saved.ctx; vw = saved.vw; vh = saved.vh; cam.z = saved.z; clean = false;
      ctx.setTransform(1, 0, 0, 1, 0, 0);
    }
    g.setTransform(1, 0, 0, 1, 0, 0);
    invalidate();
    if (card.caption) caption(g, out.width, out.height, dpr * k);
    out.toBlob(blob => {
      if (!blob) { toast('The postcard could not be made. Try again.', 'error'); return; }
      const a = h('a', { href: URL.createObjectURL(blob), download: 'nullovation-city-' + ymd() + '.png' });
      document.body.append(a); a.click();
      setTimeout(() => { URL.revokeObjectURL(a.href); a.remove(); }, 1500);
      toast('Postcard saved as a PNG.');
    }, 'image/png');
  }
  function caption(g, vw, vh, u) {
    const fs = Math.round(15 * u), pad = Math.round(14 * u), padIn = Math.round(9 * u), bw = Math.max(2, Math.round(2 * u));
    const text = 'Nullovation City, ' + new Date().toLocaleDateString('en-GB', { day: 'numeric', month: 'long', year: 'numeric' });
    g.font = `600 ${fs}px "Readex Pro", system-ui, sans-serif`;
    const tw = Math.ceil(g.measureText(text).width);
    const boxW = tw + padIn * 2, boxH = fs + padIn * 2, x = pad, y = vh - pad - boxH;
    g.fillStyle = '#6B6388'; g.fillRect(x - bw, y - bw, boxW + bw * 2, boxH + bw * 2);
    g.fillStyle = '#221D33'; g.fillRect(x, y, boxW, boxH);
    g.fillStyle = '#ECE8F6'; g.textBaseline = 'middle'; g.fillText(text, x + padIn, y + boxH / 2 + Math.round(u));
  }

  function init() {
    canvas = $('#map'); wrap = $('#mapWrap');
    ctx = canvas.getContext('2d', { alpha: false });
    applyWorld();
    layers = renderPlotLayers();
    barePlot = renderBarePlot();
    rings = buildRings();
    dpr = window.devicePixelRatio || 1;
    resize();
    new ResizeObserver(resize).observe(wrap);
    window.addEventListener('resize', resize);
    canvas.addEventListener('pointerdown', onDown);
    canvas.addEventListener('pointermove', onMove);
    canvas.addEventListener('pointerup', onUp);
    canvas.addEventListener('pointercancel', onUp);
    canvas.addEventListener('pointerleave', () => { if (!gesture && hoverId) { hoverId = null; invalidate(); } hideTip(); });
    wrap.addEventListener('wheel', onWheel, { passive: false }); // also over the bubble and Enter button
    /* Right-click on a building opens its shortcut wheel; not while planting, moving, or in Edit City. */
    canvas.addEventListener('contextmenu', e => {
      e.preventDefault();
      if (editing || mode.name !== 'idle') return;
      const [x, y] = local(e), hit = hitProject(x, y);
      if (hit) { hideTip(); Wheel.open(hit, x, y); } else Wheel.close();
    });
    $('#camIcon').innerHTML = iconSvg('camera', 18);
    $('#camIcon').style.display = 'inline-flex';
    $('#btnPostcard').addEventListener('click', () => postcard());
    /* The options of the two drop-ups. Change an option's icon here and its button changes with it. */
    const LIGHTS = [{ value: 'auto', label: 'Auto', icon: 'clock', hint: 'Follows your clock' }, { value: 'day', label: 'Day', icon: 'sun' },
      { value: 'dusk', label: 'Dusk', icon: 'dusk' }, { value: 'night', label: 'Night', icon: 'moon' }];
    const BUBBLES = [{ value: 'all', label: 'Bubbles', icon: 'alert', hint: 'Red and yellow: what needs you' }, { value: 'red', label: 'Red only', icon: 'flag' },
      { value: 'tasks', label: 'Tasks', icon: 'task', hint: 'Open tasks in every project' }, { value: 'none', label: 'No bubbles', icon: 'close' }];
    const optionOf = (list, v) => list.find(o => o.value === v) || list[0];
    const lightUi = () => {
      const o = optionOf(LIGHTS, Light.mode);
      $('#lightLabel').textContent = o.value === 'auto' ? 'Auto: ' + Light.phase() : o.label;
      $('#lightIcon').innerHTML = iconSvg(o.icon, 14);
      $('#btnLight').title = 'Time of day: choose Auto, Day, Dusk, or Night';
    };
    $('#btnLight').addEventListener('click', () => dropUp($('#btnLight'), LIGHTS, Light.mode, v => {
      Light.setMode(v); lightUi(); Settings.refresh();
      toast(v === 'auto' ? 'The city follows your clock: day, dusk, night, and dawn.' : 'The city stays at ' + v + '.');
    }));
    Light.onChange(lightUi);
    lightUi();
    const bubUi = () => {
      const o = optionOf(BUBBLES, bubbleMode);
      $('#bubblesIcon').innerHTML = iconSvg(o.icon, 14);
      $('#bubblesLabel').textContent = o.label;
      $('#btnBubbles').title = 'Bubbles: ' + { all: 'red and yellow urgency', red: 'red urgency only', tasks: 'open tasks in every project', none: 'hidden' }[bubbleMode] + '. Click to choose.';
    };
    $('#btnBubbles').addEventListener('click', () => dropUp($('#btnBubbles'), BUBBLES, bubbleMode, v => {
      setBubbleMode(v); bubUi(); Settings.refresh();
      toast({ all: 'Showing red and yellow bubbles.', red: 'Showing red bubbles only.', tasks: 'Showing open tasks in every project.', none: 'Bubbles are hidden.' }[v]);
    }));
    bubUi();
    const trafficUi = () => {
      $('#trafficIcon').innerHTML = iconSvg('car', 14);
      $('#trafficLabel').textContent = Traffic.isOn() ? 'Traffic' : 'No traffic';
      $('#btnTraffic').setAttribute('aria-pressed', String(Traffic.isOn()));
      $('#btnTraffic').title = Traffic.isOn() ? 'Cars and people are out. Click to clear the streets.' : 'The streets are empty. Click to bring the traffic back.';
    };
    $('#btnTraffic').addEventListener('click', () => { Traffic.setOn(!Traffic.isOn()); trafficUi(); invalidate(); kick(); Settings.refresh(); });
    trafficUi();
    syncBar = () => { lightUi(); bubUi(); trafficUi(); };
    LIGHT_OPTIONS = LIGHTS; BUBBLE_OPTIONS = BUBBLES;
    $('#gearIcon').innerHTML = iconSvg('gear', 16);
    $('#btnSettings').addEventListener('click', () => Settings.toggle());
    $('#zoomIn').addEventListener('click', () => zoomStep(1));
    $('#zoomOut').addEventListener('click', () => zoomStep(-1));
    window.addEventListener('keydown', e => {
      if (e.ctrlKey || e.metaKey || e.altKey) return;
      if (typing(e) || FullView.isOpen() || Confirm.isOpen() || Panel.isOpen()) return;
      if (e.code === 'KeyQ' || e.code === 'BracketLeft' || e.code === 'KeyE' || e.code === 'BracketRight') {
        e.preventDefault();
        if (!e.repeat && mode.name === 'idle' && !editing) hop(e.code === 'KeyQ' || e.code === 'BracketLeft' ? -1 : 1);
        return;
      }
      /* F opens the selected building's shortcut wheel, round the building, and closes it again */
      if (e.code === 'KeyF') {
        e.preventDefault();
        if (e.repeat || mode.name !== 'idle' || editing) return;
        if (Wheel.close()) return;
        const p = App.selectedId && getProject(App.selectedId), a = p && anchors(p.id);
        if (a) Wheel.open(p, a.baseX, Math.round((a.topY + a.baseY) / 2));
        return;
      }
      /* Enter steps inside the selected building, unless a button or a link has the focus and takes it */
      if (e.key === 'Enter') {
        const t = e.target;
        if (e.repeat || e.shiftKey || (t && t !== document.body && t !== canvas) || mode.name !== 'idle' || editing) return;
        const id = Wheel.owner() || App.selectedId;
        if (id) { e.preventDefault(); Wheel.close(); FullView.open(id); }
        return;
      }
      const d = keyDir(e);
      if (!d || Wheel.isOpen()) return;                      // with the wheel open, the arrows move round it
      e.preventDefault(); keys.add(d); cancelGlide(); kick();
    });
    window.addEventListener('keyup', e => { const d = keyDir(e); if (d) keys.delete(d); });
    window.addEventListener('blur', () => keys.clear());
  }

  let syncBar = () => {}, LIGHT_OPTIONS = [], BUBBLE_OPTIONS = [];
  function anchors(id) {
    const p = getProject(id); if (!p) return null;
    let u = p.plot.u, v = p.plot.v;
    for (const [k, q] of displayLayout()) if (q.id === id) [u, v] = k.split(',').map(Number);
    const g = blockGeom(p, u, v);
    const [topX, topY] = worldToCss(g.X, g.top);
    const [baseX, baseY] = worldToCss(g.X, g.base);
    return { topX, topY, baseX, baseY };
  }
  /* The same block the map draws, alone on a canvas at 1x: used as the art preview. */
  const blockPreview = p => livePreview(p);

  return {
    init, invalidate, frameAll, setCam, select, deselect, glideTo, startPlace, cancelMode, anchors, blockPreview,
    resizeWorld, outerRingEmpty, canResize, addLine, canLine, lineEmpty, hop, postcard, applyWorld, blockPng,
    moving: () => mode.name === 'move',
    genericPreview: (id, scale = 2) => livePreview({ id: '__pick_' + id, art: { has: false, includesPlot: false }, generic: id }, scale),
    previewScale, profileScene, glideBeside,
    bubbleMode: () => bubbleMode, bubbleAt: id => eachBubble(b => b.p.id === id),
    crossMark, layout: () => displayLayout(), tileToWorld,
    props: () => propPlan(), propsDrawn: () => lastProps,
    _depthOrder: sprites => depthSort([], sprites),                // for the tests: figures among themselves, back to front
    lotInfo: (u, v) => (typeof LOTS !== 'undefined' && LOTS.length ? { id: LOTS[lotIndex(u, v)].id, flip: lotFlip(u, v) } : null),
    /* for the tests: a fingerprint of the ground's pixels in a box round a plot, in world pixels from its top corner */
    _groundHash: (u, v, x0, y0, w, hh) => {
      const [X, Y] = plotTop(u, v), d = worldCanvas.getContext('2d').getImageData(Math.round(X + x0 - WX0), Math.round(Y + y0 - WY0), w, hh).data;
      let x = 2166136261; for (let k = 0; k < d.length; k++) x = Math.imul(x ^ d[k], 16777619);
      return x >>> 0;
    },
    kick: () => kick(),
    thumb: p => {                                          // a still, full building, for the side bar
      let c;
      try { c = flatBlock(p, 0, 1).canvas; } catch (e) { c = mkCanvas(128, 96)[0]; }   // before the map is ready: an empty frame, redrawn later
      c.className = 'thumb';
      return c;
    },
    artFor,
    dropCache: id => { bcache.delete(id); flat.delete(id); },
    plotCss: (u, v) => { const [X, Y] = plotTop(u, v); return worldToCss(X, Y + 32); },
    camState: () => ({ x: cam.x, y: cam.y, z: cam.z, dpr }),
    _paints: () => paints,                                  // for the tests: how many times the map has been drawn
    editing: () => editing, setEditing, cyclePark,
    syncBar: () => syncBar(), setBubbleMode, lightOptions: () => LIGHT_OPTIONS, bubbleOptions: () => BUBBLE_OPTIONS,
    card: () => ({ ...card }), setCard, CARD_DEFAULT,
  };
})();
