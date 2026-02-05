# Reproduce Experiment

## Overview

Every model in the registry is linked to an MLflow run with specific parameters and data versions.
To reproduce an experiment, you need to:
1. Get the experiment parameters
2. Update params.yaml
3. Rerun the pipeline

## Quick Reproduction

```bash
# View experiment details for production model
make reproduce MODEL=iris-classifier VERSION=production

# View experiment details for specific version
make reproduce MODEL=iris-classifier VERSION=5

# Auto-update params.yaml and show instructions
make reproduce MODEL=iris-classifier VERSION=production ARGS=--update-params

# Then run pipeline
make run
```

## Manual Reproduction

### Step 1: Get Model Info

Via DagsHub UI:
1. Go to Models tab
2. Click on iris-classifier
3. Select version
4. Note the run_id and parameters

### Step 2: Get Parameters from Metadata

```bash
# Check local metadata
cat models/model_metadata.json

# Output example:
{
  "run_id": "4068d4d1e3b94b2f8b2e99857dca0aeb",
  "params": {
    "n_estimators": 100,
    "max_depth": 5
  }
}
```

### Step 3: Update params.yaml

```bash
vim params.yaml
# Update train section with parameters from above
```

### Step 4: Rerun Pipeline

```bash
make run
```

## Data Lineage

### Current Limitations

The pipeline currently tracks:
- Model parameters (in MLflow)
- Model metrics (in MLflow)
- Model artifacts (in MLflow registry)

NOT tracked automatically:
- Exact data version (DVC commit hash)
- Code version (Git commit hash)
- Pipeline dependencies

### Future Enhancement

To fully reproduce experiments, add Git SHA to metadata:

```python
# In train.py
import subprocess
git_sha = subprocess.check_output(['git', 'rev-parse', 'HEAD']).decode().strip()
mlflow.log_param("git_commit", git_sha)
```

Then checkout that commit:
```bash
git checkout <git_sha>
make run
```

## Example Workflow

```bash
# 1. List production model details
make reproduce MODEL=iris-classifier VERSION=production

# Output shows:
#   Parameters: n_estimators=100, max_depth=5
#   Metrics: test_accuracy=0.9333

# 2. Auto-update params.yaml
make reproduce MODEL=iris-classifier VERSION=production ARGS=--update-params

# 3. Reproduce
make run

# 4. Compare results
cat metrics/metrics.json
```

## Verifying Reproduction

If parameters and data are identical, you should get:
- Same metrics (within floating point precision)
- Same model behavior
- Same run results

Differences can come from:
- Different random seeds
- Different data versions
- Different code versions
- Non-deterministic algorithms
