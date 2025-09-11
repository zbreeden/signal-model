#!/usr/bin/env python3
# scripts/pulse_signals.py

import os, sys, json, datetime, urllib.request, urllib.error
import yaml
from hashlib import sha256

ROOT = os.path.dirname(os.path.dirname(__file__))

def today_str_ymd():
    # Use UTC to match ts_utc behavior
    return datetime.datetime.utcnow().strftime("%Y-%m-%d")

def fetch_json(url: str):
    try:
        with urllib.request.urlopen(url, timeout=15) as r:
            return json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None
        raise
    except Exception:
        return None

def main():
    seeds_path = os.path.join(ROOT, "seeds", "constellation.yml")
    with open(seeds_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    stars = config.get("constellation", [])
    if not stars:
        print("No stars listed in seeds/constellation.yml")
        sys.exit(0)

    ymd = today_str_ymd()
    broadcasts = []

    for star in stars:
        repo = star["repo"]
        owner = os.environ.get("HUB_OWNER", "zbreeden")  # default to your GH user
        # Prefer today's dated file
        dated_path = f"signals/{ymd}.{repo}.latest.json"
        fallback_path = "signals/latest.json"

        urls = [
            f"https://raw.githubusercontent.com/{owner}/{repo}/main/{dated_path}",
            f"https://raw.githubusercontent.com/{owner}/{repo}/main/{fallback_path}",
        ]

        chosen = None
        for u in urls:
            data = fetch_json(u)
            if data:
                chosen = data
                break

        if chosen:
            # Ensure minimally valid, and compute checksum if missing
            serialized = json.dumps(chosen, sort_keys=True).encode("utf-8")
            checksum = sha256(serialized).hexdigest()
            chosen.setdefault("checksum", checksum)
            # Ensure date convenience field
            if "ts_utc" in chosen and "date" not in chosen:
                try:
                    chosen_date = chosen["ts_utc"][:10]
                    chosen["date"] = chosen_date
                except Exception:
                    chosen["date"] = ymd
            broadcasts.append(chosen)
        else:
            # star missing; we can skip silently or emit a placeholder
            pass

    # Write master array
    os.makedirs(os.path.join(ROOT, "signals"), exist_ok=True)
    master_path = os.path.join(ROOT, "signals", "latest.json")
    with open(master_path, "w", encoding="utf-8") as f:
        json.dump(broadcasts, f, indent=2, ensure_ascii=False)

    # KPIs precompute
    # - time since last broadcast per star (days)
    # - rating counts & percentage critical by star
    # - stars missing broadcasts today
    from collections import defaultdict
    last_by_repo = {}
    rating_counts = defaultdict(lambda: defaultdict(int))

    by_repo = defaultdict(list)
    for b in broadcasts:
        by_repo[b.get("repo","")].append(b)

    for repo, items in by_repo.items():
        # Use max ts_utc
        def key_ts(x):
            return x.get("ts_utc","")
        latest = max(items, key=key_ts)
        last_by_repo[repo] = latest
        rating_counts[repo][latest.get("rating","normal")] += 1

    def days_since(ts_utc):
        try:
            dt = datetime.datetime.strptime(ts_utc, "%Y-%m-%dT%H:%M:%SZ")
            return (datetime.datetime.utcnow() - dt).days
        except Exception:
            return None

    kpis = {
        "generated_utc": datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "today": ymd,
        "repos": [],
        "rating_distribution": {}
    }

    for repo, latest in last_by_repo.items():
        kpis["repos"].append({
            "repo": repo,
            "module": latest.get("module",""),
            "last_ts_utc": latest.get("ts_utc"),
            "days_since_last": days_since(latest.get("ts_utc","")),
            "latest_rating": latest.get("rating","normal"),
            "page": latest.get("links",{}).get("page","")
        })
        rating_map = rating_counts[repo]
        total = sum(rating_map.values()) or 1
        kpis["rating_distribution"][repo] = {
            "counts": rating_map,
            "pct_critical": round(100.0 * rating_map.get("critical",0) / total, 2)
        }

    # who is stale (sorted by days_since_last desc)
    kpis["stale_repos"] = sorted(
        [r for r in kpis["repos"] if r["days_since_last"] is not None],
        key=lambda x: x["days_since_last"],
        reverse=True
    )

    with open(os.path.join(ROOT, "signals", "kpis.json"), "w", encoding="utf-8") as f:
        json.dump(kpis, f, indent=2, ensure_ascii=False)

    print(f"Wrote {master_path} with {len(broadcasts)} broadcasts")
    print("Wrote signals/kpis.json")

if __name__ == "__main__":
    main()
