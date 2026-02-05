# Project Summary

Reference implementation of containerized ML pipeline with DVC orchestration and experiment tracking.

## Architecture

```
GitHub -> DagsHub (mirror)
   |
DVC Orchestrator (Docker)
   |
Stage Containers (Ingest, Preprocess, Train, Evaluate)
   |
MLflow (DagsHub) + Model Registry
```

## Components

| Component | Technology | Purpose |
|-----------|-----------|---------|
| Code | Git + GitHub | Version control |
| Data | DVC + DagsHub | Large file versioning |
| Experiments | MLflow + DagsHub | Metrics tracking |
| Models | MLflow Registry | Model versioning |
| Runtime | Docker | Isolated environments |
| Orchestration | DVC | Pipeline execution |

## Pipeline

### Ingest
- Input: scikit-learn datasets API
- Output: `data/raw/iris.csv` (150 samples)

### Preprocess
- Input: `data/raw/iris.csv`
- Output: `data/processed/train.csv` (120), `test.csv` (30)
- Split: 80/20

### Train
- Input: Train/test data, `params.yaml`
- Output: `models/model_metadata.json`, MLflow run
- Model: RandomForest classifier
- Registry: iris-classifier

### Evaluate
- Input: Model metadata, test data
- Output: `metrics/metrics.json`, `confusion_matrix.json`
- Metrics: accuracy, precision, recall, F1

## Setup

```bash
git clone <repo>
cd mlops-dvc-docker-reference
make setup-env
# Edit .env and dvc.yaml paths
make build
make run
make push
```

## Key Files

**Committed:**
- `dvc.yaml` - Pipeline definition
- `params.yaml` - Hyperparameters
- `.dvc/config` - Remote URL
- `dvc.lock` - Pipeline state
- `Makefile` - Commands

**Ignored:**
- `.env` - Credentials
- `.dvc/config.local` - Auth
- `data/` - Datasets
- `models/` - Artifacts
- `metrics/` - Outputs

## Commands

```bash
make help     # List commands
make run      # Run pipeline
make push     # Upload to DagsHub
make status   # Check state
make test     # Verify outputs
```

## Technical Notes

**Sibling Containers**: DVC runner uses Docker socket to spawn stage containers. All containers run at host level, requiring absolute paths in volume mounts.

**DVC Variables**: `dvc.yaml` uses `${mlflow.tracking_uri}` resolved from `params.yaml`.

**Path Configuration**: Update `/home/seb/project/mlops-dvc-docker-reference` in `dvc.yaml` to match your directory.

## Results

- Test accuracy: 93.33%
- Model: iris-classifier v1
- MLflow run: 28817f39a3dd49d48ee8f8431df9e871
- DVC files: 4 pushed to DagsHub

## Links

- GitHub: https://github.com/ssime-git/mlops-dvc-docker-reference
- DagsHub: https://dagshub.com/ssime-git/mlops-dvc-docker-reference
