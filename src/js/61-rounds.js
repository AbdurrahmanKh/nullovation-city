/* Wizard rounds in a task (0.1.55), in the city: the card in the task panel, the hats on the rows, Wizard it, a round
   file dropped on the task, and the answers read back from the Claude folder's wizard-rounds.
   How a round travels (Wizard Rounds in a Task, Rounds 1 to 3):
   - Make a wizard round, in Open in Claude's second row, sends the task's copy asking Claude for a round. From Claude
     Code it comes back through the inbox (add-round, applied at once with Undo), its file already in wizard-rounds;
     from a chat, you drop the file Claude gives you on the task's panel (W1, P2).
   - Wizard it (or a click on a hat) opens your wizard in a tab of its own, and makes sure the round's file is in
     wizard-rounds, where the wizard, given that folder once, opens it by itself and saves the answers as you go (W3, F1).
     With no Claude folder it downloads the file instead, and the answers file is dropped back on the task.
   - The answers come back into the task as the wizard saves them, with a toast once they stop arriving (X1), and the
     hat turns teal once nothing is open, or once you mark the round answered with the rest skipped (A1, S1). */
const Rounds = (() => {
  const unfolded = new Set();            // the cards showing their answers; every panel opens folded (P1a)
  const stamps = new Map();              // task id -> the round file's stamp when last read
  const waits = new Map();               // task id -> the toast waiting for its answers to stop arriving
  const HINT_KEY = 'nullovation-city:wizardHint';
  let wiz = null;                        // the wizard's tab
  const clone = x => JSON.parse(JSON.stringify(x));

  /* ---------- files ---------- */
  /* What goes in a round's file: the questions alone, or the answers with the round under them, as the wizard saves. */
  const fileText = r => JSON.stringify(r.a ? { meta: r.a.meta, answers: r.a.answers, round: r.q } : r.q, null, 2) + '\n';
  async function roundsDir(dir, create) { return dir.getDirectoryHandle(ROUNDS_DIR, create ? { create: true } : undefined); }
  async function readFile(dir, name) {
    const n = safeRoundFile(name);
    if (!n) return null;
    try {
      const f = await (await (await roundsDir(dir, false)).getFileHandle(n)).getFile();
      return { w: readWizardFile(JSON.parse(await f.text())), stamp: f.lastModified + ':' + f.size };
    } catch (e) { return null; }
  }
  async function writeFile(dir, r) {
    const w = await (await (await roundsDir(dir, true)).getFileHandle(r.file, { create: true })).createWritable();
    await w.write(fileText(r)); await w.close();
  }
  async function hasFile(dir, name) {
    try { await (await roundsDir(dir, false)).getFileHandle(name); return true; } catch (e) { return false; }
  }

  /* ---------- the wizard ---------- */
  /* Opens the wizard in its own tab, the same tab each time. Called straight from the click, so the browser lets it. */
  function openWizard() {
    try { if (wiz && !wiz.closed) { wiz.focus(); return true; } } catch (e) { /* a tab from before: open it again */ }
    try { wiz = window.open(wizardUrl(), 'nullovation-wizard'); } catch (e) { wiz = null; }
    return !!wiz;
  }
  /* Wizard it: the wizard opens, and the round's file is in wizard-rounds for it (written again when it is gone); with no
     Claude folder, the file downloads, to load in the wizard. */
  function wizard(p, t) {
    const r = t && t.round;
    if (!r) return;
    const opened = openWizard(), dir = typeof ClaudeWork !== 'undefined' ? ClaudeWork.folder() : null;
    const blocked = opened ? '' : ' The browser kept the wizard from opening: open it at ' + wizardUrl() + '.';
    if (!dir) {
      downloadBlob(new Blob([fileText(r)], { type: 'application/json' }), r.file);
      toast('Downloaded ' + r.file + '. Load it in your wizard, then drop its answers file on this task.' + blocked);
      return;
    }
    (async () => {
      try { if (!(await hasFile(dir, r.file))) { await writeFile(dir, r); stamps.delete(t.id); } }
      catch (e) { toast('The round could not be written in the Claude folder, so it downloaded instead.', 'error'); downloadBlob(new Blob([fileText(r)], { type: 'application/json' }), r.file); return; }
      let hinted = false;
      try { hinted = localStorage.getItem(HINT_KEY) === '1'; localStorage.setItem(HINT_KEY, '1'); } catch (e) { /* say it each time */ }
      toast((hinted ? 'Opening your wizard on ' + r.title + '.'
        : 'Opening your wizard. Give it the Claude folder\'s ' + ROUNDS_DIR + ' folder once, and ' + r.title + ' opens there by itself.') + blocked);
    })();
  }

  /* ---------- taking a file into a task ---------- */
  /* A round file attaches its round, replacing another (W6) or updating the same one by its title; an answers file
     brings the answers of the round the task has. Returns what happened, or an error starting with '!'. */
  function take(t, w, file) {
    const r = t.round;
    if (w.round) {
      if (r && r.title === roundTitleOf(w.round)) {
        r.q = w.round;
        if (answersFit(w.answers, w.round)) r.a = w.answers;
        return 'updated';
      }
      t.round = makeRound(w, file);
      return 'new';
    }
    const named = String(w.answers.meta.wizard_title || '').trim();
    if (!r) return '!Those are answers to ' + (named || 'a round') + ', and this task has no round. Drop the round\'s own file first.';
    if (!answersFit(w.answers, r.q)) return '!Those answers are for ' + named + ', not ' + r.title + '.';
    r.a = w.answers;
    return 'answers';
  }
  /* A file dropped on the task's panel. With the Claude folder, its round goes into wizard-rounds too, so Claude and the
     wizard read the same file. Not work: Updated, urgency and Activity stay as they are. */
  async function dropFile(p, t, file) {
    if (!file) return false;
    if (!/\.json$/i.test(file.name)) { toast('That is not a round: drop the .json file Claude gave you, or its answers.', 'error'); return false; }
    let w = null;
    try { w = readWizardFile(JSON.parse(await file.text())); } catch (e) { w = null; }
    if (!w) { toast(file.name + ' is not a decision wizard round or its answers.', 'error'); return false; }
    const was = t.round ? clone(t.round) : null, oldTitle = was && was.title;
    const res = take(t, w, file.name);
    if (res.startsWith('!')) { toast(res.slice(1), 'error'); return false; }
    changed(p, { touch: false });
    refresh(p);
    const dir = typeof ClaudeWork !== 'undefined' ? ClaudeWork.folder() : null;
    if (dir) writeFile(dir, t.round).then(() => stamps.delete(t.id), () => {});
    const st = roundState(t);
    const said = res === 'new' ? 'Attached ' + t.round.title + ' to ' + t.text + '.' + (oldTitle ? ' It replaces ' + oldTitle + '.' : '')
      : res === 'updated' ? 'Updated ' + t.round.title + ' in ' + t.text + (t.round.a ? ': ' + st.answered + ' of ' + st.total + ' answered.' : '.')
      : 'Answers in for ' + t.text + ': ' + st.answered + ' of ' + st.total + '.';
    toast(said, '', { label: 'Undo', run: () => putBack(p, t, was) });
    return true;
  }
  function putBack(p, t, was) {
    if (was) t.round = was; else delete t.round;
    changed(p, { touch: false });
    refresh(p);
  }

  /* ---------- the answers coming back ---------- */
  /* Reads each round's file in wizard-rounds, every few seconds with the rest of the Claude folder. The wizard saves the
     answers into it as you go; the task takes them, and a toast says so once they stop arriving for a moment. One tab
     takes them: the one that writes the data file. */
  let busy = false;
  async function poll(dir, writer) {
    if (!dir || !writer || busy) return false;
    busy = true;
    let moved = false;
    try {
      let d = null;
      try { d = await roundsDir(dir, false); } catch (e) { d = null; }
      if (d) for (const p of DB.projects) for (const t of p.todos) {
        const r = t.round;
        if (!r || t.archived) continue;
        let f;
        try { f = await (await d.getFileHandle(r.file)).getFile(); } catch (e) { continue; }
        const stamp = f.lastModified + ':' + f.size;
        if (stamps.get(t.id) === stamp) continue;
        stamps.set(t.id, stamp);
        let w = null;
        try { w = readWizardFile(JSON.parse(await f.text())); } catch (e) { continue; }   // half written: its next stamp
        if (!w || !w.answers || (w.round && roundTitleOf(w.round) !== r.title) || !answersFit(w.answers, r.q)) continue;
        if (JSON.stringify(w.answers) === JSON.stringify(r.a || null)) continue;
        r.a = w.answers;
        if (w.round) r.q = w.round;
        changed(p, { touch: false });
        moved = true;
        announce(p, t);
      }
    } catch (e) { /* the folder went: the Claude folder's own state says so */ }
    busy = false;
    if (moved) refresh();
    return moved;
  }
  function announce(p, t) {
    clearTimeout(waits.get(t.id));
    waits.set(t.id, setTimeout(() => {
      waits.delete(t.id);
      const st = roundState(t);
      if (!st) return;
      /* its leader says it, in place of the toast (Leader UX, T1, 0.1.59), with Open; it waits with its leader */
      News.add(p, 'answers', { round: t.round.title, n: st.answered, total: st.total }, { ref: { tid: t.id }, key: 'answers:' + t.id });
    }, ANNOUNCE_MS));
  }
  const ANNOUNCE_MS = 4000;

  /* ---------- in the change files Claude sends (add-round) ---------- */
  /* A change naming a task and its round's file in wizard-rounds, or carrying the round itself. */
  async function fromChange(dir, c) {
    if (c && c.round && typeof c.round === 'object') { const w = readWizardFile(c.round); return w && w.round ? { w, file: safeRoundFile(c.file) } : null; }
    const got = dir && c && c.file ? await readFile(dir, c.file) : null;
    return got && got.w && got.w.round ? { w: got.w, file: safeRoundFile(c.file) } : null;
  }

  /* ---------- marking and removing ---------- */
  function mark(p, t) {
    const r = t.round; if (!r) return;
    r.marked = true;
    changed(p, { touch: false }); refresh(p);
    const st = roundState(t);
    toast('Marked answered: ' + plural(st.skipped, 'question', 'questions') + ' skipped.', '', { label: 'Undo', run: () => { r.marked = false; changed(p, { touch: false }); refresh(p); } });
  }
  function remove(p, t) {
    const was = t.round; if (!was) return;
    delete t.round;
    changed(p, { touch: false }); refresh(p);
    toast('Took ' + was.title + ' off this task. Its file stays in the folder.', '', { label: 'Undo', run: () => putBack(p, t, was) });
  }
  /* Everything showing a round, redrawn: the panel's card and the rows (the status card and the side bar redraw on any
     change already). */
  function refresh() { if (typeof FullView !== 'undefined' && FullView.isOpen()) FullView.refreshRounds(); }

  /* ---------- what shows it ---------- */
  const hatTitle = st => st.done ? 'Wizard round answered. Click to open it in your wizard' : 'Wizard round: ' + st.answered + ' of ' + st.total + ' answered. Click to answer it in your wizard';
  /* The hat on a task's row: gray until the round is answered, teal after (A2, H1); a click is Wizard it (X1). */
  function hatButton(p, t, cls = '') {
    if (!wearsHat(t)) return null;
    const st = roundState(t);
    return h('button', { class: 'icon-btn round-hat ' + (st.done ? 'hat-done' : 'hat-open') + (cls ? ' ' + cls : ''), type: 'button', 'data-task': t.id,
      'aria-label': (st.done ? 'Wizard round answered, for ' : 'Wizard round, ' + st.answered + ' of ' + st.total + ' answered, for ') + t.text + '. Open it in your wizard',
      title: hatTitle(st), html: hatSvg(14), onclick: e => { e.stopPropagation(); wizard(p, t); } });
  }
  /* What is next's chip, beside Pinned and Starred: the count while open, Answered after. */
  function chip(p, t) {
    if (!wearsHat(t)) return null;
    const st = roundState(t);
    return h('button', { id: 'pvNextRound', class: 'round-chip', type: 'button', title: hatTitle(st), onclick: () => wizard(p, t) },
      h('span', { class: 'hat ' + (st.done ? 'hat-done' : 'hat-open'), 'aria-hidden': 'true', html: hatSvg(12) }), st.done ? 'Answered' : st.answered + ' of ' + st.total);
  }
  /* The card in the task panel, under Pin and Star (P1): the state, the title, the file, Wizard it, Mark answered,
     Remove, and the answers, folded until asked for (P1a). An archived task's card is to read. */
  function card(p, t, { readOnly = false } = {}) {
    const r = t && t.round;
    if (!r) return null;
    const st = roundState(t), open = unfolded.has(t.id), hasAnswers = !!r.a || st.marked;
    const el = h('section', { class: 'pv-round' + (st.done ? ' done' : ''), 'aria-label': 'Wizard round' });
    const fold = hasAnswers ? h('button', { class: 'pv-round-fold', type: 'button', 'aria-expanded': String(open),
      onclick: () => { if (open) unfolded.delete(t.id); else unfolded.add(t.id); const nu = card(p, t, { readOnly }); el.replaceWith(nu); const b = $('.pv-round-fold', nu); if (b) b.focus(); } },
      h('span', { 'aria-hidden': 'true', html: iconSvg(open ? 'caretD' : 'caretR', 9) }), open ? 'Answers' : 'Show the answers') : null;
    el.append(
      h('div', { class: 'pv-round-head' }, hatEl(t, 16), h('span', { class: 'pv-round-lbl' }, 'Wizard round'), h('span', { class: 'pv-round-state' }, roundStateText(st))),
      h('p', { class: 'pv-round-title', dir: 'auto' }, r.title),
      h('p', { class: 'pv-round-file', dir: 'ltr', title: roundPath(r) || ROUNDS_DIR + '\\' + r.file + ', in the Claude folder' }, ROUNDS_DIR + '\\' + r.file),
      h('div', { class: 'pv-round-btns' },
        h('button', { id: 'pvRoundWizard', class: 'btn btn-small' + (st.done ? '' : ' btn-accent'), type: 'button', title: st.done ? 'Opens it in your wizard' : 'Answers it in your wizard',
          onclick: () => wizard(p, t) }, h('span', { class: 'hat', 'aria-hidden': 'true', html: hatSvg(14) }), st.done ? 'Open in wizard' : 'Wizard it'),
        !readOnly && !st.done && st.answered > 0 ? h('button', { id: 'pvRoundMark', class: 'btn btn-quiet btn-small', type: 'button', title: 'Every open question counts as skipped on purpose, and the hat turns teal',
          onclick: () => { mark(p, t); const b = side() && $('#pvRoundWizard', side()); if (b) b.focus(); } }, 'Mark answered') : null,
        !readOnly ? h('button', { id: 'pvRoundRemove', class: 'btn btn-quiet btn-small pv-round-remove', type: 'button', title: 'Takes the round off this task; its file stays in the folder',
          onclick: () => remove(p, t) }, 'Remove') : null),
      ...[fold, open && hasAnswers ? answersList(r, st) : null].filter(Boolean));
    return el;
  }
  const side = () => $('#pvSide');
  function answersList(r, st) {
    const byId = new Map((r.a ? r.a.answers : []).filter(a => a && a.id).map(a => [a.id, a]));
    return h('ul', { class: 'pv-round-ans' }, r.q.questions.map(q => {
      const a = byId.get(q.id), got = isAnswered(a);
      const li = h('li', { class: got ? null : st.marked ? 'skip' : 'open' },
        h('span', { class: 'id' }, q.id),
        h('span', { class: 'q', dir: 'auto' }, [q.title, q.question].filter(Boolean).join(': ')),
        h('span', { class: 'a', dir: 'auto' }, a && a.status === 'batch' && !got ? answerWords(a, st.marked) : got ? answerWords(a, false) : st.marked ? 'Skipped' : 'Open'));
      if (a && a.status === 'batch' && Array.isArray(a.items)) for (const it of a.items) if (it.answer) li.append(h('span', { class: 'sub', dir: 'auto' }, String(it.label || it.id) + ': ' + it.answer + (it.comment ? ' (' + it.comment + ')' : '')));
      if (a && Array.isArray(a.followups)) for (const f of a.followups) if (isAnswered(f)) li.append(h('span', { class: 'sub', dir: 'auto' }, (f.issue || f.id) + ': ' + answerWords(f, false)));
      if (a && a.comment && String(a.comment).trim()) li.append(h('span', { class: 'n', dir: 'auto' }, 'Note: ' + String(a.comment).trim()));
      return li;
    }));
  }
  /* The line a round file dragged over the panel lights up (P2: only while dragging). */
  const dropLine = t => h('div', { class: 'pv-round-drop', 'aria-hidden': 'true' }, h('span', { class: 'hat hat-done', html: hatSvg(16) }),
    t && t.round ? 'Drop a round or its answers file here' : 'Drop the round file to attach it to this task');
  /* The round's file for Cowork, when its full path is known. */
  const files = t => (t && t.round && roundPath(t.round) ? [roundPath(t.round)] : []);

  return { wizard, openWizard, take, dropFile, poll, fromChange, mark, remove, hatButton, chip, card, dropLine, files, fileText, writeFile, readFile,
    foldAll: () => unfolded.clear(), ANNOUNCE_MS };
})();
