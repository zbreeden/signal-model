#!/usr/bin/env python3

rng = np.random.default_rng(11)

# Heuristic conversions
def plays_from_pace(seconds_per_play, possession_time=1800):
# possession_time ~ 30 minutes per team (regulation), rough heuristic before game script
return max(45, min(int(possession_time / seconds_per_play), 80))

def pts_per_play(epa, rz_td_rate):
# EPA/play is already expected points delta; add simple redzone finishing boost
base = 0.40 + 3.0*max(0, epa) # baseline ~0.4 ppp + EPA influence
return base * (0.9 + 0.2*rz_td_rate) # amplify with redzone efficiency

def implied_prob(american_odds: int) -> float:
return (abs(american_odds) / (abs(american_odds) + 100)) if american_odds < 0 else (100 / (american_odds + 100))

rows = []
N = 50000
for g in slate:
plays_a = plays_from_pace(g["pace_away"]) # away plays
plays_h = plays_from_pace(g["pace_home"]) # home plays
ppp_a = pts_per_play(g["epa_away"], g["redzone_td_away"]) * g["weather_mult"]
ppp_h = pts_per_play(g["epa_home"], g["redzone_td_home"]) * g["weather_mult"]

mean_pts_a = plays_a * ppp_a / 100.0
mean_pts_h = plays_h * ppp_h / 100.0

# Use Negative Binomial via Poisson‑Gamma mixture: approx with variance inflation k
k = 1.4 # dispersion (>1 inflates variance vs Poisson)
lam_a = mean_pts_a
lam_h = mean_pts_h

# Sample by Gamma‑Poisson: draw rate then Poisson
rate_a = rng.gamma(shape=lam_a/k, scale=k, size=N)
rate_h = rng.gamma(shape=lam_h/k, scale=k, size=N)
sim_a = rng.poisson(rate_a)
sim_h = rng.poisson(rate_h)

sim_tot = sim_a + sim_h
proj_total = float(sim_tot.mean())
over_prob = float((sim_tot > g["market_total"]).mean())
under_prob = 1.0 - over_prob

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
"proj_total": round(proj_total, 1),
"market_total": g["market_total"],
"over_prob": round(over_prob, 4),
"under_prob": round(under_prob, 4),
"edge_pct": round(edge, 4),
"suggested_side": side
})

rows.sort(key=lambda r: r["edge_pct"], reverse=True)
for i, r in enumerate(rows, 1):
r["rank"] = i

payload = {
"broadcast_key": "gambler_top3",
"season": SEASON,
"week": WEEK,
"sport": "NFL",
"generated_at": now.isoformat(),
"source": "the_gambler",
"items": rows[:3]
}

out_dir = Path("data/broadcasts/gambler")
out_dir.mkdir(parents=True, exist_ok=True)
with open(out_dir / f"top3_{SEASON}-w{WEEK:02d}.json", "w") as f:
json.dump(payload, f, indent=2)
with open(out_dir / "latest.json", "w") as f:
json.dump(payload, f, indent=2)
print("Wrote NFL broadcast:", out_dir)
