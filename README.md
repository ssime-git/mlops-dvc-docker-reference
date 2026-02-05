# MLOps Pipeline with DVC + Docker + DagsHub

Reference implementation showing containerized ML pipeline orchestration with GitHub + DagsHub integration.

## Architecture

```
GitHub (Code) ←→ DagsHub (Mirror + Data + Experiments)
                      ↓
              DVC Orchestrator (container)
                      ↓ via /var/run/docker.sock
          Spawns → [Ingest] → [Preprocess] → [Train] → [Evaluate]
                   (containers running as siblings)
                      ↓
              MLflow Tracking (DagsHub)
              Model Registry (DagsHub)
```

## Stack

- **GitHub**: Code versioning & collaboration
- **DagsHub**: Connected repository (auto-syncs from GitHub) + DVC remote storage + MLflow tracking + model registry
- **DVC**: Pipeline orchestration & data versioning
- **Docker**: Container isolation per stage
- **MLflow**: Experiment tracking & model registry
- **Docker Socket**: Orchestrator pattern (sibling containers)

## Quick Start

### 1. Setup

```bash
# Clone the repository
git clone https://github.com/ssime-git/mlops-dvc-docker-reference.git
cd mlops-dvc-docker-reference

# Create .env file
make setup-env
# Edit .env with your DagsHub credentials

# Build Docker images
make build
```

### 2. Configure DagsHub

1. Create a DagsHub account at https://dagshub.com
2. Create a "Connected Repository" linking to your GitHub repo
3. Get your DagsHub token from Settings → Access Tokens
4. Update `.env` with your credentials:
   ```bash
   DAGSHUB_USER_NAME=your-username
   DAGSHUB_TOKEN=your-token
   MLFLOW_TRACKING_URI=https://dagshub.com/your-username/mlops-dvc-docker-reference.mlflow
   ```

5. Update paths in `dvc.yaml` to match your local path:
   ```yaml
   # Replace /home/seb/project/mlops-dvc-docker-reference
   # with your actual project path
   ```

### 3. Run Pipeline

```bash
# Run complete pipeline
make run

# Or run individual stages
make run-ingest
make run-preprocess
make run-train
make run-evaluate
```

### 4. Push Results

```bash
# Push data to DagsHub storage
make push

# Commit and push code to GitHub (auto-syncs to DagsHub)
make git-sync
```

## Makefile Commands

```bash
make help           # Show all available commands

# Setup
make setup-env      # Create .env from template
make build          # Build Docker images

# Pipeline
make run            # Run complete pipeline
make run-ingest     # Run only ingest stage
make run-train      # Run only train stage

# Data & Experiments
make push           # Push data to DagsHub
make pull           # Pull data from DagsHub
make status         # Show pipeline status
make dag            # Show pipeline DAG

# Git
make git-sync       # Commit and push to GitHub

# Cleanup
make clean          # Remove generated files
make test           # Test pipeline
```

## Project Structure

```
├── Makefile                   # Convenient commands
├── Dockerfile.dvc-runner      # Orchestrator container
├── docker-compose.yml         # Local dev setup
├── dvc.yaml                   # Pipeline definition
├── params.yaml                # Pipeline parameters
├── .env                       # Credentials (gitignored)
├── stages/                    # Microservices
│   ├── ingest/
│   │   ├── Dockerfile
│   │   ├── ingest.py
│   │   └── requirements.txt
│   ├── preprocess/
│   ├── train/
│   └── evaluate/
├── data/                      # DVC tracked (gitignored)
│   ├── raw/iris.csv
│   └── processed/
├── models/                    # DVC tracked (gitignored)
└── metrics/                   # Pipeline outputs
```

## Pipeline Stages

Each stage is an isolated Docker container:

1. **Ingest**: Download Iris dataset → `data/raw/iris.csv`
2. **Preprocess**: Split train/test → `data/processed/{train,test}.csv`
3. **Train**: Train RandomForest → log to MLflow + register model in DagsHub
4. **Evaluate**: Calculate metrics → `metrics/metrics.json` + log to MLflow

## GitHub + DagsHub Integration

### How It Works

1. **Code**: Pushed to GitHub
2. **Auto-Sync**: DagsHub detects changes via webhook and syncs automatically
3. **Data**: Tracked by DVC, stored in DagsHub storage
4. **Experiments**: Logged to MLflow on DagsHub
5. **Models**: Registered in DagsHub model registry

### Workflow

```bash
# 1. Modify code
vim stages/train/train.py

# 2. Commit to GitHub
git add .
git commit -m "Improve model"
git push origin main
# → DagsHub automatically syncs the code

# 3. Run pipeline
make run

# 4. Push data to DagsHub
make push
# → MLflow experiments already logged during training
```

### View Results on DagsHub

After running the pipeline, check https://dagshub.com/your-username/mlops-dvc-docker-reference:

- **Files**: Code synced from GitHub
- **Data**: DVC-tracked datasets
- **Experiments**: MLflow runs with metrics
- **Models**: Registered models in model registry

## What Makes This Different?

**Traditional approach:**
```bash
python ingest.py      # Run on host
python preprocess.py  # Run on host
python train.py       # Run on host
```

**This approach:**
```bash
make run  # DVC (in container) orchestrates other containers
```

Benefits:
- Each stage runs in isolation with exact dependencies
- Reproducible across different environments
- Easy to scale to production (same pattern as Airflow)
- Data versioned separately from code
- Experiments tracked automatically

## Key Concepts to Research

1. **Docker Socket Sharing**: Why does the DVC runner need `/var/run/docker.sock`?
   - Allows the DVC container to spawn sibling containers (not nested)
   - Containers share the host's Docker daemon

2. **Sibling Containers**: How do containers spawn other containers without nesting?
   - DVC runner mounts Docker socket: `/var/run/docker.sock`
   - Spawned containers are siblings, not children
   - All containers run at the same level on the host

3. **Volume Strategy**: How do stages share data without copying?
   - Host path mounted into all stage containers
   - Files written by one stage are immediately visible to the next

4. **DVC Remote**: How does DagsHub storage work?
   - DagsHub provides S3-compatible storage
   - DVC uses this as a remote for data versioning
   - Configured in `.dvc/config` and `.dvc/config.local`

5. **MLflow Registry**: Why save models to DagsHub instead of locally?
   - Models versioned with experiments
   - Team access without file sharing
   - Easy deployment (pull from registry)
   - Stage transitions (Staging → Production)

## Path Configuration

The `dvc.yaml` file uses absolute paths for volume mounting. If you clone this repo to a different location, you must update these paths.

**Current paths:**
```yaml
-v /home/seb/project/mlops-dvc-docker-reference/data:/data
```

**Your paths:**
Replace with your actual project directory in all stages (ingest, preprocess, train, evaluate).

**Why absolute paths?**
The DVC container spawns sibling containers via Docker socket. These containers need to mount volumes using the **host's** filesystem paths, not the DVC container's internal paths.

## Migration to Airflow (Phase 3)

The pattern here (orchestrator container → worker containers) is identical to Airflow:
- Each DVC stage → Airflow task
- `dvc.yaml` dependencies → Airflow DAG dependencies
- Docker containers → Airflow DockerOperator

Study how `dvc.yaml` defines stages, then translate to Airflow DAGs.

## Documentation

- [DagsHub Setup](docs/DAGSHUB_SETUP.md) - DVC remote + MLflow + Model Registry
- [Docker Socket Pattern](docs/DOCKER_SOCKET.md) - Why and how
- [Architecture](docs/ARCHITECTURE.md) - System design
- [Quick Start](QUICKSTART.md) - Step-by-step guide

## Troubleshooting

### Pipeline fails with "output does not exist"
- Check that paths in `dvc.yaml` match your project location
- Ensure volumes are mounted correctly in Docker

### MLflow authentication fails
- Verify `.env` file has correct credentials
- Check `params.yaml` has MLflow configuration

### DVC push fails
- Verify DagsHub token in `.dvc/config.local`
- Check network connectivity to dagshub.com

### Permission denied on Docker socket
```bash
sudo usermod -aG docker $USER
# Then logout/login
```

## Research Questions

1. How does DVC know when to skip a stage?
   - Compares MD5 hashes of dependencies in `dvc.lock`
   - Skips if deps, params, and code unchanged

2. What's the difference between `deps`, `outs`, and `metrics` in `dvc.yaml`?
   - `deps`: Input files that trigger stage reruns
   - `outs`: Output files tracked by DVC
   - `metrics`: Special outputs for comparison (not cached)

3. Why mount `/var/run/docker.sock` instead of using Docker-in-Docker?
   - Simpler architecture
   - Better performance (no nested Docker daemons)
   - Containers are siblings, not parent-child

4. How does MLflow autologging work with DagsHub?
   - Set `MLFLOW_TRACKING_URI` to DagsHub MLflow server
   - `mlflow.sklearn.log_model()` automatically uploads to DagsHub
   - Experiments visible in DagsHub UI

5. What happens if two stages modify the same file?
   - DVC detects conflict via hash mismatch
   - Pipeline fails with error
   - Fix: Ensure stages have distinct outputs

## Contributing

This is a reference implementation for learning MLOps patterns. Feel free to:
- Adapt for your own datasets
- Add new pipeline stages
- Experiment with different ML models
- Translate to Airflow or other orchestrators

## License

MIT License - feel free to use for learning and production projects.

## Links

- GitHub Repository: https://github.com/ssime-git/mlops-dvc-docker-reference
- DagsHub Mirror: https://dagshub.com/ssime-git/mlops-dvc-docker-reference
