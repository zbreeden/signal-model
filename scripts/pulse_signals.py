#!/usr/bin/env python3
"""
Nightly pulse (history-first version):

- Reads seeds/constellation.yml
- For each star, fetches raw .../<repo>/main/signals/latest.json (single-object broadcast)
- Appends new (by unique id) into signals/master_history.json (array of all broadcasts, all time)
- Computes KPIs using the full history
- Writes:
    signals/master_history.json  (append-only ledger)
    signals/latest.json          (full, sorted history array for The Signal renderer)
    signals/kpis.json            (KPIs computed from full history)
"""

import os, json, datetime, urllib.request, urllib.error
from hashlib import sha256
from collections import defaultdict
import yaml

ROOT = os.path.dirname(os.path.dirname(__file__))
SIGNALS_DIR = os.path.join(ROOT, "signals")
HISTORY_PATH = os.path.join(SIGNALS_DIR, "master_history.json")
LATEST_PATH  = os.path.join(SIGNALS_DIR, "latest.json")
KPIS_PATH    = os.path.join(SIGNALS_DIR, "kpis.json")
CONSTELLATION_PATH = os.path.join(ROOT, "seeds", "constellation.yml")

OWNER = os.environ.get("HUB_OWNER", "zbreeden")

def parse_latest_variants(raw_text: str):
    """
    Accepts:
      1) single object: {...}
      2) array: [{...}, {...}]
      3) NDJSON: {...}\n{...}\n...
    Returns a list[dict].
    """
    raw_text = (raw_text or "").strip()
    if not raw_text:
        return []

    # Try as proper JSON
    try:
        data = json.loads(raw_text)
        if isinstance(data, dict):
            return [data]
        if isinstance(data, list):
            return [x for x in data if isinstance(x, dict)]
    except json.JSONDecodeError:
        pass

    # Try NDJSON (one JSON object per line)
    items = []
    for line in raw_text.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
            if isinstance(obj, dict):
                items.append(obj)
        except json.JSONDecodeError:
            # ignore malformed lines
            continue
    return items

def fetch_latest_list(url: str):
    try:
        import urllib.request
        with urllib.request.urlopen(url, timeout=20) as r:
            txt = r.read().decode("utf-8", errors="replace")
            return parse_latest_variants(txt)
    except Exception:
        return []

def utcnow_iso():
    return datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

def fetch_json(url: str):
    try:
        with urllib.request.urlopen(url, timeout=20) as r:
            return json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None
        raise
    except Exception:
        return None

def ensure_date(obj):
    # ensure convenient YYYY-MM-DD date field derived from ts_utc
    if "date" not in obj and "ts_utc" in obj and isinstance(obj["ts_utc"], str):
        obj["date"] = obj["ts_utc"][:10]

def ensure_checksum(obj):
    if "checksum" not in obj:
        serialized = json.dumps(obj, sort_keys=True, ensure_ascii=False).encode("utf-8")
        obj["checksum"] = sha256(serialized).hexdigest()

def load_history():
    if not os.path.exists(HISTORY_PATH):
        return []
    try:
        with open(HISTORY_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, list) else []
    except Exception:
        return []

def save_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def compute_kpis(history):
    """
    KPIs over full history:
      - repos: last_ts_utc, days_since_last, last_rating, page link
      - rating_distribution lifetime + pct_critical per repo
      - stale_repos sorted by days_since_last
      - totals for today / total / critical total
    """
    kpis = {
        "generated_utc": utcnow_iso(),
        "today": datetime.datetime.utcnow().strftime("%Y-%m-%d"),
        "repos": [],
        "rating_distribution": {},
        "totals": {}
    }

    by_repo = defaultdict(list)
    for b in history:
        by_repo[b.get("repo","")].append(b)

    def days_since(ts_utc):
        try:
            dt = datetime.datetime.strptime(ts_utc, "%Y-%m-%dT%H:%M:%SZ")
            return (datetime.datetime.utcnow() - dt).days
        except Exception:
            return None

    # lifetime distributions
    for repo, items in by_repo.items():
        # sort by ts desc
        items_sorted = sorted(items, key=lambda x: x.get("ts_utc",""), reverse=True)
        latest = items_sorted[0]
        # rating counts lifetime
        counts = defaultdict(int)
        for it in items:
            counts[it.get("rating","normal")] += 1
        total = sum(counts.values()) or 1
        pct_critical = round(100.0 * counts.get("critical",0) / total, 2)

        kpis["repos"].append({
            "repo": repo,
            "module": latest.get("module",""),
            "last_ts_utc": latest.get("ts_utc"),
            "days_since_last": days_since(latest.get("ts_utc","")),
            "latest_rating": latest.get("rating","normal"),
            "page": (latest.get("links") or {}).get("page","")
        })
        kpis["rating_distribution"][repo] = {
            "counts": counts,
            "pct_critical": pct_critical
        }

    # stale list
    kpis["stale_repos"] = sorted(
        [r for r in kpis["repos"] if r["days_since_last"] is not None],
        key=lambda x: x["days_since_last"],
        reverse=True
    )

    # overall totals
    today = kpis["today"]
    kpis["totals"]["broadcasts_today"] = sum(1 for b in history if b.get("date")==today)
    kpis["totals"]["broadcasts_total"] = len(history)
    kpis["totals"]["critical_total"]   = sum(1 for b in history if b.get("rating")=="critical")

    return kpis

def main():
    # load constellation
    with open(CONSTELLATION_PATH, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f) or {}
    stars = cfg.get("constellation", [])

    # load existing history (append-only)
    history = load_history()
    seen_ids = {b.get("id") for b in history if isinstance(b, dict)}

    # collect this run's entries (one per repo)
    for star in stars:
        repo = star.get("repo")
        if not repo: 
            continue
        url = f"https://raw.githubusercontent.com/{OWNER}/{repo}/main/signals/latest.json"
latest_list = fetch_latest_list(url)  # may be 0..N items
for obj in latest_list:
    ensure_date(obj)
    ensure_checksum(obj)
    _id = obj.get("id") or f"{obj.get('ts_utc', utcnow_iso())}-{repo}-latest"
    obj["id"] = _id
    if _id not in seen_ids:
        history.append(obj)
        seen_ids.add(_id)
      
           
        

    # sort full history by ts_utc desc for rendering
    history_sorted = sorted(history, key=lambda x: x.get("ts_utc",""), reverse=True)

    # compute KPIs on full history
    kpis = compute_kpis(history_sorted)

    # write files
    save_json(HISTORY_PATH, history_sorted)  # append-only master ledger
    save_json(LATEST_PATH,  history_sorted)  # dashboard now reads full history array
    save_json(KPIS_PATH,    kpis)

    print(f"History size: {len(history_sorted)} broadcasts")
    print(f"Wrote: {HISTORY_PATH}, {LATEST_PATH}, {KPIS_PATH}")

if __name__ == "__main__":
    main()
