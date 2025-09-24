#!/usr/bin/env bash
set -euo pipefail

# 📡 Signal Model Constellation Aggregator
# Nightly workflow to collect all star signals into a timestamped aggregation file

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SIGNAL_MODEL_ROOT="$(dirname "$SCRIPT_DIR")"
CONSTELLATION_ROOT="$(dirname "$SIGNAL_MODEL_ROOT")"

echo "📡 Signal Model Constellation Aggregator"
echo "🌌 Scanning constellation for star signals..."
echo

# Generate timestamp for this aggregation run
TS_RUN=$(date -u +%Y%m%dT%H%M%SZ)
AGGREGATION_FILE="$SIGNAL_MODEL_ROOT/signals/$TS_RUN.latest.json"

# Temporary array to hold signal data
SIGNALS_JSON="[]"

# Function to validate JSON using jq if available
validate_json() {
    local file="$1"
    if command -v jq >/dev/null 2>&1; then
        if ! jq empty "$file" 2>/dev/null; then
            return 1
        fi
    else
        # Basic validation - check if file starts with { or [
        if [[ ! $(head -c 1 "$file") =~ ^[\{\[] ]]; then
            return 1
        fi
    fi
    return 0
}

# Function to extract repo name from directory
get_repo_name() {
    local dir="$1"
    basename "$dir"
}

# Function to check if directory is a star module
is_star_module() {
    local dir="$1"
    local repo_name
    repo_name=$(get_repo_name "$dir")
    
    # Check if it ends with -model and has required structure
    if [[ "$repo_name" == *-model ]] && [[ -d "$dir/signals" ]]; then
        return 0
    fi
    return 1
}

# Scan constellation root for star modules
STARS_FOUND=0
SIGNALS_COLLECTED=0
ERRORS_ENCOUNTERED=0

echo "🔍 Discovering stars in constellation..."

for star_dir in "$CONSTELLATION_ROOT"/*-model; do
    if [[ ! -d "$star_dir" ]]; then
        continue
    fi
    
    repo_name=$(get_repo_name "$star_dir")
    echo "  ⭐ Found star: $repo_name"
    STARS_FOUND=$((STARS_FOUND + 1))
    
    # Check for latest.json signal
    signal_file="$star_dir/signals/latest.json"
    if [[ -f "$signal_file" ]]; then
        echo "    📡 Signal file exists: signals/latest.json"
        
        # Validate JSON structure
        if validate_json "$signal_file"; then
            echo "    ✅ Signal validated"
            
            # Add to aggregation using jq if available, otherwise manual append
            if command -v jq >/dev/null 2>&1; then
                # Use jq to safely add the signal to our array
                TEMP_SIGNAL=$(cat "$signal_file")
                SIGNALS_JSON=$(echo "$SIGNALS_JSON" | jq --argjson signal "$TEMP_SIGNAL" '. += [$signal]')
                SIGNALS_COLLECTED=$((SIGNALS_COLLECTED + 1))
                echo "    📥 Signal collected"
            else
                echo "    ⚠️  jq not available - skipping signal collection"
                ERRORS_ENCOUNTERED=$((ERRORS_ENCOUNTERED + 1))
            fi
        else
            echo "    ❌ Invalid JSON in signal file"
            ERRORS_ENCOUNTERED=$((ERRORS_ENCOUNTERED + 1))
        fi
    else
        echo "    ⚪ No signal file found"
    fi
    echo
done

# Create aggregation metadata
AGGREGATION_METADATA=$(cat <<EOF
{
  "id": "${TS_RUN}-signal-model-constellation_aggregation",
  "ts_utc": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "date": "$(date -u +%Y-%m-%d)",
  "module": "Signal Model",
  "repo": "signal-model",
  "title": "Constellation Signal Aggregation",
  "summary": "Nightly aggregation of all constellation star signals - ${SIGNALS_COLLECTED} signals from ${STARS_FOUND} stars",
  "rating": "normal",
  "origin": {
    "name": "Signal Model Aggregator",
    "url": "https://zbreeden.github.io/signal-model/",
    "emoji": "📡"
  },
  "links": {
    "readme": "https://github.com/zbreeden/signal-model#readme",
    "page": "https://zbreeden.github.io/signal-model/"
  },
  "payload": {
    "module_key": "signal_model",
    "broadcast_key": "constellation_aggregation",
    "aggregation_run": "${TS_RUN}",
    "stats": {
      "stars_found": ${STARS_FOUND},
      "signals_collected": ${SIGNALS_COLLECTED},
      "errors_encountered": ${ERRORS_ENCOUNTERED}
    },
    "signals": ${SIGNALS_JSON}
  }
}
EOF
)

# Write aggregation file
echo "$AGGREGATION_METADATA" > "$AGGREGATION_FILE"

# Validate the final aggregation file
if validate_json "$AGGREGATION_FILE"; then
    echo "✅ Aggregation completed successfully"
    echo "📁 Output: signals/$(basename "$AGGREGATION_FILE")"
    echo "📊 Stats: $SIGNALS_COLLECTED signals from $STARS_FOUND stars"
    
    if [[ $ERRORS_ENCOUNTERED -gt 0 ]]; then
        echo "⚠️  Encountered $ERRORS_ENCOUNTERED errors during collection"
    fi
    
    # Update the signal-model's own latest.json to reflect this aggregation
    cp "$AGGREGATION_FILE" "$SIGNAL_MODEL_ROOT/signals/latest.json"
    echo "🔄 Updated signal-model/signals/latest.json"
    
else
    echo "❌ Failed to create valid aggregation file"
    rm -f "$AGGREGATION_FILE"
    exit 1
fi

echo
echo "🌌 Constellation aggregation complete - The Signal has collected all star transmissions"