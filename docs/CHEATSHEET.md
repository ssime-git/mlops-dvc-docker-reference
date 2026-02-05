# Command Reference

## Setup

```bash
git clone https://github.com/ssime-git/mlops-dvc-docker-reference.git
cd mlops-dvc-docker-reference
make setup-env          # Create .env
# Edit .env with DagsHub credentials
# Update paths in dvc.yaml
make build
```

## Daily Workflow

```bash
make run                # Run pipeline
make push               # Upload to DagsHub
make git-sync           # Commit and push to GitHub
```

## Pipeline

```bash
make run                # Complete pipeline
make run-ingest         # Data download
make run-preprocess     # Train/test split
make run-train          # Model training
make run-evaluate       # Metrics calculation
```

## Inspection

```bash
make status             # Pipeline state
make dag                # Show dependencies
make test               # Run and verify
```

## DVC

```bash
# Via Makefile
make push               # Push data
make pull               # Pull data
make status             # Check state

# Direct
docker-compose run --rm dvc-runner dvc status
docker-compose run --rm dvc-runner dvc repro --force
docker-compose run --rm dvc-runner dvc push
```

## Docker

```bash
docker-compose build                    # Build all
docker-compose build dvc-runner         # Build one
docker-compose run --rm dvc-runner bash # Shell
docker images | grep mlops              # List images
```

## Configuration

### .env
```bash
DAGSHUB_USER_NAME=username
DAGSHUB_TOKEN=token
MLFLOW_TRACKING_URI=https://dagshub.com/username/repo.mlflow
MLFLOW_TRACKING_USERNAME=username
MLFLOW_TRACKING_PASSWORD=token
```

### Update Paths
In `dvc.yaml`, replace:
```yaml
-v /home/seb/project/mlops-dvc-docker-reference/data:/data
```
With your project path.

## Files

```
.env                    # Credentials (gitignored)
params.yaml             # Hyperparameters
dvc.yaml                # Pipeline definition
dvc.lock                # Pipeline state
.dvc/config             # Remote URL
.dvc/config.local       # Auth (gitignored)
```

## Troubleshooting

**Output does not exist**
```bash
pwd
# Update paths in dvc.yaml
```

**MLflow auth fails**
```bash
cat .env                # Check credentials
cat params.yaml | grep mlflow
```

**DVC push fails**
```bash
cat .dvc/config.local   # Check auth
```

**Docker permission**
```bash
sudo usermod -aG docker $USER
# Logout and login
```

## Experiment Workflow

```bash
vim params.yaml         # Change hyperparameters
make run                # Rerun pipeline
make push               # Upload results
# View experiments on DagsHub
make git-sync           # Commit if satisfied
```

## URLs

- GitHub: https://github.com/ssime-git/mlops-dvc-docker-reference
- DagsHub: https://dagshub.com/ssime-git/mlops-dvc-docker-reference
- MLflow: https://dagshub.com/ssime-git/mlops-dvc-docker-reference.mlflow
