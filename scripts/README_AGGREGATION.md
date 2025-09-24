# 📡 Signal Model Constellation Aggregation Workflow

## Overview

The Signal Model serves as the constellation's central nervous system, automatically collecting and aggregating signals from all stars (modules) in the FourTwenty Analytics constellation. This workflow implements a nightly aggregation system that:

- 🔍 **Discovers** all star modules (`*-model` directories)
- 📡 **Collects** their `signals/latest.json` files  
- 🔄 **Aggregates** them into timestamped collection files
- ✅ **Validates** JSON structure and schema conformance
- 📊 **Reports** statistics and errors

## Architecture

### Files Created

```
signal-model/
├── scripts/
│   ├── aggregate-constellation.sh    # Core aggregation logic
│   ├── nightly-aggregation.sh       # Cron-friendly wrapper with logging
│   └── setup-cron.sh               # Cron job setup helper
├── schema/
│   └── constellation_aggregation.schema.yml  # Aggregation output schema
├── signals/
│   ├── latest.json                  # Most recent aggregation (updated)
│   └── YYYYMMDDTHHMMSSZ.latest.json # Timestamped aggregation files
└── data/
    └── aggregation.log              # Runtime logs
```

### Output Format

Each aggregation creates a timestamped file (`YYYYMMDDTHHMMSSZ.latest.json`) containing:

```json
{
  "id": "20250923T020000Z-signal-model-constellation_aggregation",
  "ts_utc": "2025-09-23T02:00:00Z",
  "module": "Signal Model",
  "repo": "signal-model", 
  "title": "Constellation Signal Aggregation",
  "summary": "Nightly aggregation of all constellation star signals - X signals from Y stars",
  "rating": "normal",
  "payload": {
    "module_key": "signal_model",
    "broadcast_key": "constellation_aggregation",
    "aggregation_run": "20250923T020000Z",
    "stats": {
      "stars_found": 15,
      "signals_collected": 12,
      "errors_encountered": 0
    },
    "signals": [
      {/* array of collected star signals */}
    ]
  }
}
```

## Usage

### Manual Execution

```bash
# Run aggregation immediately
cd signal-model
./scripts/aggregate-constellation.sh

# Run with logging (as cron would)
./scripts/nightly-aggregation.sh
```

### Automated Setup

```bash
# Set up nightly cron job (interactive)
cd signal-model  
./scripts/setup-cron.sh

# View current cron jobs
crontab -l

# View aggregation logs
tail -f data/aggregation.log
```

### Default Schedule

- **When**: 2:00 AM UTC daily (configurable)
- **Output**: New timestamped aggregation file + updated `latest.json`
- **Cleanup**: Removes aggregation files older than 30 days
- **Logging**: Rotates logs when they exceed 10MB

## Validation & Error Handling

### Signal Validation
- ✅ JSON structure validation using `jq` (with graceful fallback)
- ✅ File existence checks for each star module
- ✅ Schema conformance for aggregation output
- ⚠️ Non-fatal errors logged but don't stop aggregation

### Error Scenarios
- **Missing `jq`**: Warns but continues (basic validation only)
- **Invalid JSON**: Logs error, skips signal, continues
- **Missing signal file**: Logs info, continues with other stars
- **Write permissions**: Fatal error, exits with code 1

### Concurrent Execution Protection
- PID file prevents multiple simultaneous runs
- Automatic cleanup on script exit
- Logs conflicts for troubleshooting

## Integration with Constellation

### Discovery Logic
Automatically finds all directories matching pattern:
- Name ends with `-model`
- Contains `signals/` subdirectory
- Located in constellation root directory

### Star Requirements
For a module to be aggregated, it needs:
```
<module-name>/
└── signals/
    └── latest.json  # Must exist and contain valid JSON
```

### Downstream Usage
The aggregated signals array enables:
- 📊 Cross-constellation analytics
- 🔍 Signal pattern analysis  
- 📈 Constellation health monitoring
- 🚨 Alert aggregation and routing
- 📝 Historical signal tracking

## Maintenance

### Log Management
```bash
# View recent logs
tail -20 signal-model/data/aggregation.log

# Search for errors
grep "ERROR\|❌" signal-model/data/aggregation.log

# Monitor live aggregation
tail -f signal-model/data/aggregation.log
```

### File Cleanup
```bash
# Manual cleanup of old aggregation files (30+ days)
find signal-model/signals -name "????????T??????Z.latest.json" -mtime +30 -delete

# Check aggregation file sizes
ls -lah signal-model/signals/????????T??????Z.latest.json
```

### Troubleshooting

**No signals collected**: Check if stars have `signals/latest.json` files  
**JSON validation fails**: Install `jq` for robust validation  
**Cron job not running**: Check `crontab -l` and system logs  
**Permission errors**: Ensure scripts are executable (`chmod +x`)  
**Disk space**: Monitor aggregation file growth and log size

## Schema Conformance

All aggregation outputs conform to:
- `schema/constellation_aggregation.schema.yml` (aggregation structure)
- Individual signals conform to `schemas/latest.schema.yml` (constellation standard)

This ensures compatibility with downstream constellation processes and maintains the schema-driven architecture that FourTwenty Analytics is built on.