#!/usr/bin/env bash
set -euo pipefail

# 🕒 Cron Setup Helper for Signal Model Constellation Aggregation
# Sets up nightly cron job to aggregate constellation signals

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "🕒 Setting up nightly constellation aggregation cron job"
echo

# Default cron time: 2:00 AM UTC daily
read -rp "Enter cron schedule (default: 0 2 * * * for 2 AM UTC daily): " CRON_SCHEDULE
CRON_SCHEDULE=${CRON_SCHEDULE:-"0 2 * * *"}

# Build cron command
CRON_COMMAND="$SCRIPT_DIR/nightly-aggregation.sh"

# Create new cron entry
CRON_ENTRY="$CRON_SCHEDULE $CRON_COMMAND"

echo "📅 Proposed cron entry:"
echo "$CRON_ENTRY"
echo

read -rp "Add this cron job? (y/N): " confirm
if [[ $confirm != [yY] ]]; then
    echo "❌ Cron job setup cancelled"
    exit 0
fi

# Add to crontab
(crontab -l 2>/dev/null || true; echo "$CRON_ENTRY") | crontab -

echo "✅ Cron job added successfully"
echo
echo "📊 To view current cron jobs: crontab -l"
echo "🗑️  To remove this job later: crontab -e (then delete the line)"
echo "📝 Logs will be written to: $SCRIPT_DIR/../data/aggregation.log"
echo
echo "🌌 The Signal Model will now automatically aggregate constellation signals nightly!"