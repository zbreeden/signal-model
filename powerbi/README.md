# Power BI notes

This repo doesn't track `.pbix` files. Instead, keep **modeling notes** here so others can rebuild locally.

## Star schema sketch
- **fact_events** (date_key, event_name, user_key, session_key, params JSON, ts)
- **dim_event** (event_name, category, description)
- **dim_date**, **dim_user**, **dim_session** as needed

## Suggested visuals
- Events over time (line)
- Top CTAs by clicks (bar)
- Search queries with results and CTR (table)
- Funnel: page_view → cta_click → form_submit

## Data pipeline
- For GA4 BigQuery export, build a thin view that flattens event params to columns you care about.
