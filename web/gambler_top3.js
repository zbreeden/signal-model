// Single-source renderer: ONLY reads ./signals/latest.json
// Shows a header from `source` (Option A), but prefers `origin` if present.
export async function renderGamblerTop3(elId = 'gambler-top3') {
  const el = document.getElementById(elId);
  if (!el) return;

  // Loading state
  el.innerHTML = '<div class="muted">Loading…</div>';

  try {
    // Fetch payload
    const res = await fetch(`./signals/latest.json?ts=${Date.now()}`, { cache: 'no-store' });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const payload = await res.json();

    const items = Array.isArray(payload.items) ? payload.items : [];
    if (!items.length) throw new Error('No items');

    // --- Branding header (Option A + origin-aware) ---
    const origin = payload.origin || {};
    const label  = origin.label || (payload.source === 'the_gambler' ? 'The Gambler' : (payload.source || 'Broadcast'));
    const emoji  = origin.emoji || (payload.source === 'the_gambler' ? '🎲' : '📡');
    const url    = origin.url || null;

    const header = document.createElement('div');
    header.className = 'broadcast-header';
    header.innerHTML = url
      ? `<h3><a href="${url}" target="_blank" rel="noopener">${emoji} ${label}</a> — Top-3 Edges</h3>`
      : `<h3>${emoji} ${label} — Top-3 Edges</h3>`;

    // Optional analytics ping
    try {
      window.dataLayer = window.dataLayer || [];
      window.dataLayer.push({
        event: 'signal_broadcast_viewed',
        source: payload.source || 'the_gambler',
        label,
        items: items.length
      });
    } catch {}

    // --- List render ---
    const list = document.createElement('div');
    list.className = 'broadcast-list';

    items.forEach(it => {
      const edgePctNum = Number(it.edge_pct);
      const edgePct = Number.isFinite(edgePctNum) ? (edgePctNum * 100).toFixed(1) : null;
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
            Suggested: <b>${it.suggested_side || '?'}</b>${edgePct ? ` · Edge: <b>${edgePct}%</b>` : ''}
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

    // Replace content with header + list
    el.replaceChildren(header, list);

  } catch (e) {
    el.textContent = 'No Gambler broadcast available yet.';
    console.warn('Gambler latest.json load failed:', e);
  }
}
