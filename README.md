# MLOps Pipeline with DVC + Docker + DagsHub

Reference implementation showing containerized ML pipeline orchestration.

## Architecture

```
DVC Orchestrator (container)
    ↓ via /var/run/docker.sock
Spawns → [Ingest] → [Preprocess] → [Train] → [Evaluate]
         (containers running as siblings)
```

## Stack

- **DVC**: Pipeline orchestration & data versioning
- **Docker**: Container isolation per stage
- **DagsHub**: Remote storage (DVC) + experiment tracking (MLflow) + model registry
- **Docker Socket**: Orchestrator pattern (research this!)

## Quick Start

```bash
# 1. Configure DagsHub (see docs/DAGSHUB_SETUP.md)
# 2. Build images
docker-compose build

# 3. Run pipeline
docker-compose run dvc-runner dvc repro

# 4. Push to DagsHub
docker-compose run dvc-runner dvc push
```

## Key Concepts to Research

1. **Docker Socket Sharing**: Why does the DVC runner need `/var/run/docker.sock`?
2. **Sibling Containers**: How do containers spawn other containers without nesting?
3. **Volume Strategy**: How do stages share data without copying?
4. **DVC Remote**: How does DagsHub storage work with S3 protocol?
5. **MLflow Registry**: Why save models to DagsHub instead of locally?

## Project Structure

```
├── Dockerfile.dvc-runner      # Orchestrator container
├── docker-compose.yml         # Local dev setup
├── dvc.yaml                   # Pipeline definition
├── stages/                    # Microservices
│   ├── ingest/
│   ├── preprocess/
│   ├── train/
│   └── evaluate/
├── data/                      # Shared volume (DVC tracked)
├── models/                    # Shared volume (DVC tracked)
└── metrics/                   # Shared volume
```

## Pipeline Stages

Each stage is an isolated Docker container:

1. **Ingest**: Download raw data → `data/raw/`
2. **Preprocess**: Transform data → `data/processed/`
3. **Train**: Train model → log to MLflow, save to DagsHub registry
4. **Evaluate**: Generate metrics → `metrics/`

## What Makes This Different?

**Traditional approach:**
```bash
python ingest.py      # Run on host
python preprocess.py  # Run on host
python train.py       # Run on host
```

**This approach:**
```bash
dvc repro  # DVC (in container) orchestrates other containers
```

Each stage runs in isolation with exact dependencies.

## Migration to Airflow (Phase 3)

The pattern here (orchestrator container → worker containers) is identical to Airflow.
Study how `dvc.yaml` defines stages, then translate to Airflow DAGs.

## Documentation

- [DagsHub Setup](docs/DAGSHUB_SETUP.md) - DVC remote + MLflow + Model Registry
- [Docker Socket Pattern](docs/DOCKER_SOCKET.md) - Why and how

## Research Questions

1. How does DVC know when to skip a stage?
2. What's the difference between `deps`, `outs`, and `metrics` in `dvc.yaml`?
3. Why mount `/var/run/docker.sock` instead of using Docker-in-Docker?
4. How does MLflow autologging work with DagsHub?
5. What happens if two stages modify the same file?
