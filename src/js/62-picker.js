/* The building picker: every generic building, live, in one grid. It opens as a dialog when a new
   project is planted, and sits inside the project view's side panel when a building changes. */
const Picker = (() => {
  function grid({ current = null, onPick, zoom = 2 }) {
    const box = h('div', { class: 'pick-grid', role: 'listbox', 'aria-label': 'Buildings' });
    const scale = MapView.previewScale();
    for (const g of GENERICS) {
      const on = g.id === current;
      const art = MapView.genericPreview(g.id, scale);
      art.style.width = Math.round(art.width * zoom / scale) + 'px';    // zoom screen pixels per map pixel
      art.style.height = Math.round(art.height * zoom / scale) + 'px';
      box.append(h('button', { class: 'pick-card' + (on ? ' on' : ''), type: 'button', role: 'option', 'aria-selected': String(on), 'data-id': g.id,
        onclick: () => onPick(g.id) },
        h('span', { class: 'pick-art' }, art),
        h('span', { class: 'pick-name' }, g.name),
        h('span', { class: 'pick-foot' }, g.footprint)));
    }
    return box;
  }
  function open({ name, current = null, onPick }) {
    Panel.open(['Pick a building for ', h('bdi', null, name)], [
      h('p', { class: 'recap-range' }, 'Every building here is live. Pick one, then aim at a free plot and click to plant it.'),
      grid({ current, onPick: id => { Panel.close(); onPick(id); } })]);
    const panel = $('.modal.panel'); if (panel) panel.classList.add('wide');
    const first = $('.pick-card.on', document) || $('.pick-card', document);
    if (first) first.focus();
  }
  return { open, grid };
})();
