# MLOps Pipeline with DVC + Docker + DagHub

Containerized, reproducible ML pipeline with DVC data versioning and MLflow tracking on DagHub.

## Prerequisites
- Docker & Docker Compose
- DagHub account (MLflow endpoint)
- Git

## Setup

```bash
git clone https://github.com/ssime-git/mlops-dvc-docker-reference.git
cd mlops-dvc-docker-reference
make setup-env               # creates .env; fill credentials
make build                   # build stage images
```

## Run

```bash
make run            # run pipeline locally
make run-push       # run + push data/model to DagHub
make status         # pipeline status
make restore        # pull exact data from DagHub
```

## Restore

```bash
make restore        # pulls data per dvc.lock (requires DagHub creds)
```

## Reproduce

- From registry metadata: `make reproduce MODEL=iris-classifier VERSION=<n|alias> ARGS=--update-params`
- From saved JSON (worktree-isolated):

  ```bash
  export DAGSHUB_USER_NAME=... DAGSHUB_TOKEN=... MLFLOW_TRACKING_URI=...
  make reproduce-json FILE=experiment_<run>.json WORKTREE=/tmp/repro-<hash>
  ```
  
Creates a git worktree at the recorded commit, updates params, then runs `dvc pull` and `dvc repro` inside Docker.

Example (reproduce production model; grab the commit’s `dvc.lock`, pull matching data, then run):

```bash
make reproduce MODEL=iris-classifier VERSION=production ARGS=--update-params
# Output shows git commit, e.g., 1ea53d7
commit=1ea53d7
work=/tmp/repro-$commit
git worktree add "$work" "$commit"   # reads that commit’s dvc.lock without touching main
cd "$work"
make restore                            # pulls data per that dvc.lock
make run                                # reproduces with matching code+data
cd -
git worktree remove "$work"
```

## Environment
`.env` (MLflow/DagHub):

```
DAGSHUB_USER_NAME=your-username
DAGSHUB_TOKEN=your-token
MLFLOW_TRACKING_URI=https://dagshub.com/your-username/your-repo.mlflow
MLFLOW_TRACKING_USERNAME=your-username
MLFLOW_TRACKING_PASSWORD=your-token
```

`.dvc/config.local` (DVC remote):

```
dvc remote modify origin --local auth basic
dvc remote modify origin --local user YOUR_USER
dvc remote modify origin --local password YOUR_TOKEN
```

## Operational Guardrails
- Docker socket mount in `docker-compose.yml` is privileged; remove if nested Docker not required.
- Keep secrets in `.env` / `.dvc/config.local`; never commit them. Rotate tokens regularly.
- Run commands from repo root so volume mounts resolve correctly.

## Documentation (essentials)
- `docs/README.md` – setup, run/restore, reproduction, lineage, promotion, guardrails

## Troubleshooting
- DVC/MLflow auth errors: recheck `.env` and `.dvc/config.local`.
- Data mismatch: verify `data_version` and `dvc.lock` match the target commit.
- Pipelines not writing data: ensure commands are run from repo root so mounts resolve.

## Testing
```bash
make test                      # full pipeline via Docker
docker-compose run --rm dvc-runner pytest tests/test_lineage.py
```
