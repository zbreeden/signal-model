async function renderGamblerTop3(elId = 'gambler-top3') {
const el = document.getElementById(elId);
if (!el) return;
try {
const res = await fetch('./data/broadcasts/gambler/latest.json', { cache: 'no-store' });
if (!res.ok) throw new Error('fetch failed');
const { date, sport, items } = await res.json();

const header = document.createElement('div');
header.className = 'broadcast-header';
header.innerHTML = `<h3>🎲 The Gambler — Top‑3 Edges <small>${sport} · ${date}</small></h3>`;

const list = document.createElement('div');
list.className = 'broadcast-list';

items.forEach(it => {
const edgePct = (it.edge_pct * 100).toFixed(1);
const card = document.createElement('div');
card.className = 'edge-card';
card.innerHTML = `
<div class="edge-rank">#${it.rank}</div>
<div class="edge-body">
<div class="edge-title">${it.away} @ ${it.home}</div>
<div class="edge-meta">${it.venue} · ${new Date(it.start_et).toLocaleTimeString([], {hour:'2-digit', minute:'2-digit'})}</div>
<div class="edge-line">Proj Total: <b>${it.proj_total}</b> · Market: <b>${it.market_total}</b></div>
<div class="edge-signal ${it.suggested_side.toLowerCase()}">Suggested: <b>${it.suggested_side}</b> · Edge: <b>${edgePct}%</b></div>
</div>`;
list.appendChild(card);
});

el.replaceChildren(header, list);

// GA4 ping example (optional)
window.dataLayer = window.dataLayer || [];
window.dataLayer.push({ event: 'signal_broadcast_viewed', source: 'the_gambler', items: items.length });
} catch (e) {
el.textContent = 'No Gambler broadcast available yet.';
}
}
