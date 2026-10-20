ICONS.tail = ['#oooooooooo#', '.#oooooooo#.', '..#oooooo#..', '...#oooo#...', '....#oo#....', '.....##.....'];

function progressRow(p, cls) {
  const pr = progressOf(p);
  const fill = h('i');
  fill.style.width = pr.pct + '%';
  const bar = h('div', { class: 'bar', role: 'progressbar', 'aria-valuemin': '0', 'aria-valuemax': '100', 'aria-valuenow': String(pr.pct), 'aria-label': 'Progress' }, fill);
  return h('div', { class: cls }, bar, h('span', { class: 'pct' }, pr.pct + '%'), pr.manual ? h('span', { class: 'manual-note' }, 'manual') : null);
}
function dueChip(t) {
  const d = dueInfo(t);
  return d ? h('span', { class: 'due ' + (d.tone || '') }, d.text) : null;
}
/* The pin for one open task (Tasks, Round 2, M4), as a small icon button: pressed, it stays in view; otherwise it
   shows while the row is pointed at or has the focus. After a change, the panels that show the task redraw, and the
   focus comes back to the same button. The star is set only in the task panel (0.1.40), so lists stay quiet. With
   chip, as in What is next, a pressed pin says Pinned beside it (0.1.41). */
function markButtons(p, t, cls = '', { chip = false } = {}) {
  if (!isOpenTask(t)) return [];
  const one = (kind, on, label, title, flip) => h('button', {
    class: 'icon-btn task-mark mark-' + kind + (on ? ' on' : '') + (chip ? ' mark-chip' : '') + (cls ? ' ' + cls : ''), type: 'button', 'data-mark': kind, 'data-task': t.id,
    'aria-pressed': String(on), 'aria-label': label, title, html: iconSvg(kind, chip ? 12 : 14, on ? undefined : 'transparent') + (chip && on ? '<span>Pinned</span>' : ''),
    onclick: e => {
      e.stopPropagation();
      const scope = e.currentTarget.closest('[id]'), sid = scope ? scope.id : null;
      flip();
      if (typeof FullView !== 'undefined' && FullView.isOpen()) FullView.render();
      const place = cls ? '.' + cls.split(' ')[0] : '', back = sid && document.getElementById(sid);   // the same place: a task's row and What is next share a pin
      const b = back && ($(`[data-mark="${kind}"][data-task="${t.id}"]${place}`, back) || (place === '.next-mark' ? $(`[data-mark="${kind}"]${place}`, back) : null));   // What is next may show another task now
      if (b) b.focus();
    },
  });
  const pin = isPinned(p, t);
  return [
    one('pin', pin, (pin ? 'Unpin: ' : 'Pin as next: ') + t.text, pin ? 'Pinned: it comes first in What is next. Click to unpin.' : 'Pin it: it comes first in What is next and the status card',
      () => setPin(p, t, !pin)),
  ];
}
function metaRow(p) {
  const bits = [];
  const dl = deadlineInfo(p.deadline);
  if (dl) bits.push(h('span', { class: dl.tone || null }, dl.text));
  bits.push(h('span', null, 'Updated ' + relAgo(p.updatedAt)));
  return h('p', { class: 'meta' }, bits);
}

const Bubble = (() => {
  let el, enter, tail = null, openId = null;
  let shownIds = new Set();
  const ticking = new Map();
  const was = new Map();                    // a ticked repeat's date and state before the tick, for unticking it
  let addIn = null, addHint = null;         // the add field (O2), kept across redraws so what is typed stays

  function init() {
    el = $('#bubble'); enter = $('#enterBtn');
    $('#doorIcon').innerHTML = iconSvg('door', 20, '#FFC2DD');
    enter.addEventListener('click', () => { if (openId) FullView.open(openId); });
  }
  function clearTicks() { for (const t of ticking.values()) clearTimeout(t); ticking.clear(); }
  function open(id) {
    if (openId !== id) { shownIds = new Set(); clearTicks(); if (addIn) addIn.value = ''; }
    openId = id;
    el.hidden = false; enter.hidden = false;
    el.classList.remove('show');
    render(false); position();
    requestAnimationFrame(() => el.classList.add('show'));
  }
  function close() {
    openId = null; clearTicks();
    el.hidden = true; enter.hidden = true; el.classList.remove('show');
  }
  function refresh() {
    if (!openId) return;
    if (!getProject(openId)) { close(); return; }
    render(false); position();
  }
  function height() { return el && !el.hidden ? el.offsetHeight : 0; }

  function tick(p, t, checked, li) {
    /* ticks from the bubble count in Activity and the week too; a repeat moves on to its next date (R4) */
    if (checked) { const w = tickTask(p, t); if (t.repeat) { was.set(t.id, w); repeatToast(p, t, w); } }
    else { untickTask(p, t, was.get(t.id)); was.delete(t.id); }
    clearTimeout(ticking.get(t.id)); ticking.delete(t.id);
    if (checked) {
      /* the ticked line stays struck through for a moment, then the next one slides up */
      ticking.set(t.id, setTimeout(() => {
        ticking.delete(t.id);
        if (openId === p.id) { render(true); position(); }
      }, reducedMotion() ? 0 : 750));
    }
    if (li) li.classList.toggle('ticked', checked);
    p.updatedAt = Date.now();
    persistSoon(); MapView.invalidate(); Menu.refresh();
    const prog = $('.b-prog', el), meta = $('.meta', el);
    if (prog) prog.replaceWith(progressRow(p, 'b-prog'));
    if (meta) meta.replaceWith(metaRow(p));
  }

  function render(animateNew) {
    const p = getProject(openId); if (!p) return;
    const focusId = document.activeElement && el.contains(document.activeElement) ? (document.activeElement.closest('li') || {}).dataset?.id : null;
    const typing = !!addIn && document.activeElement === addIn, sel = typing ? [addIn.selectionStart, addIn.selectionEnd] : null;   // before the field moves into the new card
    const { list: visible, current } = bubbleTodos(p, BUBBLE_TODOS, new Set(ticking.keys()));
    const openCount = openTasks(p).length;
    const moreCount = openCount - visible.filter(t => isOpenTask(t)).length;
    const waiting = waitingTasks(p);

    const kids = [
      h('button', { class: 'icon-btn b-close', type: 'button', 'aria-label': 'Close status', html: iconSvg('close', 16), onclick: () => MapView.deselect() }),
      h('h2', { class: 'b-title', dir: 'auto' }, p.name),
      Leaders.statusLine(p),                                   // who leads it (0.1.51, L1)
    ];
    const urg = urgencyOf(p);
    if (urg.color) kids.push(h('p', { class: 'b-urg ' + urg.color }, h('span', { class: 'b-urg-dot', 'aria-hidden': 'true' }),
      h('span', null, (urg.color === 'red' ? 'Red: ' : 'Yellow: ') + urg.reasons.join('. ') + '.')));
    if (typeof ClaudeWork !== 'undefined') kids.push(ClaudeWork.line(p));
    if (typeof ClaudeInbox !== 'undefined') kids.push(...ClaudeInbox.cards(p));
    if (current && current.ms) kids.push(h('p', { class: 'b-ms' }, 'Milestone: ', h('bdi', null, current.ms.name)));
    if (visible.length) {
      const ul = h('ul', { class: 'b-todos', 'aria-label': 'Next todos' });
      for (const t of visible) {
        const cls = [ticking.has(t.id) ? 'ticked' : '', animateNew && !shownIds.has(t.id) ? 'slide-in' : ''].join(' ').trim() || null;
        const li = h('li', { class: cls, 'data-id': t.id });
        /* one line: the square ticks it, the text opens it, the copy button sits at the end */
        li.append(
          h('input', { type: 'checkbox', class: 'cb', checked: t.done || ticking.has(t.id), 'aria-label': 'Done: ' + t.text, onchange: e => tick(p, t, e.target.checked, li) }),
          h('button', { class: 'txt b-task', type: 'button', dir: 'auto', title: 'Open this task', onclick: () => FullView.openTask(p.id, t.id) }, t.text, dueChip(t) ? ' ' : null, dueChip(t),
            t.repeat ? h('span', { class: 'repeat-mark', title: 'Repeats: ' + repeatText(t.repeat), 'aria-label': 'Repeats: ' + repeatText(t.repeat), html: iconSvg('repeat', 12) }) : null,
            shiftTag(t, 'b-shift')),
          ...(ticking.has(t.id) ? [] : markButtons(p, t, 'b-mark')),
          h('button', { class: 'icon-btn b-copy', type: 'button', 'aria-label': 'Copy this task for Claude', title: 'Copy this task for Claude', html: iconSvg('copy', 14), onclick: () => copyTask(p, t) }));
        ul.append(li);
      }
      kids.push(ul);
    } else {
      kids.push(h('p', { class: 'b-empty' }, !p.todos.length ? 'No todos yet. Add one here, or enter the building.' : waiting.length
        ? 'Nothing open now. ' + (waiting.length === 1 ? waiting[0].text + ' comes back ' + backWhen(waiting[0]) + '.' : plural(waiting.length, 'repeat comes', 'repeats come') + ' back from ' + backWhen(waiting[0]) + '.')
        : 'All todos are done.'));
    }
    shownIds = new Set(visible.map(t => t.id));
    if (moreCount > 0) kids.push(h('p', { class: 'b-more' }, moreCount === 1 ? '1 more open todo inside' : moreCount + ' more open todos inside'));
    kids.push(addField(p));
    kids.push(progressRow(p, 'b-prog'));
    kids.push(metaRow(p));
    kids.push(h('div', { class: 'b-actions' },
      h('button', { class: 'btn btn-quiet btn-small b-status', type: 'button', title: 'Copies this project\u2019s full status for a Claude chat', onclick: () => copyProjectStatus(p) }, iconEl('copy', 14), 'Copy status'),
      p.urgency.system !== 'none' ? h('button', { class: 'btn btn-small b-worked', type: 'button', title: 'Counts as finishing a task, for ' + urgencyName(p), onclick: () => {
        iWorked(p); changed(p); render(false); position(); FullView.render();
        toast('Checked in. ' + (p.urgency.system === 'finish' ? 'Work until finished stays yellow for 24 hours.' : 'No bubble until ' + (p.urgency.days === 1 ? 'tomorrow at this time.' : p.urgency.days + ' days from now.')));
      } }, 'I worked!') : null));
    tail = h('span', { class: 'tail', 'aria-hidden': 'true', html: iconSvg('tail', 24) });
    tail.style.color = 'var(--edge)';
    tail.style.setProperty('--ic-o', 'var(--paper)');
    kids.push(tail);
    el.replaceChildren(...kids.filter(Boolean));
    if (focusId) { const cb = $(`li[data-id="${focusId}"] .cb`, el); if (cb) cb.focus(); }
    if (typing) { addIn.focus({ preventScroll: true }); try { addIn.setSelectionRange(sel[0], sel[1]); } catch (e) { /* none */ } }
    if (typeof ClaudeWork !== 'undefined') ClaudeWork.markSeen(p.id);
  }

  /* A new add field (O2): a task in one line, with the marks for its date, its repeat and its milestone. Enter adds it
     to this project, by default to its current milestone, and the field stays for the next one. */
  function addField(p) {
    if (!addIn) {
      addIn = h('input', { id: 'bAdd', class: 'field b-add-in', type: 'text', dir: 'auto', autocomplete: 'off', maxlength: '700', placeholder: 'Add a task', 'aria-label': 'Add a task', 'aria-describedby': 'bAddHint',
        oninput: () => { hint(); position(); },
        onfocus: () => { hint(); position(); },
        onblur: () => setTimeout(() => { if (document.activeElement !== addIn && !addIn.value) { addHint.hidden = true; position(); } }, 0),
        onkeydown: e => {
          if (e.key === 'Escape' && addIn.value) { e.preventDefault(); e.stopPropagation(); addIn.value = ''; hint(); return; }
          if (e.key !== 'Enter') return;
          e.preventDefault();
          const q = getProject(openId), r = q && readTaskLine(addIn.value, { project: q });
          if (!r || !r.ok) { hint(); addHint.classList.add('bad'); return; }
          addIn.value = '';
          const t = addTaskLine(r);
          toast('Added ' + t.text + (r.msNew ? ' in a new milestone, ' + r.msNew : '') + '.');
        } });
      addHint = h('p', { id: 'bAddHint', class: 'add-hint b-add-hint', 'aria-live': 'polite', hidden: true });
    }
    hint(p);
    return h('div', { class: 'b-add' }, addIn, addHint);
  }
  function hint(p = getProject(openId)) {
    if (!addIn || !p) return;
    addHint.hidden = document.activeElement !== addIn && !addIn.value;
    taskLineHint(addHint, addIn.value, { project: p });
  }

  function position() {
    if (!openId || !el) return;
    const hide = MapView.moving() || FullView.shows(openId);   // the project view already shows this project
    el.style.visibility = hide ? 'hidden' : '';
    enter.style.visibility = hide ? 'hidden' : '';
    if (hide) return;
    const a = MapView.anchors(openId); if (!a) return;
    const wrap = $('#mapWrap');
    const W = wrap.clientWidth;
    const bw = el.offsetWidth, bh = el.offsetHeight;
    const left = clamp(a.topX - bw / 2, 12, Math.max(12, W - bw - 12));
    const top = Math.max(12, a.topY - bh - 20);
    el.style.transform = `translate(${Math.round(left)}px, ${Math.round(top)}px)`;
    if (tail) tail.style.left = Math.round(clamp(a.topX - left, 24, bw - 24) - 12) + 'px';
    const ew = enter.offsetWidth;
    enter.style.transform = `translate(${Math.round(a.baseX - ew / 2)}px, ${Math.round(a.baseY + 12)}px)`;
  }

  return { init, open, close, refresh, position, height, isOpen: () => !!openId };
})();

const Confirm = (() => {
  let back = null, resolver = null, prevFocus = null;
  function ask({ title, body, confirm = 'Confirm', danger = false }) {
    if (back) done(false);
    return new Promise(resolve => {
      prevFocus = document.activeElement;
      resolver = resolve;
      const no = h('button', { class: 'btn', type: 'button', onclick: () => done(false) }, 'Cancel');
      const yes = h('button', { class: 'btn ' + (danger ? 'btn-danger' : 'btn-accent'), type: 'button', onclick: () => done(true) }, confirm);
      const m = h('div', { class: 'modal small', role: 'alertdialog', 'aria-modal': 'true', 'aria-labelledby': 'cfTitle', 'aria-describedby': 'cfBody' },
        h('h2', { id: 'cfTitle', class: 'fv-title' }, title),
        h('p', { id: 'cfBody', class: 'confirm-body' }, body),
        h('div', { class: 'confirm-actions' }, no, yes));
      m.addEventListener('keydown', e => { if (e.key === 'Tab') { e.preventDefault(); (document.activeElement === yes ? no : yes).focus(); } });
      back = h('div', { class: 'backdrop top' }, m);
      back.addEventListener('mousedown', e => { if (e.target === back) done(false); });
      document.body.append(back);
      requestAnimationFrame(() => { if (back) no.focus(); });  // not during the key press that opened it
    });
  }
  function done(v) {
    if (!back) return;
    back.remove(); back = null;
    const r = resolver; resolver = null;
    if (prevFocus && document.contains(prevFocus)) prevFocus.focus();
    if (r) r(v);
  }
  return { ask, isOpen: () => !!back, cancel: () => done(false) };
})();

/* A plain centered panel: used by the week recap. */
const Panel = (() => {
  let back = null, prevFocus = null;
  function open(titleText, bodyNodes) {
    close();
    prevFocus = document.activeElement;
    const m = h('div', { class: 'modal panel', role: 'dialog', 'aria-modal': 'true', 'aria-labelledby': 'pnTitle', tabindex: '-1' },
      h('header', { class: 'fv-head' },
        h('h2', { id: 'pnTitle', class: 'fv-title' }, titleText),
        h('div', { class: 'fv-actions' }, h('button', { class: 'icon-btn', type: 'button', 'aria-label': 'Close', html: iconSvg('close', 18), onclick: close }))),
      bodyNodes);
    back = h('div', { class: 'backdrop' }, m);
    back.addEventListener('mousedown', e => { if (e.target === back) close(); });
    document.body.append(back);
    m.focus();
  }
  function close() {
    if (!back) return;
    back.remove(); back = null;
    if (prevFocus && document.contains(prevFocus)) prevFocus.focus();
  }
  return { open, close, isOpen: () => !!back };
})();
