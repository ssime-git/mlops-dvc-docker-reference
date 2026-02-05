# DagsHub Setup

## Create Repository

1. Go to dagshub.com
2. Create new repository: "Connect a Repository"
3. Select your GitHub repo
4. Auto-sync enabled via webhook

## Configure DVC Remote

```bash
dvc remote modify origin --local auth basic
dvc remote modify origin --local user YOUR_USER
dvc remote modify origin --local password YOUR_TOKEN
```

## Configure MLflow

Add to `.env`:
```bash
MLFLOW_TRACKING_URI=https://dagshub.com/YOUR_USER/YOUR_REPO.mlflow
MLFLOW_TRACKING_USERNAME=YOUR_USER
MLFLOW_TRACKING_PASSWORD=YOUR_TOKEN
```

## Verify

```bash
dvc push                                    # Test DVC
docker-compose run dvc-runner dvc repro     # Test MLflow
```

Check DagsHub UI:
- Data tab: DVC files
- Experiments tab: MLflow runs
- Models tab: Registered models
