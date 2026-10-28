/*
  City sounds (0.1.78; City Sounds, Rounds 1 and 2, section 6 of the knowledge file): made in code with the browser's
  own audio, as the sound board played them. This first build brings the events (O1): tasks and alerts in the SNES era
  style (FM bells with a soft echo), the street party and the characters' voices in the 8-bit chip style (S1). The city's
  own sounds (its hum, street life and cleanup) come with the second build.
  - On by default, from the first click, tap or key, since a browser plays nothing before (C1).
  - The Sound button on the map's bar and in Settings, in step (C2): All sounds, Events only (no city sounds), No sound.
  - A volume for each group, as his Round 2 note groups them (C3): Alerts (alerts and tasks), Character voices, and Music
    (the party); City sounds comes with the city's own sounds.
  - Out of view, only Claude Code's alerts play, so the Claude folder is read while hidden too (C4).
  - From the view (C5): a sound with a place is panned by where it is on screen, a little louder zoomed in (his note on
    A1), and the party fades once its block is out of view.
  Kept in this browser (nullovation-city:sound): the choice and the volumes.
*/
const Sound = (() => {
  const KEY = 'nullovation-city:sound';
  const MODES = ['all', 'events', 'off'];
  const GROUPS = ['alerts', 'voices', 'music'];
  const VOL_DEF = 0.8, MASTER = 0.85;
  const STYLE = { alerts: 'snes', voices: 'chip', music: 'chip' };           // S1: tasks and alerts SNES, the party and voices chip
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
      const v = level[g] = set.mode === 'off' ? 0 : document.hidden && g !== 'alerts' ? 0 : set.vol[g];
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
  }

  return { init, OPTIONS, GROUPS, mode: () => set.mode, setMode, vol: g => set.vol[g], setVol, VOL_DEF, onChange: fn => listeners.push(fn),
    ticked, task, claude, bubble, gusAlarm, say, party, stopParty,
    /* whether Claude Code's alerts can play while the city is out of view, so the Claude folder is read then too (C4) */
    listening: () => set.mode !== 'off' && set.vol.alerts > 0 && running(),
    _test: {
      log: () => log.slice(), clear: () => { log.length = 0; }, state: () => (ctx ? ctx.state : 'none'), parties: () => [...parties.keys()],
      levels: () => Object.fromEntries(GROUPS.map(g => [g, g in level ? level[g] : null])), placeOf: pid => placeOf(getProject(pid)),
      /* every sound rendered offline, for its level without ears: peak, loudness, length, and any bad sample */
      ids: () => [...Object.keys(TASKS), ...Object.keys(ALERTS), 'party', 'voice:gus', 'voice:proxima', 'voice:quill', 'voice:ld:x1'],
      render: async (id, secs = 6) => {
        const sr = 44100, c = new OfflineAudioContext(2, Math.ceil(sr * secs), sr), m = masterChain(c, MASTER * VOL_DEF);
        const group = TASKS[id] ? 'alerts' : ALERTS[id] ? 'alerts' : id === 'party' ? 'music' : 'voices';
        const v = voiceFor(group, 0, 1, hash(id), c, chain(c, m, STYLE[group]));
        if (TASKS[id]) TASKS[id](v.A, 0.02);
        else if (ALERTS[id]) ALERTS[id](v.A, 0.02);
        else if (id === 'party') { cheer(v.A, 0.02, 0.35); const g = c.createGain(); g.gain.value = 0.4; g.connect(v.g); const M = { ...v.A, out: g }; for (let k = 0; 0.27 + k * STEP < secs - 0.3; k++) partyStep(M, 0.27 + k * STEP, k); }
        else talk(v.A, 0.02, id.slice(6), [...'Took you long enough. 3 tasks waiting. Sound Plan for the city first.'], 0.026);
        const buf = await c.startRendering();
        let peak = 0, sum = 0, last = 0, bad = 0;
        for (let ch = 0; ch < 2; ch++) { const d = buf.getChannelData(ch); for (let i = 0; i < d.length; i++) { const x = d[i]; if (!isFinite(x)) { bad++; continue; } const a = Math.abs(x); if (a > peak) peak = a; sum += x * x; if (a > 0.002 && i > last) last = i; } }
        return { id, peak: +peak.toFixed(3), rmsDb: +(10 * Math.log10(sum / (2 * Math.max(last, 1)) + 1e-12)).toFixed(1), seconds: +(last / sr).toFixed(2), bad };
      },
    },
  };
})();
