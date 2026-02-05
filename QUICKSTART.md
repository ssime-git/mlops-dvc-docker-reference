# Quick Start

## Prerequisites

- Docker & Docker Compose installed
- DagsHub account
- Git configured

## Setup (5 minutes)

### 1. Clone Repository

```bash
git clone <your-repo-url>
cd mlops-dvc-docker-reference
```

### 2. Configure DagsHub

Create `.env` file:
```bash
cp .env.example .env
# Edit .env with your DagsHub credentials
```

Configure DVC remote:
```bash
# Get these commands from DagsHub UI (Remote → Data → DVC)
dvc remote add origin https://dagshub.com/YOUR_USER/mlops-pipeline.dvc
dvc remote modify origin --local auth basic
dvc remote modify origin --local user YOUR_USER
dvc remote modify origin --local password YOUR_TOKEN
```

### 3. Build Images

```bash
docker-compose build
```

This builds:
- `mlops-dvc-runner` (orchestrator)
- `mlops-ingest`
- `mlops-preprocess`
- `mlops-train`
- `mlops-evaluate`

### 4. Run Pipeline

```bash
# Full pipeline
docker-compose run dvc-runner dvc repro

# Or step by step
docker-compose run dvc-runner dvc repro ingest
docker-compose run dvc-runner dvc repro preprocess
docker-compose run dvc-runner dvc repro train
docker-compose run dvc-runner dvc repro evaluate
```

### 5. Push to DagsHub

```bash
# Push data versioned by DVC
docker-compose run dvc-runner dvc push

# MLflow experiments already logged during training
```

### 6. View Results

**DagsHub UI:**
- Data: See DVC-tracked files
- Experiments: MLflow runs with metrics
- Models: Registered models in model registry

## Testing Individual Stages

```bash
# Test ingest alone
docker-compose run ingest python ingest.py

# Test preprocess alone
docker-compose run preprocess python preprocess.py

# etc.
```

## Troubleshooting

**"Permission denied" on socket:**
```bash
# Add your user to docker group
sudo usermod -aG docker $USER
# Then logout/login
```

**"DVC remote not configured":**
```bash
# Check .dvc/config.local exists
cat .dvc/config.local
```

**"MLflow authentication failed":**
```bash
# Verify .env variables are loaded
docker-compose run dvc-runner env | grep MLFLOW
```

## Understanding the Flow

```
1. DVC reads dvc.yaml
   ↓
2. For each stage, runs: docker run --rm -v ... mlops-<stage>
   ↓
3. Stage container executes script
   ↓
4. Output saved to shared volume
   ↓
5. DVC tracks output hash in dvc.lock
   ↓
6. Next stage uses previous stage's output
```

## What Gets Tracked Where?

| Data Type | Tracked By | Stored In |
|-----------|-----------|-----------|
| Raw data | DVC | DagsHub storage |
| Processed data | DVC | DagsHub storage |
| Model files | MLflow | DagsHub registry |
| Metrics | DVC + MLflow | Both |
| Code | Git | GitHub/DagsHub |
| Pipeline definition | Git (dvc.yaml) | GitHub/DagsHub |

## Next Steps

1. Read `docs/DOCKER_SOCKET.md` to understand the pattern
2. Read `docs/DAGSHUB_SETUP.md` for full DagsHub integration
3. Modify `params.yaml` and rerun to see DVC skip unchanged stages
4. Study how train.py logs to MLflow model registry
