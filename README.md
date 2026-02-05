# MLOps Pipeline with DVC + Docker + DagsHub

ML pipeline orchestration using containerized stages, data versioning, and experiment tracking.

## Architecture

```
GitHub (Code) <-> DagsHub (Mirror + Data + MLflow)
                       |
                DVC Orchestrator
                       |
        [Ingest] -> [Preprocess] -> [Train] -> [Evaluate]
```

## Stack

- **GitHub**: Code versioning
- **DagsHub**: Connected repository (auto-sync) + DVC storage + MLflow server + model registry
- **DVC**: Pipeline orchestration and data versioning
- **Docker**: Isolated containers per stage
- **MLflow**: Experiment tracking

## Quick Start

```bash
# 1. Clone
git clone https://github.com/ssime-git/mlops-dvc-docker-reference.git
cd mlops-dvc-docker-reference

# 2. Setup (generates dvc.yaml with correct paths + creates .env)
make setup
# Edit .env with your DagsHub token

# 3. Build and run
make build
make run
make push
```

## Configuration

### .env file
```bash
DAGSHUB_USER_NAME=your-username
DAGSHUB_TOKEN=your-token
MLFLOW_TRACKING_URI=https://dagshub.com/your-username/your-repo.mlflow
```

### dvc.yaml generation
Run `make setup-dvc` to auto-generate dvc.yaml with correct paths.
File is generated from `dvc.yaml.template` using current directory.

## Common Commands

```bash
make help           # List all commands
make build          # Build Docker images
make run            # Run pipeline
make push           # Push data to DagsHub
make status         # Check pipeline status
make test           # Run and verify outputs
```

## Pipeline Stages

1. **ingest**: Download Iris dataset -> `data/raw/iris.csv`
2. **preprocess**: Split train/test -> `data/processed/{train,test}.csv`
3. **train**: Train RandomForest -> compare with production -> promote if better
4. **evaluate**: Calculate metrics -> `metrics/metrics.json`

## Model Promotion

Train stage automatically compares new model with current production model:
- If no production model exists: promote new model to Production
- If new model has better test accuracy: promote to Production, archive old
- Otherwise: register as new version in Staging

Check model stage on DagsHub: Models tab -> iris-classifier

## Project Structure

```
├── Makefile                   # Command shortcuts
├── dvc.yaml                   # Pipeline definition
├── params.yaml                # Hyperparameters
├── stages/                    # Stage implementations
│   ├── ingest/
│   ├── preprocess/
│   ├── train/
│   └── evaluate/
├── data/                      # DVC tracked (gitignored)
├── models/                    # DVC tracked (gitignored)
└── metrics/                   # Pipeline outputs
```

## Key Concepts

**Sibling Container Pattern**: DVC runner spawns stage containers via Docker socket. Containers run as siblings on the host, not nested. Requires absolute host paths in volume mounts.

**DVC Caching**: Pipeline skips stages when dependencies unchanged (checked via MD5 hashes in `dvc.lock`).

**GitHub + DagsHub Sync**: Code pushed to GitHub automatically syncs to DagsHub via webhook.

## Troubleshooting

**"output does not exist"**
Run `make setup-dvc` to regenerate dvc.yaml with correct paths.

**MLflow authentication fails**
Verify `.env` credentials and `params.yaml` mlflow section.

**DVC push fails**
Check `.dvc/config.local` has valid credentials.

## Links

- GitHub: https://github.com/ssime-git/mlops-dvc-docker-reference
- DagsHub: https://dagshub.com/ssime-git/mlops-dvc-docker-reference
