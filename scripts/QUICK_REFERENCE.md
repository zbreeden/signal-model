# 📡 Signal Model Constellation Aggregation - Quick Reference

## Quick Start

```bash
cd signal-model

# Run aggregation now
./scripts/aggregate-constellation.sh

# Set up nightly automation  
./scripts/setup-cron.sh

# Validate aggregation files
./scripts/validate-aggregations.sh

# View aggregation logs
tail -f data/aggregation.log
```

## Key Files

| File | Purpose |
|------|---------|
| `scripts/aggregate-constellation.sh` | Core aggregation logic |
| `scripts/nightly-aggregation.sh` | Cron-friendly wrapper |
| `scripts/setup-cron.sh` | Automated cron setup |
| `scripts/validate-aggregations.sh` | Validate aggregation files |
| `signals/latest.json` | Current aggregation (updated nightly) |
| `signals/YYYYMMDDTHHMMSSZ.latest.json` | Timestamped aggregations |
| `data/aggregation.log` | Runtime logs |

## Output Structure

Each aggregation creates an array of all constellation signals:

```json
{
  "payload": {
    "stats": {
      "stars_found": 20,
      "signals_collected": 20, 
      "errors_encountered": 0
    },
    "signals": [
      {/* signal from archive-model */},
      {/* signal from launch-model */},
      {/* ... all other star signals */}
    ]
  }
}
```

## Cron Setup

Default: **2:00 AM UTC daily**

```bash
# View active cron jobs
crontab -l

# Remove aggregation cron job
crontab -e  # Delete the line with nightly-aggregation.sh
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| No signals collected | Check if stars have `signals/latest.json` |
| JSON validation fails | Install `jq`: `brew install jq` |
| Permission errors | Run: `chmod +x scripts/*.sh` |
| Cron not running | Check: `crontab -l` and system logs |

## Integration 

The aggregated signals array enables downstream analytics:

- Cross-constellation pattern analysis
- Health monitoring dashboards  
- Alert aggregation and routing
- Historical trend tracking
- Signal correlation studies

Perfect for feeding into evaluator-model, visualizer-model, or external analytics systems!