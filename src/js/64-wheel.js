/* The shortcut wheel: right-click a building, or press F with one selected, and its shortcuts fan out round it like
   a pie menu. They are its links marked as shortcuts, in the links' order, at most MAX_SHORTCUTS. The middle holds its
   leader's face (0.1.51), and stays empty while it has none. Each shortcut grows outward from the ring, so a label
   of about three words fits. A click opens a link the way the project view does; Enter, the key or the button under
   the wheel, steps inside. The wheel and the status bubble never show together. Esc, a click elsewhere, or moving
   the map closes it. */
const Wheel = (() => {
  const R = 112;                                     // the ring the shortcuts stand on, in CSS pixels from the middle
  const R_SMALL = 76;                                // on a map narrower than the wheel, as a phone's (0.1.74)
  const EDGE = 8;                                    // the wheel keeps this far inside the map
  let el = null, onOutside = null;
  function open(p, x, y) {
    close();
    if (App.selectedId && !FullView.shows(App.selectedId)) MapView.deselect();   // the status bubble closes for the wheel
    const list = shortcutLinks(p).slice(0, MAX_SHORTCUTS), n = list.length;
    const l = leaderOf(p);
    el = h('div', { class: 'wheel', role: 'menu', tabindex: '-1', 'aria-label': 'Shortcuts of ' + p.name + (l ? ', led by ' + leaderName(l) : ''), 'data-id': p.id },
      Leaders.hub(p),
      h('p', { class: 'wheel-name', dir: 'auto' }, p.name));
    list.forEach((l, k) => {
      const ang = k * 2 * Math.PI / n, t = linkTarget(l);                  // from the top, clockwise
      const sx = Math.sin(ang), cy = Math.cos(ang);
      /* the edge nearest the middle touches the ring: left-aligned on the right, right-aligned on the left, centered
         only near the top and the bottom, so two buttons either side of the bottom keep apart */
      const a = h('a', { class: 'btn wheel-item', role: 'menuitem', href: t.href, target: t.blank ? '_blank' : null, rel: t.blank ? 'noopener noreferrer' : null, title: t.title,
        'data-id': l.id, style: `--ax: ${clamp(0.5 - sx, 0, 1).toFixed(3)}; --ay: ${((1 + cy) / 2).toFixed(3)}` },
        iconEl(l.icon, 16), h('span', { class: 'wheel-label', dir: 'auto' }, t.name));
      a.addEventListener('click', () => setTimeout(close, 0));
      el.append(a);
    });
    if (!n) el.append(h('p', { class: 'wheel-empty' }, 'No shortcuts yet. Links added in the project view show here.'));
    const enter = h('button', { class: 'btn btn-accent wheel-enter', type: 'button', title: 'Step inside ' + p.name + ' (Enter)' }, iconEl('door', 16), 'Enter');
    enter.addEventListener('click', () => step(p.id));
    el.append(enter);
    $('#overlay').append(el);
    const items = $$('.wheel-item', el);
    const name = $('.wheel-name', el);
    const parts = [...el.children].filter(c => c !== enter && c !== name);
    const off = c => { const r = c.getBoundingClientRect(), o = el.getBoundingClientRect(); return { left: r.left - o.left, right: r.right - o.left, top: r.top - o.top, bottom: r.bottom - o.top }; };
    /* the shortcuts stand on a ring of radius r; given half, the room either side of the middle, each is cut short where
       it would pass it, so those at the sides are cut and those at the top and the bottom keep their room. The name sits
       over the highest piece and Enter under the lowest; what it all spans comes back. */
    const ring = (r, half) => {
      el.style.setProperty('--r', r + 'px');
      items.forEach((a, k) => {
        const ang = k * 2 * Math.PI / n, x = Math.sin(ang) * r, ax = clamp(0.5 - Math.sin(ang), 0, 1);
        a.style.setProperty('--x', Math.round(x) + 'px');
        a.style.setProperty('--y', Math.round(-Math.cos(ang) * r) + 'px');
        const room = Math.min(ax < 1 ? (half - x) / (1 - ax) : Infinity, ax > 0 ? (half + x) / ax : Infinity);
        a.style.maxWidth = half ? Math.max(64, Math.floor(Math.min(216, room))) + 'px' : '';
      });
      const rects = parts.map(off);
      const hi = Math.min(...rects.map(q => q.top)), lo = Math.max(...rects.map(q => q.bottom));
      name.style.top = Math.round(hi - name.offsetHeight - 8) + 'px';
      enter.style.top = Math.round(lo + 10) + 'px';
      const all = [...el.children].map(off);
      return { minX: Math.min(...all.map(q => q.left)), maxX: Math.max(...all.map(q => q.right)),
        minY: Math.min(...all.map(q => q.top)), maxY: Math.max(...all.map(q => q.bottom)) };
    };
    /* then the whole wheel stays inside the map: one wider than the map, as on a phone, stands on a smaller ring with
       shorter labels (0.1.74) */
    const W = $('#mapWrap').clientWidth, H = $('#mapWrap').clientHeight;
    let { minX, maxX, minY, maxY } = ring(R);
    if (maxX - minX > W - 2 * EDGE) ({ minX, maxX, minY, maxY } = ring(R_SMALL, (W - 2 * EDGE) / 2));
    el.style.left = Math.round(clamp(x, EDGE - minX, Math.max(EDGE - minX, W - EDGE - maxX))) + 'px';
    el.style.top = Math.round(clamp(y, EDGE - minY, Math.max(EDGE - minY, H - EDGE - maxY))) + 'px';
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
