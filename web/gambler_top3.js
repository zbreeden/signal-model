// Single-source renderer: ONLY reads ./signals/latest.json
export async function renderGamblerTop3(elId = 'gambler-top3') {
  const el = document.getElementById(elId);
  if (!el) return;
  el.innerHTML = '<div class="muted">Loading…</div>';

  try {
    const res = await fetch(`./signals/latest.json?ts=${Date.now()}`, { cache: 'no-store' });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const payload = await res.json();

    const items = Array.isArray(payload.items) ? payload.items : [];
    if (!items.length) throw new Error('No items');

    // Optional analytics ping
    try {
      window.dataLayer = window.dataLayer || [];
      window.dataLayer.push({
        event: 'signal_broadcast_viewed',
        source: payload.source || 'the_gambler',
        sport: payload.sport || 'NFL',
        items: items.length
      });
    } catch {}

    const list = document.createElement('div');
    list.className = 'broadcast-list';

    items.forEach(it => {
      const edgePct = (Number(it.edge_pct) * 100).toFixed(1);
      const start = it.start_et ? new Date(it.start_et).toLocaleTimeString([], {hour:'2-digit', minute:'2-digit'}) : '';
      const card = document.createElement('div');
      card.className = 'edge-card';
      card.innerHTML = `
        <div class="edge-rank">#${it.rank ?? ''}</div>
        <div class="edge-body">
          <div class="edge-title">${(it.away || '?')} @ ${(it.home || '?')}</div>
          <div class="muted">${(it.venue || '')}${start ? ' · ' + start : ''}</div>
          <div>Proj Total: <b>${it.proj_total ?? '?'}</b> · Market: <b>${it.market_total ?? '?'}</b></div>
          <div class="edge-signal ${(it.suggested_side || '').toLowerCase()}">
            Suggested: <b>${it.suggested_side || '?'}</b> · Edge: <b>${isNaN(edgePct) ? '?' : edgePct + '%'}</b>
          </div>
        </div>`;
      card.addEventListener('click', () => {
        try {
          window.dataLayer = window.dataLayer || [];
          window.dataLayer.push({
            event: 'edge_card_clicked',
            source: payload.source || 'the_gambler',
            game_id: it.game_id,
            side: it.suggested_side,
            edge_pct: it.edge_pct
          });
        } catch {}
      });
      list.appendChild(card);
    });

    el.replaceChildren(list);
  } catch (e) {
    el.textContent = 'No Gambler broadcast available yet.';
    console.warn('Gambler latest.json load failed:', e);
  }
}
