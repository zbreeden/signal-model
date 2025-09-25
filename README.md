# Signal Model

> **The Signal is the rhythmic pulse**

## 🌌 Constellation Information

- **Module Key**: `signal_model`  
- **Repository**: `signal-model`
- **Orbit**: `core`
- **Status**: `developing`
- **Emoji**: 📡

## 🚀 Quick Start

1. **Review seeds/**: Adapt seeded data for this module
2. **Configure schemas/**: Update schema definitions as needed  
3. **Generate signals/**: Create latest.json broadcast file
4. **Run validation**: `scripts/validate.sh`

## 📡 Broadcasting

This module produces a `signals/latest.json` file conforming to the constellation's broadcast schema. The Signal (📡) aggregates these across all stars.

### 🌌 Constellation Signal Aggregation

The Signal Model serves as the constellation's **central nervous system**, automatically collecting and aggregating signals from all stars. This provides real-time visibility into the entire constellation's status and activities.

#### Key Features

- **🔍 Auto-Discovery**: Automatically finds all `*-model` directories with signals
- **📊 Nightly Collection**: Aggregates all constellation signals into timestamped files  
- **✅ Validation**: Ensures JSON structure and schema conformance
- **📈 Statistics**: Reports collection success rates and error counts
- **🔄 Real-time Updates**: Updates `latest.json` with most recent aggregation

#### Usage

```bash
# Manual aggregation (immediate)
./scripts/aggregate-constellation.sh

# Set up automated nightly collection
./scripts/setup-cron.sh

# Validate aggregated signals
./scripts/validate-aggregations.sh

# Monitor aggregation logs
tail -f data/aggregation.log
```

#### Output Structure

Each aggregation creates a timestamped file containing an **array of all constellation signals**:

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
      {/* ... all star signals */}
    ]
  }
}
```

This aggregated data enables downstream analytics, cross-constellation pattern analysis, and constellation health monitoring.

**📖 Complete Documentation**: `scripts/README_AGGREGATION.md` & `scripts/QUICK_REFERENCE.md`

## 🔗 Constellation Links

- **Hub**: [FourTwenty Analytics](https://github.com/zbreeden/FourTwentyAnalytics)
- **Archive**: Glossary, tags, and canonical definitions
- **Signal**: Cross-constellation broadcasting and telemetry

---

*This star is part of the FourTwenty Analytics constellation - a modular analytics sandbox where each repository is a specialized "model" within an orbital system.*
