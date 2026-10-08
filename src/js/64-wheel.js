/* The shortcut wheel: right-click a building, or press F with one selected, and its shortcuts fan out round it like
   a pie menu. They are its links marked as shortcuts, in the links' order, at most MAX_SHORTCUTS. The middle is kept
   for the leader's face, and stays empty until leaders come. Each shortcut grows outward from the ring, so a label
   of about three words fits. A click opens a link the way the project view does; Enter, the key or the button under
   the wheel, steps inside. The wheel and the status bubble never show together. Esc, a click elsewhere, or moving
   the map closes it. */
const Wheel = (() => {
  const R = 112;                                     // the ring the shortcuts stand on, in CSS pixels from the middle
  const EDGE = 8;                                    // the wheel keeps this far inside the map
  let el = null, onOutside = null;
  function open(p, x, y) {
    close();
    if (App.selectedId && !FullView.shows(App.selectedId)) MapView.deselect();   // the status bubble closes for the wheel
    const list = shortcutLinks(p).slice(0, MAX_SHORTCUTS), n = list.length;
    el = h('div', { class: 'wheel', role: 'menu', tabindex: '-1', 'aria-label': 'Shortcuts of ' + p.name, 'data-id': p.id },
      h('div', { class: 'wheel-hub', 'aria-hidden': 'true' }),
      h('p', { class: 'wheel-name', dir: 'auto' }, p.name));
    list.forEach((l, k) => {
      const ang = k * 2 * Math.PI / n, t = linkTarget(l);                  // from the top, clockwise
      const sx = Math.sin(ang), cy = Math.cos(ang);
      /* the edge nearest the middle touches the ring: left-aligned on the right, right-aligned on the left, centered
         only near the top and the bottom, so two buttons either side of the bottom keep apart */
      const a = h('a', { class: 'btn wheel-item', role: 'menuitem', href: t.href, target: t.blank ? '_blank' : null, rel: t.blank ? 'noopener noreferrer' : null, title: t.title,
        'data-id': l.id, style: `--x: ${Math.round(sx * R)}px; --y: ${Math.round(-cy * R)}px; --ax: ${clamp(0.5 - sx, 0, 1).toFixed(3)}; --ay: ${((1 + cy) / 2).toFixed(3)}` },
        iconEl(l.icon, 16), h('span', { class: 'wheel-label', dir: 'auto' }, t.name));
      a.addEventListener('click', () => setTimeout(close, 0));
      el.append(a);
    });
    if (!n) el.append(h('p', { class: 'wheel-empty' }, 'No shortcuts yet. Links added in the project view show here.'));
    const enter = h('button', { class: 'btn btn-accent wheel-enter', type: 'button', title: 'Step inside ' + p.name + ' (Enter)' }, iconEl('door', 16), 'Enter');
    enter.addEventListener('click', () => step(p.id));
    el.append(enter);
    $('#overlay').append(el);
    /* the name sits over the highest piece and Enter under the lowest; then the whole wheel stays inside the map */
    const parts = [...el.children].filter(c => c !== enter && !c.classList.contains('wheel-name'));
    const off = c => { const r = c.getBoundingClientRect(), o = el.getBoundingClientRect(); return { left: r.left - o.left, right: r.right - o.left, top: r.top - o.top, bottom: r.bottom - o.top }; };
    const rects = parts.map(off);
    const hi = Math.min(...rects.map(r => r.top)), lo = Math.max(...rects.map(r => r.bottom));
    const name = $('.wheel-name', el);
    name.style.top = Math.round(hi - name.offsetHeight - 8) + 'px';
    enter.style.top = Math.round(lo + 10) + 'px';
    const all = [...el.children].map(off);
    const minX = Math.min(...all.map(r => r.left)), maxX = Math.max(...all.map(r => r.right));
    const minY = Math.min(...all.map(r => r.top)), maxY = Math.max(...all.map(r => r.bottom));
    const W = $('#mapWrap').clientWidth, H = $('#mapWrap').clientHeight;
    el.style.left = Math.round(clamp(x, EDGE - minX, Math.max(EDGE - minX, W - EDGE - maxX))) + 'px';
    el.style.top = Math.round(clamp(y, EDGE - minY, Math.max(EDGE - minY, H - EDGE - maxY))) + 'px';
    const items = $$('.wheel-item', el);
    el.focus({ preventScroll: true });              // no shortcut picked yet, so Enter steps inside
    el.addEventListener('keydown', e => {
      const i = items.indexOf(document.activeElement);
      if (e.key === 'Enter' && document.activeElement === el) { e.preventDefault(); e.stopPropagation(); step(p.id); return; }
      if (!items.length) return;
      if (e.key === 'ArrowRight' || e.key === 'ArrowDown') { e.preventDefault(); items[(i + 1) % items.length].focus(); }
      else if (e.key === 'ArrowLeft' || e.key === 'ArrowUp') { e.preventDefault(); items[i < 0 ? items.length - 1 : (i - 1 + items.length) % items.length].focus(); }
      else if (e.key === 'Tab') close();
    });
    onOutside = e => { if (el && !el.contains(e.target)) close(); };
    setTimeout(() => { if (!el) return; document.addEventListener('pointerdown', onOutside, true); window.addEventListener('wheel', close, { passive: true }); window.addEventListener('resize', close); }, 0);
  }
  /* steps inside, as the Enter button under the status bubble does */
  function step(id) {
    close();
    if (getProject(id)) FullView.open(id);
  }
  function close() {
    if (!el) return false;
    el.remove(); el = null;
    document.removeEventListener('pointerdown', onOutside, true);
    window.removeEventListener('wheel', close); window.removeEventListener('resize', close);
    return true;
  }
  return { open, close, step, isOpen: () => !!el, owner: () => el && el.dataset.id };
})();
