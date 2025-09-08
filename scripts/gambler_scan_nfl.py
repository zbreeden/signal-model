#!/usr/bin/env python3

import os, json, datetime as dt
from pathlib import Path
import numpy as np

# --- Config ---
ET = dt.timezone(dt.timedelta(hours=-4))  # adjust for DST if you prefer pytz/zoneinfo
now = dt.datetime.now(ET)

# Allow overrides via env (useful in Actions)
SEASON = int(os.getenv("GAMBLER_SEASON", "2025"))
WEEK   = int(os.getenv("GAMBLER_WEEK",   "1"))
SPORT  = os.getenv("GAMBLER_SPORT", "NFL")

rng = np.random.default_rng(11)

def plays_from_pace(seconds_per_play, possession_time=1800):
    return max(45, min(int(possession_time / seconds_per_play), 80))

def pts_per_play(epa, rz_td_rate):
    base = 0.40 + 3.0*max(0, epa)
    return base * (0.9 + 0.2*rz_td_rate)

def implied_prob(odds: int) -> float:
    return (abs(odds)/(abs(odds)+100)) if odds < 0 else (100/(odds+100))

# ---- Stub slate: replace with real schedule + odds ingestion ----
slate = [
  {"game_id":"CIN@CLE","start_et":f"{SEASON}-09-14T13:00:00-04:00","venue":"Cleveland Browns Stadium",
   "away":"CIN","home":"CLE",
   "pace_away":27.0,"pace_home":28.5,"epa_away":0.08,"epa_home":0.02,"redzone_td_away":0.62,"redzone_td_home":0.58,
   "weather_mult":0.98,"market_total":45.5,"market_odds_over":-110,"market_odds_under":-110},
  {"game_id":"KC@LAC","start_et":f"{SEASON}-09-14T16:25:00-04:00","venue":"SoFi Stadium",
   "away":"KC","home":"LAC",
   "pace_away":26.5,"pace_home":27.5,"epa_away":0.12,"epa_home":0.05,"redzone_td_away":0.65,"redzone_td_home":0.60,
   "weather_mult":1.02,"market_total":49.5,"market_odds_over":-112,"market_odds_under":-108},
]

rows = []
N = int(os.getenv("GAMBLER_SIMS", "50000"))
k = float(os.getenv("GAMBLER_DISPERSION", "1.4"))  # variance inflation for NegBin-like distribution

for g in slate:
    plays_a = plays_from_pace(g["pace_away"])
    plays_h = plays_from_pace(g["pace_home"])
    ppp_a = pts_per_play(g["epa_away"], g["redzone_td_away"]) * g["weather_mult"]
    ppp_h = pts_per_play(g["epa_home"], g["redzone_td_home"]) * g["weather_mult"]

    mean_pts_a = plays_a * ppp_a / 100.0
    mean_pts_h = plays_h * ppp_h / 100.0

    rate_a = rng.gamma(shape=max(mean_pts_a/k, 1e-6), scale=k, size=N)
    rate_h = rng.gamma(shape=max(mean_pts_h/k, 1e-6), scale=k, size=N)
    sim_a = rng.poisson(rate_a)
    sim_h = rng.poisson(rate_h)
    tot = sim_a + sim_h

    over_p = float((tot > g["market_total"]).mean())
    under_p = 1.0 - over_p

    edge_over = over_p - implied_prob(g["market_odds_over"])
    edge_under = under_p - implied_prob(g["market_odds_under"])
    if edge_over >= edge_under:
        side, edge = "Over", edge_over
    else:
        side, edge = "Under", edge_under

    rows.append({
      "game_id": g["game_id"], "start_et": g["start_et"], "venue": g["venue"],
      "away": g["away"], "home": g["home"],
      "proj_total": round(float(tot.mean()), 1), "market_total": g["market_total"],
      "over_prob": round(over_p, 4), "under_prob": round(under_p, 4),
      "edge_pct": round(edge, 4), "suggested_side": side
    })

rows.sort(key=lambda r: r["edge_pct"], reverse=True)
for i, r in enumerate(rows, 1):
    r["rank"] = i

payload = {
  "broadcast_key": "gambler_top3",
  "season": SEASON, "week": WEEK, "sport": SPORT,
  "generated_at": now.isoformat(),
  "source": "the_gambler",
  "items": rows[:3]
}

# ---- Write to ./signals/ ----
out_dir = Path("signals")
out_dir.mkdir(parents=True, exist_ok=True)
(out_dir / "latest.json").write_text(json.dumps(payload, indent=2))
(out_dir / f"top3_{SEASON}-w{WEEK:02d}.json").write_text(json.dumps(payload, indent=2))
print("Wrote signals:", out_dir.resolve())
