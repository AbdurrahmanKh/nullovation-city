/* Bubbles held for a break (0.1.91, City as My Terminal, Brainstorm 1, Round 2, x2, and Round 1, L2): a bubble that
   would open by itself, a leader's news, Gus's word or Proxima's report, waits while you are at something, and opens
   at a break instead. Studies of interruptions (Iqbal and Bailey, 2008) found notifications held until a break in the
   work lowered frustration and sped up reactions.
   - At something: a panel open (a task, a note, Settings, Reports, the Leaders panel or a leader's editor, All tasks,
     the line over the map, Open in Claude, a small panel or a question), inside a building, Edit City, typing in a
     field, or the city's tab out of view.
   - A break (L2): closing a panel, stepping out of a building back to the map, coming back to the city's tab. A pause
     in typing is not one, so the field still open goes on holding.
   - Quiet (x2, Green's change): every bubble waits in News, the faces still counting, until it is turned off, which
     is a break too. Kept in this browser.
   A bubble opened with a click is never held: you asked for it. */
const Hold = (() => {
  const KEY = 'nullovation-city:quiet';
  let quiet = (() => { try { return localStorage.getItem(KEY) === '1'; } catch (e) { return false; } })();
  const subs = new Set();
  /* A field being typed in: text, not a checkbox or a button, and not inside a bubble itself. */
  function typing() {
    const a = document.activeElement;
    if (!a || a === document.body || a.closest('#ldSay, #gusSay, #pxSay')) return false;
    if (a.isContentEditable || a.tagName === 'TEXTAREA') return true;
    return a.tagName === 'INPUT' && !/^(checkbox|radio|button|submit|reset|range|color|file|image)$/i.test(a.type || 'text');
  }
  /* A panel open, or inside a building, or Edit City (L2's panel and building rows). */
  function panel() {
    return (typeof FullView !== 'undefined' && FullView.isOpen()) || (typeof AllTasks !== 'undefined' && AllTasks.isOpen())
      || (typeof Settings !== 'undefined' && Settings.isOpen()) || (typeof Reports !== 'undefined' && Reports.isOpen())
      || (typeof Leaders !== 'undefined' && (Leaders.isOpen() || Leaders.editorOpen())) || (typeof QuickAdd !== 'undefined' && QuickAdd.isOpen())
      || (typeof OpenInClaude !== 'undefined' && OpenInClaude.isOpen()) || (typeof Panel !== 'undefined' && Panel.isOpen())
      || (typeof Confirm !== 'undefined' && Confirm.isOpen()) || (typeof MapView !== 'undefined' && MapView.editing && MapView.editing());
  }
  /* Why a bubble would wait now, or '' when it may open. */
  function why() {
    if (quiet) return 'quiet';
    if (document.hidden) return 'away';
    if (panel()) return 'panel';
    if (typing()) return 'typing';
    return '';
  }
  const busy = () => !!why();
  function setQuiet(v) {
    v = !!v;
    if (v === quiet) return;
    quiet = v;
    try { if (v) localStorage.setItem(KEY, '1'); else localStorage.removeItem(KEY); } catch (e) { /* this visit only */ }
    subs.forEach(fn => { try { fn(v); } catch (e) { /* one listener failing leaves the rest */ } });
  }
  return { busy, why, quiet: () => quiet, setQuiet, onQuiet: fn => subs.add(fn) };
})();
