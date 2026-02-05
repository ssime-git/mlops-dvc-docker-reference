#!/bin/bash
# Restore data and reproduce experiment from DagHub
# Usage: ./scripts/restore_from_dagshub.sh

set -e

echo "🔄 Restoring project from DagHub..."
echo ""

# Check if .dvc directory exists
if [ ! -d ".dvc" ]; then
    echo "❌ Error: Not in a DVC project directory"
    exit 1
fi

# Pull data from DagHub DVC storage
echo "📥 Step 1/2: Pulling data from DagHub DVC storage..."
dvc pull

echo ""
echo "✅ Data restored successfully!"
echo ""

# List what was pulled
echo "📊 Data files restored:"
dvc list . data/raw --dvc-only
dvc list . data/processed --dvc-only

echo ""
echo "🎯 To reproduce the experiment:"
echo "   make run"
echo ""
echo "✅ Done! Your local copy matches DagHub."
