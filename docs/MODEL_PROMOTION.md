# Model Promotion Workflow

## Overview

The train stage automatically compares new models with the current production model and promotes them based on performance.

## How It Works

### 1. Model Training
```python
# Train new model
model = RandomForestClassifier(...)
model.fit(X_train, y_train)
test_accuracy = model.score(X_test, y_test)
```

### 2. Compare with Production
```python
# Get current production model
prod_versions = client.get_latest_versions("iris-classifier", stages=["Production"])
prod_accuracy = prod_versions[0].run.data.metrics["test_accuracy"]
```

### 3. Promotion Logic

**Scenario A: No production model exists**
```
Action: Promote new model to Production
Stage: Production
```

**Scenario B: New model better than production**
```
Condition: new_accuracy > prod_accuracy
Action: Promote to Production, archive old production model
Stage: Production
```

**Scenario C: New model not better**
```
Condition: new_accuracy <= prod_accuracy
Action: Register as new version
Stage: Staging
```

## Model Stages

| Stage | Description | Purpose |
|-------|-------------|---------|
| None | Newly registered | Default for new versions |
| Staging | Candidate model | Testing before production |
| Production | Active model | Currently deployed |
| Archived | Old production | Replaced by better model |

## Viewing Models

### DagsHub UI
1. Go to your repo on DagsHub
2. Click "Models" tab
3. Select "iris-classifier"
4. View all versions with their stages

### Via API
```python
from mlflow.tracking import MlflowClient

client = MlflowClient()

# Get production model
prod = client.get_latest_versions("iris-classifier", stages=["Production"])
print(f"Production: v{prod[0].version}")

# Get staging models
staging = client.get_latest_versions("iris-classifier", stages=["Staging"])
for model in staging:
    print(f"Staging: v{model.version}")

# Load production model
model = mlflow.sklearn.load_model("models:/iris-classifier/Production")
```

## Manual Stage Transitions

You can manually change stages on DagsHub:

1. Navigate to Models -> iris-classifier
2. Click on a version
3. Select new stage from dropdown
4. Confirm transition

Or via MLflow API:
```python
client.transition_model_version_stage(
    name="iris-classifier",
    version=2,
    stage="Production"
)
```

## Metadata File

Each training run creates `models/model_metadata.json`:
```json
{
  "run_id": "abc123...",
  "model_name": "iris-classifier",
  "version": 3,
  "train_accuracy": 1.0,
  "test_accuracy": 0.9333,
  "promoted_to_production": true,
  "model_type": "RandomForest",
  "params": {
    "n_estimators": 100,
    "max_depth": 5
  }
}
```

## Testing the Workflow

### Experiment 1: Initial model
```bash
make run
# Result: v1 promoted to Production (no existing production)
```

### Experiment 2: Worse model
```bash
vim params.yaml
# Change max_depth: 5 -> 2
make run
# Result: v2 in Staging (worse than v1)
```

### Experiment 3: Better model
```bash
vim params.yaml
# Change n_estimators: 100 -> 200
make run
# Result: v3 promoted to Production, v1 archived
```

## Best Practices

1. **Always compare on same metric**: Currently uses test_accuracy
2. **Consider threshold**: Add minimum performance requirement
3. **Manual review**: Review staging models before manual promotion
4. **Version tracking**: Keep metadata.json for audit trail
5. **Rollback**: Can always revert to archived versions

## Future Enhancements

- Add configurable promotion threshold
- Multi-metric comparison (precision, recall, F1)
- A/B testing support
- Approval workflow before production
- Automatic rollback on deployment failures
