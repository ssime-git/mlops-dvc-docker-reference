# Project Summary - MLOps Pipeline Reference

## What Was Built

A production-ready MLOps pipeline demonstrating best practices for:
- Containerized machine learning workflows
- Data versioning with DVC
- Experiment tracking with MLflow
- GitHub + DagsHub integration
- Reproducible ML pipelines

## Architecture Overview

```
GitHub (Code Repository)
    ↓ (automatic sync via webhook)
DagsHub (Connected Repository)
    ├── Code Mirror (synced from GitHub)
    ├── DVC Storage (data versioning)
    ├── MLflow Server (experiment tracking)
    └── Model Registry (model versioning)

Local Development:
    Docker Compose
        └── DVC Runner Container
            └── Spawns sibling containers via Docker socket
                ├── Ingest Container
                ├── Preprocess Container
                ├── Train Container
                └── Evaluate Container
```

## Key Features

### 1. GitHub + DagsHub Integration (Option B)
- **GitHub**: Primary code repository
- **DagsHub**: Automatically mirrors GitHub repository
- **Workflow**: `git push` to GitHub → DagsHub syncs automatically
- **Benefits**: Single source of truth with dual visibility

### 2. DVC Pipeline
- **4 Stages**: Ingest → Preprocess → Train → Evaluate
- **Each stage**: Isolated Docker container with specific dependencies
- **Orchestration**: DVC manages execution order and caching
- **Data Versioning**: Large files tracked separately from code

### 3. MLflow Integration
- **Experiment Tracking**: Automatic logging of parameters, metrics, artifacts
- **Model Registry**: Models registered with version control
- **DagsHub Hosting**: MLflow server hosted on DagsHub (no setup required)

### 4. Docker Orchestration
- **Pattern**: Sibling containers (not Docker-in-Docker)
- **Socket Mounting**: DVC runner accesses host Docker daemon
- **Benefits**: Better performance, simpler architecture

### 5. Makefile Commands
- **Simplified workflow**: `make run`, `make push`, `make git-sync`
- **Developer-friendly**: No need to remember long docker-compose commands
- **Documentation**: `make help` shows all available commands

## Technology Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| Code Versioning | Git + GitHub | Source control and collaboration |
| Data Versioning | DVC + DagsHub | Track large files separately |
| Experiment Tracking | MLflow + DagsHub | Log runs, compare metrics |
| Model Registry | MLflow + DagsHub | Version and stage models |
| Container Runtime | Docker | Isolated, reproducible environments |
| Orchestration | DVC | Pipeline execution and caching |
| Workflow Automation | Makefile | Simplified command interface |

## Pipeline Details

### Stage 1: Ingest
```
Input:  Internet (scikit-learn datasets)
Output: data/raw/iris.csv (150 samples, 6 columns)
Action: Download Iris dataset
```

### Stage 2: Preprocess
```
Input:  data/raw/iris.csv
Output: data/processed/train.csv (120 samples)
        data/processed/test.csv (30 samples)
Action: Split data 80/20 train/test
```

### Stage 3: Train
```
Input:  data/processed/train.csv
        data/processed/test.csv
        params.yaml (hyperparameters)
Output: models/model_metadata.json
        MLflow: logged model + metrics
        DagsHub: registered model "iris-classifier"
Action: Train RandomForest classifier
        Log to MLflow
        Register in model registry
```

### Stage 4: Evaluate
```
Input:  models/model_metadata.json
        data/processed/test.csv
Output: metrics/metrics.json
        metrics/confusion_matrix.json
        MLflow: evaluation metrics
Action: Calculate accuracy, precision, recall, F1
        Generate confusion matrix
        Log to same MLflow run as training
```

## Current State

### ✅ What Works

1. **GitHub Repository**: https://github.com/ssime-git/mlops-dvc-docker-reference
   - Code committed and pushed
   - Git history clean and well-documented

2. **DagsHub Repository**: https://dagshub.com/ssime-git/mlops-dvc-docker-reference
   - Connected to GitHub (automatic sync)
   - DVC remote configured
   - MLflow server active

3. **DVC Pipeline**
   - All 4 stages execute successfully
   - Data versioning working
   - `dvc push` tested (4 files uploaded)
   - Pipeline caching functional

4. **MLflow Tracking**
   - Experiment logged (Run ID: 28817f39a3dd49d48ee8f8431df9e871)
   - Metrics recorded:
     * Train accuracy: 1.0000
     * Test accuracy: 0.9333
   - Model registered: iris-classifier version 1

5. **Docker Setup**
   - 5 images built successfully
   - Sibling container pattern working
   - Volume mounting correct
   - Network communication functional

6. **Makefile**
   - 15+ commands available
   - All tested and working
   - Help documentation clear

### 📝 Configuration Files

**Committed to Git:**
- `.dvc/config` - DVC remote URL
- `dvc.yaml` - Pipeline definition
- `params.yaml` - Hyperparameters + MLflow config
- `dvc.lock` - Pipeline state (hashes)
- `Makefile` - Workflow commands
- `docker-compose.yml` - Container orchestration
- `Dockerfile.dvc-runner` - Orchestrator image
- `stages/*/Dockerfile` - Stage images

**Gitignored (sensitive/generated):**
- `.env` - Credentials
- `.dvc/config.local` - DVC authentication
- `data/raw/` - Raw data files
- `data/processed/` - Processed data
- `models/*.pkl` - Model artifacts
- `metrics/*.json` - Metrics files

## Quick Start for New Users

```bash
# 1. Clone
git clone https://github.com/ssime-git/mlops-dvc-docker-reference.git
cd mlops-dvc-docker-reference

# 2. Configure
make setup-env
# Edit .env with DagsHub credentials
# Edit dvc.yaml paths to match your directory

# 3. Build
make build

# 4. Run
make run

# 5. Push
make push
```

## Commands Reference

### Most Used Commands
```bash
make help           # Show all commands
make build          # Build Docker images
make run            # Run complete pipeline
make push           # Push data to DagsHub
make status         # Check pipeline status
make dag            # Visualize pipeline DAG
make test           # Test pipeline and verify outputs
```

### Development Workflow
```bash
# Modify code
vim stages/train/train.py

# Test locally
make run

# Commit to GitHub (auto-syncs to DagsHub)
make git-sync

# Push data
make push
```

## Results Verification

After running the pipeline, check:

### Local Files
```bash
ls data/raw/           # iris.csv
ls data/processed/     # train.csv, test.csv
ls models/             # model_metadata.json
ls metrics/            # metrics.json, confusion_matrix.json
cat dvc.lock          # Pipeline state with hashes
```

### GitHub
- https://github.com/ssime-git/mlops-dvc-docker-reference
- Code, Dockerfiles, pipeline configs

### DagsHub
- https://dagshub.com/ssime-git/mlops-dvc-docker-reference
- **Files**: Code synced from GitHub
- **Data**: 4 DVC-tracked files (iris.csv, train.csv, test.csv, metadata)
- **Experiments**: MLflow run with metrics
- **Models**: iris-classifier v1 in registry

## Key Learnings

### 1. Sibling Container Pattern
- DVC runner doesn't spawn child containers
- Uses host Docker daemon via socket mount
- Containers are siblings on the host
- Requires absolute host paths in volume mounts

### 2. DVC Variable Substitution
- Variables in `dvc.yaml` resolved from `params.yaml`
- Format: `${mlflow.tracking_uri}`
- Allows sensitive values to be configurable

### 3. GitHub + DagsHub Sync
- DagsHub "Connected Repository" feature
- Automatic webhook-based sync
- One `git push` updates both platforms

### 4. MLflow Without Local Storage
- Models saved directly to DagsHub registry
- No need to track large .pkl files in DVC
- Model versioning separate from data versioning

## Next Steps

### For Learning
1. Modify hyperparameters in `params.yaml`
2. Run pipeline and compare experiments in DagsHub
3. Add a new pipeline stage
4. Try different ML models
5. Translate pipeline to Airflow

### For Production
1. Add model validation stage
2. Implement A/B testing
3. Add monitoring and alerting
4. Set up CI/CD with GitHub Actions
5. Deploy model from DagsHub registry

## Important Notes

### Path Configuration
The `dvc.yaml` file contains absolute paths:
```yaml
-v /home/seb/project/mlops-dvc-docker-reference/data:/data
```

**If you clone this repo**, you MUST update these paths to match your directory.

**Why?** The DVC container spawns sibling containers that need the host's actual filesystem paths.

### Credentials
Never commit:
- `.env` (DagsHub credentials)
- `.dvc/config.local` (DVC authentication)

Always keep these in `.gitignore`.

## Troubleshooting

### Pipeline outputs not found
- Check paths in `dvc.yaml` match your project directory
- Verify volumes mounted correctly: `docker-compose run --rm dvc-runner ls /workspace/data`

### MLflow authentication fails
- Verify `.env` has correct credentials
- Check `params.yaml` has MLflow config section
- Ensure environment variables loaded in docker-compose

### DVC push fails
- Check `.dvc/config.local` has credentials
- Verify network access to dagshub.com
- Confirm DagsHub token is valid

## Project Statistics

- **Files**: 27 committed to Git
- **Docker Images**: 5 (1 orchestrator + 4 stages)
- **Pipeline Stages**: 4
- **Data Files**: 4 tracked by DVC
- **MLflow Runs**: 1 (with 6 metrics)
- **Models Registered**: 1 (iris-classifier v1)
- **Lines of Code**: ~500 (Python + YAML + Dockerfiles)
- **Documentation**: 6 markdown files

## Links

- **GitHub**: https://github.com/ssime-git/mlops-dvc-docker-reference
- **DagsHub**: https://dagshub.com/ssime-git/mlops-dvc-docker-reference
- **MLflow**: https://dagshub.com/ssime-git/mlops-dvc-docker-reference.mlflow

## Contact & Contributions

This is a reference implementation for learning MLOps patterns. Feel free to:
- Fork and adapt for your projects
- Open issues for questions
- Submit PRs for improvements
- Use in educational contexts

---

**Last Updated**: 2026-02-05
**Status**: Production-ready reference implementation
**Next Review**: When translating to Airflow (Phase 3)
