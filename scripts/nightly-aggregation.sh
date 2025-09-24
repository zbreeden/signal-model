#!/usr/bin/env bash
set -euo pipefail

# 📡 Nightly Constellation Aggregation Runner
# Cron-friendly wrapper for the constellation aggregation script
# Designed to run as a nightly job with proper logging and error handling

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_FILE="$SCRIPT_DIR/../data/aggregation.log"
PID_FILE="$SCRIPT_DIR/../data/aggregation.pid"

# Ensure data directory exists
mkdir -p "$(dirname "$LOG_FILE")"

# Function to log with timestamp
log() {
    echo "[$(date -u '+%Y-%m-%d %H:%M:%S UTC')] $*" | tee -a "$LOG_FILE"
}

# Function to cleanup on exit
cleanup() {
    rm -f "$PID_FILE"
}
trap cleanup EXIT

# Check if another instance is running
if [[ -f "$PID_FILE" ]] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
    log "ERROR: Another aggregation instance is already running (PID: $(cat "$PID_FILE"))"
    exit 1
fi

# Create PID file
echo $$ > "$PID_FILE"

log "🌌 Starting nightly constellation aggregation..."

# Run the aggregation script with full output logging
if "$SCRIPT_DIR/aggregate-constellation.sh" 2>&1 | tee -a "$LOG_FILE"; then
    log "✅ Constellation aggregation completed successfully"
    
    # Optional: Clean up old aggregation files (keep last 30 days)
    find "$SCRIPT_DIR/../signals" -name "????????T??????Z.latest.json" -type f -mtime +30 -delete 2>/dev/null || true
    
    # Optional: Rotate log file if it gets too large (>10MB)
    if [[ -f "$LOG_FILE" ]] && [[ $(stat -f%z "$LOG_FILE" 2>/dev/null || stat -c%s "$LOG_FILE" 2>/dev/null || echo 0) -gt 10485760 ]]; then
        mv "$LOG_FILE" "${LOG_FILE}.old"
        log "📝 Log file rotated"
    fi
    
    exit 0
else
    log "❌ Constellation aggregation failed"
    exit 1
fi