# MLOps Pipeline with DVC + Docker + DagsHub

ML pipeline orchestration using containerized stages, data versioning, and experiment tracking.

## Quick Start

```bash
git clone https://github.com/ssime-git/mlops-dvc-docker-reference.git
cd mlops-dvc-docker-reference
make setup-env
# Edit .env with your DagsHub credentials
make build
make run
make push
```

## Configuration

Create `.env`:
```bash
DAGSHUB_USER_NAME=your-username
DAGSHUB_TOKEN=your-token
MLFLOW_TRACKING_URI=https://dagshub.com/your-username/your-repo.mlflow
```

Configure DVC remote in `.dvc/config.local`:
```bash
dvc remote modify origin --local auth basic
dvc remote modify origin --local user YOUR_USER
dvc remote modify origin --local password YOUR_TOKEN
```

## Commands

```bash
make build          # Build Docker images
make run            # Run pipeline
make push           # Push data to DagsHub
make status         # Check pipeline status
```

## Pipeline Stages

1. **ingest**: Download Iris dataset
2. **preprocess**: Split train/test (80/20)
3. **train**: Train RandomForest, compare with production, promote if better
4. **evaluate**: Calculate metrics

## Model Promotion

Training automatically compares with production model:
- Better accuracy → promote to Production
- Otherwise → register in Staging

## Project Structure

```
├── dvc.yaml        # Pipeline definition
├── params.yaml     # Hyperparameters
├── stages/         # Stage scripts
├── data/           # DVC tracked
├── models/         # DVC tracked
└── metrics/        # Outputs
```

## Links

- GitHub: https://github.com/ssime-git/mlops-dvc-docker-reference
- DagsHub: https://dagshub.com/ssime-git/mlops-dvc-docker-reference
- Docs: See `docs/` for technical details
