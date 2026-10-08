/* The shortcut wheel: right-click a building, and its shortcuts fan out round the pointer like a pie menu. They are
   its links marked as shortcuts, in the links' order, at most MAX_SHORTCUTS. The middle is kept for the leader's
   face, and stays empty until leaders come. A click opens a link the way the project view does; Esc, a click
   elsewhere, or moving the map closes it. */
const Wheel = (() => {
  const R = 118;                                     // how far the shortcuts sit from the middle, in CSS pixels
  let el = null, onOutside = null;
  function open(p, x, y) {
    close();
    const list = shortcutLinks(p).slice(0, MAX_SHORTCUTS), n = list.length;
    el = h('div', { class: 'wheel', role: 'menu', 'aria-label': 'Shortcuts of ' + p.name, 'data-id': p.id },
      h('div', { class: 'wheel-hub', 'aria-hidden': 'true' }),
      h('p', { class: 'wheel-name', dir: 'auto' }, p.name));
    list.forEach((l, k) => {
      const ang = -Math.PI / 2 + k * 2 * Math.PI / n, t = linkTarget(l);       // from the top, clockwise
      const a = h('a', { class: 'btn wheel-item', role: 'menuitem', href: t.href, target: t.blank ? '_blank' : null, rel: t.blank ? 'noopener noreferrer' : null, title: t.title,
        'data-id': l.id, style: `--x: ${Math.round(Math.cos(ang) * R)}px; --y: ${Math.round(Math.sin(ang) * R)}px` },
        iconEl(l.icon, 16), h('span', { class: 'wheel-label', dir: 'auto' }, t.name));
      a.addEventListener('click', () => setTimeout(close, 0));
      el.append(a);
    });
    if (!n) el.append(h('p', { class: 'wheel-empty' }, 'No shortcuts yet. Links added in the project view show here.'));
    $('#overlay').append(el);
    /* the whole wheel stays inside the map */
    const W = $('#mapWrap').clientWidth, H = $('#mapWrap').clientHeight;
    const halfW = R + 76, top = R + 60, bottom = R + 24;           // the name sits above the top shortcut
    el.style.left = Math.round(clamp(x, halfW, Math.max(halfW, W - halfW))) + 'px';
    el.style.top = Math.round(clamp(y, top, Math.max(top, H - bottom))) + 'px';
    const items = $$('.wheel-item', el);
    if (items.length) items[0].focus();
    el.addEventListener('keydown', e => {
      const i = items.indexOf(document.activeElement);
      if (!items.length) return;
      if (e.key === 'ArrowRight' || e.key === 'ArrowDown') { e.preventDefault(); items[(i + 1) % items.length].focus(); }
      else if (e.key === 'ArrowLeft' || e.key === 'ArrowUp') { e.preventDefault(); items[(i - 1 + items.length) % items.length].focus(); }
      else if (e.key === 'Tab') close();
    });
    onOutside = e => { if (el && !el.contains(e.target)) close(); };
    setTimeout(() => { if (!el) return; document.addEventListener('pointerdown', onOutside, true); window.addEventListener('wheel', close, { passive: true }); window.addEventListener('resize', close); }, 0);
  }
  function close() {
    if (!el) return false;
    el.remove(); el = null;
    document.removeEventListener('pointerdown', onOutside, true);
    window.removeEventListener('wheel', close); window.removeEventListener('resize', close);
    return true;
  }
  return { open, close, isOpen: () => !!el, owner: () => el && el.dataset.id };
})();
