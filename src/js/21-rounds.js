/* A task's decision wizard round (0.1.55): idea 3 of the task ideas, from Tasks, Round 2 (W1 to W6) and Wizard Rounds
   in a Task, Rounds 1 to 3. A round is a questions file for Abdurrahman's Decision Wizard, which Claude writes with the
   d-wizard skill. The task keeps it, and its answers, in the city's data (W2, W4); its file sits in the Claude folder's
   wizard-rounds, which the city and the wizard share (F1); and a hat on the task's rows says where it stands: gray
   until it is answered, teal once it is (A2, H1). A new round replaces the old one (W6).
   This file is the model: reading a wizard's files, a round's state, its words for Claude, and the hat. */
const ROUNDS_DIR = 'wizard-rounds';
const WIZARD_HOSTED = 'https://abdurrahmankh.github.io/decision-wizard/';
const WIZARD_KEY = 'nullovation-city:wizard';
const ROUND_MAX = 300000;                  // characters a round and its answers may take in a task
/* The last line of Make a wizard round's copy, in place of the update line (Wizard Rounds in a Task, Round 1). */
const ROUND_LINE = 'Plan this task further with a decision wizard round: write it with the d-wizard skill, asking only what is still open, then send it to Nullovation City with the nullovation-city skill so it attaches to this task (from a chat, give it to me as a file). Do not start the task itself yet.';

/* Where Wizard it opens the wizard: the hosted one, unless Settings, Links names your own copy. */
function wizardSetting() { try { return (localStorage.getItem(WIZARD_KEY) || '').trim(); } catch (e) { return ''; } }
function wizardUrl() { const v = wizardSetting(); return /^(https?|file):\/\//i.test(v) ? v : WIZARD_HOSTED; }

/* What a wizard's file holds: a round ({ config, questions }), its answers ({ meta, answers }, with the round under
   `round` when the wizard saved them), or neither (null). */
function readWizardFile(d) {
  if (!d || typeof d !== 'object') return null;
  const isRound = r => !!(r && typeof r === 'object' && r.config && typeof r.config === 'object' && typeof r.config.title === 'string' && r.config.title.trim()
    && Array.isArray(r.questions) && r.questions.length && r.questions.every(q => q && typeof q === 'object' && typeof q.id === 'string'));
  if (d.meta && typeof d.meta === 'object' && d.meta.tool === 'decision-wizard' && Array.isArray(d.answers))
    return { round: isRound(d.round) ? { config: d.round.config, questions: d.round.questions } : null, answers: { meta: d.meta, answers: d.answers } };
  if (isRound(d)) return { round: { config: d.config, questions: d.questions }, answers: null };
  return null;
}
const roundTitleOf = q => String(q.config.title).trim().slice(0, 200);
/* A file name the folder can hold: a name only, never a path. */
function safeRoundFile(name) {
  const n = String(name || '').split(/[\\/]/).pop().trim();
  return /^[^:*?"<>|]{1,150}\.json$/i.test(n) ? n : '';
}
const roundFileName = title => ymd() + '-' + slug(title) + '.json';
/* A round as a task keeps it: its title, its file in wizard-rounds, the folder it names (its full path, when Claude
   Code wrote it), the questions, the answers, and whether you marked it answered with questions skipped (S1). */
function makeRound(w, file = '') {
  const c = w.round.config;
  return { title: roundTitleOf(w.round), file: safeRoundFile(file) || roundFileName(c.title), folder: typeof c.folder === 'string' ? c.folder.trim().slice(0, 400) : '',
    q: w.round, a: answersFit(w.answers, w.round) ? w.answers : null, marked: false, at: Date.now() };
}
/* Answers belong to a round when the wizard named it, or named nothing. */
function answersFit(a, q) {
  if (!a) return false;
  const named = String(a.meta.wizard_title || '').trim();
  return !named || named === roundTitleOf(q);
}
/* A task's round as read from saved data: whole, or not at all. */
function readRound(t) {
  const r = t && t.round;
  if (!r || typeof r !== 'object') return {};
  const q = readWizardFile(r.q), a = r.a ? readWizardFile(r.a) : null;
  if (!q || !q.round) return {};
  const out = { title: roundTitleOf(q.round), file: safeRoundFile(r.file) || roundFileName(q.round.config.title), folder: typeof r.folder === 'string' ? r.folder.slice(0, 400) : '',
    q: q.round, a: a && a.answers ? a.answers : null, marked: r.marked === true, at: typeof r.at === 'number' ? r.at : Date.now() };
  try { if (JSON.stringify(out).length > ROUND_MAX) return {}; } catch (e) { return {}; }
  return { round: out };
}

/* ---------- where a round stands ---------- */
const isBatchDone = a => a.status === 'batch' && a.total_items > 0 && a.answered_items >= a.total_items;
const isAnswered = a => !!a && (['picked', 'custom', 'ranked'].includes(a.status) || isBatchDone(a));
/* How many questions, how many answered, how many open, and whether it counts as answered: nothing open (A1), or
   marked answered with the rest skipped on purpose (S1). */
function roundState(t) {
  const r = t && t.round;
  if (!r) return null;
  let total = r.q.questions.length, answered = 0;
  if (r.a) {
    const m = r.a.meta || {};
    answered = Number.isFinite(m.answered) ? m.answered : r.a.answers.filter(isAnswered).length;
    if (Number.isFinite(m.total) && m.total > 0) total = m.total;
  }
  answered = clamp(answered, 0, total);
  const open = total - answered;
  const done = (open === 0 && total > 0) || (r.marked && answered > 0);
  return { total, answered, open, done, marked: r.marked && open > 0, skipped: r.marked ? open : 0 };
}
/* In the card: "Waiting: 3 of 8 answered", "Answered: 8 of 8", "Answered: 6 of 8, 2 skipped". */
function roundStateText(st) {
  if (!st.done) return 'Waiting: ' + st.answered + ' of ' + st.total + ' answered';
  return 'Answered: ' + st.answered + ' of ' + st.total + (st.skipped ? ', ' + st.skipped + ' skipped' : '');
}
/* For Claude: "Waiting for answers (8 questions)", "3 of 8 answered", "Answered, 8 of 8", "6 of 8 answered, 2 skipped on purpose". */
function roundWords(st) {
  if (!st.done) return st.answered ? st.answered + ' of ' + st.total + ' answered' : 'Waiting for answers (' + plural(st.total, 'question', 'questions') + ')';
  return st.skipped ? st.answered + ' of ' + st.total + ' answered, ' + st.skipped + ' skipped on purpose' : 'Answered, ' + st.answered + ' of ' + st.total;
}

/* ---------- a round's answers, in words ---------- */
const endStop = s => (/[.!?:]$/.test(s) ? s : s + '.');
/* One answer: what was picked or typed, the order of a ranking, a number with its unit; Open or Skipped when there is
   none. */
function answerWords(a, marked) {
  const none = marked ? 'Skipped' : 'Open';
  if (!a) return none;
  if (a.status === 'picked' || a.status === 'custom') {
    if (typeof a.answer === 'number') return a.answer + (a.unit ? ' ' + a.unit : '');
    return String(a.answer == null ? '' : a.answer).trim() || none;
  }
  if (a.status === 'ranked') return Array.isArray(a.answer) && a.answer.length ? 'In this order: ' + a.answer.join(', ') : none;
  if (a.status === 'not_needed') return 'Not needed';
  if (a.status === 'batch') return (a.answered_items || 0) + ' of ' + (a.total_items || 0) + ' rows answered';
  return none;
}
function answerLine(a, q, marked, indent = '') {
  const id = a.id || (q && q.id) || '', title = String(a.issue || (q && q.title) || '').trim(), question = String(a.question || (q && q.question) || '').trim();
  let s = indent + '- ' + [id, title].filter(Boolean).join(', ') + ': ' + (question ? question + ' ' : '') + endStop(answerWords(a, marked));
  if (a.comment && String(a.comment).trim()) s += ' Note: ' + endStop(String(a.comment).trim());
  const out = [s];
  if (a.status === 'batch' && Array.isArray(a.items)) for (const it of a.items)
    out.push(indent + '  - ' + String(it.label || it.id || '').trim() + ': ' + endStop(String(it.answer || '').trim() || (marked ? 'Skipped' : 'Open')) + (it.comment && String(it.comment).trim() ? ' Note: ' + endStop(String(it.comment).trim()) : ''));
  if (Array.isArray(a.followups)) for (const f of a.followups) if (f && f.status !== 'not_needed') out.push(...answerLine(f, null, marked, indent + '  '));
  return out;
}
/* Every question of the round with its answer, in the round's order; a question the answers do not have yet is open. */
function roundAnswerLines(r) {
  const st = roundState({ round: r }), byId = new Map((r.a ? r.a.answers : []).filter(a => a && a.id).map(a => [a.id, a]));
  const out = [];
  for (const q of r.q.questions) out.push(...answerLine(byId.get(q.id) || { id: q.id, status: 'open' }, q, st.marked));
  return out;
}
/* The round's full path, when the round named its folder (Claude Code writes it so); else ''. */
function roundPath(r) {
  if (!r || !r.folder) return '';
  const sep = r.folder.includes('\\') || /^[a-z]:/i.test(r.folder) ? '\\' : '/';
  return r.folder.replace(/[\\/]+$/, '') + sep + r.file;
}
/* What a copy for Claude says about the task's round. Through its file (A2) wherever Claude can read the file; with
   the answers written in for a chat, which cannot (C1), and on a computer with no Claude folder. */
function roundForClaude(t, { inline = false } = {}) {
  const r = t.round;
  if (!r) return [];
  const st = roundState(t);
  const L = ['', '## Wizard round: ' + r.title, endStop(roundWords(st))];
  if (!inline) {
    const path = roundPath(r);
    L.push(path ? 'Its questions and answers are in ' + path + ': read them there.'
      : 'Its questions and answers are in ' + ROUNDS_DIR + '/' + r.file + ' in the Claude folder, which ~/.claude/nullovation-city.json names: read them there.');
  } else if (r.a || st.marked) L.push(...roundAnswerLines(r));
  return L;
}

/* ---------- the hat ---------- */
/* The Decision Wizard's own hat, flat and in one color (H1): gray while the round waits for answers, teal once it is
   answered. */
const HAT_PATHS = '<path d="M5.2 17.2 10.4 4.1c.4-1 1.4-1.6 2.4-1.3 1.4.4 2.9 1.6 4.6 3.9.3.4-.2.9-.6.6-1.1-.8-2.2-1.2-3.2-1.1l3.3 11z"/><path d="M1.8 18.6c0-1.4 4.5-2.6 10.2-2.6s10.2 1.2 10.2 2.6S17.7 21 12 21 1.8 20 1.8 18.6z"/>';
const hatSvg = size => `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="${size}" height="${size}" fill="currentColor" aria-hidden="true" focusable="false">${HAT_PATHS}</svg>`;
function hatEl(t, size = 14) {
  const st = roundState(t);
  if (!st) return null;
  return h('span', { class: 'hat ' + (st.done ? 'hat-done' : 'hat-open'), 'aria-hidden': 'true', html: hatSvg(size) });
}
/* A hat shows on an open task only: a ticked, waiting or archived task keeps its round, and wears none. */
const wearsHat = t => !!(t && t.round && isOpenTask(t));
