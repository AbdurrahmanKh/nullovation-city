"""Wizard rounds in a task (0.1.55): idea 3 of the task ideas, from Tasks, Round 2 (W1 to W6) and Wizard Rounds in a
Task, Rounds 1 to 3. A task carries its own decision wizard round: made through Open in Claude's second row, attached
from Claude Code's inbox or by a file dropped on the task's panel, answered in the wizard through the Claude folder's
wizard-rounds or an answers file dropped back, its answers kept in the task, and a hat on the task's rows, gray until
answered, teal after. Since 0.1.65 Wizard it opens the wizard through a link carrying the round, which the installed app
takes, so the wizard opens this round whatever it had open. Since 0.1.66, with the Claude folder connected, it opens the
installed wizard app from any browser through a web+dwizard: link naming the round, or a tab, as Settings, Links says."""
import base64, json, pathlib
from urllib.parse import unquote
from playwright.sync_api import sync_playwright
from testkit import FILE, SHOTS, TEST_CITY, open_settings

errors = []
def ok(label, cond, got=None): print(('PASS ' if cond else 'FAIL ') + label + ('' if cond or got is None else '  (got ' + repr(got) + ')'))

TITLE = 'Draw the beds, Round 1'
ROUND = {"config": {"title": TITLE, "tagline": "The beds", "product": "Garden planner", "needs_wizard": "0.4.0"}, "questions": [
    {"id": "B1", "section": "Beds", "title": "Bed layout", "question": "How should the beds be laid out?", "options": ["Three rows", "A grid"],
     "followups": [{"id": "B1a", "when": ["A grid"], "title": "Grid paths", "question": "How wide are the paths?", "options": ["30 cm", "50 cm"]}]},
    {"id": "B2", "section": "Beds", "title": "Grid size", "question": "How big is one square of the grid?", "type": "number", "min": 10, "max": 60, "unit": "cm"},
    {"id": "B3", "section": "Beds", "title": "Paths", "question": "Should paths show on the grid?", "options": ["Yes", "No"]},
    {"id": "B4", "section": "Water", "title": "Watering", "question": "How often should the beds be watered?", "options": ["Daily", "Every 2 days"]},
    {"id": "B5", "section": "Water", "title": "Order", "question": "Which beds come first?", "type": "rank", "options": ["Herbs", "Greens", "Roots"]},
    {"id": "B6", "section": "Water", "title": "Sun", "question": "Should the plan show where the sun falls?", "options": ["Yes", "No"]},
    {"id": "B7", "section": "Rows", "title": "Plants to keep", "question": "Which plants stay in the first release?", "type": "batch", "options": ["Keep", "Drop"],
     "items": [{"id": "tomato", "label": "Tomatoes"}, {"id": "basil", "label": "Basil"}]},
    {"id": "B8", "section": "Rows", "title": "Export", "question": "Which file should a plan save as?", "options": ["PNG", "JSON"]},
]}
def answers(n, title=TITLE, with_round=False):
    """The wizard's answers file with the first n of the 8 answered, as the wizard saves them."""
    full = [
        {"id": "B1", "issue": "Bed layout", "question": "How should the beds be laid out?", "status": "picked", "answer": "A grid", "comment": "keep the middle path wide",
         "followups": [{"id": "B1a", "issue": "Grid paths", "question": "How wide are the paths?", "status": "picked", "answer": "50 cm"}]},
        {"id": "B2", "issue": "Grid size", "question": "How big is one square of the grid?", "status": "picked", "answer": 30, "unit": "cm"},
        {"id": "B3", "issue": "Paths", "question": "Should paths show on the grid?", "status": "custom", "answer": "Yes, in gravel grey"},
        {"id": "B4", "issue": "Watering", "question": "How often should the beds be watered?", "status": "picked", "answer": "Every 2 days"},
        {"id": "B5", "issue": "Order", "question": "Which beds come first?", "status": "ranked", "answer": ["Herbs", "Roots", "Greens"]},
        {"id": "B6", "issue": "Sun", "question": "Should the plan show where the sun falls?", "status": "picked", "answer": "Yes"},
        {"id": "B7", "issue": "Plants to keep", "question": "Which plants stay in the first release?", "status": "batch", "answered_items": 2, "total_items": 2,
         "items": [{"id": "tomato", "label": "Tomatoes", "answer": "Keep", "comment": ""}, {"id": "basil", "label": "Basil", "answer": "Drop", "comment": "next year"}]},
        {"id": "B8", "issue": "Export", "question": "Which file should a plan save as?", "status": "picked", "answer": "JSON"},
    ]
    out = []
    for i, a in enumerate(full):
        if i < n: out.append(a)
        else: out.append({"id": a["id"], "issue": a["issue"], "question": a["question"], "status": "open", "answer": ""})
    d = {"meta": {"tool": "decision-wizard", "wizard_version": "0.10.1", "wizard_title": title, "exported_at": "2026-10-22T18:00:00.000Z", "total": 8, "answered": n, "open": 8 - n}, "answers": out}
    if with_round: d["round"] = ROUND
    return d

# the Claude folder held in memory, as test24 does: the files Claude Code and the wizard would write, by path
FAKE = """
window.__cf = new Map(); window.__cperm = 'granted'; window.__cwperm = 'granted'; window.__ct = 1;
window.__sub = new Map(); window.__dirs = new Set(); window.__writes = 0;
const fail = n => { const e = new Error(n); e.name = n; throw e; };
const subfile = path => ({ kind: 'file', name: path.split('/').pop(),
  getFile: async () => { const f = window.__sub.get(path); if (!f) fail('NotFoundError'); return new File([f.text], path.split('/').pop(), { lastModified: f.t }); },
  createWritable: async () => { if (window.__cwperm !== 'granted') fail('NotAllowedError'); let buf = '';
    return { write: async d => { buf += d; }, close: async () => { window.__sub.set(path, { text: buf, t: Date.now() + (window.__ct++) }); window.__writes++; } }; } });
const subdirOf = (path, o) => { if (!(o && o.create) && !window.__dirs.has(path) && ![...window.__sub.keys()].some(k => k.startsWith(path + '/'))) fail('NotFoundError');
  if (o && o.create && window.__cwperm !== 'granted') fail('NotAllowedError'); window.__dirs.add(path); return subdir(path); };
const subdir = prefix => ({ kind: 'directory', name: prefix.split('/').pop(),
  getDirectoryHandle: async (n, o) => subdirOf(prefix + '/' + n, o),
  getFileHandle: async (n, o) => { const path = prefix + '/' + n; if (!window.__sub.has(path)) { if (!(o && o.create)) fail('NotFoundError'); if (window.__cwperm !== 'granted') fail('NotAllowedError'); } return subfile(path); },
  removeEntry: async n => { if (!window.__sub.has(prefix + '/' + n)) fail('NotFoundError'); window.__sub.delete(prefix + '/' + n); },
  entries: async function* () { const ds = new Set();
    for (const k of [...window.__sub.keys()]) { if (!k.startsWith(prefix + '/')) continue; const rest = k.slice(prefix.length + 1);
      if (rest.includes('/')) { const d = rest.split('/')[0]; if (!ds.has(d)) { ds.add(d); yield [d, subdir(prefix + '/' + d)]; } } else yield [rest, subfile(k)]; } } });
window.__subjson = path => { const f = window.__sub.get(path); return f ? JSON.parse(f.text) : null; };
window.__subput = (path, d) => window.__sub.set(path, { text: JSON.stringify(d), t: Date.now() + (window.__ct++) });
window.__cdir = { kind: 'directory', name: 'Claude',
  queryPermission: async o => (o && o.mode === 'readwrite') ? window.__cwperm : window.__cperm,
  requestPermission: async o => 'granted',
  getDirectoryHandle: async (n, o) => subdirOf(n, o),
  entries: async function* () { yield ['README-nullovation-city.txt', { kind: 'file', name: 'README-nullovation-city.txt', getFile: async () => new File(['x'], 'README-nullovation-city.txt') }]; } };
window.showDirectoryPicker = async () => window.__cdir;
/* the wizard: Wizard it is a link to it, opened by a click; every one is recorded here rather than followed */
window.__opened = [];
const anchorClick = HTMLAnchorElement.prototype.click;
HTMLAnchorElement.prototype.click = function () { const href = this.getAttribute('href') || '';
  if (this.target === '_blank' || /^web\+dwizard:/i.test(href)) { window.__opened.push([href, this.target, this.rel]); return; } return anchorClick.call(this); };
"""

with sync_playwright() as p:
    b = p.chromium.launch(channel='chrome')
    ctx = b.new_context(viewport={'width': 1440, 'height': 1000}, device_scale_factor=1, accept_downloads=True)
    ctx.add_init_script(TEST_CITY)
    ctx.add_init_script("try { if (!sessionStorage.getItem('nc-t37')) { sessionStorage.setItem('nc-t37', '1'); localStorage.setItem('nullovation-city:light', 'day'); localStorage.setItem('nullovation-city:bubbles', 'all'); } } catch (e) {}")
    ctx.add_init_script(FAKE)
    pg = ctx.new_page()
    pg.on('pageerror', lambda e: errors.append(str(e))); pg.on('console', lambda m: errors.append(m.text) if m.type in ('error', 'warning') else None)
    downloads = []
    pg.on('download', lambda d: downloads.append(d.suggested_filename))
    pg.goto(FILE); pg.wait_for_timeout(2200)
    ev = pg.evaluate
    gp = ev("() => DB.projects.find(p => p.name === 'Garden planner').id")
    T1, T2, T3 = 'Draw the beds on a grid', 'Save a plan as a file', 'Add plant icons'
    task = lambda text: f"getProject('{gp}').todos.find(t => t.text === {json.dumps(text)})"
    get = lambda text: ev(f"() => JSON.parse(JSON.stringify({task(text)} || null))")
    tid = lambda text: ev(f"() => {task(text)}.id")
    quiet = lambda: ev("() => { const t = document.querySelector('#toast'); t.className = 'toast'; t.textContent = ''; document.querySelectorAll('#gusSay, #pxSay').forEach(e => e.hidden = true); }")
    said = lambda: ev("() => { const t = document.querySelector('#toast'); return t.classList.contains('show') ? t.firstChild.textContent : ''; }")
    undo = lambda: ev("() => { const b = document.querySelector('#toast.show .toast-act'); if (!b) return false; b.click(); return true; }")
    proj = lambda: ev(f"() => JSON.parse(JSON.stringify(getProject('{gp}')))")
    state = lambda text: ev(f"() => roundState({task(text)})")
    def open_view():
        ev(f"() => FullView.open('{gp}')"); pg.wait_for_timeout(450); quiet()
    def open_task(text):
        open_view()
        pg.click(f'li.task[data-id="{tid(text)}"] .task-title'); pg.wait_for_timeout(300); quiet()
    def drop(name, data, over_only=False):
        """A file dragged over the task's panel, then dropped on it, as from File Explorer."""
        text = data if isinstance(data, str) else json.dumps(data)
        r = ev("""async ([name, text, overOnly]) => { const dt = new DataTransfer(); dt.items.add(new File([text], name, { type: 'application/json' }));
          const side = document.querySelector('#pvSide'), slot = side.querySelector('.pv-round-slot');
          side.dispatchEvent(new DragEvent('dragover', { dataTransfer: dt, bubbles: true, cancelable: true }));
          const shown = slot && slot.querySelector('.pv-round-drop') ? slot.querySelector('.pv-round-drop').textContent : '';
          if (overOnly) return shown;
          side.dispatchEvent(new DragEvent('drop', { dataTransfer: dt, bubbles: true, cancelable: true }));
          return shown; }""", [name, text, over_only])
        pg.wait_for_timeout(300)
        return r
    opened = lambda: ev("() => window.__opened.slice()")
    def unlink(href):
        """The wizard's address and what a Wizard it link carries after #open=, as the wizard reads it."""
        base, _, code = href.partition('#open=')
        return base, json.loads(base64.urlsafe_b64decode(code + '=' * (-len(code) % 4)).decode('utf-8'))
    sent = lambda: unlink(opened()[-1][0])
    def unref(href):
        """What a web+dwizard: link names, as the wizard app reads it."""
        assert href.startswith('web+dwizard:open/'), href
        code = href[len('web+dwizard:open/'):]
        return json.loads(base64.urlsafe_b64decode(code + '=' * (-len(code) % 4)).decode('utf-8'))
    hat = lambda sel: ev(f"() => {{ const b = document.querySelector({json.dumps(sel)}); return b ? (b.classList.contains('hat-done') || !!b.querySelector('.hat-done') ? 'done' : 'open') : null; }}")
    quiet()

    # ---------- the model: a wizard's files, and where a round stands ----------
    rd = ev(f"() => readWizardFile({json.dumps(ROUND)})")
    ok('a round file reads as a round with no answers', rd and rd['round']['config']['title'] == TITLE and rd['answers'] is None)
    an = ev(f"() => readWizardFile({json.dumps(answers(3))})")
    ok('an answers file reads as answers, with no round', an and an['round'] is None and an['answers']['meta']['answered'] == 3)
    aw = ev(f"() => readWizardFile({json.dumps(answers(3, with_round=True))})")
    ok('an answers file the wizard saved carries the round under it, and reads as both', aw and aw['round']['config']['title'] == TITLE and aw['answers'] is not None)
    ok('anything else is not a wizard file: no title, no questions, a question without an id, another tool',
       ev("""() => [readWizardFile({ config: {}, questions: [{ id: 'A' }] }), readWizardFile({ config: { title: 'X' }, questions: [] }),
         readWizardFile({ config: { title: 'X' }, questions: [{ title: 'no id' }] }), readWizardFile({ meta: { tool: 'other' }, answers: [] }), readWizardFile('x')].every(x => x === null)"""))
    ok('a round\'s file is a name in wizard-rounds, never a path', ev("() => [safeRoundFile('r1.json'), safeRoundFile('..\\\\up.json'), safeRoundFile('a/b.json'), safeRoundFile('x.txt')]") == ['r1.json', 'up.json', 'b.json', ''])
    mk = ev(f"() => makeRound(readWizardFile({json.dumps({**ROUND, 'config': {**ROUND['config'], 'folder': 'D:\\City\\Claude\\wizard-rounds', 'project': 'Nullovation City'}})}), '2026-10-22-draw-the-beds-round1.json')")
    ok('a round keeps its title, its file and the folder it names', mk['title'] == TITLE and mk['file'] == '2026-10-22-draw-the-beds-round1.json' and mk['folder'] == 'D:\\City\\Claude\\wizard-rounds' and mk['a'] is None and mk['marked'] is False)
    ok('with no file name, a round is named by the day and its title', ev(f"() => makeRound(readWizardFile({json.dumps(ROUND)}), '').file").endswith('-draw-the-beds-round-1.json'))
    st = lambda r, marked=False: ev(f"() => roundState({{ round: {{ ...makeRound(readWizardFile({json.dumps(ROUND)}), 'r.json'), a: {json.dumps(r)}, marked: {json.dumps(marked)} }} }})")
    s0, s3, s8, sm, sm0 = st(None), st(answers(3)), st(answers(8)), st(answers(3), True), st(answers(0), True)
    ok(f'no answers: 0 of 8, waiting ({s0})', s0['answered'] == 0 and s0['total'] == 8 and not s0['done'])
    ok(f'3 of 8: still waiting, the hat gray (A1: answered when nothing is open) ({s3})', s3['answered'] == 3 and s3['open'] == 5 and not s3['done'])
    ok('8 of 8: answered', s8['done'] and s8['open'] == 0)
    ok(f'3 of 8 marked answered: answered, 5 skipped (S1) ({sm})', sm['done'] and sm['skipped'] == 5 and sm['marked'])
    ok('marked with nothing answered is still waiting', not sm0['done'])
    ok('the card\'s words for each', ev(f"() => [{json.dumps(s0)}, {json.dumps(s3)}, {json.dumps(s8)}, {json.dumps(sm)}].map(roundStateText)")
       == ['Waiting: 0 of 8 answered', 'Waiting: 3 of 8 answered', 'Answered: 8 of 8', 'Answered: 3 of 8, 5 skipped'])
    ok('and Claude\'s', ev(f"() => [{json.dumps(s0)}, {json.dumps(s3)}, {json.dumps(s8)}, {json.dumps(sm)}].map(roundWords)")
       == ['Waiting for answers (8 questions)', '3 of 8 answered', 'Answered, 8 of 8', '3 of 8 answered, 5 skipped on purpose'])

    # ---------- the round in a copy for Claude, with no Claude folder: the answers written in ----------
    ev(f"() => {{ const t = {task(T1)}; t.round = makeRound(readWizardFile({json.dumps(ROUND)}), 'r1.json'); t.round.a = {json.dumps(answers(8))}; }}")
    copy = ev(f"() => taskForClaude(getProject('{gp}'), {task(T1)})")
    lines = copy.split('\n')
    ok('Copy task carries the round after the description, under its title', '## Wizard round: ' + TITLE in lines and lines.index('## Wizard round: ' + TITLE) > lines.index('## Description'))
    ok('then where it stands', 'Answered, 8 of 8.' in lines)
    ok('then each answer with its id, title and question, and the note',
       '- B1, Bed layout: How should the beds be laid out? A grid. Note: keep the middle path wide.' in lines, [l for l in lines if l.startswith('- B1')])
    ok('a follow-up under its question', '  - B1a, Grid paths: How wide are the paths? 50 cm.' in lines)
    ok('a number with its unit, a typed answer, a ranking in its order',
       '- B2, Grid size: How big is one square of the grid? 30 cm.' in lines and '- B3, Paths: Should paths show on the grid? Yes, in gravel grey.' in lines
       and '- B5, Order: Which beds come first? In this order: Herbs, Roots, Greens.' in lines)
    ok('a batch with each of its rows and their notes', '- B7, Plants to keep: Which plants stay in the first release? 2 of 2 rows answered.' in lines
       and '  - Tomatoes: Keep.' in lines and '  - Basil: Drop. Note: next year.' in lines)
    ok('and the update line still ends it', lines[-1] == 'When you finish, send Nullovation City an update with the nullovation-city skill.')
    ev(f"() => {{ {task(T1)}.round.a = {json.dumps(answers(3))}; }}")
    lines = ev(f"() => taskForClaude(getProject('{gp}'), {task(T1)})").split('\n')
    ok('a round partly answered: 3 of 8, and the open ones say Open', '3 of 8 answered.' in lines and '- B4, Watering: How often should the beds be watered? Open.' in lines)
    ev(f"() => {{ {task(T1)}.round.marked = true; }}")
    lines = ev(f"() => taskForClaude(getProject('{gp}'), {task(T1)})").split('\n')
    ok('marked answered: the open ones say Skipped', '3 of 8 answered, 5 skipped on purpose.' in lines and '- B4, Watering: How often should the beds be watered? Skipped.' in lines)
    ev(f"() => {{ const r = {task(T1)}.round; r.marked = false; r.a = null; }}")
    lines = ev(f"() => taskForClaude(getProject('{gp}'), {task(T1)})").split('\n')
    ok('a round with no answers yet: one line, waiting', 'Waiting for answers (8 questions).' in lines and not any(l.startswith('- B') for l in lines))
    ask = ev(f"() => taskForClaude(getProject('{gp}'), {task(T1)}, Date.now(), {{ ask: true }})").split('\n')
    ok('Make a wizard round\'s copy ends with its request, in place of the update line', ask[-1] == ev("() => ROUND_LINE") and 'When you finish' not in '\n'.join(ask)
       and ask[-1].startswith('Plan this task further with a decision wizard round: write it with the d-wizard skill'))
    ok('a milestone\'s copy names the round under its task', f'Wizard round: {TITLE} (waiting for answers (8 questions))' in ev(f"() => milestoneForClaude(getProject('{gp}'), getProject('{gp}').milestones[0])"))
    ok('a task with no round says nothing of one', '## Wizard round' not in ev(f"() => taskForClaude(getProject('{gp}'), {task(T2)})"))

    # ---------- saved data ----------
    ev("() => persistNow()")
    pg.reload(); pg.wait_for_timeout(2200); quiet()
    r = get(T1)['round']
    ok('a round survives a reload, whole', r and r['title'] == TITLE and len(r['q']['questions']) == 8 and r['file'] == 'r1.json')
    ok('reading a city drops a broken round and keeps the task', ev("""() => { const raw = JSON.parse(JSON.stringify(DB.projects)); const t = raw.find(p => p.name === 'Garden planner').todos[0];
       t.round = { q: { config: {}, questions: 'no' } }; const k = sanitizeProjects(raw).map(x => x.p); const u = k.find(p => p.name === 'Garden planner').todos[0]; return !u.round && u.text === 'Draw the beds on a grid'; }"""))
    ok('a round over the size a task may carry is dropped', ev("""() => { const raw = JSON.parse(JSON.stringify(DB.projects)); const t = raw.find(p => p.name === 'Garden planner').todos[0];
       t.round.q.questions[0].question = 'x'.repeat(400000); return !sanitizeProjects(raw).map(x => x.p).find(p => p.name === 'Garden planner').todos[0].round; }"""))
    bk = ev(f"async () => {{ const b = await buildBackup(); return b.projects.find(p => p.id === '{gp}').todos[0].round.title; }}")
    ok('a backup and the data file carry it', bk == TITLE)
    ev(f"() => {{ delete {task(T1)}.round; changed(getProject('{gp}'), {{ touch: false }}); }}")

    # ---------- a round file dropped on the task's panel (W1, P2) ----------
    open_task(T1)
    ok('a task with no round: no card, and no line until a file comes (P2)', pg.locator('#pvSide .pv-round').count() == 0 and pg.locator('#pvSide .pv-round-drop').count() == 0)
    over = drop('2026-10-22-draw-the-beds-round1.json', ROUND, over_only=True)
    ok(f'a file dragged over the panel lights the line ({over})', over == 'Drop the round file to attach it to this task')
    pg.screenshot(path=str(SHOTS / '370-drop-line.png'), clip=pg.query_selector('#pvSide').bounding_box())
    ev("() => document.querySelector('#pvSide').dispatchEvent(new DragEvent('dragleave', { bubbles: true, relatedTarget: document.body }))")
    ok('and it goes when the file leaves the panel', pg.locator('#pvSide .pv-round-drop').count() == 0)
    before = proj()
    drop('2026-10-22-draw-the-beds-round1.json', ROUND)
    t1 = get(T1)
    ok('dropped, the round attaches to the task, by its own file name', t1['round'] and t1['round']['title'] == TITLE and t1['round']['file'] == '2026-10-22-draw-the-beds-round1.json')
    ok(f'with a toast and Undo ({said()})', said() == 'Attached ' + TITLE + ' to ' + T1 + '.' and pg.locator('#toast.show .toast-act').count() == 1)
    after = proj()
    ok('it is not work: Updated, urgency and Activity stay', after['updatedAt'] == before['updatedAt'] and len(after['activity']) == len(before['activity']))
    ok('the card shows under Pin and Star, before the description (P1)', ev("""() => { const s = document.querySelector('#pvSide'), c = s.querySelector('.pv-round'), m = s.querySelector('.pv-task-marks'), d = s.querySelector('#pvTaskDesc');
       return !!c && !!(m.compareDocumentPosition(c) & 4) && !!(c.compareDocumentPosition(d) & 4); }"""))
    ok('its head: a gray hat, Wizard round, and Waiting: 0 of 8 answered', hat('#pvSide .pv-round-head .hat') == 'open' and pg.text_content('#pvSide .pv-round-state') == 'Waiting: 0 of 8 answered'
       and pg.text_content('#pvSide .pv-round-lbl') == 'Wizard round')
    ok('its title and its file in wizard-rounds', pg.text_content('#pvSide .pv-round-title') == TITLE and pg.text_content('#pvSide .pv-round-file') == 'wizard-rounds\\2026-10-22-draw-the-beds-round1.json')
    ok('Wizard it and Remove; no Mark answered with nothing answered, and no answers to show',
       pg.text_content('#pvRoundWizard').strip() == 'Wizard it' and pg.is_visible('#pvRoundRemove') and pg.locator('#pvRoundMark').count() == 0 and pg.locator('#pvSide .pv-round-fold').count() == 0)
    pg.screenshot(path=str(SHOTS / '371-card-waiting.png'), clip=pg.query_selector('#pvSide').bounding_box())
    ok('Undo takes it off again', undo() and not get(T1).get('round') and pg.locator('#pvSide .pv-round').count() == 0)
    drop('2026-10-22-draw-the-beds-round1.json', ROUND); quiet()

    # Wizard it with no Claude folder: the wizard opens on the round, through a link the installed app takes (0.1.65)
    n_dl = len(downloads)
    pg.click('#pvRoundWizard'); pg.wait_for_timeout(300)
    base, got = sent()
    ok(f'Wizard it opens the hosted wizard through a link to a new tab, which the installed app takes ({opened()[-1][1:]})',
       base == 'https://abdurrahmankh.github.io/decision-wizard/' and opened()[-1][1:] == ['_blank', 'noopener'])
    ok("the link carries the round and its file's name, with no answers yet", got['app'] == 'nullovation-city' and got['kind'] == 'open-round'
       and got['file'] == '2026-10-22-draw-the-beds-round1.json' and got['round'] == ROUND and got['answers'] is None)
    ok('nothing downloads, and the link leaves nothing in the page', len(downloads) == n_dl and pg.locator('body > a[target="_blank"]').count() == 0)
    ok(f'saying what to do with its answers ({said()})', said() == 'Opening ' + TITLE + ' in your wizard. Once it is answered, save its file there and drop it on this task.')
    ar = ev("() => Rounds.openLink({ file: 'r.json', q: { config: { title: 'خطة الحديقة' }, questions: [{ id: 'A', question: 'أين؟' }] }, a: null })")
    ok('Arabic travels whole in the link', unlink(ar)[1]['round']['questions'][0]['question'] == 'أين؟' and unlink(ar)[1]['round']['config']['title'] == 'خطة الحديقة')
    quiet()

    # the answers dropped back
    drop('Draw the beds, Round 1-answers-2026-10-22.json', answers(3))
    ok(f'its answers file dropped on the task brings the answers in ({said()})', said() == 'Answers in for ' + T1 + ': 3 of 8.' and get(T1)['round']['a']['meta']['answered'] == 3)
    ok('the card says 3 of 8, the hat still gray', pg.text_content('#pvSide .pv-round-state') == 'Waiting: 3 of 8 answered' and hat('#pvSide .pv-round-head .hat') == 'open')
    pg.click('#pvRoundWizard'); pg.wait_for_timeout(200)
    ok('Wizard it now carries the answers so far, so a wizard without the round gets them too', sent()[1]['answers']['meta']['answered'] == 3
       and sent()[1]['answers'] == answers(3) and sent()[1]['round']['config']['title'] == TITLE)
    quiet()
    ok('with Mark answered now, and the answers folded (P1a)', pg.is_visible('#pvRoundMark') and pg.text_content('#pvSide .pv-round-fold').strip() == 'Show the answers'
       and pg.locator('#pvSide .pv-round-ans').count() == 0 and pg.get_attribute('#pvSide .pv-round-fold', 'aria-expanded') == 'false')
    pg.screenshot(path=str(SHOTS / '372-card-folded.png'), clip=pg.query_selector('#pvSide').bounding_box())
    pg.click('#pvSide .pv-round-fold'); pg.wait_for_timeout(150)
    li = ev("() => [...document.querySelectorAll('#pvSide .pv-round-ans li')].map(l => [l.className, l.querySelector('.id').textContent, l.querySelector('.a').textContent])")
    ok(f'a click shows every question with its answer ({len(li)})', len(li) == 8 and li[0][1:] == ['B1', 'A grid'] and li[1][2] == '30 cm' and li[2][2] == 'Yes, in gravel grey')
    ok('the open ones say Open', li[3] == ['open', 'B4', 'Open'] and li[7] == ['open', 'B8', 'Open'])
    ok('a note and a follow-up under their answer', 'Note: keep the middle path wide' in pg.text_content('#pvSide .pv-round-ans li:first-child') and 'Grid paths: 50 cm' in pg.text_content('#pvSide .pv-round-ans li:first-child'))
    ok('the focus stays on the fold', ev("() => document.activeElement && document.activeElement.classList.contains('pv-round-fold')") and pg.get_attribute('#pvSide .pv-round-fold', 'aria-expanded') == 'true')
    pg.screenshot(path=str(SHOTS / '373-card-answers.png'), clip=pg.query_selector('#pvSide').bounding_box())
    open_task(T1)
    ok('the panel opened again starts folded (P1a)', pg.locator('#pvSide .pv-round-ans').count() == 0)

    # what will not attach
    drop('other-answers.json', answers(3, title='Another round, Round 4'))
    ok(f'answers to another round are refused, saying why ({said()})', said() == 'Those answers are for Another round, Round 4, not ' + TITLE + '.' and get(T1)['round']['a']['meta']['answered'] == 3)
    drop('notes.txt', 'just words')
    ok(f'a file that is not .json is refused ({said()})', said().startswith('That is not a round'))
    drop('broken.json', '{ not json')
    ok(f'and so is one that is not a wizard file ({said()})', said() == 'broken.json is not a decision wizard round or its answers.')
    open_task(T3)
    drop('lost-answers.json', answers(2))
    ok(f'answers dropped on a task with no round ask for the round first ({said()})', 'this task has no round' in said() and not get(T3).get('round'))
    quiet()

    # Mark answered (S1), and Remove
    open_task(T1)
    pg.click('#pvRoundMark'); pg.wait_for_timeout(150)
    ok(f'Mark answered: the round counts as answered, the rest skipped ({said()})', said() == 'Marked answered: 5 questions skipped.' and pg.text_content('#pvSide .pv-round-state') == 'Answered: 3 of 8, 5 skipped')
    ok('the hat turns teal, the card\'s edge too, and Wizard it reads Open in wizard', hat('#pvSide .pv-round-head .hat') == 'done' and ev("() => document.querySelector('#pvSide .pv-round').classList.contains('done')")
       and pg.text_content('#pvRoundWizard').strip() == 'Open in wizard' and pg.locator('#pvRoundMark').count() == 0)
    pg.click('#pvSide .pv-round-fold'); pg.wait_for_timeout(150)
    ok('its open questions say Skipped', ev("() => [...document.querySelectorAll('#pvSide .pv-round-ans li.skip .a')].map(a => a.textContent)") == ['Skipped'] * 5)
    pg.screenshot(path=str(SHOTS / '374-card-marked.png'), clip=pg.query_selector('#pvSide').bounding_box())
    ok('Undo takes the mark back', undo() and not get(T1)['round']['marked'] and pg.text_content('#pvSide .pv-round-state') == 'Waiting: 3 of 8 answered')
    quiet()
    pg.click('#pvRoundRemove'); pg.wait_for_timeout(150)
    ok(f'Remove takes the round off the task, its file left ({said()})', said() == 'Took ' + TITLE + ' off this task. Its file stays in the folder.' and not get(T1).get('round') and pg.locator('#pvSide .pv-round').count() == 0)
    ok('Undo puts it back, answers and all', undo() and get(T1)['round']['a']['meta']['answered'] == 3)
    quiet()
    # Esc in the panel undoes what was typed, and leaves the round, as it leaves pins
    pg.fill('#pvTaskDesc', 'Typed, then undone'); pg.wait_for_timeout(100)
    drop('Draw the beds, Round 1-answers.json', answers(4)); quiet()
    pg.keyboard.press('Escape'); pg.wait_for_timeout(300)
    ok('Esc in the panel undoes the typing and keeps the round with the answers that came while it was open',
       get(T1)['description'] == '' and get(T1)['round']['a']['meta']['answered'] == 4)
    quiet()

    # ---------- the hats (W5, X1, A2, H1) ----------
    open_view()
    ok('a gray hat on the task\'s row in the project view', hat(f'li.task[data-id="{tid(T1)}"] .round-hat') == 'open')
    ok('no hat on a task with no round', pg.locator(f'li.task[data-id="{tid(T2)}"] .round-hat').count() == 0)
    ok('the hat\'s tooltip says where it stands', pg.get_attribute(f'li.task[data-id="{tid(T1)}"] .round-hat', 'title') == 'Wizard round: 4 of 8 answered. Click to answer it in your wizard')
    ok('What is next has the round\'s chip beside the pin: 4 of 8', pg.text_content('#pvNextRound').strip() == '4 of 8' and hat('#pvNextRound .hat') == 'open'
       and ev("() => { const c = document.querySelector('#pvNextRound'), pin = document.querySelector('.pv-next-marks .task-mark'); return !!pin && !!(c.compareDocumentPosition(pin) & 4); }"))
    pg.screenshot(path=str(SHOTS / '375-row-and-next.png'), clip={'x': 290, 'y': 690, 'width': 750, 'height': 310})
    n0 = len(opened())
    box = pg.query_selector(f'li.task[data-id="{tid(T1)}"] .round-hat').bounding_box()
    pg.mouse.move(box['x'] + box['width'] / 2, box['y'] + box['height'] / 2); pg.mouse.down(); pg.mouse.up(); pg.wait_for_timeout(200)
    ok('a click on the row\'s hat is Wizard it, and neither opens nor drags the task', len(opened()) == n0 + 1 and pg.locator('#pvSide').count() == 0)
    quiet()
    pg.click('#pvNextRound'); pg.wait_for_timeout(150)
    ok('and so is a click on What is next\'s chip', len(opened()) == n0 + 2)
    quiet()
    # the status card, All tasks and the hover
    ev("() => FullView.close()"); pg.wait_for_timeout(300)
    ev(f"() => Bubble.open('{gp}')"); pg.wait_for_timeout(500)
    ok('the status card\'s row wears it, before the pin', hat(f'.b-todos li[data-id="{tid(T1)}"] .round-hat') == 'open'
       and ev(f"() => {{ const li = document.querySelector('.b-todos li[data-id=\"{tid(T1)}\"]'); const kids = [...li.children]; return kids.indexOf(li.querySelector('.round-hat')) === kids.indexOf(li.querySelector('.b-task')) + 1; }}"))
    ok('a row without a round shows nothing in its place, not "null"', ev("() => ![...document.querySelectorAll('.b-todos li')].some(li => /null/.test(li.textContent))")
       and ev("() => [...document.querySelectorAll('.b-todos li')].filter(li => li.querySelector('.round-hat')).length") == 1)
    pg.screenshot(path=str(SHOTS / '376-status-card.png'), clip=pg.query_selector('#bubble').bounding_box())
    ev("() => MapView.deselect()"); pg.wait_for_timeout(200)
    ev("() => AllTasks.open()"); pg.wait_for_timeout(400)
    at = ev(f"() => {{ const r = document.querySelector('#atList .at-row[data-id=\"{tid(T1)}\"]'); return r && r.querySelector('.at-meta .round-hat') ? r.querySelector('.at-meta .round-hat').className : null; }}")
    ok(f'All tasks wears it at the start of the row\'s line ({at})', at and 'hat-open' in at)
    ev("() => AllTasks.close()"); pg.wait_for_timeout(200)
    ev("() => MapView.setCam({ x: 0, y: 230, z: 2 })"); pg.wait_for_timeout(300)
    left = ev("() => document.querySelector('#mapWrap').getBoundingClientRect().left")
    a = ev(f"() => MapView.anchors('{gp}')")
    pg.mouse.move(left + a['topX'] - 30, (a['topY'] + a['baseY']) / 2); pg.mouse.move(left + a['topX'], (a['topY'] + a['baseY']) / 2); pg.wait_for_timeout(600)
    ok('the hover\'s next-task line wears it, beside the pin', pg.is_visible('#hoverTask') and pg.locator('#hoverTask .hat-open').count() == 1 and 'Draw the beds' in pg.text_content('#hoverTask'))
    pg.screenshot(path=str(SHOTS / '377-hover.png'), clip={'x': left + a['topX'] - 170, 'y': a['topY'] - 80, 'width': 340, 'height': 150})
    pg.mouse.move(left + 40, 40); pg.wait_for_timeout(200)

    # answered: teal everywhere
    ev(f"() => {{ const t = {task(T1)}; t.round.a = {json.dumps(answers(8))}; changed(getProject('{gp}'), {{ touch: false }}); }}"); pg.wait_for_timeout(200)
    pg.mouse.move(left + a['topX'] - 30, (a['topY'] + a['baseY']) / 2); pg.mouse.move(left + a['topX'], (a['topY'] + a['baseY']) / 2); pg.wait_for_timeout(600)
    ok('answered, the hover\'s hat is teal', pg.locator('#hoverTask .hat-done').count() == 1)
    pg.mouse.move(left + 40, 40); pg.wait_for_timeout(200)
    open_view()
    ok('and so are the row\'s hat and What is next\'s chip, which says Answered', hat(f'li.task[data-id="{tid(T1)}"] .round-hat') == 'done' and pg.text_content('#pvNextRound').strip() == 'Answered' and hat('#pvNextRound .hat') == 'done')
    pg.screenshot(path=str(SHOTS / '378-answered.png'), clip={'x': 290, 'y': 690, 'width': 750, 'height': 310})
    # a ticked task keeps its round and wears no hat
    ev(f"() => {{ const p = getProject('{gp}'), t = {task(T2)}; t.round = makeRound(readWizardFile({json.dumps(ROUND)}), 'r2.json'); tickTask(p, t); changed(p); }}")
    open_view()
    ok('a ticked task keeps its round and wears no hat', get(T2)['round'] and pg.locator(f'li.task[data-id="{tid(T2)}"] .round-hat').count() == 0)
    pg.click(f'li.task[data-id="{tid(T2)}"] .task-title'); pg.wait_for_timeout(300)
    ok('its panel still shows the card', pg.is_visible('#pvSide .pv-round'))
    ok('a done task\'s Open in Claude has no Think tab (A2)', ev("() => { document.querySelector('#pvTaskClaude').click(); return !!document.querySelector('.oc-panel') && !document.querySelector('.oc-panel .oc-tabs'); }"))
    pg.keyboard.press('Escape'); pg.wait_for_timeout(100)
    ev(f"() => {{ const p = getProject('{gp}'), t = {task(T2)}; untickTask(p, t); delete t.round; changed(p); }}")

    # ---------- Open in Claude: the Think tab, a wizard round or a brainstorm (0.1.63) ----------
    TILES = "() => [...document.querySelectorAll('.oc-panel .oc-tile')].map(a => [a.dataset.kind, a.tagName, a.getAttribute('href') || ''])"
    open_task(T1)
    pg.click('#pvTaskClaude'); pg.wait_for_timeout(200)
    ok('an open task\'s panel opens on Build it, with Think beside it', ev("() => [...document.querySelectorAll('.oc-panel .oc-tab')].map(t => t.textContent.trim() + (t.classList.contains('on') ? '*' : '')).join()") == 'Build it*,Think')
    main_chat = unquote(ev("() => document.querySelector('.oc-panel .oc-tile[data-kind=\"chat\"]').getAttribute('href')").split('q=', 1)[1])
    ok('Build it\'s Chat sends the copy with the answers written in', main_chat.endswith('When you finish, send Nullovation City an update with the nullovation-city skill.') and '- B8, Export: Which file should a plan save as? JSON.' in main_chat)
    pg.click('#ocTabThink'); pg.wait_for_timeout(150)
    row = ev(TILES)
    ok(f'Think has the same tiles: Chat, Cowork, Code, Terminal and Copy ({[r[:2] for r in row]})', [r[0] for r in row] == ['chat', 'cowork', 'code', 'terminal', 'copy'])
    ok('Code and Terminal wait for a folder link there too', row[2][1] == 'SPAN' and row[3][1] == 'SPAN' and row[0][1] == 'A' and row[1][1] == 'A')
    ok('Think has the brainstorm box, unticked', pg.is_visible('#ocBrainstorm') and not pg.is_checked('#ocBrainstorm'))
    chat_q = unquote(row[0][2].split('q=', 1)[1].split('&')[0])
    ok('its Chat sends the task asking for a round, the answers so far written in (C1)', chat_q.endswith(ev("() => ROUND_LINE")) and '- B1, Bed layout:' in chat_q and chat_q.startswith('# Task: ' + T1))
    pg.screenshot(path=str(SHOTS / '379-menu.png'))
    pg.click('#ocBrainstorm'); pg.wait_for_timeout(150)
    row = ev(TILES)
    bs_q = unquote(row[0][2].split('q=', 1)[1].split('&')[0])
    ok('ticked, it asks for a brainstorm instead', bs_q.endswith(ev("() => BRAINSTORM_LINE")) and bs_q.startswith('# Task: ' + T1) and pg.is_checked('#ocBrainstorm'))
    ev("() => { window.__clip = ''; navigator.clipboard.writeText = t => { window.__clip = t; return Promise.resolve(); }; }")
    pg.click('.oc-panel .oc-tile[data-kind="copy"]'); pg.wait_for_timeout(200)
    ok('and Copy copies that, saying so', ev("() => window.__clip").endswith(ev("() => BRAINSTORM_LINE")) and 'a brainstorm on this task' in pg.text_content('#toast') and not pg.is_visible('.oc-panel'))
    ev(f"() => {{ getProject('{gp}').links.push({{ id: 'l_g', label: '', url: 'C:\\\\Users\\\\me\\\\garden', icon: 'folder', shortcut: true }}); changed(getProject('{gp}'), {{ touch: false }}); }}")
    open_task(T1)
    pg.click('#pvTaskClaude'); pg.wait_for_timeout(200)
    ok('the panel opens on Build it again, the box unticked', ev("() => document.querySelector('#ocTabBuild').classList.contains('on')"))
    pg.click('#ocTabThink'); pg.wait_for_timeout(150)
    row = ev(TILES)
    ok('with a folder link, Code and Terminal open Claude Code there, asked for a round', row[2][1] == 'A' and 'folder=C%3A%5CUsers%5Cme%5Cgarden' in row[2][2] and row[3][1] == 'A' and 'cwd=' in row[3][2]
       and unquote(row[3][2].split('q=', 1)[1].split('&')[0]).endswith(ev("() => ROUND_LINE")))
    pg.keyboard.press('Escape'); pg.wait_for_timeout(100)
    ok('What is next\'s Open in Claude has Think too', ev("() => { document.querySelector('#pvNextClaude').click(); return !!document.querySelector('.oc-panel #ocTabThink'); }"))
    pg.keyboard.press('Escape'); pg.wait_for_timeout(100)
    ok('a note\'s and a milestone\'s do not', ev("""() => { document.querySelector('.ms-name-btn').click(); return new Promise(r => setTimeout(() => { document.querySelector('#pvMsClaude').click(); r(!!document.querySelector('.oc-panel') && !document.querySelector('.oc-panel .oc-tabs')); }, 200)); }"""))
    pg.keyboard.press('Escape'); pg.wait_for_timeout(100)

    # a new round replaces the old one (W6)
    open_task(T1)
    R2 = {**ROUND, 'config': {**ROUND['config'], 'title': 'Draw the beds, Round 2'}, 'questions': ROUND['questions'][:2]}
    drop('2026-10-23-draw-the-beds-round2.json', R2)
    ok(f'a new round dropped replaces the old one, saying so (W6) ({said()})', said() == 'Attached Draw the beds, Round 2 to ' + T1 + '. It replaces ' + TITLE + '.'
       and get(T1)['round']['title'] == 'Draw the beds, Round 2' and get(T1)['round']['a'] is None)
    ok('the hat is gray again', hat(f'li.task[data-id="{tid(T1)}"] .round-hat') == 'open' and pg.text_content('#pvSide .pv-round-state') == 'Waiting: 0 of 2 answered')
    ok('Undo brings the old one back, answered', undo() and get(T1)['round']['title'] == TITLE and get(T1)['round']['a']['meta']['answered'] == 8)
    drop('round1-again.json', answers(5, with_round=True))
    ok('the same round dropped again, with answers the wizard saved, updates it in place', get(T1)['round']['a']['meta']['answered'] == 5 and get(T1)['round']['file'] == '2026-10-22-draw-the-beds-round1.json'
       and said() == 'Updated ' + TITLE + ' in ' + T1 + ': 5 of 8 answered.')
    quiet()

    # ---------- Settings, Links: the wizard's address ----------
    ev("() => FullView.close()"); pg.wait_for_timeout(200)
    open_settings(pg, 'links')
    ok('Settings, Links has Wizard app and Browser tab, the app pressed by default', ev("() => [...document.querySelectorAll('#optWizardOpen .set-choice')].map(b => b.textContent + ':' + b.getAttribute('aria-pressed'))") == ['Wizard app:true', 'Browser tab:false']
       and not ev("() => document.querySelector('[data-set=\"wizardOpen\"]').classList.contains('changed')"))
    ok('Settings, Links has the wizard\'s address, empty for the hosted one', pg.is_visible('#optWizard') and pg.input_value('#optWizard') == '' and pg.get_attribute('#optWizard', 'placeholder') == 'https://abdurrahmankh.github.io/decision-wizard/')
    pg.fill('#optWizard', 'file:///D:/Tools/decision-wizard/index.html'); pg.press('#optWizard', 'Tab'); pg.wait_for_timeout(150)
    ok('an address of your own is kept on this computer, with its dot', ev("() => localStorage.getItem('nullovation-city:wizard')") == 'file:///D:/Tools/decision-wizard/index.html'
       and ev("() => document.querySelector('[data-set=\"wizard\"]').classList.contains('changed')"))
    pg.fill('#optWizard', 'not an address'); pg.press('#optWizard', 'Tab'); pg.wait_for_timeout(150)
    ok(f'one that is not an address is refused ({said()})', 'starts with https://' in said() and pg.input_value('#optWizard') == 'file:///D:/Tools/decision-wizard/index.html')
    quiet()
    open_task(T1)
    pg.click('#pvRoundWizard'); pg.wait_for_timeout(200)
    ok('Wizard it opens your own copy, with the round', sent()[0] == 'file:///D:/Tools/decision-wizard/index.html' and sent()[1]['round']['config']['title'] == TITLE)
    quiet()
    ev("() => FullView.close()"); pg.wait_for_timeout(200)
    open_settings(pg, 'links')
    pg.click('#btnTabReset'); pg.wait_for_timeout(150)
    ok('Reset to defaults goes back to the hosted wizard', pg.input_value('#optWizard') == '' and ev("() => wizardUrl()") == 'https://abdurrahmankh.github.io/decision-wizard/')
    pg.click('#optWizardOpen [data-value="tab"]'); pg.wait_for_timeout(150)
    ok('Browser tab is kept on this computer, with its dot', ev("() => localStorage.getItem('nullovation-city:wizardOpen')") == 'tab' and ev("() => wizardOpens()") == 'tab'
       and ev("() => document.querySelector('[data-set=\"wizardOpen\"]').classList.contains('changed')") and pg.get_attribute('#optWizardOpen [data-value="tab"]', 'aria-pressed') == 'true')
    pg.click('#btnTabReset'); pg.wait_for_timeout(150)
    ok('and Reset to defaults puts the app back', ev("() => wizardOpens()") == 'app' and ev("() => localStorage.getItem('nullovation-city:wizardOpen')") is None)
    pg.screenshot(path=str(SHOTS / '380-settings-wizard.png'), clip={'x': 0, 'y': 0, 'width': 300, 'height': 1000})

    # ---------- with the Claude folder: wizard-rounds, shared with the wizard (F1) ----------
    pg.click('#btnClaudeConnect'); pg.wait_for_timeout(600)
    ok('the Claude folder connects, and the city may write in it', ev("() => ClaudeWork.state()") == 'on' and ev("() => ClaudeWork.canWrite()"))
    pg.click('#setBack'); pg.wait_for_timeout(150)
    copy = ev(f"() => taskForClaude(getProject('{gp}'), {task(T1)})").split('\n')
    ok('Copy task names the round\'s file now, rather than writing the answers in (A2)', '5 of 8 answered.' in copy and not any(l.startswith('- B') for l in copy)
       and 'Its questions and answers are in wizard-rounds/2026-10-22-draw-the-beds-round1.json in the Claude folder, which ~/.claude/nullovation-city.json names: read them there.' in copy)
    ok('while a chat still gets them written in (C1)', '- B1, Bed layout: How should the beds be laid out? A grid. Note: keep the middle path wide.' in ev(f"() => taskForClaude(getProject('{gp}'), {task(T1)}, Date.now(), {{ kind: 'chat' }})"))
    ev(f"() => {{ {task(T1)}.round.folder = 'D:\\\\City\\\\Claude\\\\wizard-rounds'; }}")
    ok('a round whose folder is known is named by its full path', 'Its questions and answers are in D:\\City\\Claude\\wizard-rounds\\2026-10-22-draw-the-beds-round1.json: read them there.' in ev(f"() => taskForClaude(getProject('{gp}'), {task(T1)})"))
    open_task(T1)
    pg.click('#pvTaskClaude'); pg.wait_for_timeout(200)
    cw = unquote(ev("() => document.querySelector('.oc-panel .oc-tile[data-kind=\"cowork\"]').getAttribute('href')"))
    ok('and Cowork gets the round\'s file attached', 'file=D:\\City\\Claude\\wizard-rounds\\2026-10-22-draw-the-beds-round1.json' in cw)
    pg.keyboard.press('Escape'); pg.wait_for_timeout(100)
    summ = ev("() => ClaudeWork.citySummary()")
    open_ = [t for pr in summ['projects'] if pr['name'] == 'Garden planner' for ms in pr['milestones'] for t in ms['open'] if t['task'] == T1][0]
    ok(f'the city summary names an open task\'s round ({open_.get("round")})', open_.get('round') == {'title': TITLE, 'kind': 'round', 'file': 'wizard-rounds/2026-10-22-draw-the-beds-round1.json', 'state': '5 of 8 answered'})
    quiet()
    n0 = len(opened())
    pg.click('#pvRoundWizard'); pg.wait_for_timeout(500)
    f = ev("() => window.__subjson('wizard-rounds/2026-10-22-draw-the-beds-round1.json')")
    ok('Wizard it writes the round\'s file in wizard-rounds when it is not there, with its answers so far', f and f['round']['config']['title'] == TITLE and f['meta']['answered'] == 5)
    ok(f'and opens the wizard app through a web+dwizard: link, followed in place rather than in a tab ({opened()[-1][1:]})', len(opened()) == n0 + 1
       and opened()[-1][0].startswith('web+dwizard:open/') and opened()[-1][1:] == ['', ''])
    ok(f'the link names the round by its file and title, short enough for the system ({len(opened()[-1][0])} characters)',
       unref(opened()[-1][0]) == {'file': '2026-10-22-draw-the-beds-round1.json', 'title': TITLE} and len(opened()[-1][0]) < 2000)
    ok(f'the first time saying to give the app that folder ({said()})',
       said() == 'Opening ' + TITLE + " in your wizard app. The first time, give the app the Claude folder's wizard-rounds folder, and rounds open there by themselves.")
    ok('with Open in a tab, which opens the hosted wizard carrying the round', undo() and sent()[0] == 'https://abdurrahmankh.github.io/decision-wizard/'
       and opened()[-1][1:] == ['_blank', 'noopener'] and sent()[1]['round']['config']['title'] == TITLE and len(opened()) == n0 + 2)
    quiet()
    w0 = ev("() => window.__writes")
    pg.click('#pvRoundWizard'); pg.wait_for_timeout(500)
    ok(f'the next time it is shorter, and a file already there is left as it is ({said()})', said() == 'Opening ' + TITLE + ' in your wizard app.' and ev("() => window.__writes") == w0
       and opened()[-1][0].startswith('web+dwizard:open/'))
    quiet()
    ev("() => localStorage.setItem('nullovation-city:wizardOpen', 'tab')")
    pg.click('#pvRoundWizard'); pg.wait_for_timeout(500)
    ok(f'set to a browser tab, it opens a tab carrying the round, as with no Claude folder ({said()})', said() == 'Opening ' + TITLE + ' in your wizard.'
       and opened()[-1][1:] == ['_blank', 'noopener'] and sent()[1]['file'] == '2026-10-22-draw-the-beds-round1.json')
    quiet()
    ev("() => { localStorage.removeItem('nullovation-city:wizardOpen'); localStorage.setItem('nullovation-city:wizard', 'file:///D:/Tools/decision-wizard/index.html'); }")
    pg.click('#pvRoundWizard'); pg.wait_for_timeout(500)
    ok('an address of your own opens in a tab there, since the app is the hosted wizard', sent()[0] == 'file:///D:/Tools/decision-wizard/index.html' and opened()[-1][1:] == ['_blank', 'noopener'])
    ev("() => localStorage.removeItem('nullovation-city:wizard')")
    quiet()

    # the wizard saves the answers into the file as you go, and the task takes them
    u0 = proj()['updatedAt']
    ev(f"() => window.__subput('wizard-rounds/2026-10-22-draw-the-beds-round1.json', {json.dumps(answers(7, with_round=True))})")
    pg.wait_for_timeout(3600)
    ok('answers the wizard saves into the file come into the task within a few seconds', get(T1)['round']['a']['meta']['answered'] == 7)
    ok('the card follows, in place', pg.text_content('#pvSide .pv-round-state') == 'Waiting: 7 of 8 answered')
    ok('no toast while they keep arriving', said() == '')
    ev(f"() => window.__subput('wizard-rounds/2026-10-22-draw-the-beds-round1.json', {json.dumps(answers(8, with_round=True))})")
    pg.wait_for_timeout(3400)
    ok('the last one lands: answered, the hat teal', get(T1)['round']['a']['meta']['answered'] == 8 and hat(f'li.task[data-id="{tid(T1)}"] .round-hat') == 'done')
    pg.wait_for_timeout(4200)
    news = ev("() => News.items().filter(it => it.moment === 'answers').map(it => News.lineOf(it))")
    ok(f'once they stop arriving, its building\'s news says so in place of the toast, waiting with Proxima for a building with no leader (X1, Leader UX T1) ({news})',
       news == ['Your answers are in for ' + TITLE + ': 8 of 8.'] and said() == '' and ev("() => !!document.querySelector('#newsList .news-tile[data-k=\"px\"]')"))
    pg.click('#newsList .news-tile[data-k="px"] .news-face'); pg.wait_for_timeout(300)
    acts = ev("() => [...document.querySelectorAll('#ldSayActs button')].map(b => b.textContent)")
    ok(f'a click on the face says it, with Open ({acts})', acts[:1] == ['Open'])
    pg.screenshot(path=str(SHOTS / '381-answers-in.png'))
    pg.click('#ldSay .ld-open'); pg.wait_for_timeout(400)
    ok('Open opens the task, and the news is read', ev("() => News.items().filter(it => it.moment === 'answers').length") == 0 and ev("() => document.querySelector('#ldSay').hidden")
       and ev("() => !!document.querySelector('#pvSide #pvTaskDesc')"))
    ev("() => document.activeElement && document.activeElement.blur()")
    ok('the answers coming in are not work: Updated stays', proj()['updatedAt'] == u0)
    quiet()
    ev(f"() => window.__subput('wizard-rounds/2026-10-22-draw-the-beds-round1.json', {json.dumps(ROUND)})")
    pg.wait_for_timeout(3600)
    ok('a round file with no answers in it changes nothing in the task', get(T1)['round']['a']['meta']['answered'] == 8)

    # Claude Code attaches a round through the inbox (W1): add-round
    R9 = {**ROUND, 'config': {**ROUND['config'], 'title': 'Icons, Round 1', 'folder': 'D:\\City\\Claude\\wizard-rounds', 'project': 'Nullovation City'}}
    ev(f"() => window.__subput('wizard-rounds/2026-10-22-icons-round1.json', {json.dumps(R9)})")
    ev(f"""() => window.__subput('inbox/2026-10-22-1900-garden.json', {{ app: 'nullovation-city', kind: 'change', version: 1, project: 'Garden planner', summary: 'A wizard round for the icons',
         changes: [{{ do: 'add-round', task: '{T3}', file: '2026-10-22-icons-round1.json' }}] }})""")
    pg.wait_for_timeout(3600)
    t3 = get(T3)
    ok('add-round attaches the round Claude wrote in wizard-rounds to the task it names', t3.get('round') and t3['round']['title'] == 'Icons, Round 1' and t3['round']['file'] == '2026-10-22-icons-round1.json'
       and t3['round']['folder'] == 'D:\\City\\Claude\\wizard-rounds')
    news = ev("() => { const b = document.querySelector('#ldSay'); return b.hidden ? null : [$('#ldSayText').textContent, [...b.querySelectorAll('#ldSayActs button')].map(x => x.textContent)]; }")
    ok(f'at once, its building\'s news saying so in place of the toast, with Undo (Leader UX, 0.1.59) ({news})', news == ['Claude attached a wizard round to ' + T3 + ': Icons, Round 1.', ['Undo', 'Go to it']] and said() == '')
    ok('with lines in Activity', any(e['text'] == 'Claude attached a wizard round to ' + T3 + ': Icons, Round 1' for e in proj()['activity']) and any(e['text'] == 'Claude: A wizard round for the icons' for e in proj()['activity']))
    ok('the change file moves to inbox/done', ev("() => [...window.__sub.keys()].some(k => k === 'inbox/done/2026-10-22-1900-garden.json') && !window.__sub.has('inbox/2026-10-22-1900-garden.json')"))
    ok('its row wears a gray hat', hat(f'li.task[data-id="{tid(T3)}"] .round-hat') == 'open')
    ok('Undo takes it off', ev("() => { const b = document.querySelector('#ldSay .ld-undo'); if (!b) return false; b.click(); return true; }") and not get(T3).get('round'))
    quiet()
    ev(f"""() => window.__subput('inbox/2026-10-22-1901-garden.json', {{ app: 'nullovation-city', kind: 'change', version: 1, project: 'Garden planner', summary: 'Round, inline',
         changes: [{{ do: 'add-round', task: '{T3}', file: 'inline-round.json', round: {json.dumps({**ROUND, 'config': {**ROUND['config'], 'title': 'Inline, Round 1'}})} }}] }})""")
    pg.wait_for_timeout(3600)
    ok('a change may carry the round itself', get(T3).get('round') and get(T3)['round']['title'] == 'Inline, Round 1' and get(T3)['round']['file'] == 'inline-round.json')
    quiet()
    ev(f"""() => window.__subput('inbox/2026-10-22-1902-garden.json', {{ app: 'nullovation-city', kind: 'change', version: 1, project: 'Garden planner', summary: 'Missing',
         changes: [{{ do: 'add-round', task: '{T2}', file: 'no-such-round.json' }}] }})""")
    pg.wait_for_timeout(3600)
    ok('one whose file is not there attaches nothing', not get(T2).get('round'))
    quiet()

    # a round dropped with the folder connected is written there too, for Claude and the wizard
    open_task(T2)
    drop('2026-10-22-save-round1.json', {**ROUND, 'config': {**ROUND['config'], 'title': 'Saving, Round 1'}})
    pg.wait_for_timeout(300)
    ok('a round dropped with the Claude folder connected is written into wizard-rounds', (ev("() => window.__subjson('wizard-rounds/2026-10-22-save-round1.json')") or {}).get('config', {}).get('title') == 'Saving, Round 1')
    pg.screenshot(path=str(SHOTS / '382-panel.png'), clip=pg.query_selector('#pvSide').bounding_box())


    # ---------- a brainstorm, Think's Make a brainstorming round (0.1.63, A3): it attaches like a round ----------
    HATS = ['blue', 'white', 'red', 'yellow', 'black', 'green']
    BT = 'Plant icons, Brainstorm 1'
    BS1 = {'config': {'title': BT, 'tagline': 'Round 1: your ideas first', 'product': 'Garden planner', 'kind': 'brainstorm', 'round': 1, 'needs_wizard': '0.9.0'},
           'topic': {'title': 'Plant icons', 'question': 'What could the plant icons be?', 'context': 'The planner shows plants as names only.'},
           'hold': [{'hat': h, 'question': 'Your turn, ' + h} for h in HATS],
           'sparks': [{'hat': 'yellow', 'line': 'One to start.', 'sparks': [{'id': 's1', 'text': 'What if the icon grew with the plant?'}]},
                      {'hat': 'green', 'line': 'One more.', 'sparks': [{'id': 's2', 'text': 'Icons you could smell?'}]}],
           'suggest': [{'hat': h, 'line': 'A few.', 'question': "What's within reach?" if h == 'white' else 'More?', 'ideas': [{'id': h[0] + '1', 'text': 'An idea from ' + h}]} for h in HATS],
           'recap': {'line': "That's round 1."}}
    def bs_answers(seen, last=False, title=BT):
        a = [{'id': 'h-blue', 'step': 'hold', 'hat': 'blue', 'issue': 'Blue: your turn', 'status': 'brainstorm', 'seen': True, 'question': 'Where is this going?',
              'yours': [{'text': 'Icons a child can read.'}, {'text': 'Photos of each plant.', 'killed': True}]},
             {'id': 's-yellow', 'step': 'spark', 'hat': 'yellow', 'issue': 'Yellow: sparks', 'status': 'brainstorm', 'seen': True, 'question': 'What do these set off?',
              'sparks': [{'id': 's1', 'text': 'What if the icon grew with the plant?', 'yours': [{'text': 'A sprout, then a leaf, then a flower.'}]}]},
             {'id': 'g-white', 'step': 'suggest', 'hat': 'white', 'issue': 'White: suggests', 'status': 'brainstorm', 'seen': True, 'question': "What's within reach?",
              'ideas': [{'id': 'w1', 'text': 'Leaf shapes for herbs.', 'killed': False}, {'id': 'w2', 'text': 'Emoji for everything.', 'killed': True}]},
             {'id': 'recap', 'step': 'recap', 'hat': 'blue', 'issue': 'Blue: recap', 'status': 'brainstorm', 'seen': last, 'question': "What's standing after round 1?"}]
        return {'meta': {'tool': 'decision-wizard', 'kind': 'brainstorm', 'round': 1, 'wizard_version': '0.10.1', 'wizard_title': title, 'exported_at': '2026-10-23T10:00:00.000Z',
                         'total': 17, 'seen': seen, 'yours': 3, 'killed': 2, 'suggested': 6}, 'topic': {'title': 'Plant icons', 'question': 'What could the plant icons be?'}, 'answers': a}
    w = ev(f"() => readWizardFile({json.dumps(BS1)})")
    ok('a brainstorm file reads as a round, kept whole: its topic, hats, sparks, suggestions and recap', w and w['round'] == BS1 and w['answers'] is None)
    ok('a brainstorm with no topic, or no suggestions or ideas, is not one', ev(f"""() => [readWizardFile({{ ...{json.dumps(BS1)}, topic: null }}), readWizardFile({{ config: {json.dumps(BS1['config'])}, topic: {json.dumps(BS1['topic'])} }})].every(x => x === null)"""))
    open_task(T3)
    old = get(T3)['round']['title']
    drop('2026-10-23-plant-icons-brainstorm1.json', BS1)
    t3 = get(T3)
    ok(f'dropped on a task, it attaches like a round, replacing the one there ({said()})', t3['round']['title'] == BT and t3['round']['q']['config']['kind'] == 'brainstorm'
       and said() == 'Attached ' + BT + ' to ' + T3 + '. It replaces ' + old + '.')
    quiet()
    lbl = ev("() => [document.querySelector('#pvSide .pv-round-lbl').textContent, document.querySelector('#pvSide .pv-round-state').textContent, document.querySelector('#pvSide .pv-round').classList.contains('brainstorm')]")
    ok(f'its card says Brainstorm, round 1, counting the cards it holds ({lbl})', lbl == ['Brainstorm, round 1', 'Waiting: 0 of 15 cards seen', True])
    st = state(T3)
    ok('where it stands: 15 cards (6 hats, 2 sparks, 6 suggestions and the recap), none seen', st['total'] == 15 and st['answered'] == 0 and not st['done'] and st['brainstorm'] == 1)
    cp = ev(f"() => taskForClaude(getProject('{gp}'), {task(T3)})")
    ok('Copy says Brainstorm, round 1, waiting for answers, its cards in its file', '## Brainstorm, round 1: ' + BT in cp and 'Waiting for answers (15 cards).' in cp
       and 'Its cards and answers are in wizard-rounds/2026-10-23-plant-icons-brainstorm1.json in the Claude folder' in cp)
    ok('its row wears the gray hat, saying brainstorm', hat(f'li.task[data-id="{tid(T3)}"] .round-hat') == 'open'
       and 'Brainstorm' in ev(f"() => document.querySelector('li.task[data-id=\"{tid(T3)}\"] .round-hat').getAttribute('aria-label')"))
    drop('2026-10-23-plant-icons-brainstorm1-answers.json', bs_answers(5))
    pg.wait_for_timeout(200)
    st = state(T3)
    ok(f'its answers count the cards seen, of the wizard\'s total ({st["answered"]} of {st["total"]})', st['answered'] == 5 and st['total'] == 17 and not st['done']
       and pg.text_content('#pvSide .pv-round-state') == 'Waiting: 5 of 17 cards seen')
    quiet()
    chat = ev(f"() => taskForClaude(getProject('{gp}'), {task(T3)}, Date.now(), {{ kind: 'chat' }})")
    ok('a chat gets them written in: your cards, what you killed, the sparks and what the hats suggested', all(x in chat for x in [
        '- Blue, your turn: Where is this going? "Icons a child can read."; "Photos of each plant." (killed).',
        "- Yellow's sparks:", '  - What if the icon grew with the plant? "A sprout, then a leaf, then a flower."',
        "- White suggests: What's within reach?", '  - "Leaf shapes for herbs." (kept)', '  - "Emoji for everything." (killed)']) and '5 of 17 cards seen.' in chat)
    pg.click('#pvSide .pv-round-fold'); pg.wait_for_timeout(150)
    lines = ev("() => [...document.querySelectorAll('#pvSide .pv-round-brain li')].map(l => (l.classList.contains('sub') ? '> ' : '') + l.textContent)")
    ok(f'Show the answers lists them card by card ({len(lines)} lines)', lines[:2] == ['Blue, your turn: Where is this going? "Icons a child can read."; "Photos of each plant." (killed).', "Yellow's sparks:"]
       and '> "Leaf shapes for herbs." (kept)' in lines)
    pg.screenshot(path=str(SHOTS / '383-brainstorm-card.png'), clip=pg.query_selector('#pvSide').bounding_box())
    pg.click('#pvRoundMark'); pg.wait_for_timeout(200)
    ok(f'Mark answered counts the cards not seen as skipped ({said()})', said() == 'Marked answered: 12 cards skipped.' and state(T3)['done'] and state(T3)['skipped'] == 12)
    undo(); pg.wait_for_timeout(150); quiet()
    drop('2026-10-23-plant-icons-brainstorm1-answers.json', bs_answers(16, last=True))
    st = state(T3)
    ok('once its recap is seen it counts as answered, a card skipped on the way or not, and the hat turns teal', st['done'] and not st['marked'] and st['skipped'] == 0
       and hat(f'li.task[data-id="{tid(T3)}"] .round-hat') == 'done' and pg.text_content('#pvSide .pv-round-state') == 'Answered: 16 of 17 cards seen')
    ok('a copy says so', 'Answered, 16 of 17 cards seen.' in ev(f"() => taskForClaude(getProject('{gp}'), {task(T3)})"))
    quiet()
    ok('answers to another brainstorm are refused, naming it', drop('other.json', bs_answers(3, title='Something else, Brainstorm 1')) is not None and 'Something else, Brainstorm 1' in said() and state(T3)['answered'] == 16)
    quiet()
    summ = ev("() => ClaudeWork.citySummary()")
    r3 = [t for pr in summ['projects'] if pr['name'] == 'Garden planner' for ms in pr['milestones'] for t in ms['open'] if t['task'] == T3][0].get('round')
    ok(f'the city summary gives its kind ({r3})', r3 == {'title': BT, 'kind': 'brainstorm', 'file': 'wizard-rounds/2026-10-23-plant-icons-brainstorm1.json', 'state': 'Answered, 16 of 17 cards seen'})
    # round 2, written from round 1's answers, comes back through the inbox and replaces it
    BS2 = {'config': {'title': BT + ', Round 2', 'tagline': 'From ' + BT, 'kind': 'brainstorm', 'round': 2, 'needs_wizard': '0.10.0', 'folder': 'D:\\City\\Claude\\wizard-rounds'},
           'topic': BS1['topic'], 'aims': {'line': 'Round 2.', 'goals': ['Icons a child can read.']},
           'extras': {'line': 'A few more.', 'ideas': [{'id': 'x1', 'hat': 'red', 'text': 'Icons that smile when watered.'}]},
           'ideas': [{'id': 'i1', 'text': 'A sprout, then a leaf, then a flower.', 'by': 'you', 'hat': 'yellow'}, {'id': 'i2', 'text': 'Leaf shapes for herbs.', 'by': 'white', 'hat': 'white'}],
           'order': {'line': 'These made it through.'}}
    ev(f"() => window.__subput('wizard-rounds/2026-10-23-plant-icons-brainstorm1-round2.json', {json.dumps(BS2)})")
    ev(f"""() => window.__subput('inbox/2026-10-23-1100-garden.json', {{ app: 'nullovation-city', kind: 'change', version: 1, project: 'Garden planner', summary: 'Round 2 of the icons brainstorm',
         changes: [{{ do: 'add-round', task: '{T3}', file: '2026-10-23-plant-icons-brainstorm1-round2.json' }}] }})""")
    pg.wait_for_timeout(3600)
    st = state(T3)
    ok(f'Claude\'s add-round brings round 2, which replaces round 1: aims, extras, 1 extra, 2 ideas and the order make 6 cards ({st})', get(T3)['round']['title'] == BT + ', Round 2'
       and st['brainstorm'] == 2 and st['total'] == 6 and st['answered'] == 0)
    news = ev("() => News.items().filter(it => it.moment === 'round').map(it => News.lineOf(it))")
    ok(f'its building\'s news says so ({news[-1:]})', news[-1:] == ['Claude attached a wizard round to ' + T3 + ': ' + BT + ', Round 2.'])
    ev("() => { const b = document.querySelector('#ldSayClose'); if (b && !document.querySelector('#ldSay').hidden) b.click(); }"); quiet()
    A2 = {'meta': {'tool': 'decision-wizard', 'kind': 'brainstorm', 'round': 2, 'wizard_version': '0.10.1', 'wizard_title': BT + ', Round 2', 'total': 6, 'seen': 6, 'ideas': 3},
          'topic': BS1['topic'], 'answers': [
        {'id': 'aims', 'step': 'aims', 'hat': 'blue', 'issue': 'Blue: your aims', 'status': 'brainstorm', 'seen': True, 'question': 'What could the plant icons be?'},
        {'id': 'extras', 'step': 'extras', 'hat': 'blue', 'issue': 'Extras', 'status': 'brainstorm', 'seen': True, 'question': 'Anything here worth keeping?', 'ideas': [{'id': 'x1', 'text': 'Icons that smile when watered.', 'killed': False, 'hat': 'red'}]},
        {'id': 'c-i1', 'step': 'council', 'hat': 'yellow', 'issue': 'A sprout, then a leaf, then a flower.', 'status': 'brainstorm', 'seen': True,
         'idea': {'id': 'i1', 'text': 'A sprout, then a leaf, then a flower.', 'by': 'you', 'hat': 'yellow'}, 'killed': False,
         'changes': [{'text': 'Three stages only.', 'hat': 'black'}], 'answers': [{'text': 'Herbs first.', 'hat': 'white', 'question': 'Which plants first?'}],
         'taken': [{'text': 'Animate the growth.', 'hat': 'green'}], 'variants': [{'text': 'A seed before the sprout.'}], 'rewrite': {'text': 'Icons that grow in three stages.'}},
        {'id': 'order', 'step': 'order', 'hat': 'blue', 'issue': 'Blue: your order', 'status': 'brainstorm', 'seen': True, 'question': 'Which ideas matter most?', 'ranked': True,
         'order': [{'text': 'Icons that grow in three stages.'}, {'text': 'Leaf shapes for herbs.'}]}]}
    ev(f"() => window.__subput('wizard-rounds/2026-10-23-plant-icons-brainstorm1-round2.json', {json.dumps({**A2, 'round': BS2})})")
    pg.wait_for_timeout(8000)
    chat = ev(f"() => taskForClaude(getProject('{gp}'), {task(T3)}, Date.now(), {{ kind: 'chat' }})")
    ok('its answers come in from wizard-rounds, answered with the order seen', state(T3)['done'] and state(T3)['answered'] == 6)
    ok('and a chat gets the council and your order written in', all(x in chat for x in [
        '## Brainstorm, round 2: ' + BT + ', Round 2', '- Extras:', '  - "Icons that smile when watered." (kept)', '- Idea i1: "A sprout, then a leaf, then a flower."',
        '  - In your words: "Icons that grow in three stages."', '  - A change, from Black: "Three stages only."', '  - You answered White (Which plants first?): "Herbs first."',
        '  - Taken from Green as a new idea: "Animate the growth."', '  - Your variant: "A seed before the sprout."', '- Your order:', '  1. "Icons that grow in three stages."', '  2. "Leaf shapes for herbs."']))
    news = ev("() => News.items().filter(it => it.moment === 'answers').map(it => News.lineOf(it))")
    ok(f'its news says the answers are in, in cards ({news})', news == ['Your answers are in for ' + BT + ', Round 2: 6 of 6.'])
    quiet()

    print('errors:', errors)
    ok('no console errors', not errors)
    b.close()
