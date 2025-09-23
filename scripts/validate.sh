#!/usr/bin/env bash
set -euo pipefail

MODULE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
echo "🔍 Validating module: $(basename "$MODULE_DIR")"

# Check required files exist
echo "📁 Checking required files..."
required_files=(
  "README.md"
  "index.html"
  "signals/latest.json"
  "seeds/modules.yml"
  "schema/latest.schema.yml"
)

for file in "${required_files[@]}"; do
  if [ -f "$MODULE_DIR/$file" ]; then
    echo "  ✓ $file"
  else
    echo "  ❌ Missing: $file"
  fi
done

# Validate signals/latest.json structure (basic check)
echo "📡 Validating signal structure..."
if [ -f "$MODULE_DIR/signals/latest.json" ]; then
  if command -v jq >/dev/null 2>&1; then
    if jq empty "$MODULE_DIR/signals/latest.json" 2>/dev/null; then
      echo "  ✓ signals/latest.json is valid JSON"
      # Check required fields
      required_fields=("id" "ts_utc" "module" "repo" "title" "summary" "rating" "origin" "links" "payload")
      for field in "${required_fields[@]}"; do
        if jq -e ".$field" "$MODULE_DIR/signals/latest.json" >/dev/null 2>&1; then
          echo "  ✓ Field: $field"
        else
          echo "  ❌ Missing field: $field"
        fi
      done
    else
      echo "  ❌ signals/latest.json is invalid JSON"
    fi
  else
    echo "  ⚠️ jq not available, skipping JSON validation"
  fi
else
  echo "  ❌ signals/latest.json not found"
fi

echo "✅ Validation complete"
