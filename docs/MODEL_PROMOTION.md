# Model Promotion

## Workflow

Training automatically compares new model with production:

```python
prod_accuracy = get_production_model_accuracy()
new_accuracy = model.score(X_test, y_test)

if prod_accuracy is None or new_accuracy > prod_accuracy:
    promote_to_production()
else:
    register_in_staging()
```

## Stages

| Stage | Description |
|-------|-------------|
| Production | Currently deployed model |
| Staging | Candidate for promotion |
| Archived | Replaced production model |

## View Models

DagsHub UI: Models tab → iris-classifier

Via API:
```python
from mlflow.tracking import MlflowClient

client = MlflowClient()
prod = client.get_latest_versions("iris-classifier", stages=["Production"])
model = mlflow.sklearn.load_model(f"models:/iris-classifier/Production")
```

## Manual Promotion

DagsHub UI or:
```python
client.transition_model_version_stage(
    name="iris-classifier",
    version=2,
    stage="Production"
)
```
