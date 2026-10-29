/*
  City sounds (City Sounds, Rounds 1 and 2, section 6 of the knowledge file): made in code with the browser's own audio,
  as the sound board played them. Two builds (O1): the events at 0.1.78, tasks and alerts in the SNES era style (FM bells
  with a soft echo), the street party and the characters' voices in the 8-bit chip style (S1); and the city's own sounds
  at 0.1.79, its hum, street life and cleanup, in the SNES era style, rebuilt at 0.1.80 as a loop from the third sound board.
  - On by default, from the first click, tap or key, since a browser plays nothing before (C1).
  - The Sound button on the map's bar and in Settings, in step (C2): All sounds, Events only (no city sounds), No sound.
  - A volume for each group, as his Round 2 note groups them (C3): City sounds (the hum, street life and cleanup),
    Alerts (alerts and tasks), Character voices, and Music (the party).
  - Out of view, only Claude Code's alerts play, so the Claude folder is read while hidden too (C4).
  - From the view (C5): a sound with a place is panned by where it is on screen, a little louder zoomed in (his note on
    A1), and the party fades once its block is out of view; the city's loop gets louder as you zoom in, the hum aside.
  Kept in this browser (nullovation-city:sound): the choice and the volumes.
*/
const Sound = (() => {
  const KEY = 'nullovation-city:sound';
  const MODES = ['all', 'events', 'off'];
  const GROUPS = ['city', 'alerts', 'voices', 'music'];
  const VOL_DEF = 0.8, MASTER = 0.85;
  const STYLE = { city: 'snes', alerts: 'snes', voices: 'chip', music: 'chip' };   // S1: the city, tasks and alerts SNES, the party and voices chip
  const OPTIONS = [
    { value: 'all', label: 'All sounds', icon: 'sound', hint: 'Every sound the city makes' },
    { value: 'events', label: 'Events only', icon: 'soundEvents', hint: 'Tasks, alerts, voices and the party: not the city around them' },
    { value: 'off', label: 'No sound', icon: 'soundOff' }];
  const dflt = () => ({ mode: 'all', vol: Object.fromEntries(GROUPS.map(g => [g, VOL_DEF])) });
  function load() {
    const out = dflt();
    try {
      const v = JSON.parse(localStorage.getItem(KEY) || 'null');
      if (v && MODES.includes(v.mode)) out.mode = v.mode;
      if (v && v.vol) for (const g of GROUPS) { const n = +v.vol[g]; if (isFinite(n)) out.vol[g] = Math.min(1, Math.max(0, n)); }
    } catch (e) { /* the defaults */ }
    return out;
  }
  let set = load();
  const save = () => { try { localStorage.setItem(KEY, JSON.stringify(set)); } catch (e) { /* this visit only */ } };

  /* ---------- the engine ---------- */
  let ctx = null, master = null;
  const bus = {}, ins = {};                         // a gain per group, and the group's style chain into it
  const m2f = m => 440 * Math.pow(2, (m - 69) / 12);
  function rng(seed) { let s = (seed >>> 0) || 1; return () => { s ^= s << 13; s >>>= 0; s ^= s >>> 17; s ^= s << 5; s >>>= 0; return s / 4294967296; }; }
  function hash(str) { let x = 2166136261; for (const c of String(str)) { x ^= c.charCodeAt(0); x = Math.imul(x, 16777619); } return x >>> 0; }
  const kits = new WeakMap();
  function kit(c) {
    let k = kits.get(c); if (k) return k;
    const sr = c.sampleRate, r = rng(7), len = sr * 2;
    const mono = (n, fill) => { const b = c.createBuffer(1, n, sr); fill(b.getChannelData(0)); return b; };
    k = { pulse: {} };
    k.white = mono(len, d => { for (let i = 0; i < d.length; i++) d[i] = r() * 2 - 1; });
    k.chip = mono(len, d => { let v = 0; for (let i = 0; i < d.length; i++) { if (i % 4 === 0) v = r() < 0.5 ? -1 : 1; d[i] = v; } });
    k.brown = mono(len, d => { let v = 0; for (let i = 0; i < d.length; i++) { v = (v + 0.02 * (r() * 2 - 1)) / 1.02; d[i] = v * 3.5; } });
    k.smooth = mono(sr * 8, d => { const seg = Math.floor(sr * 0.18); let a = 0, b = r(); for (let i = 0; i < d.length; i++) { const j = i % seg; if (j === 0) { a = b; b = r() * r(); } d[i] = a + (b - a) * (1 - Math.cos(Math.PI * j / seg)) / 2; } });
    const n = Math.floor(sr * 1.6), ir = c.createBuffer(2, n, sr);
    for (let ch = 0; ch < 2; ch++) { const d = ir.getChannelData(ch); for (let i = 0; i < n; i++) d[i] = (r() * 2 - 1) * Math.pow(1 - i / n, 2.6); }
    k.ir = ir;
    const ns = Math.floor(sr * 0.9), irs = c.createBuffer(2, ns, sr);
    for (let ch = 0; ch < 2; ch++) { const d = irs.getChannelData(ch); for (let i = 0; i < ns; i++) d[i] = (r() * 2 - 1) * Math.pow(1 - i / ns, 3.5); }
    k.irSoft = irs;
    kits.set(c, k); return k;
  }
  function pulseWave(c, duty) {
    const k = kit(c); if (k.pulse[duty]) return k.pulse[duty];
    const H = 48, re = new Float32Array(H), im = new Float32Array(H);
    for (let n = 1; n < H; n++) { re[n] = 2 * Math.sin(2 * Math.PI * n * duty) / (Math.PI * n); im[n] = 2 * (1 - Math.cos(2 * Math.PI * n * duty)) / (Math.PI * n); }
    return (k.pulse[duty] = c.createPeriodicWave(re, im));
  }
  function biq(c, type, f, q) { const b = c.createBiquadFilter(); b.type = type; b.frequency.value = f; if (q != null) b.Q.value = q; return b; }
  /* The style's sound: SNES gets a soft top, an echo and a little room; chip stays raw. */
  function chain(c, dest, style) {
    const input = c.createGain();
    if (style === 'snes') {
      const lp = biq(c, 'lowpass', 5200, 0.5); input.connect(lp); lp.connect(dest);
      const dl = c.createDelay(1); dl.delayTime.value = 0.21;
      const fl = biq(c, 'lowpass', 2600, 0.5), fb = c.createGain(), wet = c.createGain();
      fb.gain.value = 0.33; wet.gain.value = 0.3;
      lp.connect(dl); dl.connect(fl); fl.connect(fb); fb.connect(dl); fl.connect(wet); wet.connect(dest);
      const cv = c.createConvolver(), rw = c.createGain(); cv.buffer = kit(c).ir; rw.gain.value = 0.18; lp.connect(cv); cv.connect(rw); rw.connect(dest);
    } else if (style === 'soft') {                     // the crowd's soft version: a little open air
      const lp = biq(c, 'lowpass', 8000, 0.5); input.connect(lp); lp.connect(dest);
      const cv = c.createConvolver(), rw = c.createGain(); cv.buffer = kit(c).irSoft; rw.gain.value = 0.14; lp.connect(cv); cv.connect(rw); rw.connect(dest);
    } else { const lp = biq(c, 'lowpass', 9000, 0.5); input.connect(lp); lp.connect(dest); }
    return input;
  }
  function masterChain(c, vol) {
    const g = c.createGain(), k = c.createDynamicsCompressor();
    g.gain.value = vol; k.threshold.value = -12; k.knee.value = 8; k.ratio.value = 5; k.attack.value = 0.003; k.release.value = 0.2;
    g.connect(k); k.connect(c.destination); return g;
  }

  /* ---------- the building blocks, as on the sound board ---------- */
  function route(A, node, o = {}) {
    if (o.dest) { node.connect(o.dest); return node; }
    if (o.pan != null) { const p = A.ctx.createStereoPanner(); p.pan.value = o.pan; node.connect(p); p.connect(A.out); return p; }
    node.connect(A.out); return node;
  }
  function envGain(A, t, { a = 0.005, peak = 0.3, dur = 0.3, curve = 'exp', hold = 0 } = {}) {
    const g = A.ctx.createGain(), p = g.gain;
    p.setValueAtTime(0.0001, t); p.linearRampToValueAtTime(peak, t + a); p.setValueAtTime(peak, t + a + hold);
    if (curve === 'exp') p.exponentialRampToValueAtTime(0.0001, t + Math.max(dur, a + hold + 0.01));
    else p.linearRampToValueAtTime(0, t + Math.max(dur, a + hold + 0.01));
    return g;
  }
  function mkOsc(A, type, f, t, end, o = {}) {
    const s = A.ctx.createOscillator();
    if (type.startsWith('pulse')) s.setPeriodicWave(pulseWave(A.ctx, parseFloat(type.slice(5)) || 0.25)); else s.type = type;
    const fr = s.frequency;
    if (o.from) { fr.setValueAtTime(f * o.from, t); fr.exponentialRampToValueAtTime(f, t + (o.glide || 0.04)); } else fr.setValueAtTime(f, t);
    if (o.to) fr.exponentialRampToValueAtTime(f * o.to, end);
    s.start(t); if (isFinite(end)) s.stop(end + 0.05);
    return s;
  }
  const TONE = { snes: 'triangle', chip: 'pulse0.25' };
  const loud = type => type.startsWith('pulse') || type === 'square' || type === 'sawtooth';
  function tone(A, t, f, dur, o = {}) {
    const type = o.type || TONE[A.style], chip = A.style === 'chip';
    const s = mkOsc(A, type, f, t, t + dur, o);
    const g = envGain(A, t, { a: o.a ?? 0.004, peak: (o.vol ?? 0.2) * (loud(type) ? 0.55 : 1), dur, curve: o.curve || (chip ? 'lin' : 'exp'), hold: o.hold ?? (chip ? dur * 0.4 : 0) });
    s.connect(g); return route(A, g, o);
  }
  /* A note on the style's instrument: an FM bell for SNES, a pulse for chip. */
  function note(A, t, f, dur, o = {}) {
    const vol = o.vol ?? 0.2, end = t + dur, c = A.ctx, mix = c.createGain();
    if (A.style === 'snes') {
      const ratio = o.ratio ?? 2, idx = o.index ?? 1.3;
      const car = mkOsc(A, 'sine', f, t, end, o), mod = mkOsc(A, 'sine', f * ratio, t, end, o), mg = c.createGain();
      mg.gain.setValueAtTime(f * idx, t); mg.gain.exponentialRampToValueAtTime(Math.max(f * idx * 0.06, 0.5), t + Math.max(dur * 0.6, 0.02));
      mod.connect(mg); mg.connect(car.frequency);
      const g = envGain(A, t, { a: 0.004, peak: vol, dur }); car.connect(g); g.connect(mix);
    } else {
      const type = o.chip || ('pulse' + (o.duty || 0.25));
      const s = mkOsc(A, type, f, t, end, o);
      const g = envGain(A, t, { a: 0.002, peak: vol * (type === 'triangle' ? 1 : 0.5), dur, curve: 'lin', hold: dur * 0.35 }); s.connect(g); g.connect(mix);
    }
    return route(A, mix, o);
  }
  function noise(A, t, dur, o = {}) {
    const c = A.ctx, k = kit(c), src = c.createBufferSource();
    src.buffer = k[A.style === 'chip' ? 'chip' : 'white']; src.loop = true;
    src.start(t, A.r() * 1.5); src.stop(t + dur + 0.05);
    let node = src;
    if (o.type) {
      const fl = biq(c, o.type, o.f, o.q ?? 0.7);
      if (o.fTo) { fl.frequency.setValueAtTime(o.f, t); fl.frequency.exponentialRampToValueAtTime(o.fTo, t + (o.fDur || dur)); }
      src.connect(fl); node = fl;
    }
    const g = envGain(A, t, { a: o.a ?? 0.005, peak: o.vol ?? 0.2, dur, curve: o.curve || 'exp', hold: o.hold || 0 });
    node.connect(g); return route(A, g, o);
  }
  function arp(A, t, notes, step, dur, vol, o = {}) { notes.forEach((m, i) => note(A, t + i * step, m2f(m), i === notes.length - 1 ? dur * 1.8 : dur, { vol, ...o })); return (notes.length - 1) * step + dur * 1.8; }
  function sparkle(A, t, n = 9, span = 0.7, vol = 0.1) {
    const P = [84, 86, 88, 91, 93, 96, 98, 100];
    for (let i = 0; i < n; i++) note(A, t + A.r() * span, m2f(P[Math.floor(A.r() * P.length)]), 0.3, { vol, pan: A.r() * 1.2 - 0.6 });
    return span + 0.5;
  }

  /* ---------- tasks, in the SNES era style ---------- */
  const TASKS = {
    tick: (A, t) => { arp(A, t, [84, 88, 91, 96], 0.055, 0.35, 0.2); sparkle(A, t + 0.2, 4, 0.35, 0.05); return 1.2; },
    coins: (A, t) => { note(A, t, m2f(83), 0.1, { vol: 0.2 }); note(A, t + 0.08, m2f(88), 0.5, { vol: 0.2 }); return 0.9; },
    repeat: (A, t) => {
      noise(A, t, 0.4, { type: 'bandpass', f: 500, fTo: 3000, fDur: 0.35, q: 1.2, vol: 0.12, a: 0.12 });
      note(A, t + 0.25, m2f(72), 0.25, { vol: 0.18 }); note(A, t + 0.38, m2f(79), 0.5, { vol: 0.18 });
      return 1.1;
    },
    added: (A, t) => { note(A, t, m2f(79), 0.25, { vol: 0.38, from: 0.6, glide: 0.03 }); return 0.6; },
    /* not on the board: starring rises to a high pair with a shimmer, archiving files the task away, downward */
    star: (A, t) => { note(A, t, m2f(93), 0.45, { vol: 0.17 }); note(A, t + 0.09, m2f(100), 0.7, { vol: 0.13 }); sparkle(A, t + 0.16, 5, 0.4, 0.05); return 1.2; },
    archive: (A, t) => {
      noise(A, t, 0.2, { type: 'bandpass', f: 1800, fTo: 600, q: 1, vol: 0.08, a: 0.03 });
      note(A, t + 0.05, m2f(76), 0.22, { vol: 0.17 }); note(A, t + 0.17, m2f(69), 0.5, { vol: 0.17 });
      return 0.9;
    },
  };
  /* ---------- alerts, in the SNES era style ---------- */
  function horn(A, t, dur) {
    const c = A.ctx, mix = c.createGain();
    [196, 247].forEach(f => { const s = mkOsc(A, 'sawtooth', f, t, t + dur), fl = biq(c, 'lowpass', 1400, 0.7); s.connect(fl); fl.connect(mix); });
    const g = envGain(A, t, { a: 0.02, peak: 0.16, dur, hold: dur * 0.6 }); mix.connect(g); route(A, g);
  }
  const ALERTS = {
    finished: (A, t) => arp(A, t, [76, 79, 84], 0.1, 0.3, 0.22),
    waiting: (A, t) => { note(A, t, m2f(79), 0.18, { vol: 0.2 }); note(A, t + 0.12, m2f(86), 0.35, { vol: 0.2 }); note(A, t + 0.6, m2f(79), 0.18, { vol: 0.12 }); note(A, t + 0.72, m2f(86), 0.35, { vol: 0.12 }); return 1.2; },
    error: (A, t) => { note(A, t, m2f(64), 0.3, { vol: 0.22, ratio: 1 }); note(A, t + 0.2, m2f(60), 0.6, { vol: 0.22, ratio: 1 }); return 1; },
    bubble: (A, t) => { tone(A, t, 840, 0.09, { from: 0.33, glide: 0.05, vol: 0.3 }); note(A, t + 0.05, m2f(81), 0.25, { vol: 0.2 }); return 0.5; },
    gusAlarm: (A, t) => { horn(A, t, 0.35); horn(A, t + 0.45, 0.35); return 1; },
  };

  /* ---------- the street party, in the 8-bit chip style: a cheer, then its music for the party's 30 seconds ---------- */
  function kick(A, t, vol = 0.45) {
    const s = mkOsc(A, 'triangle', 150, t, t + 0.3); s.frequency.exponentialRampToValueAtTime(48, t + 0.12);
    const g = envGain(A, t, { a: 0.002, peak: vol, dur: 0.28, curve: 'lin', hold: 0.06 }); s.connect(g); route(A, g);
  }
  function snare(A, t, vol = 0.24) { noise(A, t, 0.16, { type: 'bandpass', f: 2500, q: 0.6, vol, a: 0.001 }); tone(A, t, 185, 0.09, { vol: vol * 0.6, a: 0.001, to: 0.7 }); }
  function hat(A, t, vol = 0.05) { noise(A, t, 0.04, { type: 'highpass', f: 7000, vol, a: 0.001 }); }
  function cheer(A, t, vol = 0.35) {
    for (let i = 0; i < 6; i++) { const st = t + A.r() * 0.25, f = 600 + A.r() * 700; noise(A, st, 1.3 + A.r() * 0.6, { type: 'bandpass', f, fTo: f * 1.5, fDur: 0.4, q: 2.5, vol: vol * 0.35, a: 0.08, pan: A.r() * 1.6 - 0.8 }); }
    for (let i = 0; i < 2; i++) { const st = t + 0.2 + A.r() * 0.4; tone(A, st, 1900 + A.r() * 400, 0.35, { vol: vol * 0.22, from: 0.8, glide: 0.2, pan: A.r() * 1.4 - 0.7 }); }
  }
  const STEP = 60 / 118 / 4;                         // a sixteenth at 118 beats a minute
  const CHORDS = [[60, 64, 67], [59, 62, 67], [57, 60, 64], [57, 60, 65]], ROOTS = [48, 43, 45, 41];
  const MEL = [{ 0: 76, 3: 79, 6: 76, 8: 72 }, { 0: 74, 3: 79, 6: 71, 10: 74 }, { 0: 72, 3: 76, 6: 81, 8: 79 }, { 0: 81, 2: 79, 4: 77, 6: 76, 8: 72 }];
  /* The k-th sixteenth: four bars that come round every 8 seconds; the third time round drops the tune and most of the
     kick for a breather, the fourth brings them back. */
  function partyStep(A, tt, k) {
    const bar = Math.floor(k / 16) % 4, s = k % 16, rest = Math.floor(k / 64) % 4 === 2;
    if (s === 0 || (!rest && (s === 8 || s === 11))) kick(A, tt);
    if (!rest && (s === 4 || s === 12)) snare(A, tt);
    if (s % 2 === 1) hat(A, tt, s % 4 === 3 ? 0.07 : 0.045);
    if ([0, 3, 6, 8, 10, 14].includes(s)) note(A, tt, m2f(ROOTS[bar] + (s === 6 || s === 14 ? 12 : 0)), STEP * 1.6, { vol: 0.26, chip: 'triangle' });
    if ([2, 6, 10, 14].includes(s)) CHORDS[bar].forEach(n => note(A, tt, m2f(n), STEP * 1.2, { vol: 0.06, duty: 0.125 }));
    if (!rest && MEL[bar][s] != null) note(A, tt, m2f(MEL[bar][s]), STEP * 2.5, { vol: 0.14 });
  }

  /* ---------- the characters' voices, in the 8-bit chip style: a blip per letter as the line types out ---------- */
  const VOICES = {
    gus: { base: 98, range: 3, len: 0.075, every: 3, duty: 0.5 },             // low and gruff
    proxima: { base: 330, range: 5, len: 0.045, every: 2, radio: true },      // a bright radio chirp
    quill: { base: 523, range: 4, len: 0.05, every: 2, sparkle: true },       // a sparkle at the end
  };
  const LEADER_BASES = [131, 147, 165, 175, 196, 220, 247], DUTIES = [0.125, 0.25, 0.5];
  /* Each leader its own pitch and tone, from its id. */
  const voiceOf = who => VOICES[who] || (() => { const k = hash(who); return { base: LEADER_BASES[k % LEADER_BASES.length], range: 4, len: 0.055, every: 2, duty: DUTIES[(k >>> 8) % 3] }; })();
  const lettered = ch => /[\p{L}\p{N}]/u.test(ch);
  function radio(A, t) { noise(A, t, 0.05, { type: 'bandpass', f: 2600, q: 1.2, vol: 0.12, a: 0.001 }); tone(A, t, 1800, 0.035, { vol: 0.05, a: 0.001 }); }
  /* chars: the line's letters from the one typing next; step: seconds a letter. */
  function talk(A, t, who, chars, step) {
    const v = voiceOf(who), vol = 0.2;
    let dest = null;
    if (v.radio) { const hp = biq(A.ctx, 'highpass', 450, 0.7), lp = biq(A.ctx, 'lowpass', 3200, 0.7); hp.connect(lp); route(A, lp); dest = hp; }
    const t0 = t; if (v.radio) t += 0.06;
    let n = 0;
    chars.forEach((ch, i) => {
      if (!lettered(ch) || n++ % v.every) return;
      const semi = ((ch.toLowerCase().codePointAt(0) * 7) % (2 * v.range + 1)) - v.range, dur = Math.min(v.len, step * v.every * 0.92);
      tone(A, t + i * step, v.base * Math.pow(2, semi / 12), dur, { vol: vol * 0.75, type: 'pulse' + (v.duty || 0.25), hold: dur * 0.6, curve: 'lin', a: 0.002, dest });
    });
    const end = t + chars.length * step;
    if (v.radio) { radio(A, t0); radio(A, end + 0.04); }
    if (v.sparkle) [88, 91, 93, 96].forEach((m, j) => note(A, end + 0.05 + j * 0.06, m2f(m), 0.25, { vol: 0.06 }));
    return end - t0 + 0.5;
  }

  /* ---------- playing ---------- */
  function build() {
    if (ctx) return ctx;
    const AC = window.AudioContext || window.webkitAudioContext;
    if (!AC) return null;
    try { ctx = new AC(); } catch (e) { ctx = null; return null; }
    master = masterChain(ctx, MASTER);
    for (const g of GROUPS) { bus[g] = ctx.createGain(); bus[g].connect(master); ins[g] = chain(ctx, bus[g], STYLE[g]); }
    levels(true);
    return ctx;
  }
  /* The groups' volumes; out of view, only the alerts' group stays up, for Claude Code's (C4). */
  const level = {};                                     // what each group's gain is set to
  function levels(now = false) {
    if (!ctx) return;
    for (const g of GROUPS) {
      const v = level[g] = set.mode === 'off' || (g === 'city' && set.mode !== 'all') ? 0 : document.hidden && g !== 'alerts' ? 0 : set.vol[g];
      if (now) bus[g].gain.value = v; else bus[g].gain.setTargetAtTime(v, ctx.currentTime, 0.05);
    }
  }
  /* The first click, tap or key: the browser lets the city's audio start (C1). Off, nothing is made until it is on. */
  let unlockedAt = 0;
  function unlock() {
    if (set.mode === 'off') return;
    if (!build()) return;
    unlockedAt = Date.now();
    if (ctx.state === 'suspended') ctx.resume().catch(() => {});
  }
  /* Running, or just let start by a click and about to run: what is played then waits the moment it takes. */
  const running = () => !!ctx && (ctx.state === 'running' || (ctx.state === 'suspended' && Date.now() - unlockedAt < 1000));
  /* Whether a sound of this group may play now: never with No sound, nor at no volume; out of view only Claude Code's. */
  function may(group, claude = false) {
    if (set.mode === 'off' || !running()) return false;
    if (group === 'city' && set.mode !== 'all') return false;               // Events only leaves the city's own sounds out
    if (!(set.vol[group] > 0)) return false;
    if (document.hidden && !claude) return false;
    return true;
  }
  /* What a sound plays through: a gain and a pan of its own, into its group's style. */
  function voiceFor(group, pan = 0, gain = 1, seed = 0, c = ctx, into = ins[group]) {
    const g = c.createGain(), p = c.createStereoPanner();
    g.gain.value = gain; p.pan.value = pan; g.connect(p); p.connect(into);
    return { A: { ctx: c, out: g, style: STYLE[group], r: rng(seed || (Date.now() ^ hash(group))) }, g, p };
  }
  const drop = (v, secs) => setTimeout(() => { try { v.p.disconnect(); } catch (e) { /* gone */ } }, (secs + 3) * 1000);
  const log = [];
  function note2log(id, group, pan, gain) {
    log.push({ id, group, pan: Math.round(pan * 100) / 100, gain: Math.round(gain * 100) / 100, hidden: document.hidden, at: Date.now() });
    if (log.length > 200) log.shift();
  }
  function play(id, group, fn, { pan = 0, gain = 1, claude = false } = {}) {
    if (!may(group, claude)) return false;
    const v = voiceFor(group, pan, gain, hash(id) ^ Date.now());
    drop(v, fn(v.A, ctx.currentTime + 0.03));
    note2log(id, group, pan, gain);
    return true;
  }

  /* ---------- from the view (C5) ---------- */
  /* Where a building is on screen: the pan from its place across the map, a little louder zoomed in (1x 0.8, 4x 1.0, 8x
     1.1), and how far out of view it is (1 in view, down to 0.3 a map's width away). */
  function placeOf(p) {
    const wrap = $('#mapWrap');
    if (!p || !p.plot || !wrap || typeof MapView === 'undefined' || !MapView.plotCss) return { pan: 0, zoom: 1, near: 1 };
    const W = wrap.clientWidth || 1, H = wrap.clientHeight || 1, [x, y] = MapView.plotCss(p.plot.u, p.plot.v), cam = MapView.camState();
    const z = Math.min(8, Math.max(1, cam.z / (cam.dpr || 1)));
    const out = Math.max(0, -x, x - W, -y, y - H);
    return { pan: Math.max(-1, Math.min(1, (x - W / 2) / (W / 2))) * 0.7, zoom: 0.8 + 0.1 * Math.log2(z), near: Math.max(0.3, 1 - out / W) };
  }

  /* ---------- the events ---------- */
  const COIN_KINDS = new Set(['coins', 'dollars']);
  /* A tick anywhere: a repeat moving on, else its chime, coins for a building whose particles are coins or dollars. */
  function ticked(p, t) {
    const pl = placeOf(p), id = t.repeat ? 'repeat' : COIN_KINDS.has(p.particles) ? 'coins' : 'tick';
    play(id, 'alerts', TASKS[id], { pan: pl.pan, gain: pl.zoom });
  }
  /* A task added from the line over the map, starred or archived by hand. */
  function task(id, p) { const pl = placeOf(p); play(id, 'alerts', TASKS[id], { pan: pl.pan * 0.5, gain: pl.zoom }); }
  /* Claude Code finishing, waiting for you or stopping on an error: out of view too (C4), from its building's side. */
  let lastClaude = 0, lastKind = {};
  function claude(state, p) {
    const id = { done: 'finished', waiting: 'waiting', failed: 'error' }[state];
    if (!id || Date.now() - (lastKind[id] || 0) < 1500) return false;
    const pl = placeOf(p);
    if (!play(id, 'alerts', ALERTS[id], { pan: pl.pan * 0.5, claude: true })) return false;
    lastKind[id] = lastClaude = Date.now();
    return true;
  }
  /* A bubble opening by itself, unless Claude's alert just said it; Gus's alarm at 50 and 200 has its own horn. */
  function bubble() { if (Date.now() - lastClaude > 2500) play('bubble', 'alerts', ALERTS.bubble); }
  function gusAlarm() { play('gusAlarm', 'alerts', ALERTS.gusAlarm); }

  /* A line typing out, a blip per letter; stop() when the bubble closes before it ends. */
  function say(who, chars, step) {
    if (!who || !chars || !chars.length || !may('voices')) return null;
    const v = voiceFor('voices', 0, 1, hash(who));
    drop(v, talk(v.A, ctx.currentTime + 0.02, who, chars, step));
    note2log('voice:' + who, 'voices', 0, 1);
    return { stop: () => { try { v.g.gain.setTargetAtTime(0, ctx.currentTime, 0.02); } catch (e) { /* gone */ } } };
  }

  /* The street party: the cheer, then its music for as long as it lasts, quieter once its block leaves the view. */
  const parties = new Map();
  function party(p, ms) {
    stopParty(p.id);
    if (!may('music')) return;
    const pl = placeOf(p), v = voiceFor('music', pl.pan, pl.zoom * pl.near, hash(p.id) ^ Date.now());
    const music = ctx.createGain(); music.gain.value = 0.4; music.connect(v.g);
    const M = { ...v.A, out: music }, t0 = ctx.currentTime + 0.05, end = t0 + ms / 1000;
    cheer(v.A, t0, 0.35);
    const pt = { pid: p.id, v, M, t0: t0 + 0.25, end, k: 0, timer: 0 };
    const pump = () => {
      if (!ctx) return;
      const now = ctx.currentTime, q = getProject(pt.pid);
      if (!q || now > pt.end + 0.3) { stopParty(pt.pid); return; }
      const at = placeOf(q);
      v.p.pan.setTargetAtTime(at.pan, now, 0.2);
      v.g.gain.setTargetAtTime(at.zoom * at.near, now, 0.2);
      if (document.hidden) { pt.k = Math.max(pt.k, Math.ceil((now - pt.t0) / STEP)); return; }   // out of view: no music (C4), and none owed
      while (pt.t0 + pt.k * STEP < Math.min(now + 0.6, pt.end - 0.2)) { const tt = pt.t0 + pt.k * STEP; if (tt >= now) partyStep(M, tt, pt.k); pt.k++; }
    };
    music.gain.setValueAtTime(0.4, Math.max(t0, end - 1.5)); music.gain.linearRampToValueAtTime(0.0001, end);
    pump();
    pt.timer = setInterval(pump, 150);
    parties.set(p.id, pt);
    note2log('party', 'music', pl.pan, pl.zoom * pl.near);
  }
  function stopParty(pid) {
    const pt = parties.get(pid); if (!pt) return;
    parties.delete(pid); clearInterval(pt.timer);
    try { pt.v.g.gain.setTargetAtTime(0, ctx.currentTime, 0.08); } catch (e) { /* gone */ }
    drop(pt.v, 0.5);
  }


  /* ---------- the city's own sounds (0.1.80): a loop, as the third sound board played it ---------- */
  /* His picks on the third board (section 6, City Sounds): the hum, Less air by day and subtler at night, crossfading with
     the time of day and rising and falling with no pattern; the server room and the relays on top of it; now and then a
     street sound, on two layers by day and one at night, every 3 to 5 seconds; the crowd on a layer of its own at the
     closest zoom; and the computers at work and the power hum while Claude Code works. The street and the buildings at
     work get louder as you zoom in, the hum stays. It is not tied to the cars on the map (0.1.79 followed them, and he
     found it a hiss): it follows the time of day, the zoom, Traffic and who is out. */
  const clamp01 = x => Math.max(0, Math.min(1, x));
  const under = (A, v) => { const g = A.ctx.createGain(); g.gain.value = v; g.connect(A.out); return { ...A, out: g, gain: g.gain }; };
  const HUM = { day: { f: 65.4, lp: 220, level: 0.1, tone: 0.05 }, night: { f: 55, lp: 240, level: 0.06, tone: 0.025 } };
  const STREET = 0.55;                                        // the street under the hum, as on the boards
  const ZOOM_LEVEL = [[1.5, 0.4], [2.5, 0.6], [3.5, 0.75], [5, 0.9]];   // 1x 40%, 2x 60%, 3x 75%, 4x 90%, 6x and 8x 100%
  /* The zoom's level, by the building pixel's size on screen, so a phone at its own zoom reads as a computer does. */
  function zoomLevel() {
    if (typeof MapView === 'undefined' || !MapView.camState) return 0.6;
    const c = MapView.camState(), z = c.z / (c.dpr || 1);
    for (const [below, v] of ZOOM_LEVEL) if (z < below) return v;
    return 1;
  }
  /* The hum: a low rumble with hardly any air in it, under one low note and its octave. */
  function humBed(A, t, h) {
    const c = A.ctx, nodes = [], mix = c.createGain(); mix.gain.value = 0; mix.connect(A.out);
    const s = c.createBufferSource(); s.buffer = kit(c).brown; s.loop = true; s.start(t, A.r());
    const lp = biq(c, 'lowpass', h.lp, 0.6), g = c.createGain(); g.gain.value = h.level;
    s.connect(lp); lp.connect(g); g.connect(mix);
    const lfo = c.createOscillator(), lg = c.createGain(); lfo.frequency.value = 0.09; lg.gain.value = h.level * 0.35; lfo.connect(lg); lg.connect(g.gain); lfo.start(t);
    const d = mkOsc(A, 'sine', h.f, t, Infinity), d2 = mkOsc(A, 'sine', h.f * 2, t, Infinity), dg = c.createGain(), dg2 = c.createGain();
    dg.gain.value = h.tone; dg2.gain.value = h.tone / 3; d.connect(dg); d2.connect(dg2); dg.connect(mix); dg2.connect(mix);
    nodes.push(s, lfo, d, d2);
    return { nodes, mix };
  }
  /* Rise and fall: the hum drifts down and up, each stretch 4 to 12 seconds to between 45% and 100%, never twice alike. */
  function drift(cs, to) {
    while (cs.driftAt < to) { const len = 4 + cs.A.r() * 8; cs.hum.gain.linearRampToValueAtTime(0.45 + cs.A.r() * 0.55, cs.driftAt + len); cs.driftAt += len; }
  }

  /* Now and then. The honks: three ways, low and muffled, one picked at random each time. */
  function hornTone(A, t, dur, fs, lp, vol, pan, type = 'triangle') {
    const c = A.ctx, mix = c.createGain(), fl = biq(c, 'lowpass', lp, 0.7); mix.connect(fl);
    fs.forEach(f => mkOsc(A, type, f, t, t + dur).connect(mix));
    const g = envGain(A, t, { a: 0.02, peak: vol, dur, hold: dur * 0.6, curve: 'lin' }); fl.connect(g); route(A, g, { pan });
  }
  const HONKS = {
    double: (A, t, pan) => { hornTone(A, t, 0.2, [311, 392], 900, 0.13, pan); hornTone(A, t + 0.3, 0.26, [311, 392], 900, 0.13, pan); },
    far: (A, t, pan) => hornTone(A, t, 0.45, [262, 330], 650, 0.11, pan),
    beep: (A, t, pan) => { hornTone(A, t, 0.12, [233, 294], 700, 0.1, pan, 'square'); hornTone(A, t + 0.19, 0.14, [233, 294], 700, 0.1, pan, 'square'); },
  };
  const HONK_KEYS = Object.keys(HONKS), anyHonk = A => HONKS[HONK_KEYS[Math.floor(A.r() * HONK_KEYS.length)]];
  function passing(A, t, dur, panFrom, panTo) {
    const c = A.ctx, p = c.createStereoPanner(), g = c.createGain();
    p.pan.setValueAtTime(panFrom, t); p.pan.linearRampToValueAtTime(panTo, t + dur); p.connect(A.out);
    g.gain.setValueAtTime(0.0001, t); g.gain.exponentialRampToValueAtTime(1, t + dur / 2); g.gain.exponentialRampToValueAtTime(0.0001, t + dur); g.connect(p);
    return g;
  }
  /* A car: its engine going by, no rush of air, and a honk on the way. */
  function carPass(A, t, dir) {
    const dur = 2.6, mid = t + dur / 2, c = A.ctx, g = passing(A, t, dur, -0.9 * dir, 0.9 * dir);
    const e = mkOsc(A, 'triangle', 58 * 1.06, t, t + dur);
    e.frequency.setValueAtTime(58 * 1.06, mid - 0.15); e.frequency.linearRampToValueAtTime(58 * 0.92, mid + 0.15);
    const el = biq(c, 'lowpass', 320, 0.9), eg = c.createGain();
    el.frequency.setValueAtTime(220, t); el.frequency.linearRampToValueAtTime(420, mid); el.frequency.linearRampToValueAtTime(220, t + dur);
    eg.gain.value = 0.34; e.connect(el); el.connect(eg); eg.connect(g);
    anyHonk(A)(A, t + dur * 0.35 + A.r() * 0.6, -0.3 * dir);
    return dur;
  }
  function thump(A, t, vol, pan) {
    const s = mkOsc(A, 'sine', 120, t, t + 0.18); s.frequency.exponentialRampToValueAtTime(55, t + 0.12);
    const g = envGain(A, t, { a: 0.002, peak: vol, dur: 0.18 }); s.connect(g); route(A, g, { pan });
    noise(A, t, 0.03, { type: 'lowpass', f: 900, vol: vol * 0.5, a: 0.001, pan });
  }
  /* The bus at its stop, as on the first board, which he loves: engine, brakes, air, doors. No ding (his note on O1). */
  function busStop(A, t, pan) {
    const c = A.ctx, e = mkOsc(A, 'triangle', 50, t, t + 1.6);
    e.frequency.linearRampToValueAtTime(40, t + 1.3);
    const el = biq(c, 'lowpass', 300, 0.8), eg = envGain(A, t, { a: 0.4, peak: 0.24, dur: 1.6, hold: 0.6 });
    e.connect(el); el.connect(eg); route(A, eg, { pan });
    tone(A, t + 0.7, 2300, 0.35, { vol: 0.035, to: 0.94, a: 0.05, hold: 0.15, pan });
    noise(A, t + 1.05, 0.7, { type: 'highpass', f: 2500, vol: 0.12, a: 0.005, pan });
    thump(A, t + 1.35, 0.28, pan);
    return 2.4;
  }
  /* A drone passing, as on the first board. */
  function dronePass(A, t, dir) {
    const dur = 3, c = A.ctx, g = passing(A, t, dur, -0.8 * dir, 0.8 * dir), trem = c.createGain(); trem.gain.value = 0.6; trem.connect(g);
    const lfo = mkOsc(A, 'square', 36, t, t + dur), lg = c.createGain(); lg.gain.value = 0.4; lfo.connect(lg); lg.connect(trem.gain);
    const s = mkOsc(A, 'triangle', 185 * 1.03, t, t + dur);
    s.frequency.setValueAtTime(185 * 1.03, t + dur * 0.45); s.frequency.linearRampToValueAtTime(185 * 0.97, t + dur * 0.55);
    const fl = biq(c, 'lowpass', 2400, 1), sg = c.createGain(); sg.gain.value = 0.32; s.connect(fl); fl.connect(sg); sg.connect(trem);
    noise(A, t, dur, { type: 'bandpass', f: 2200, q: 0.8, vol: 0.09, a: 0.01, hold: dur * 0.9, dest: trem });
    return dur;
  }
  /* The cyclist's bell, as on the first board: two rings. */
  function bell(A, t, pan) { [0, 0.22].forEach(d => note(A, t + d, 2093, 0.6, { vol: 0.16, ratio: 1.41, index: 1.2, pan })); return 1; }
  /* The crowd round a busy building, the soft version: four voices through vowel shapes, and footsteps. */
  const VOWELS = { a: [800, 1200], e: [420, 2000], i: [300, 2400], o: [460, 820], u: [330, 700] };
  const vowelOf = ch => { const k = ch.toLowerCase(); if ('aeiou'.includes(k)) return k; if (k === 'y') return 'i'; if (k === 'w') return 'u'; return 'aeiou'[k.charCodeAt(0) % 5]; };
  function voiceBlip(A, t, f, dur, ch, vol, pan) {
    const c = A.ctx, s = mkOsc(A, 'sawtooth', f, t, t + dur, { from: 1.05, glide: dur }), [f1, f2] = VOWELS[vowelOf(ch)];
    const b1 = biq(c, 'bandpass', f1, 6), b2 = biq(c, 'bandpass', f2, 9), g2 = c.createGain();
    const g = envGain(A, t, { a: 0.01, peak: vol * 3.2, dur, hold: dur * 0.4 });
    g2.gain.value = 0.6; s.connect(b1); s.connect(b2); b1.connect(g); b2.connect(g2); g2.connect(g);
    route(A, g, { pan });
  }
  function crowd(A, t) {
    const L = 'abdeghiklmnoprstuy';
    for (let p = 0; p < 4; p++) {
      let x = t + A.r() * 1.5; const pan = A.r() * 1.4 - 0.7, base = 140 + A.r() * 160;
      for (let w = 0; w < 2; w++) {
        let text = ''; for (let k = 0, n = 4 + Math.floor(A.r() * 4); k < n; k++) { for (let i = 0, m = 2 + Math.floor(A.r() * 5); i < m; i++) text += L[Math.floor(A.r() * L.length)]; text += ' '; }
        const step = Math.min(0.026, 1.8 / text.length); let n = 0;
        [...text].forEach((ch, i) => { if (ch === ' ' || n++ % 2) return; const semi = ((ch.charCodeAt(0) * 7) % 9) - 4; voiceBlip(A, x + i * step, base * Math.pow(2, semi / 12), Math.min(0.06, step * 1.84), ch, 0.08, pan); });
        x += text.length * step + 0.5 + A.r() * 0.6;
      }
    }
    let pan = -0.3; for (let x = t; x < t + 4; x += 0.27 + A.r() * 0.05) { noise(A, x, 0.05, { type: 'lowpass', f: 600, vol: 0.1, a: 0.002, pan }); pan = -pan; }
    return 4.6;
  }
  /* The hover garbage truck, as on the first board, landing quietly: no burst of air (his note on O1). */
  function truckSound(A, t, side) {
    const dur = 4.2, c = A.ctx, p = c.createStereoPanner(), g = c.createGain(), wob = c.createGain();
    p.pan.setValueAtTime(side, t); p.pan.linearRampToValueAtTime(side * 0.25, t + 2.8); p.connect(A.out);
    g.gain.setValueAtTime(0.0001, t); g.gain.exponentialRampToValueAtTime(1, t + 2.4); g.gain.setValueAtTime(1, t + 3.2); g.gain.exponentialRampToValueAtTime(0.0001, t + dur); g.connect(p);
    wob.gain.value = 0.85; wob.connect(g);
    const lfo = mkOsc(A, 'sine', 5.5, t, t + dur), lg = c.createGain(); lg.gain.value = 0.15; lfo.connect(lg); lg.connect(wob.gain);
    [72, 144.6].forEach((f, i) => {
      const s = mkOsc(A, 'triangle', f, t, t + dur); s.frequency.setValueAtTime(f, t + 2.8); s.frequency.exponentialRampToValueAtTime(f * 0.78, t + 3.7);
      const fl = biq(c, 'lowpass', 520, 0.8), sg = c.createGain(); sg.gain.value = 0.18 * (i ? 0.5 : 1); s.connect(fl); fl.connect(sg); sg.connect(wob);
    });
    noise(A, t, dur - 0.3, { type: 'bandpass', f: 420, q: 0.7, vol: 0.12, a: 1.5, hold: 1.5, dest: wob });
    return dur;
  }

  /* The crickets at night: each plays 4 to 8 seconds, then rests about as long, then plays again. */
  const cricketsOf = (A, t) => [{ f: 4300, pan: -0.5, gap: [0.62, 0.1] }, { f: 3900, pan: 0.6, gap: [0.9, 0.25] }]
    .map(k => ({ ...k, on: true, until: t + 4 + A.r() * 4, next: t + 0.3 + A.r() * 0.5 }));
  function crickets(A, cs, from, to) {
    for (const k of cs.crickets) {
      while (k.next < to) {
        if (k.next >= k.until) { k.on = !k.on; k.until = k.next + 4 + A.r() * 4; if (!k.on) { k.next = k.until; continue; } }
        const x = Math.max(k.next, from);
        for (let i = 0; i < 3; i++) note(A, x + i * 0.042, k.f / 2, 0.03, { vol: 0.035, pan: k.pan, ratio: 2, index: 0.4 });
        counts.cricket = (counts.cricket || 0) + 1;
        k.next += k.gap[0] + A.r() * k.gap[1];
      }
    }
  }
  /* Buildings at work. The relays: runs of 2 to 4, 1.6 to 6 seconds apart, two in three clicks and one in three knocks. */
  const RELAYS = {
    clicks: (A, t, pan) => { noise(A, t, 0.01, { type: 'bandpass', f: 1800, q: 1.2, vol: 0.5, a: 0.0005, pan }); tone(A, t, 1100, 0.012, { type: 'sine', vol: 0.08, a: 0.0005, pan }); },
    knocks: (A, t, pan) => { tone(A, t, 700, 0.03, { type: 'sine', vol: 0.32, a: 0.0005, to: 0.36, pan }); noise(A, t, 0.015, { type: 'lowpass', f: 1500, vol: 0.22, a: 0.0005, pan }); },
  };
  function relays(A, cs, from, to) {
    while (cs.relayAt < to) {
      const x = Math.max(cs.relayAt, from), n = 2 + Math.floor(A.r() * 3), pan = A.r() * 1.2 - 0.6, kind = A.r() < 1 / 3 ? 'knocks' : 'clicks';
      for (let k = 0; k < n; k++) RELAYS[kind](A, x + k * (0.05 + A.r() * 0.04), pan);
      counts['relay:' + kind] = (counts['relay:' + kind] || 0) + 1;
      cs.relayAt += 1.6 + A.r() * 4.4;
    }
  }
  /* The server room, all the time: a steady electric hum with a slow beat in it. */
  function serverRoom(A, t) {
    const c = A.ctx, nodes = [], lp = biq(c, 'lowpass', 600, 0.7), g = c.createGain(); g.gain.setValueAtTime(0.0001, t); g.gain.linearRampToValueAtTime(1, t + 1.5); lp.connect(g); route(A, g);
    [[100, 0.016], [100.6, 0.016], [200, 0.006], [300, 0.003]].forEach(([f, v]) => { const o = mkOsc(A, 'sine', f, t, Infinity), og = c.createGain(); og.gain.value = v; o.connect(og); og.connect(lp); nodes.push(o); });
    const lfo = mkOsc(A, 'sine', 0.13, t, Infinity), lg = c.createGain(); lg.gain.value = 0.25; lfo.connect(lg); lg.connect(g.gain); nodes.push(lfo);
    return nodes;
  }
  /* While Claude Code works: the power hum, a low electric drone that swells and settles ... */
  function powerHum(A, t) {
    const c = A.ctx, nodes = [], lp = biq(c, 'lowpass', 260, 0.8), g = c.createGain(); g.gain.setValueAtTime(0.0001, t); g.gain.linearRampToValueAtTime(1, t + 1.5);
    const sw = mkOsc(A, 'sine', 0.05, t, Infinity), swg = c.createGain(); swg.gain.value = 140; sw.connect(swg); swg.connect(lp.frequency); nodes.push(sw);
    lp.connect(g); route(A, g);
    const o = mkOsc(A, 'sawtooth', 60, t, Infinity), og = c.createGain(); og.gain.value = 0.05; o.connect(og); og.connect(lp); nodes.push(o);
    const tr = mkOsc(A, 'sine', 0.25, t, Infinity), tg = c.createGain(); tg.gain.value = 0.2; tr.connect(tg); tg.connect(g.gain); nodes.push(tr);
    return nodes;
  }
  /* ... and the computers at work, soft little bleeps in bursts. */
  function computers(A, cs, from, to) {
    const P = [60, 62, 64, 67, 69, 72];
    while (cs.compAt < to) {
      const x = Math.max(cs.compAt, from);
      if (cs.burst <= 0) { cs.burst = 6 + Math.floor(A.r() * 14); cs.cpan = A.r() * 1.2 - 0.6; }
      note(A, x, m2f(P[Math.floor(A.r() * P.length)]), 0.05, { vol: 0.09, ratio: 1, index: 0.5, pan: cs.cpan });
      counts.bleep = (counts.bleep || 0) + 1;
      cs.burst--; cs.compAt += cs.burst > 0 ? 0.08 + A.r() * 0.12 : 1.2 + A.r() * 3;
    }
  }

  /* ---------- the loop, a lookahead of 0.6 seconds every 200 ms ---------- */
  let city = null;
  const counts = {};
  const cityOn = () => may('city') && typeof Traffic !== 'undefined' && !document.hidden;
  function cityStart() {
    const t = ctx.currentTime + 0.05, A = { ctx, out: ins.city, style: 'snes', r: rng(Date.now() >>> 0) };
    const hum = under(A, 1), street = under(A, 0), work = under(A, 0), crk = under(A, 0);
    hum.gain.setValueAtTime(0.0001, t); hum.gain.linearRampToValueAtTime(1, t + 1.5);
    const day = humBed(hum, t, HUM.day), night = humBed(hum, t, HUM.night);
    city = { A, hum, street, work, crk, C: { ...street, out: chain(ctx, street.out, 'soft') }, day, night,
      nodes: [...day.nodes, ...night.nodes, ...serverRoom(work, t)], upto: t, driftAt: t + 1.5,
      layers: [t + 1 + A.r() * 2, t + 2.5 + A.r() * 2], crowdAt: t, relayAt: t + 0.6, compAt: t, burst: 0, crickets: cricketsOf(A, t), power: null, zl: 0, dark: 0, layersOn: 0 };
    note2log('hum', 'city', 0, 1);
  }
  function cityStop() {
    if (!city) return;
    const cs = city, now = ctx.currentTime; city = null;
    for (const g of [cs.hum, cs.street, cs.work, cs.crk]) g.gain.cancelScheduledValues(now), g.gain.setTargetAtTime(0, now, 0.1);
    const nodes = cs.nodes.concat(cs.power ? cs.power.nodes : []);
    setTimeout(() => { for (const n of nodes) { try { n.stop(); } catch (e) { /* gone */ } } for (const g of [cs.hum, cs.street, cs.work, cs.crk]) { try { g.out.disconnect(); } catch (e) { /* gone */ } } }, 700);
  }
  /* What the street may play now: nothing with Traffic off or on Still; each kind only while it is out (Settings, Life). */
  function streetKinds() {
    if (!Traffic.active()) return { kinds: [], crowd: false };
    const c = DB.city, kinds = [];
    if (c.cars) kinds.push('car', 'honk');
    if (c.buses) kinds.push('bus');
    if (c.drones) kinds.push('drone');
    if (c.cyclists) kinds.push('bell');
    return { kinds, crowd: !!c.walkers && !!MapView.atMaxZoom && MapView.atMaxZoom() };
  }
  function nowAndThen(cs, kinds, t) {
    const E = cs.street, k = kinds[Math.floor(E.r() * kinds.length)], dir = E.r() < 0.5 ? 1 : -1, pan = E.r() * 1.2 - 0.6;
    if (k === 'car') carPass(E, t, dir);
    else if (k === 'honk') anyHonk(E)(E, t, pan);
    else if (k === 'bus') busStop(E, t, pan);
    else if (k === 'drone') dronePass(E, t, dir);
    else bell(E, t, pan);
    note2log(k, 'city', pan, Math.round(STREET * cs.zl * 100) / 100);
  }
  /* Claude Code working anywhere in the city brings the power hum and the computers; they fade once it stops. */
  function claudeWorks(cs, now) {
    const on = typeof ClaudeWork !== 'undefined' && !!ClaudeWork.working && ClaudeWork.working();
    if (on && !cs.power) { const P = under(cs.work, 1); cs.power = { P, nodes: powerHum(P, now + 0.05) }; cs.compAt = now + 0.3; note2log('claude-works', 'city', 0, 1); }
    else if (!on && cs.power) {
      const p = cs.power; cs.power = null; p.P.gain.setTargetAtTime(0, now, 0.3);
      setTimeout(() => { for (const n of p.nodes) { try { n.stop(); } catch (e) { /* gone */ } } }, 2500);
    }
  }
  function cityTick() {
    if (!cityOn()) { cityStop(); return; }
    if (!city) cityStart();
    const cs = city, now = ctx.currentTime, to = now + 0.6, from = Math.max(cs.upto, now), dark = typeof Light !== 'undefined' ? Light.t : 0, zl = zoomLevel();
    cs.day.mix.gain.setTargetAtTime(1 - dark, now, 0.6); cs.night.mix.gain.setTargetAtTime(dark, now, 0.6);
    cs.street.gain.setTargetAtTime(STREET * zl, now, 0.15); cs.work.gain.setTargetAtTime(zl, now, 0.15);
    cs.crk.gain.setTargetAtTime(clamp01((dark - 0.5) * 2), now, 0.6);
    cs.zl = zl; cs.dark = dark;
    claudeWorks(cs, now);
    if (to <= cs.upto) return;
    drift(cs, to);
    if (dark > 0.5) crickets(cs.crk, cs, from, to); else for (const k of cs.crickets) k.next = Math.max(k.next, to);
    relays(cs.work, cs, from, to);
    if (cs.power) computers(cs.work, cs, from, to);
    const out = streetKinds(), n = dark > 0.5 ? 1 : 2;           // two layers by day, one at night, every 3 to 5 seconds
    cs.layersOn = out.kinds.length ? n : 0;
    cs.layers = cs.layers.map((at, i) => {
      if (i >= n || !out.kinds.length) return Math.max(at, to);
      while (at < to) { nowAndThen(cs, out.kinds, Math.max(at, from)); at += 3 + cs.A.r() * 2; }
      return at;
    });
    /* the crowd: its own layer at the closest zoom, every 3 to 9 seconds; zooming in brings the first at once */
    if (!out.crowd) cs.crowdAt = Math.max(cs.crowdAt, to);
    else while (cs.crowdAt < to) { crowd(cs.C, Math.max(cs.crowdAt, from)); note2log('crowd', 'city', 0, Math.round(STREET * zl * 100) / 100); cs.crowdAt += 3 + cs.A.r() * 6; }
    cs.upto = to;
  }
  /* A garbage truck setting off: its hover hum, from its building's side, while the city's sounds play. */
  function truck(p) {
    if (!city) return;
    const side = placeOf(p).pan >= 0 ? 1 : -1;
    play('truck', 'city', (A, t) => truckSound(A, t, side), { gain: STREET * zoomLevel() });
  }

  const CITY_IDS = new Set(['hum-day', 'hum-night', 'car', 'honk-double', 'honk-far', 'honk-beep', 'bus', 'drone', 'bell', 'crowd', 'truck', 'relays', 'server', 'computers', 'power', 'crickets']);
  function measure(id, buf, sr) {
    let peak = 0, sum = 0, last = 0, bad = 0;
    for (let ch = 0; ch < 2; ch++) { const d = buf.getChannelData(ch); for (let i = 0; i < d.length; i++) { const x = d[i]; if (!isFinite(x)) { bad++; continue; } const a = Math.abs(x); if (a > peak) peak = a; sum += x * x; if (a > 0.002 && i > last) last = i; } }
    return { id, peak: +peak.toFixed(3), rmsDb: +(10 * Math.log10(sum / (2 * Math.max(last, 1)) + 1e-12)).toFixed(1), seconds: +(last / sr).toFixed(2), bad };
  }

  /* ---------- the choice and the volumes ---------- */
  const listeners = [];
  function changed() { save(); levels(); listeners.forEach(fn => fn()); }
  function setMode(v) {
    if (!MODES.includes(v) || v === set.mode) return;
    set.mode = v;
    if (v === 'off') for (const id of [...parties.keys()]) stopParty(id);
    else unlock();                                     // picked with a click: the browser lets it start
    changed();
  }
  function setVol(g, v) {
    if (!GROUPS.includes(g)) return;
    v = Math.min(1, Math.max(0, +v || 0));
    if (v === set.vol[g]) return;
    set.vol[g] = v;
    changed();
  }

  /* ---------- the bar's button and its drop-up ---------- */
  const optionOf = v => OPTIONS.find(o => o.value === v) || OPTIONS[0];
  function barUi() {
    const b = $('#btnSound'); if (!b) return;
    const o = optionOf(set.mode);
    $('#soundIcon').innerHTML = iconSvg(o.icon, 16);                // the gear's size, as it wears no words
    $('#soundLabel').textContent = o.label;
    b.title = 'Sound: ' + { all: 'every sound the city makes', events: 'events only', off: 'off' }[set.mode] + '. Click to choose.';
  }
  function init() {
    const b = $('#btnSound');
    if (b) b.addEventListener('click', () => MapView.dropUp(b, OPTIONS, set.mode, v => {
      setMode(v); Settings.refresh();
      toast({ all: 'Sound is on.', events: 'Only events make sound now.', off: 'The city is silent.' }[v]);
    }));
    listeners.push(barUi);
    barUi();
    window.addEventListener('pointerdown', unlock, true);
    window.addEventListener('keydown', unlock, true);
    document.addEventListener('visibilitychange', () => levels());
    setInterval(cityTick, 200);                                       // the city's own loop (0.1.80)
  }

  return { init, OPTIONS, GROUPS, mode: () => set.mode, setMode, vol: g => set.vol[g], setVol, VOL_DEF, onChange: fn => listeners.push(fn),
    ticked, task, claude, bubble, gusAlarm, say, party, stopParty, truck,
    /* whether Claude Code's alerts can play while the city is out of view, so the Claude folder is read then too (C4) */
    listening: () => set.mode !== 'off' && set.vol.alerts > 0 && running(),
    _test: {
      log: () => log.slice(), clear: () => { log.length = 0; }, state: () => (ctx ? ctx.state : 'none'), parties: () => [...parties.keys()],
      levels: () => Object.fromEntries(GROUPS.map(g => [g, g in level ? level[g] : null])), placeOf: pid => placeOf(getProject(pid)),
      /* every sound rendered offline, for its level without ears: peak, loudness, length, and any bad sample */
      city: () => city && { dark: Math.round(city.dark * 100) / 100, street: Math.round(STREET * city.zl * 100) / 100, work: city.zl, layers: city.layersOn, claude: !!city.power, counts: { ...counts } },
      zoomLevel: () => zoomLevel(),
      ids: () => [...Object.keys(TASKS), ...Object.keys(ALERTS), 'party', 'voice:gus', 'voice:proxima', 'voice:quill', 'voice:ld:x1', ...CITY_IDS],
      render: async (id, secs = 6) => {
        const sr = 44100, c = new OfflineAudioContext(2, Math.ceil(sr * secs), sr), m = masterChain(c, MASTER * VOL_DEF);
        if (CITY_IDS.has(id)) {                               // the city's own, alone, at the street's level (the hum and buildings at full)
          const A = { ctx: c, out: chain(c, m, 'snes'), style: 'snes', r: rng(hash(id)) }, E = under(A, STREET), st = { relayAt: 0.1, compAt: 0.1, burst: 0, crickets: cricketsOf(A, 0) };
          if (id === 'hum-day' || id === 'hum-night') humBed(A, 0, HUM[id.slice(4)]).mix.gain.value = 1;
          else if (id === 'car') carPass(E, 0.02, 1);
          else if (id.startsWith('honk-')) HONKS[id.slice(5)](E, 0.02, 0);
          else if (id === 'bus') busStop(E, 0.02, 0);
          else if (id === 'drone') dronePass(E, 0.02, 1);
          else if (id === 'bell') bell(E, 0.02, 0);
          else if (id === 'crowd') crowd({ ...E, out: chain(c, E.out, 'soft') }, 0.02);
          else if (id === 'truck') truckSound(E, 0.02, -1);
          else if (id === 'relays') relays(A, st, 0, secs);
          else if (id === 'server') serverRoom(A, 0);
          else if (id === 'power') powerHum(A, 0);
          else if (id === 'computers') computers(A, st, 0, secs);
          else if (id === 'crickets') crickets(A, st, 0, secs);
          return measure(id, await c.startRendering(), sr);
        }
        const group = TASKS[id] ? 'alerts' : ALERTS[id] ? 'alerts' : id === 'party' ? 'music' : 'voices';
        const v = voiceFor(group, 0, 1, hash(id), c, chain(c, m, STYLE[group]));
        if (TASKS[id]) TASKS[id](v.A, 0.02);
        else if (ALERTS[id]) ALERTS[id](v.A, 0.02);
        else if (id === 'party') { cheer(v.A, 0.02, 0.35); const g = c.createGain(); g.gain.value = 0.4; g.connect(v.g); const M = { ...v.A, out: g }; for (let k = 0; 0.27 + k * STEP < secs - 0.3; k++) partyStep(M, 0.27 + k * STEP, k); }
        else talk(v.A, 0.02, id.slice(6), [...'Took you long enough. 3 tasks waiting. Sound Plan for the city first.'], 0.026);
        return measure(id, await c.startRendering(), sr);
      },
    },
  };
})();
