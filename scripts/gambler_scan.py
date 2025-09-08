#!/usr/bin/env python3
sim_a = rng.poisson(la, size=N)
sim_h = rng.poisson(lh, size=N)
sim_tot = sim_a + sim_h

proj_total = float(sim_tot.mean())
over_prob = float((sim_tot > g["market_total"]).mean())
under_prob = 1.0 - over_prob

# pick side w/ bigger model prob vs the corresponding implied
imp_over = implied_prob(g["market_odds_over"])
imp_under = implied_prob(g["market_odds_under"])
edge_over = over_prob - imp_over
edge_under = under_prob - imp_under
if edge_over >= edge_under:
side, model_p, imp_p, edge = "Over", over_prob, imp_over, edge_over
else:
side, model_p, imp_p, edge = "Under", under_prob, imp_under, edge_under

rows.append({
"game_id": g["game_id"],
"start_et": g["start_et"],
"venue": g["venue"],
"away": g["away"],
"home": g["home"],
"proj_total": round(proj_total, 2),
"market_total": g["market_total"],
"over_prob": round(over_prob, 4),
"under_prob": round(under_prob, 4),
"edge_pct": round(edge, 4),
"suggested_side": side
})

# rank & top‑3
rows.sort(key=lambda r: r["edge_pct"], reverse=True)
for i, r in enumerate(rows, 1):
r["rank"] = i

payload = {
"broadcast_key": "gambler_top3",
"date": TODAY,
"sport": "MLB",
"generated_at": dt.datetime.now(ET).isoformat(),
"source": "the_gambler",
"items": rows[:3]
}

out_dir = Path("data/broadcasts/gambler")
out_dir.mkdir(parents=True, exist_ok=True)
with open(out_dir / f"top3_{TODAY}.json", "w") as f:
json.dump(payload, f, indent=2)
with open(out_dir / "latest.json", "w") as f:
json.dump(payload, f, indent=2)
print("Wrote broadcast:", out_dir)
