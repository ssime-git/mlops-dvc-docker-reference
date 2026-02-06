# Docs

## Current Architecture
```text
GitHub <-> DagHub (code, data, MLflow)
Host/CI DVC orchestration (uvx dvc first, dvc fallback)
  -> Docker stage containers (ingest, preprocess, train, evaluate)
```

Default runtime is host-orchestrated (`make run`).  
Nested Docker (`make run-nested`) is explicit opt-in only.

## Setup
1. Create `.env`:
   ```bash
   make setup-env
   ```
2. Fill credentials in `.env`:
   ```env
   DAGSHUB_USER_NAME=...
   DAGSHUB_TOKEN=...
   MLFLOW_TRACKING_URI=https://dagshub.com/<user>/<repo>.mlflow
   MLFLOW_TRACKING_USERNAME=...
   MLFLOW_TRACKING_PASSWORD=...
   ```
3. Configure DVC remote auth (local only):
   ```bash
   uvx dvc remote modify origin --local auth basic
   uvx dvc remote modify origin --local user "$DAGSHUB_USER_NAME"
   uvx dvc remote modify origin --local password "$DAGSHUB_TOKEN"
   ```
4. Build images:
   ```bash
   make build
   ```

## Operations
```bash
make run                # recommended (host/CI orchestration)
make run-nested         # optional nested docker mode
make run-push           # run + dvc push
make restore            # dvc pull to current dvc.lock
make status             # dvc status
make dag                # dvc dag
```

If you hit `.dvc/tmp` permission issues:
```bash
make fix-dvc-perms
```

## Reproduction
From model registry metadata:
```bash
make reproduce MODEL=iris-classifier VERSION=production ARGS=--update-params
```

From saved run JSON in an isolated worktree:
```bash
make reproduce-json FILE=experiment_<run_id>.json WORKTREE=/tmp/repro-<hash>
```

`reproduce-json` now uses host-mode DVC (`uvx dvc` first, `dvc` fallback), patches older worktree `dvc.yaml` path/uid issues, and runs `dvc pull` + `dvc repro`.

## Quality Gates
```bash
make lint               # uvx ruff check .
make fmt-check          # uvx ruff format --check .
make test-unit          # pytest lineage tests
make test-pipeline-smoke
make test               # unit + full pipeline checks
```

CI workflow: `.github/workflows/ci.yml`.

## Security Notes
- `docker-compose.yml` does not mount `/var/run/docker.sock`.
- `docker-compose.nested.yml` is privileged and only for explicit nested mode.
- Keep secrets only in `.env` and `.dvc/config.local`.
