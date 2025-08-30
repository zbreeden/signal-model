# FourTwenty • The Signal
Semantic trigger layer — detects and propagates glossary‑aligned events across the suite.

## What's inside
- **Purpose:** Provide a simple, auditable event taxonomy and a tiny HTML playground to trigger/test events end‑to‑end.
- **Artifacts:** `/playground` (UX sandbox), `/gtm` (how‑to + templates), `/ga4` (event spec), `/powerbi` (BI notes), `/artifacts` (screens/GIFs).
- **Telemetry:** GA4 via **GTM** (no PII). Use Tag Assistant & GA4 **DebugView** for verification. Screenshots can live under `/artifacts`.

## Quick start
1) Open **`/playground/ux_playground.html`** locally.
   - Option A: double‑click to open in your browser.
   - Option B (recommended): serve locally so Tag Assistant works — `python3 -m http.server 5500` from repo root, then visit `http://localhost:5500/playground/ux_playground.html`.
2) In **GTM**, publish a workspace that contains GA4 Event tags mapping to the events below.
3) Replace the placeholders in the HTML (`GTM-XXXXXXX`) with your actual GTM container ID (or inject GTM via the Tag Assistant Companion).

## Event taxonomy (MVP)
We keep events small and obvious, with stable names and typed parameters.

| event_name      | when it fires                             | params                                  |
|-----------------|-------------------------------------------|-----------------------------------------|
| `cta_click`     | any primary CTA is clicked                | `cta_id`, `cta_text`, `location`        |
| `form_submit`   | lead/contact form successfully submitted  | `form_id`, `form_name`, `fields_count`  |
| `nav_search`    | a search query is submitted               | `query`, `results_count`                |
| `page_view`     | a virtual/soft page change                | `page_id`, `page_title`                 |

See the full JSON spec in [`/ga4/events.json`](ga4/events.json).

## Highlights
- **Event taxonomy:** `<event_1>`, `<event_2>` … with params `<param_a>`, `<param_b>`
- **BI views:** provide a small star schema sketch in `/powerbi` and iterate.

## Repository layout
```
/
├─ playground/         # tiny HTML app to push dataLayer events
├─ gtm/                # GTM mapping guide + import templates
├─ ga4/                # GA4/Measurement spec
├─ powerbi/            # BI modeling notes (+ PBIX lives outside git)
├─ docs/               # glossary, contributing, etc.
├─ artifacts/          # screenshots, GIFs (not tracked by LFS in this starter)
└─ scripts/            # helpers (local server, lint, etc.)
```

## Contributing
- Use feature branches: `feat/<short-name>`, `fix/<short-name>`.
- Conventional commits are encouraged, e.g. `feat(playground): add search demo`.

## License
MIT — see [LICENSE](LICENSE).
