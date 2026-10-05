'use strict';

const $ = (sel, root = document) => root.querySelector(sel);
const $$ = (sel, root = document) => Array.from(root.querySelectorAll(sel));

function h(tag, attrs, ...kids) {
  const e = document.createElement(tag);
  if (attrs) {
    for (const [k, v] of Object.entries(attrs)) {
      if (v == null || v === false) continue;
      if (k === 'class') e.className = v;
      else if (k === 'text') e.textContent = v;
      else if (k === 'html') e.innerHTML = v;
      else if (k.startsWith('on') && typeof v === 'function') e.addEventListener(k.slice(2), v);
      else if (k === 'value') e.value = v;
      else if (k === 'checked') e.checked = !!v;
      else if (v === true) e.setAttribute(k, '');
      else e.setAttribute(k, v);
    }
  }
  for (const kid of kids.flat(Infinity)) {
    if (kid == null || kid === false) continue;
    e.append(kid.nodeType ? kid : document.createTextNode(String(kid)));
  }
  return e;
}

const uid = (p = 'id') => p + '_' + Math.random().toString(36).slice(2, 8) + Date.now().toString(36).slice(-5);

function hashStr(s) {
  let x = 2166136261;
  for (let i = 0; i < s.length; i++) { x ^= s.charCodeAt(i); x = Math.imul(x, 16777619); }
  return x >>> 0;
}
function mulberry32(a) {
  return function () {
    a |= 0; a = (a + 0x6D2B79F5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

const clamp = (v, a, b) => Math.max(a, Math.min(b, v));
const lerp = (a, b, t) => a + (b - a) * t;
const easeOut = t => 1 - Math.pow(1 - t, 3);
const reducedMotion = () => !!(window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches);

function debounce(fn, ms) {
  let t = null, args = [];
  const d = (...a) => { args = a; clearTimeout(t); t = setTimeout(() => { t = null; fn(...args); }, ms); };
  d.flush = () => { if (t) { clearTimeout(t); t = null; fn(...args); } };
  return d;
}

/* ---------- dates ---------- */
const DAY = 86400000;
function startOfDay(ts) { const d = new Date(ts); d.setHours(0, 0, 0, 0); return d.getTime(); }
function fmtDate(ts) {
  const d = new Date(ts), now = new Date();
  const opts = { day: 'numeric', month: 'short' };
  if (d.getFullYear() !== now.getFullYear()) opts.year = 'numeric';
  return d.toLocaleDateString('en-GB', opts);
}
function fmtStamp(ts) {
  const d = new Date(ts);
  return fmtDate(ts) + ', ' + String(d.getHours()).padStart(2, '0') + ':' + String(d.getMinutes()).padStart(2, '0');
}
function daysBetween(a, b) { return Math.round((startOfDay(b) - startOfDay(a)) / DAY); }
function relAgo(ts, now = Date.now()) {
  const s = Math.max(0, (now - ts) / 1000);
  if (s < 60) return 'just now';
  const m = Math.floor(s / 60);
  if (m < 60) return m === 1 ? '1 minute ago' : m + ' minutes ago';
  const hr = Math.floor(m / 60);
  if (hr < 24) return hr === 1 ? '1 hour ago' : hr + ' hours ago';
  const days = daysBetween(ts, now);
  if (days <= 1) return 'yesterday';
  if (days < 45) return days + ' days ago';
  return 'on ' + fmtDate(ts);
}
function parseYmd(s) {
  const m = /^(\d{4})-(\d{2})-(\d{2})$/.exec(s || '');
  if (!m) return null;
  return new Date(+m[1], +m[2] - 1, +m[3]).getTime();
}
function ymd(ts = Date.now()) {
  const d = new Date(ts);
  return d.getFullYear() + '-' + String(d.getMonth() + 1).padStart(2, '0') + '-' + String(d.getDate()).padStart(2, '0');
}
function deadlineInfo(s, now = Date.now()) {
  const due = parseYmd(s);
  if (due == null) return null;
  const diff = daysBetween(now, due);
  if (diff === 0) return { text: 'Due today', tone: 'soon' };
  if (diff === 1) return { text: 'Due tomorrow', tone: 'soon' };
  if (diff > 1) return { text: 'Due ' + fmtDate(due) + ', in ' + diff + ' days', tone: diff <= 3 ? 'soon' : '' };
  const o = -diff;
  return { text: 'Due ' + fmtDate(due) + ', ' + (o === 1 ? '1 day' : o + ' days') + ' overdue', tone: 'late' };
}

/* ---------- search ---------- */
function norm(s) {
  return String(s || '').toLowerCase()
    .replace(/[\u064B-\u065F\u0670\u0640]/g, '')
    .replace(/[\u0623\u0625\u0622\u0671]/g, '\u0627')
    .replace(/\u0649/g, '\u064A')
    .replace(/\u0629/g, '\u0647')
    .replace(/\u0624/g, '\u0648')
    .replace(/\u0626/g, '\u064A')
    .trim();
}

/* ---------- files ---------- */
function readAsDataURL(file) {
  return new Promise((resolve, reject) => {
    const r = new FileReader();
    r.onload = () => resolve(r.result);
    r.onerror = () => reject(r.error);
    r.readAsDataURL(file);
  });
}
function loadImage(src) {
  return new Promise((resolve, reject) => {
    const img = new Image();
    img.onload = () => resolve(img);
    img.onerror = () => reject(new Error('Image failed to load'));
    img.src = src;
  });
}

function downloadBlob(blob, name) {
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob); a.download = name;
  document.body.append(a); a.click();
  setTimeout(() => { URL.revokeObjectURL(a.href); a.remove(); }, 1500);
}
const slug = s => (String(s || '').toLowerCase().replace(/[^a-z0-9\u0600-\u06ff]+/g, '-').replace(/^-+|-+$/g, '') || 'project').slice(0, 60);

/* ---------- toast ---------- */
const toast = (() => {
  let t = null;
  return (msg, kind = '') => {
    const el = $('#toast');
    el.textContent = msg;
    el.className = 'toast show' + (kind ? ' ' + kind : '');
    clearTimeout(t);
    t = setTimeout(() => { el.className = 'toast' + (kind ? ' ' + kind : ''); }, kind === 'error' ? 6000 : 3200);
  };
})();

const plural = (n, one, many) => n + ' ' + (n === 1 ? one : many);
