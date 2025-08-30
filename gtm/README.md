# GTM mapping guide

1. **Create variables** (all built‑in click/form variables + custom data layer variables):
   - `cta_id` (DLV)
   - `cta_text` (DLV)
   - `location` (DLV)
   - `form_id` (DLV)
   - `form_name` (DLV)
   - `fields_count` (DLV)
   - `query` (DLV)
   - `results_count` (DLV)
   - `page_id` (DLV)
   - `page_title` (DLV)

2. **Create GA4 Event tags** (1 tag per event, or a single router tag with Lookup Table — up to you):
   - Event `cta_click` — params: `cta_id`, `cta_text`, `location`
   - Event `form_submit` — params: `form_id`, `form_name`, `fields_count`
   - Event `nav_search` — params: `query`, `results_count`
   - Event `page_view` — params: `page_id`, `page_title`

3. **Triggers**:
   - Custom Event trigger for each event name (e.g., `Custom Event = cta_click`).

4. **Publish** and verify in **GA4 DebugView**.
