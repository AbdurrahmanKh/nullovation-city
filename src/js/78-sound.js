/*
  City sounds (City Sounds, Rounds 1 and 2, section 6 of the knowledge file): made in code with the browser's own audio,
  as the sound board played them. Two builds (O1): the events at 0.1.78, tasks and alerts in the SNES era style (FM bells
  with a soft echo), the street party and the characters' voices in the 8-bit chip style (S1); and the city's own sounds
  at 0.1.79, its hum, street life and cleanup, in the SNES era style, with no sharp sound among them (his note on O1).
  - On by default, from the first click, tap or key, since a browser plays nothing before (C1).
  - The Sound button on the map's bar and in Settings, in step (C2): All sounds, Events only (no city sounds), No sound.
  - A volume for each group, as his Round 2 note groups them (C3): City sounds (the hum, street life and cleanup),
    Alerts (alerts and tasks), Character voices, and Music (the party).
  - Out of view, only Claude Code's alerts play, so the Claude folder is read while hidden too (C4).
  - From the view (C5): a sound with a place is panned by where it is on screen, a little louder zoomed in (his note on
    A1), and the party fades once its block is out of view; the street and the cleanup are heard only on screen, coming
    in as you zoom in, so zoomed out only the hum is left.
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


  /* ---------- the city's own sounds (0.1.79): its hum, street life and cleanup, from the view ---------- */
  /* Only All sounds plays them, only in view, and only what is on screen is heard (C5): the hum always, street life and
     the cleanup coming in as you zoom in, each from where it is. None of them sharp (his note on O1: "the city and the
     hums should not have sharp sounds", the bus stop's ding sounding like an alert): no ding, no brakes' squeal, no
     cyclist's bell, and the brooms and the sparkle low and soft. */
  const clamp01 = x => Math.max(0, Math.min(1, x));
  const cityOn = () => may('city') && typeof Traffic !== 'undefined';
  /* The open part of the map and how near it is: by how much of the city it shows, so a phone and a computer agree.
     A map's width of 1,100 world pixels or more is zoomed out (only the hum), 300 or less is right in the street. */
  function viewOf() {
    const wrap = $('#mapWrap'); if (!wrap || typeof MapView === 'undefined') return null;
    const x0 = typeof panelEdge === 'function' ? panelEdge() : 0, W = wrap.clientWidth, H = wrap.clientHeight;
    if (W - x0 < 120 || H < 80) return null;
    const cam = MapView.camState(), zc = cam.z / (cam.dpr || 1), seen = (W - x0) / zc;
    return { x0, W, H, near: clamp01(Math.log2(1100 / seen) / Math.log2(1100 / 300)) };
  }
  /* Where a thing is heard from: its pan across the open map, and how loud by how near the middle it is; nothing off it. */
  function hear(v, wx, wy) {
    const [x, y] = MapView.worldCss(wx, wy), hw = (v.W - v.x0) / 2, hh = v.H / 2;
    const nx = (x - v.x0 - hw) / hw, ny = (y - hh) / hh, out = Math.max(Math.abs(nx), Math.abs(ny));
    if (out > 1.15) return null;
    return { pan: Math.max(-1, Math.min(1, nx)) * 0.8, g: clamp01(1.1 - 0.8 * Math.hypot(nx, ny)) * clamp01((1.15 - out) / 0.15) };   // the middle loudest, an edge 0.3
  }
  const ramp = (param, v, k = 0.15) => param.setTargetAtTime(v, ctx.currentTime, k);
  /* A sound that runs while it is heard: a gain and a pan of its own into the city's style; stop() lets it fade. */
  function runner() {
    const out = ctx.createGain(), pan = ctx.createStereoPanner();
    out.gain.value = 0; out.connect(pan); pan.connect(ins.city);
    const nodes = [];
    return { out, pan, nodes, start(n, at = 0) { n.start(ctx.currentTime, at); nodes.push(n); return n; },
      stop() { ramp(out.gain, 0, 0.12); const t = ctx.currentTime + 0.8; for (const n of nodes) { try { n.stop(t); } catch (e) { /* gone */ } } setTimeout(() => { try { pan.disconnect(); } catch (e) { /* gone */ } }, 1200); } };
  }
  const osc = (type, f) => { const o = ctx.createOscillator(); o.type = type; o.frequency.value = f; return o; };
  const loopOf = buf => { const b = ctx.createBufferSource(); b.buffer = kit(ctx)[buf]; b.loop = true; return b; };

  /* The hum, following Time of day: by day far traffic and voices over a low air tone, by night a lower hum with crickets,
     dusk and dawn the two blended, the evening winding down. One low note at most, never a chord, since music is never. */
  function humBed() {
    const day = runner(), night = runner(), r = rng(hash('hum'));
    const bed = (rn, lpF, level, f) => {
      const b = rn.start(loopOf('brown'), r()), lp = biq(ctx, 'lowpass', lpF, 0.6), g = ctx.createGain(); g.gain.value = level;
      b.connect(lp); lp.connect(g); g.connect(rn.out);
      const lfo = rn.start(osc('sine', 0.09)), lg = ctx.createGain(); lg.gain.value = level * 0.35; lfo.connect(lg); lg.connect(g.gain);
      const d = rn.start(osc('sine', f)), d2 = rn.start(osc('sine', f * 2)), dg = ctx.createGain(), dg2 = ctx.createGain();
      dg.gain.value = 0.045; dg2.gain.value = 0.015; d.connect(dg); d2.connect(dg2); dg.connect(rn.out); dg2.connect(rn.out);
    };
    bed(day, 420, 0.24, 65.4); bed(night, 260, 0.12, 55);
    /* voices far off by day: a murmur that rises and falls */
    const m = day.start(loopOf('white'), r()), bp = biq(ctx, 'bandpass', 650, 1.4), mg = ctx.createGain(), mod = day.start(loopOf('smooth'), r() * 4), md = ctx.createGain();
    mg.gain.value = 0; md.gain.value = 0.06; mod.connect(md); md.connect(mg.gain); m.connect(bp); bp.connect(mg); mg.connect(day.out);
    return { day, night, far: 0, cr1: 0, cr2: 0 };
  }
  const CITY_GAIN = 0.55;                                    // street life and cleanup under the hum, as on the board
  /* A car or a bus: its engine, a low triangle under a soft top, and its tyres on the road. */
  function engine(bus, seed) {
    const rn = runner(), r = rng(seed), f0 = bus ? 50 : 54 + r() * 10;
    const e = rn.start(osc('triangle', f0)), lp = biq(ctx, 'lowpass', bus ? 300 : 340, 0.9), eg = ctx.createGain(); eg.gain.value = bus ? 0.3 : 0.22;
    e.connect(lp); lp.connect(eg); eg.connect(rn.out);
    const n = rn.start(loopOf('white'), r() * 1.5), bp = biq(ctx, 'bandpass', bus ? 700 : 900, 0.6), ng = ctx.createGain(); ng.gain.value = 0.12;
    n.connect(bp); bp.connect(ng); ng.connect(rn.out);
    return Object.assign(rn, { e, ng, f0 });
  }
  /* A drone: its rotors, a buzz that flutters. */
  function rotor(seed) {
    const rn = runner(), r = rng(seed), trem = ctx.createGain(); trem.gain.value = 0.6; trem.connect(rn.out);
    const lfo = rn.start(osc('square', 34 + r() * 4)), lg = ctx.createGain(); lg.gain.value = 0.4; lfo.connect(lg); lg.connect(trem.gain);
    const s = rn.start(osc('triangle', 180 + r() * 12)), fl = biq(ctx, 'lowpass', 1800, 0.8), sg = ctx.createGain(); sg.gain.value = 0.3;
    s.connect(fl); fl.connect(sg); sg.connect(trem);
    const n = rn.start(loopOf('white'), r() * 1.5), bp = biq(ctx, 'bandpass', 1400, 0.8), ng = ctx.createGain(); ng.gain.value = 0.06;
    n.connect(bp); bp.connect(ng); ng.connect(trem);
    return rn;
  }
  /* The hover garbage truck: two low notes an octave apart, wobbling as it hovers, with a soft rush of air. */
  function hover(seed) {
    const rn = runner(), r = rng(seed), wob = ctx.createGain(); wob.gain.value = 0.85; wob.connect(rn.out);
    const lfo = rn.start(osc('sine', 5.5)), lg = ctx.createGain(); lg.gain.value = 0.15; lfo.connect(lg); lg.connect(wob.gain);
    const es = [72, 144.6].map((f, i) => { const s = rn.start(osc('triangle', f)), fl = biq(ctx, 'lowpass', 520, 0.8), g = ctx.createGain(); g.gain.value = i ? 0.09 : 0.18; s.connect(fl); fl.connect(g); g.connect(wob); return s; });
    const n = rn.start(loopOf('white'), r() * 1.5), bp = biq(ctx, 'bandpass', 420, 0.7), ng = ctx.createGain(); ng.gain.value = 0.1;
    n.connect(bp); bp.connect(ng); ng.connect(wob);
    return Object.assign(rn, { es });
  }
  /* One-shots on the street, through a gain and pan of their own. */
  function shot(id, pan, gain, fn) {
    const v = voiceFor('city', pan, gain * CITY_GAIN, hash(id) ^ Date.now());
    drop(v, fn(v.A, ctx.currentTime + 0.03));
    if (QUIET_LOG.has(id)) counts[id] = (counts[id] || 0) + 1; else note2log(id, 'city', pan, gain);
  }
  const QUIET_LOG = new Set(['cricket', 'step', 'broom', 'farCar', 'sparkle']), counts = {};   // too many to log each: counted
  /* A bus at its stop: the air as it settles and its doors, both soft; no ding and no squeal (his note on O1). */
  function busStop(A, t) {
    noise(A, t, 0.6, { type: 'bandpass', f: 1100, q: 0.7, vol: 0.08, a: 0.04 });
    const s = mkOsc(A, 'sine', 120, t + 0.35, t + 0.55); s.frequency.exponentialRampToValueAtTime(55, t + 0.47);
    const g = envGain(A, t + 0.35, { a: 0.003, peak: 0.22, dur: 0.18 }); s.connect(g); route(A, g);
    noise(A, t + 0.35, 0.04, { type: 'lowpass', f: 700, vol: 0.12, a: 0.002 });
    return 1.2;
  }
  /* Talk round a crowd: a few made-up words in soft blips, each speaker its own pitch. */
  function chatter(A, t, base) {
    const L = 'abdeghiklmnoprstuy'; let text = '';
    for (let w = 0, n = 3 + Math.floor(A.r() * 3); w < n; w++) { for (let i = 0, m = 2 + Math.floor(A.r() * 4); i < m; i++) text += L[Math.floor(A.r() * L.length)]; text += ' '; }
    let k = 0;
    [...text].forEach((ch, i) => { if (ch === ' ' || k++ % 2) return; const semi = ((ch.charCodeAt(0) * 7) % 9) - 4; note(A, t + i * 0.055, base * Math.pow(2, semi / 12), 0.05, { vol: 0.14, ratio: 2, index: 0.8 }); });
    return text.length * 0.055 + 0.4;
  }
  const step = (A, t) => { noise(A, t, 0.05, { type: 'lowpass', f: 600, vol: 0.09, a: 0.002 }); return 0.2; };
  const broom = (A, t) => { noise(A, t, 0.26, { type: 'bandpass', f: 1800, fTo: 2500, fDur: 0.2, q: 0.9, vol: 0.26, a: 0.07 }); return 0.4; };
  const LOW_SPARKLE = [72, 76, 79, 84];
  const glint = (A, t) => { note(A, t, m2f(LOW_SPARKLE[Math.floor(A.r() * LOW_SPARKLE.length)]), 0.35, { vol: 0.04, index: 0.6 }); return 0.6; };
  const farCar = (A, t) => { noise(A, t, 2.4, { type: 'bandpass', f: 600, q: 0.9, vol: 0.045, a: 1.0, pan: A.r() * 1.6 - 0.8 }); return 2.6; };
  function cricket(A, t, f) { for (let i = 0; i < 3; i++) note(A, t + i * 0.042, f / 2, 0.03, { vol: 0.03, ratio: 2, index: 0.4 }); return 0.4; }

  let city = null;                                           // the hum and what is heard from the street, while it plays
  function cityStop() {
    if (!city) return;
    city.hum.day.stop(); city.hum.night.stop();
    for (const m of [city.cars, city.drones, city.trucks]) for (const rn of m.values()) rn.stop();
    city = null;
  }
  /* Keeps a set of runners on the loudest things heard, at most n: new ones start, those no longer heard fade. */
  function follow(map, list, n, make, set) {
    const pick = list.filter(x => x.loud > 0.02).sort((a, b) => b.loud - a.loud).slice(0, n), keep = new Set(pick.map(x => x.o));
    for (const [o, rn] of [...map]) if (!keep.has(o)) { rn.stop(); map.delete(o); }
    for (const x of pick) {
      let rn = map.get(x.o);
      if (!rn) { rn = make(x); map.set(x.o, rn); note2log(x.kind, 'city', x.pan, x.loud); }
      ramp(rn.pan.pan, x.pan, 0.2); ramp(rn.out.gain, x.loud * CITY_GAIN, 0.2);
      if (set) set(rn, x);
    }
  }
  const due = (key, now, gap) => { if (city[key] > now) return false; city[key] = now + gap(); return true; };
  function cityTick() {
    if (!cityOn() || document.hidden) { cityStop(); return; }
    const now = ctx.currentTime, v = viewOf(), dark = typeof Light !== 'undefined' ? Light.t : 0;
    if (!city) { city = { hum: humBed(), cars: new Map(), drones: new Map(), trucks: new Map(), seen: new WeakSet(), stops: new WeakMap(), far: 0, cr1: 0, cr2: 0, talk: 0, step: 0, broom: new WeakMap(), near: 0 }; note2log('hum', 'city', 0, 1); }
    ramp(city.hum.day.out.gain, 1 - dark, 0.6); ramp(city.hum.night.out.gain, dark, 0.6);
    const R = rng(Date.now() >>> 0);
    const tr = Traffic.heard(), gb = typeof Garbage !== 'undefined' && Garbage.heard ? Garbage.heard() : { trucks: [], sweep: [], sparkles: [] };
    /* the hum's own life: a far car now and then by day, crickets by night */
    if (tr.cars.length && dark < 0.6 && due('far', now, () => 2.5 + R() * 3.5)) shot('farCar', 0, 1 - dark, farCar);
    if (dark > 0.5) {
      if (due('cr1', now, () => 0.62 + R() * 0.1)) shot('cricket', -0.5, (dark - 0.5) * 2, (A, t) => cricket(A, t, 4300));
      if (due('cr2', now, () => 0.9 + R() * 0.25)) shot('cricket', 0.6, (dark - 0.5) * 2, (A, t) => cricket(A, t, 3900));
    }
    city.near = v ? v.near : 0;
    const near = city.near, at = (list, kind, w = 1) => (v && near > 0 ? list.map(x => { const h = hear(v, x.x, x.y); return h ? { ...x, kind, pan: h.pan, loud: h.g * near * w * (x.waits ? 0.5 : 1) } : null; }).filter(Boolean) : []);
    /* street life: the cars, the bus and the drones on screen, the loudest followed as they move */
    const pickBus = at(tr.cars.filter(c => c.bus), 'bus', 1.2).sort((a, b) => b.loud - a.loud).slice(0, 1);
    const cars = at(tr.cars.filter(c => !c.bus), 'car').sort((a, b) => b.loud - a.loud).slice(0, 3).concat(pickBus);   // three cars and a bus at most
    follow(city.cars, cars, 4, x => engine(x.bus, hash(String(x.x)) ^ 7), (rn, x) => {
      ramp(rn.e.frequency, rn.f0 * (x.waits ? 0.85 : 1), 0.3); ramp(rn.ng.gain, x.waits ? 0.02 : 0.12, 0.3);
      const was = city.stops.get(x.o);                         // the stop it served when first heard is old news
      if (was === undefined) city.stops.set(x.o, x.stop);
      else if (x.bus && x.waits && x.stop && was !== x.stop) { city.stops.set(x.o, x.stop); shot('busStop', x.pan, x.loud, busStop); }
    });
    follow(city.drones, at(tr.drones, 'drone', 0.8), 2, x => rotor(hash(String(x.y))));
    /* people: talk round those standing together, and footsteps when you are right among them */
    const talk = at(tr.talk, 'chatter'), walk = at(tr.walk, 'step');
    const talkSum = talk.reduce((a, x) => a + x.loud, 0);
    if (talkSum > 0.05 && due('talk', now, () => Math.max(0.7, Math.min(6, 2.5 / talkSum)) * (0.7 + R() * 0.6))) {
      const x = talk[Math.floor(R() * talk.length)]; shot('chatter', x.pan, x.loud, (A, t) => chatter(A, t, 140 + R() * 160));
    }
    if (near > 0.6 && walk.length >= 2 && due('step', now, () => 0.3 + R() * 0.1)) { const x = walk[Math.floor(R() * walk.length)]; shot('step', x.pan, x.loud * 0.8, step); }
    /* the cleanup: the trucks on screen, the crew's brooms, a soft glint where a piece went */
    follow(city.trucks, at(gb.trucks, 'truck', 1.1), 3, x => hover(hash(String(x.x))), (rn, x) => { for (const e of rn.es) ramp(e.frequency, (e === rn.es[0] ? 72 : 144.6) * (x.parked ? 0.8 : 1), 0.6); });
    for (const x of at(gb.sweep, 'broom')) { const nx = city.broom.get(x.o) || 0; if (nx <= now) { city.broom.set(x.o, now + 0.4 + R() * 0.12); shot('broom', x.pan, x.loud, broom); } }
    for (const x of at(gb.sparkles, 'sparkle')) { if (city.seen.has(x.o)) continue; city.seen.add(x.o); shot('sparkle', x.pan, x.loud, glint); }
  }

  const CITY_IDS = new Set(['hum', 'car', 'bus', 'busStop', 'drone', 'truck', 'chatter', 'broom']);
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
    setInterval(cityTick, 200);                                       // the city's own sounds, as the view and the street move
  }

  return { init, OPTIONS, GROUPS, mode: () => set.mode, setMode, vol: g => set.vol[g], setVol, VOL_DEF, onChange: fn => listeners.push(fn),
    ticked, task, claude, bubble, gusAlarm, say, party, stopParty,
    /* whether Claude Code's alerts can play while the city is out of view, so the Claude folder is read then too (C4) */
    listening: () => set.mode !== 'off' && set.vol.alerts > 0 && running(),
    _test: {
      log: () => log.slice(), clear: () => { log.length = 0; }, state: () => (ctx ? ctx.state : 'none'), parties: () => [...parties.keys()],
      levels: () => Object.fromEntries(GROUPS.map(g => [g, g in level ? level[g] : null])), placeOf: pid => placeOf(getProject(pid)),
      /* every sound rendered offline, for its level without ears: peak, loudness, length, and any bad sample */
      city: () => city && { near: Math.round(city.near * 100) / 100, day: Math.round(city.hum.day.out.gain.value * 100) / 100, night: Math.round(city.hum.night.out.gain.value * 100) / 100,
        cars: city.cars.size, drones: city.drones.size, trucks: city.trucks.size, counts: { ...counts } },
      viewOf: () => viewOf(),
      ids: () => [...Object.keys(TASKS), ...Object.keys(ALERTS), 'party', 'voice:gus', 'voice:proxima', 'voice:quill', 'voice:ld:x1', 'hum', 'car', 'bus', 'busStop', 'drone', 'truck', 'chatter', 'broom'],
      render: async (id, secs = 6) => {
        const sr = 44100, c = new OfflineAudioContext(2, Math.ceil(sr * secs), sr), m = masterChain(c, MASTER * VOL_DEF);
        if (CITY_IDS.has(id)) {                               // the city's own: built on the offline context for a moment
          const keep = ctx, into = ins.city;
          ctx = c; ins.city = chain(c, m, 'snes');
          try {
            if (id === 'hum') humBed().day.out.gain.value = 1;
            else if (id === 'car' || id === 'bus') engine(id === 'bus', 1).out.gain.value = CITY_GAIN;
            else if (id === 'drone') rotor(1).out.gain.value = CITY_GAIN * 0.8;
            else if (id === 'truck') hover(1).out.gain.value = CITY_GAIN;
            else { const v = voiceFor('city', 0, CITY_GAIN, hash(id), c, ins.city); ({ busStop, broom, chatter: (A, t) => chatter(A, t, 200) })[id](v.A, 0.02); }
          } finally { ctx = keep; ins.city = into; }
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
