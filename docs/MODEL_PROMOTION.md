# Model Promotion

## Workflow

Training automatically compares new model with production using aliases:

```python
prod_version, prod_accuracy = get_production_model_version(client, model_name)
new_accuracy = model.score(X_test, y_test)

if prod_accuracy is None or new_accuracy > prod_accuracy:
    set_model_alias(client, model_name, version, "production")
else:
    set_model_alias(client, model_name, version, "staging")
```

## Aliases

| Alias | Description |
|-------|-------------|
| production | Currently deployed model |
| staging | Candidate for promotion |
| archived | Replaced production model |

## Tags

Each model version gets tagged with:
- `test_accuracy`: Model performance
- `promoted`: "true" or "false"
- `promotion_reason`: Why promoted or not

## View Models

DagsHub UI: Models tab → iris-classifier

Via API:
```python
from mlflow.tracking import MlflowClient

client = MlflowClient()
mv = client.get_model_version_by_alias("iris-classifier", "production")
model = mlflow.sklearn.load_model(f"models:/iris-classifier@production")
```

## Manual Promotion

```python
client.set_registered_model_alias("iris-classifier", "production", 2)
```
