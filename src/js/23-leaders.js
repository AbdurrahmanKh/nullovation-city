/* Leaders (0.1.51): the city's characters who run its buildings, designed over two rounds on 5 October 2026 and set up
   in Leaders, 20 October 2026. For now a leader holds a name, a role, a signature color and a portrait (L2); talking
   comes later. One leader per building, and one leader can run several. The leaders live in the side bar's Leaders
   section, are picked from a building's more menu or its project view, and show in the wheel's middle, the leader card
   in the project view and the status card (L1). Claude's copies and the city summary name them (L3). A portrait sits in
   the art store under 'leader:' and the leader's id, and travels inline in backups and the data file. */
const LEADER_COLORS = ['#F29A74', '#F08BB4', '#D9536B', '#F2C75C', '#E8DCC4', '#7FD6B5', '#6FAE5C', '#3FA79E', '#8FD0F7', '#5A6FA8', '#B9A3E3', '#8E5A9E'];
const LEADER_MAX = { name: 60, role: 60 };
const leaderColor = seed => LEADER_COLORS[hashStr(String(seed)) % LEADER_COLORS.length];
const portraitKey = id => 'leader:' + id;

function blankLeader(o = {}) {
  const id = o.id || uid('ld');
  return Object.assign({ name: '', role: '', color: leaderColor(id), portrait: false, createdAt: Date.now() }, o, { id });
}
/* Makes loaded or imported leaders safe to use, as sanitizeProjects does for projects. */
function sanitizeLeaders(raw) {
  const out = [], seen = new Set();
  const s = (v, n) => (typeof v === 'string' ? v : '').replace(/\s+/g, ' ').trim().slice(0, n);
  for (const r of Array.isArray(raw) ? raw : []) {
    if (!r || typeof r !== 'object') continue;
    let id = typeof r.id === 'string' && r.id ? r.id.slice(0, 60) : uid('ld');
    if (seen.has(id)) id = uid('ld');
    seen.add(id);
    out.push({ id, name: s(r.name, LEADER_MAX.name) || 'Leader', role: s(r.role, LEADER_MAX.role),
      color: /^#[0-9a-f]{6}$/i.test(r.color || '') ? r.color.toUpperCase() : leaderColor(id), portrait: !!r.portrait,
      createdAt: typeof r.createdAt === 'number' ? r.createdAt : Date.now() });
  }
  return out;
}
const getLeader = id => (id && Array.isArray(DB.leaders) ? DB.leaders.find(l => l.id === id) : null) || null;
const leaderOf = p => (p ? getLeader(p.leader) : null);
const leaderProjects = l => DB.projects.filter(p => p.leader === l.id);
const leaderName = l => (l && l.name.trim()) || 'Leader';
/* A building whose leader is no longer in the city is left without one. */
function tidyLeaders() {
  if (!Array.isArray(DB.leaders)) DB.leaders = [];
  const ids = new Set(DB.leaders.map(l => l.id));
  for (const p of DB.projects) if (p.leader && !ids.has(p.leader)) p.leader = '';
}
/* One line for Claude: who leads the building, and as what (L3). Nothing when it has no leader. */
function leaderLine(p) {
  const l = leaderOf(p);
  return l ? 'Leader: ' + leaderName(l) + (l.role ? ', ' + l.role : '') : null;
}
/* Picking a building's leader is not work, like a pin: Updated stays, and nothing goes in Activity. */
function setLeader(p, id) {
  p.leader = getLeader(id) ? id : '';
}
/* A signature color, darker or lighter: f below 0 mixes in black, above 0 white. */
function shadeHex(hex, f) {
  const n = parseInt(hex.slice(1), 16), c = [n >> 16, (n >> 8) & 255, n & 255];
  const m = c.map(x => Math.round(f < 0 ? x * (1 + f) : x + (255 - x) * f));
  return '#' + m.map(x => x.toString(16).padStart(2, '0')).join('').toUpperCase();
}
