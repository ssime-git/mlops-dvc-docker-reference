# MLOps Pipeline with DVC + Docker + DagHub

Containerized ML pipeline with DVC for data/version reproducibility and MLflow tracking on DagHub.

Phase 2 status: ready (DVC + Docker stages, host orchestration).  
Phase 3 plan (Airflow): `docs/next_steps.md`.

## Main Options

### Option A: Recommended (`make run`)
- Orchestration: host DVC command (`uvx dvc` first, `dvc` fallback).
- Stage execution: Docker containers per stage from `dvc.yaml`.
- Why: no persistent virtualenv required, cleaner local/CI behavior.

### Option B: Nested Docker (`make run-nested`)
- Orchestration: `dvc-runner` container runs DVC.
- Requires Docker socket mount via `docker-compose.nested.yml`.
- Why: compatibility fallback when host DVC tooling is unavailable.

## Prerequisites
- Docker and Docker Compose
- `uv` (`uvx`) preferred, or `dvc` CLI
- Git
- DagHub account and token

## Setup

```bash
git clone https://github.com/ssime-git/mlops-dvc-docker-reference.git
cd mlops-dvc-docker-reference
make setup-env
```

Fill `.env` with your DagHub/MLflow credentials:

```env
DAGSHUB_USER_NAME=your-username
DAGSHUB_TOKEN=your-token
MLFLOW_TRACKING_URI=https://dagshub.com/your-username/your-repo.mlflow
MLFLOW_TRACKING_USERNAME=your-username
MLFLOW_TRACKING_PASSWORD=your-token
```

Configure DVC remote auth once:

```bash
uvx dvc remote modify origin --local auth basic
uvx dvc remote modify origin --local user "$DAGSHUB_USER_NAME"
uvx dvc remote modify origin --local password "$DAGSHUB_TOKEN"
```

Build images:

```bash
make build
```

Optional quality checks setup:
- No local virtualenv needed; linting runs through `uvx`.

## Run Pipeline

Recommended:

```bash
make run
```

Nested fallback:

```bash
make run-nested
```

Other common commands:

```bash
make run-push
make status
make dag
make restore
```

## Reproduce Experiments

### Reproduce from model registry metadata

```bash
make reproduce MODEL=iris-classifier VERSION=production ARGS=--update-params
```

What it does:
- Reads params/metrics from MLflow model version.
- Saves an `experiment_<run_id>.json` file.
- Optionally updates `params.yaml`.

### Reproduce from saved JSON (worktree-isolated)

```bash
make reproduce-json FILE=experiment_<run_id>.json WORKTREE=/tmp/repro-<hash>
```

What it does:
- Creates a git worktree at the recorded `git_commit`.
- Updates `params.yaml` to match the run.
- Runs host-mode `dvc pull` and `dvc repro` in that worktree.
- Uses `uvx dvc` first, falls back to `dvc`.

## Testing

```bash
make test
make test-unit
make test-pipeline
make test-pipeline-smoke
make lint
make fmt-check
```

What each target does:
- `make test`: unit tests + full pipeline verification (includes train/evaluate).
- `make test-pipeline-smoke`: lightweight ingest/preprocess pipeline check for CI.
- `make lint`: `uvx ruff check .`
- `make fmt-check`: `uvx ruff format --check .`

## Troubleshooting
- Host DVC command missing:
`uv`/`uvx` is preferred; otherwise install `dvc`; or use `make run-nested`.
- `.dvc/tmp` permission error:
`make fix-dvc-perms`
- Auth errors:
recheck `.env` and `.dvc/config.local`.
- Data mismatch:
confirm target commit and corresponding `dvc.lock`.
- Running from wrong directory:
run commands from repo root so mounts resolve correctly.
- Experiment JSON clutter:
`experiment_*.json` is treated as transient local metadata and ignored by git.

## Security Notes
- `docker-compose.yml` is safe-by-default (no Docker socket mount).
- `docker-compose.nested.yml` is privileged and only for explicit opt-in nested mode.
- Keep secrets in `.env` and `.dvc/config.local`; do not commit them.

## Documentation
- `docs/README.md`
- `docs/next_steps.md`
- `.github/workflows/ci.yml`
