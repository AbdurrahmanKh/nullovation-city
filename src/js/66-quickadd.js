/* The city-wide quick add (Tasks, Round 2, O2): T, anywhere but in a field, opens one line over the map for a task
   in any project. /name picks the project, the first whose name starts with it; without one it goes to the project
   open in the view, or else the selected building. The other marks work as in every add field: !fri, #weekly, @name.
   Enter adds it and closes; Esc or a click elsewhere closes. */
const QuickAdd = (() => {
  let box = null, input = null, hint = null, prevFocus = null;
  const target = () => getProject((FullView.isOpen() && FullView.currentId()) || App.selectedId);
  const opts = () => ({ project: target(), cityWide: true });

  function build() {
    input = h('input', { id: 'quickAddIn', class: 'field quick-add-in', type: 'text', dir: 'auto', autocomplete: 'off', maxlength: '700',
      placeholder: 'A task, with /project !date #repeat @milestone', 'aria-label': 'Add a task', 'aria-describedby': 'quickAddHint',
      oninput: () => taskLineHint(hint, input.value, opts()),
      onkeydown: e => {
        if (e.key === 'Escape') { e.preventDefault(); e.stopPropagation(); close(); return; }
        if (e.key !== 'Enter') return;
        e.preventDefault();
        const r = taskLineHint(hint, input.value, opts());
        if (!r.ok) { if (!input.value.trim()) close(); return; }
        const t = addTaskLine(r), p = r.p;
        close();
        if (FullView.shows(p.id)) FullView.render();
        toast('Added to ' + p.name + ': ' + t.text + '.', '', { label: 'Open', run: () => FullView.openTask(p.id, t.id) });
      },
      onblur: () => setTimeout(() => { if (box && !box.contains(document.activeElement)) close(false); }, 120) });
    hint = h('p', { id: 'quickAddHint', class: 'add-hint quick-add-hint', 'aria-live': 'polite' });
    box = h('div', { id: 'quickAdd', class: 'quick-add', role: 'dialog', 'aria-label': 'Add a task' },
      h('div', { class: 'quick-add-head' }, h('span', { class: 'quick-add-title' }, iconEl('plus', 12), 'Add a task'), h('span', { class: 'quick-add-keys' }, 'Enter adds · Esc closes')),
      input, hint);
  }
  function open() {
    if (!box) build();
    if (!box.isConnected) { prevFocus = document.activeElement; $('#mapWrap').append(box); }
    if (typeof Wheel !== 'undefined') Wheel.close();
    input.value = '';
    taskLineHint(hint, '', opts());
    input.focus();
  }
  function close(refocus = true) {
    if (!box || !box.isConnected) return false;
    box.remove();
    if (refocus && prevFocus && document.contains(prevFocus) && prevFocus.focus) prevFocus.focus({ preventScroll: true });
    prevFocus = null;
    return true;
  }
  window.addEventListener('keydown', e => {
    if (e.code !== 'KeyT' || e.ctrlKey || e.metaKey || e.altKey || e.repeat) return;
    const t = e.target;
    if (t && (t.isContentEditable || /^(INPUT|TEXTAREA|SELECT)$/.test(t.tagName))) return;
    if (Confirm.isOpen() || Panel.isOpen()) return;
    e.preventDefault();
    open();
  });
  return { open, close, isOpen: () => !!box && box.isConnected };
})();
