#!/usr/bin/env python3
"""
Nightly pulse (robust multi-format reader):

- Reads seeds/constellation.yml
- For each star, fetches raw .../<repo>/main/signals/latest.json
  Accepts:
    1) single JSON object:            {...}
    2) array of objects:              [{...}, {...}]
    3) NDJSON / JSONL (one per line): {...}\n{...}\n...
- Appends NEW items (by unique `id`) into signals/master_history.json (append-only)
- Computes KPIs over FULL history
- Writes:
    signals/master_history.json  (append-only ledger)
    signals/latest.json          (FULL history array, newest->oldest)
    signals/kpis.json            (KPIs from full history)
"""

import os
import json
import datetime
import urllib.request
import urllib.error
from hashlib import sha256
from collections import defaultdict

import yaml  # pip install pyyaml

# --- Paths & constants -------------------------------------------------------

ROOT = os.path.dirname(os.path.dirname(__file__))
SIGNALS_DIR = os.path.join(ROOT, "signals")
HISTORY_PATH = os.path.join(SIGNALS_DIR, "master_history.json")
LATEST_PATH  = os.path.join(SIGNALS_DIR, "latest.json")
KPIS_PATH    = os.path.join(SIGNALS_DIR, "kpis.json")
CONSTELLATION_PATH = os.path.join(ROOT, "seeds", "constellation.yml")

OWNER = os.environ.get("HUB_OWNER", "zbreeden")  # default owner if env not set


# --- Utilities ---------------------------------------------------------------

def utcnow_iso() -> str:
    return datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")


def load_history() -> list:
    if not os.path.exists(HISTORY_PATH):
        return []
    try:
        with open(HISTORY_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, list) else []
    except Exception:
        return []


def save_json(path: str, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def fetch_text(url: str) -> str | None:
    try:
        with urllib.request.urlopen(url, timeout=25) as r:
            return r.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None
        raise
    except Exception:
        return None


def parse_latest_variants(raw_text: str) -> list[dict]:
    """
    Accepts:
      1) single object: {...}
      2) array:         [{...}, {...}]
      3) NDJSON:        {...}\n{...}\n...
    Returns a list[dict].
    """
    if not raw_text:
        return []

    raw_text = raw_text.strip()
    if not raw_text:
        return []

    # Try proper JSON first
    try:
        data = json.loads(raw_text)
        if isinstance(data, dict):
            return [data]
        if isinstance(data, list):
            return [x for x in data if isinstance(x, dict)]
    except json.JSONDecodeError:
        pass

    # Fallback: NDJSON lines
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
            # Ignore malformed lines to be resilient
            continue
    return items


def fetch_latest_list(url: str) -> list[dict]:
    txt = fetch_text(url)
    return parse_latest_variants(txt or "")


def ensure_date(obj: dict):
    """Ensure convenient YYYY-MM-DD `date` derived from ts_utc if missing."""
    if "date" not in obj:
        ts = obj.get("ts_utc")
        if isinstance(ts, str) and len(ts) >= 10:
            obj["date"] = ts[:10]


def ensure_checksum(obj: dict):
    if "checksum" not in obj:
        serialized = json.dumps(obj, sort_keys=True, ensure_ascii=False).encode("utf-8")
        obj["checksum"] = sha256(serialized).hexdigest()


def normalize_id(obj: dict, repo: str):
    """Guarantee a stable id; synthesize from ts_utc+repo when missing."""
    if not obj.get("id"):
        ts = obj.get("ts_utc") or utcnow_iso()
        obj["id"] = f"{ts}-{repo}-latest"


def sort_history(items: list[dict]) -> list[dict]:
    # Sort newest -> oldest by ts_utc (string ISO UTC compares correctly)
    return sorted(items, key=lambda x: x.get("ts_utc", ""), reverse=True)


# --- KPI computation ---------------------------------------------------------

def days_since(ts_utc: str | None) -> int | None:
    if not ts_utc:
        return None
    try:
        dt = datetime.datetime.strptime(ts_utc, "%Y-%m-%dT%H:%M:%SZ")
        return (datetime.datetime.utcnow() - dt).days
    except Exception:
        return None


def compute_kpis(history: list[dict]) -> dict:
    """
    KPIs over full history:
      - repos: last_ts_utc, days_since_last, latest_rating, page link
      - rating_distribution lifetime + pct_critical per repo
      - stale_repos sorted by days_since_last
      - totals: today, total, critical total
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
        by_repo[b.get("repo", "")].append(b)

    # Lifetime distributions + per-repo last activity
    for repo, items in by_repo.items():
        items_sorted = sort_history(items)
        latest = items_sorted[0]
        counts = defaultdict(int)
        for it in items:
            counts[it.get("rating", "normal")] += 1
        total = sum(counts.values()) or 1
        pct_critical = round(100.0 * counts.get("critical", 0) / total, 2)

        kpis["repos"].append({
            "repo": repo,
            "module": latest.get("module", ""),
            "last_ts_utc": latest.get("ts_utc"),
            "days_since_last": days_since(latest.get("ts_utc")),
            "latest_rating": latest.get("rating", "normal"),
            "page": (latest.get("links") or {}).get("page", "")
        })
        kpis["rating_distribution"][repo] = {
            "counts": dict(counts),
            "pct_critical": pct_critical
        }

    # Stale list (most stale first)
    kpis["stale_repos"] = sorted(
        [r for r in kpis["repos"] if r["days_since_last"] is not None],
        key=lambda x: x["days_since_last"],
        reverse=True
    )

    # Overall totals
    today = kpis["today"]
    kpis["totals"]["broadcasts_today"] = sum(1 for b in history if b.get("date") == today)
    kpis["totals"]["broadcasts_total"] = len(history)
    kpis["totals"]["critical_total"]   = sum(1 for b in history if b.get("rating") == "critical")

    return kpis


# --- Main pulse --------------------------------------------------------------

def main():
    # Load constellation
    with open(CONSTELLATION_PATH, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f) or {}
    stars = cfg.get("constellation", [])

    # Load existing history and make a set of seen ids
    history = load_history()
    seen_ids = {b.get("id") for b in history if isinstance(b, dict)}

    # Sweep each star's signals/latest.json (accept obj/array/NDJSON)
    for star in stars:
        repo = (star or {}).get("repo")
        if not repo:
            continue

        url = f"https://raw.githubusercontent.com/{OWNER}/{repo}/main/signals/latest.json"
        items = fetch_latest_list(url)  # list[dict]

        for obj in items:
            if not isinstance(obj, dict):
                continue
            ensure_date(obj)
            ensure_checksum(obj)
            normalize_id(obj, repo)

            _id = obj.get("id")
            if not _id or _id in seen_ids:
                continue

            history.append(obj)
            seen_ids.add(_id)

    # Sort full history (newest first) for renderer & KPI use
    history_sorted = sort_history(history)

    # Compute KPIs over the full history
    kpis = compute_kpis(history_sorted)

    # Write outputs
    save_json(HISTORY_PATH, history_sorted)   # append-only ledger (complete history)
    save_json(LATEST_PATH,  history_sorted)   # renderer reads the full history array
    save_json(KPIS_PATH,    kpis)

    print(f"[pulse] History size: {len(history_sorted)}")
    print(f"[pulse] Wrote: {HISTORY_PATH}, {LATEST_PATH}, {KPIS_PATH}")


if __name__ == "__main__":
    main()
