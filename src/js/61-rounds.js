/* Wizard rounds in a task (0.1.55), in the city: the card in the task panel, the hats on the rows, Wizard it, a round
   file dropped on the task, and the answers read back from the Claude folder's wizard-rounds.
   How a round travels (Wizard Rounds in a Task, Rounds 1 to 3):
   - Make a wizard round, in Open in Claude's second row, sends the task's copy asking Claude for a round. From Claude
     Code it comes back through the inbox (add-round, applied at once with Undo), its file already in wizard-rounds;
     from a chat, you drop the file Claude gives you on the task's panel (W1, P2).
   - Wizard it (or a click on a hat) opens your wizard on the round, in the installed app through a web+dwizard: link
     (0.1.66) or in a tab carrying the round (0.1.65), and makes sure the round's file is in wizard-rounds, where the
     wizard, given that folder once, saves the answers as you go (W3, F1). With no Claude folder, the answers file is
     dropped back on the task.
   - The answers come back into the task as the wizard saves them, with a toast once they stop arriving (X1), and the
     hat turns teal once nothing is open, or once you mark the round answered with the rest skipped (A1, S1).
   - Since 0.1.69 (Leader Bubbles, Round 2, C1 and C2) Quill says a round's answers coming in, and writes them in the
     task's Activity; and a round reads in a small popup with Open in wizard, from Quill's bubble, the leaders' cards,
     and the card's Show the answers. */
const Rounds = (() => {
  const stamps = new Map();              // task id -> the round file's stamp when last read
  const waits = new Map();               // task id -> the toast waiting for its answers to stop arriving
  const HINT_KEY = 'nullovation-city:wizardHint';
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
  const b64url = text => {
    const bytes = new TextEncoder().encode(text);
    let bin = '';
    for (let i = 0; i < bytes.length; i += 0x8000) bin += String.fromCharCode.apply(null, bytes.subarray(i, i + 0x8000));
    return btoa(bin).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
  };
  /* The wizard's address with the round after #open= (0.1.65): its file's name, the round and its answers so far, as
     JSON in base64url, so the wizard opens this round, whatever it had open (wizard 0.11.1). */
  const openLink = r => wizardUrl().replace(/#.*$/, '') + '#open=' + b64url(JSON.stringify({ app: 'nullovation-city', kind: 'open-round', file: r.file, round: r.q, answers: r.a || null }));
  /* The link that opens the installed wizard app from any browser (0.1.66): web+dwizard:, which the app registers with
     the system (wizard 0.11.2). The system takes only about 2,000 characters, so it names the round, its file and
     title, and the app opens the file in the Claude folder's wizard-rounds. */
  const appLink = r => 'web+dwizard:open/' + b64url(JSON.stringify({ file: r.file, title: r.title }));
  /* Follows a link as a click on it does, straight from the click, so the browser lets it: a tab for the address, the
     system for web+dwizard:. A link, not window.open, since Chrome and Edge take a link into an installed app clicked
     in the same browser. */
  function follow(href, tab) {
    const a = h('a', { href, target: tab ? '_blank' : null, rel: tab ? 'noopener' : null, hidden: true });
    document.body.append(a); a.click(); a.remove();
  }
  const openWizard = r => follow(openLink(r), true);
  /* Wizard it: the wizard opens on the round, and the round's file is in wizard-rounds, where the wizard saves its
     answers (written again when it is gone). In the wizard app when Settings, Links says so and the Claude folder is
     connected, the file in place first for the app to read; else in a tab, carrying the round. With no Claude folder,
     its answers come back as a file dropped here. */
  function wizard(p, t) {
    const r = t && t.round;
    if (!r) return;
    const dir = typeof ClaudeWork !== 'undefined' ? ClaudeWork.folder() : null, opening = 'Opening ' + r.title + ' in your wizard.';
    const app = !!dir && wizardOpens() === 'app' && !wizardSetting();
    if (!app) openWizard(r);
    if (!dir) { toast(opening + ' Once it is answered, save its file there and drop it on this task.'); return; }
    (async () => {
      try { if (!(await hasFile(dir, r.file))) { await writeFile(dir, r); stamps.delete(t.id); } }
      catch (e) {
        if (app) openWizard(r);
        toast(opening + ' Its file could not be written in the Claude folder, so save its file in the wizard once it is answered, and drop it on this task.', 'error');
        return;
      }
      let hinted = false;
      try { hinted = localStorage.getItem(HINT_KEY) === '1'; localStorage.setItem(HINT_KEY, '1'); } catch (e) { /* say it each time */ }
      if (app) {
        follow(appLink(r), false);
        toast('Opening ' + r.title + ' in your wizard app.' + (hinted ? '' : ' The first time, give the app the Claude folder\'s ' + ROUNDS_DIR + ' folder, and rounds open there by themselves.'),
          '', { label: 'Open in a tab', run: () => openWizard(r) });
        return;
      }
      toast(hinted ? opening : opening + ' Give it the Claude folder\'s ' + ROUNDS_DIR + ' folder once, and your answers come back here as you go.');
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
     wizard read the same file. Not work: Updated and urgency stay as they are. Since 0.1.70 it writes in Activity, as
     wizard rounds appear there (Leader Bubbles, Round 2, C2, and his yes in the chat): a round attached or updated, and
     the answers it brought; Undo takes the lines back out. */
  async function dropFile(p, t, file) {
    if (!file) return false;
    if (!/\.json$/i.test(file.name)) { toast('That is not a round: drop the .json file Claude gave you, or its answers.', 'error'); return false; }
    let w = null;
    try { w = readWizardFile(JSON.parse(await file.text())); } catch (e) { w = null; }
    if (!w) { toast(file.name + ' is not a decision wizard round or its answers.', 'error'); return false; }
    const was = t.round ? clone(t.round) : null, oldTitle = was && was.title;
    const res = take(t, w, file.name);
    if (res.startsWith('!')) { toast(res.slice(1), 'error'); return false; }
    const lines = [], log = text => { logActivity(p, text); lines.push(p.activity[p.activity.length - 1]); };
    const brought = !!t.round.a && JSON.stringify(t.round.a) !== JSON.stringify(res === 'new' ? null : was && was.a);
    if (res === 'new') log('Attached a wizard round to ' + t.text + ': ' + t.round.title);
    else if (res === 'updated' && !brought) log('Updated the wizard round of ' + t.text + ': ' + t.round.title);
    if (brought) log(answersLine(t.round.title, roundState(t)));
    changed(p, { touch: false });
    refresh(p);
    const dir = typeof ClaudeWork !== 'undefined' ? ClaudeWork.folder() : null;
    if (dir) writeFile(dir, t.round).then(() => stamps.delete(t.id), () => {});
    const st = roundState(t);
    const said = res === 'new' ? 'Attached ' + t.round.title + ' to ' + t.text + '.' + (oldTitle ? ' It replaces ' + oldTitle + '.' : '')
      : res === 'updated' ? 'Updated ' + t.round.title + ' in ' + t.text + (t.round.a ? ': ' + st.answered + ' of ' + st.total + ' answered.' : '.')
      : 'Answers in for ' + t.text + ': ' + st.answered + ' of ' + st.total + '.';
    toast(said, '', { label: 'Undo', run: () => {
      for (const e of lines) { const k = p.activity.indexOf(e); if (k >= 0) p.activity.splice(k, 1); }
      putBack(p, t, was);
    } });
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
      /* Quill says it, in place of the toast (Leader UX, T1, 0.1.59; Quill since 0.1.69), with Read and Open; it waits in
         News. Wizard rounds appear in Activity (Leader Bubbles, Round 2, C2): each time they come in, how far it is. */
      logActivity(p, answersLine(t.round.title, st));
      changed(p, { touch: false });
      News.add(p, 'answers', { round: t.round.title, n: st.answered, total: st.total }, { ref: { tid: t.id }, key: 'answers:' + t.id });
    }, ANNOUNCE_MS));
  }
  const ANNOUNCE_MS = 4000;
  /* The Activity line: "Answers in for <round>: 7 of 8", in cards seen for a brainstorm. */
  const answersLine = (title, st) => 'Answers in for ' + title + ': ' + st.answered + ' of ' + st.total + (st.brainstorm ? ' cards seen' : '');

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
    toast('Marked answered: ' + (st.brainstorm ? plural(st.skipped, 'card', 'cards') : plural(st.skipped, 'question', 'questions')) + ' skipped.', '', { label: 'Undo', run: () => { r.marked = false; changed(p, { touch: false }); refresh(p); } });
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
  const hatTitle = st => (st.brainstorm ? (st.done ? 'Brainstorm answered. Click to open it in your wizard' : 'Brainstorm: ' + st.answered + ' of ' + st.total + ' cards seen. Click to answer it in your wizard')
    : st.done ? 'Wizard round answered. Click to open it in your wizard' : 'Wizard round: ' + st.answered + ' of ' + st.total + ' answered. Click to answer it in your wizard');
  const kindOf = st => (st.brainstorm ? 'Brainstorm' : 'Wizard round');
  /* The hat on a task's row: gray until the round is answered, teal after (A2, H1); a click is Wizard it (X1). */
  function hatButton(p, t, cls = '') {
    if (!wearsHat(t)) return null;
    const st = roundState(t);
    return h('button', { class: 'icon-btn round-hat ' + (st.done ? 'hat-done' : 'hat-open') + (cls ? ' ' + cls : ''), type: 'button', 'data-task': t.id,
      'aria-label': (st.done ? kindOf(st) + ' answered, for ' : kindOf(st) + ', ' + st.answered + ' of ' + st.total + (st.brainstorm ? ' cards seen, for ' : ' answered, for ')) + t.text + '. Open it in your wizard',
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
     Remove, and Show the answers, which opens the round in its popup since 0.1.69 (it unfolded them in place until
     then, P1a). An archived task's card is to read. */
  function card(p, t, { readOnly = false } = {}) {
    const r = t && t.round;
    if (!r) return null;
    const st = roundState(t), hasAnswers = !!r.a || st.marked;
    const label = st.brainstorm ? 'Brainstorm, round ' + st.brainstorm : 'Wizard round';
    const el = h('section', { class: 'pv-round' + (st.done ? ' done' : '') + (st.brainstorm ? ' brainstorm' : ''), 'aria-label': label });
    const fold = hasAnswers ? h('button', { class: 'pv-round-fold', type: 'button', 'aria-haspopup': 'dialog', title: 'Read the round with its answers',
      onclick: () => view(p, t) }, h('span', { 'aria-hidden': 'true', html: iconSvg('caretR', 9) }), 'Show the answers') : null;
    el.append(
      h('div', { class: 'pv-round-head' }, hatEl(t, 16), h('span', { class: 'pv-round-lbl' }, label), h('span', { class: 'pv-round-state' }, roundStateText(st))),
      h('p', { class: 'pv-round-title', dir: 'auto' }, r.title),
      h('p', { class: 'pv-round-file', dir: 'ltr', title: roundPath(r) || ROUNDS_DIR + '\\' + r.file + ', in the Claude folder' }, ROUNDS_DIR + '\\' + r.file),
      h('div', { class: 'pv-round-btns' },
        h('button', { id: 'pvRoundWizard', class: 'btn btn-small' + (st.done ? '' : ' btn-accent'), type: 'button', title: st.done ? 'Opens it in your wizard' : 'Answers it in your wizard',
          onclick: () => wizard(p, t) }, h('span', { class: 'hat', 'aria-hidden': 'true', html: hatSvg(14) }), st.done ? 'Open in wizard' : 'Wizard it'),
        !readOnly && !st.done && st.answered > 0 ? h('button', { id: 'pvRoundMark', class: 'btn btn-quiet btn-small', type: 'button', title: st.brainstorm ? 'Every card not seen counts as skipped on purpose, and the hat turns teal' : 'Every open question counts as skipped on purpose, and the hat turns teal',
          onclick: () => { mark(p, t); const b = side() && $('#pvRoundWizard', side()); if (b) b.focus(); } }, 'Mark answered') : null,
        !readOnly ? h('button', { id: 'pvRoundRemove', class: 'btn btn-quiet btn-small pv-round-remove', type: 'button', title: 'Takes the round off this task; its file stays in the folder',
          onclick: () => remove(p, t) }, 'Remove') : null),
      ...[fold].filter(Boolean));
    return el;
  }
  /* The round in a small popup (0.1.69, Leader Bubbles, Round 2, C1: "it opens a small popup, and the same popup will
     open when we click Show the answers"): where it stands, its title and file, each question with its answer so far
     (Open, or Skipped once marked), and Open in wizard, which is Wizard it. Esc closes it. */
  function view(p, t) {
    const r = t && t.round;
    if (!r) return;
    const st = roundState(t), label = st.brainstorm ? 'Brainstorm, round ' + st.brainstorm : 'Wizard round';
    Panel.open(r.title, h('div', { class: 'cr-body rd-body' },
      h('div', { class: 'rd-head' }, hatEl(t, 16), h('span', { class: 'pv-round-lbl' }, label), h('span', { class: 'pv-round-state' }, roundStateText(st))),
      h('p', { class: 'rd-for', dir: 'auto' }, 'For ', h('bdi', null, t.text), ', in ', h('bdi', null, p.name), '.'),
      h('p', { class: 'pv-round-file', dir: 'ltr', title: roundPath(r) || ROUNDS_DIR + '\\' + r.file + ', in the Claude folder' }, ROUNDS_DIR + '\\' + r.file),
      answersList(r, st),
      h('div', { class: 'rd-btns' }, h('button', { id: 'rdWizard', class: 'btn btn-accent', type: 'button', title: st.done ? 'Opens it in your wizard' : 'Answers it in your wizard',
        onclick: () => { Panel.close(); wizard(p, t); } }, h('span', { class: 'hat', 'aria-hidden': 'true', html: hatSvg(14) }), 'Open in wizard'))), 'cr rd');
  }
  const side = () => $('#pvSide');
  function answersList(r, st) {
    if (isBrainstorm(r)) return h('ul', { class: 'pv-round-ans pv-round-brain' }, brainstormAnswerLines(r).map(line =>
      h('li', { class: /^\s/.test(line) ? 'sub' : null, dir: 'auto' }, line.replace(/^\s*(- )?/, ''))));
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

  return { wizard, openWizard, openLink, appLink, take, dropFile, poll, fromChange, mark, remove, hatButton, chip, card, view, dropLine, files, fileText, writeFile, readFile,
    answersLine, ANNOUNCE_MS };
})();
