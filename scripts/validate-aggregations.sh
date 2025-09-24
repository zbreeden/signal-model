#!/usr/bin/env bash
set -euo pipefail

# 🔍 Validate Signal Model aggregation files
# Checks aggregation files against schema and reports statistics

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SIGNAL_MODEL_ROOT="$(dirname "$SCRIPT_DIR")"

echo "🔍 Signal Model Aggregation Validator"
echo

# Check if jq is available
if ! command -v jq >/dev/null 2>&1; then
    echo "❌ jq is required but not installed"
    echo "Install with: brew install jq (macOS) or apt-get install jq (Ubuntu)"
    exit 1
fi

# Function to validate single aggregation file
validate_aggregation() {
    local file="$1"
    local filename
    filename=$(basename "$file")
    
    echo "📄 Validating: $filename"
    
    # Basic JSON validation
    if ! jq empty "$file" 2>/dev/null; then
        echo "  ❌ Invalid JSON structure"
        return 1
    fi
    
    # Check required top-level fields
    local required_fields=("id" "ts_utc" "module" "repo" "title" "summary" "rating" "origin" "links" "payload")
    for field in "${required_fields[@]}"; do
        if ! jq -e "has(\"$field\")" "$file" >/dev/null; then
            echo "  ❌ Missing required field: $field"
            return 1
        fi
    done
    
    # Check payload structure
    if ! jq -e '.payload | has("stats") and has("signals")' "$file" >/dev/null; then
        echo "  ❌ Invalid payload structure - missing stats or signals"
        return 1
    fi
    
    # Extract and display statistics
    local stats
    stats=$(jq -r '.payload.stats | "\(.stars_found) stars found, \(.signals_collected) signals collected, \(.errors_encountered) errors"' "$file")
    echo "  📊 $stats"
    
    # Validate signals array
    local signal_count
    signal_count=$(jq '.payload.signals | length' "$file")
    echo "  📡 Signals array contains $signal_count signals"
    
    # Check if each signal has required fields
    local invalid_signals
    invalid_signals=$(jq '[.payload.signals[] | select(has("id") and has("ts_utc") and has("module") and has("repo") | not)] | length' "$file")
    if [[ $invalid_signals -gt 0 ]]; then
        echo "  ⚠️  $invalid_signals signals missing required fields"
    fi
    
    echo "  ✅ Validation passed"
    return 0
}

# Validate latest.json
if [[ -f "$SIGNAL_MODEL_ROOT/signals/latest.json" ]]; then
    validate_aggregation "$SIGNAL_MODEL_ROOT/signals/latest.json"
else
    echo "⚪ No latest.json found"
fi

echo

# Find and validate all timestamped aggregation files
aggregation_files=("$SIGNAL_MODEL_ROOT"/signals/????????T??????Z.latest.json)

if [[ -f "${aggregation_files[0]}" ]]; then
    echo "📅 Found $(printf '%s\n' "${aggregation_files[@]}" | wc -l) timestamped aggregation files"
    echo
    
    valid_count=0
    total_count=0
    
    for file in "${aggregation_files[@]}"; do
        if [[ -f "$file" ]]; then
            total_count=$((total_count + 1))
            if validate_aggregation "$file"; then
                valid_count=$((valid_count + 1))
            fi
            echo
        fi
    done
    
    echo "📈 Summary: $valid_count/$total_count aggregation files are valid"
    
    if [[ $valid_count -eq $total_count ]]; then
        echo "🎉 All aggregation files passed validation!"
        exit 0
    else
        echo "⚠️  Some aggregation files have validation issues"
        exit 1
    fi
else
    echo "⚪ No timestamped aggregation files found"
    echo "Run ./scripts/aggregate-constellation.sh to create aggregation files"
fi