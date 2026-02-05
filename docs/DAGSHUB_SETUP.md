# DagsHub Setup

## What DagsHub Provides

1. **DVC Remote Storage** (100GB free)
2. **MLflow Tracking Server** (experiment logging)
3. **Model Registry** (model versioning)

All automatically configured per repository.

## Setup Steps

### 1. Create DagsHub Repository

1. Go to [dagshub.com](https://dagshub.com)
2. Create new repository: `mlops-pipeline`
3. Connect to GitHub (optional)

### 2. Get Credentials

```bash
# Your DagsHub token (Settings → Access Tokens)
DAGSHUB_USER_NAME=your-username
DAGSHUB_TOKEN=your-token
```

### 3. Configure DVC Remote

```bash
# DagsHub provides DVC remote URL in the "Remote" button
dvc remote add origin https://dagshub.com/YOUR_USER/mlops-pipeline.dvc
dvc remote modify origin --local auth basic
dvc remote modify origin --local user YOUR_USER
dvc remote modify origin --local password YOUR_TOKEN
```

Or use the commands shown in DagsHub UI (Remote → Data → DVC).

### 4. Configure MLflow

DagsHub provides MLflow server at:
```
https://dagshub.com/YOUR_USER/mlops-pipeline.mlflow
```

Set environment variables:
```bash
export MLFLOW_TRACKING_URI=https://dagshub.com/YOUR_USER/mlops-pipeline.mlflow
export MLFLOW_TRACKING_USERNAME=YOUR_USER
export MLFLOW_TRACKING_PASSWORD=YOUR_TOKEN
```

### 5. Create `.env` File

```bash
# .env (don't commit this!)
DAGSHUB_USER_NAME=your-username
DAGSHUB_TOKEN=your-token
MLFLOW_TRACKING_URI=https://dagshub.com/your-username/mlops-pipeline.mlflow
```

### 6. Test Connection

```bash
# Test DVC
dvc push

# Test MLflow (run training stage)
docker-compose run dvc-runner dvc repro train
```

## Model Registry Integration

When training, the model is automatically registered:

```python
mlflow.sklearn.log_model(
    model,
    "model",
    registered_model_name="iris-classifier"  # ← Creates registry entry
)
```

**View in DagsHub:**
- Navigate to your repo → Models tab
- See all versions of `iris-classifier`
- Stage models (Staging → Production)
- Download models for deployment

## Why Not Save Models Locally?

**Traditional approach:**
```python
joblib.dump(model, 'model.pkl')  # ❌ Large file, hard to version
```

**DagsHub approach:**
```python
mlflow.sklearn.log_model(model, "model")  # ✅ Versioned, accessible anywhere
```

**Benefits:**
- Models versioned with experiments
- Easy rollback to any version
- Team access without file sharing
- Deployment pulls from registry directly

## Research Questions

1. What's the difference between DVC storage and MLflow artifact storage?
2. How does DagsHub's S3-compatible storage work?
3. Why use model registry instead of DVC for models?
4. How do you transition a model from Staging to Production?
