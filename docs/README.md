# Docs (Concise)

## Setup
- Create DagHub repo and enable GitHub sync.
- Configure DVC remote (local scope keeps secrets):
  ```bash
  dvc remote modify origin --local auth basic
  dvc remote modify origin --local user YOUR_USER
  dvc remote modify origin --local password YOUR_TOKEN
  ```
- Add MLflow credentials to `.env`:
  ```bash
  MLFLOW_TRACKING_URI=https://dagshub.com/YOUR_USER/YOUR_REPO.mlflow
  MLFLOW_TRACKING_USERNAME=YOUR_USER
  MLFLOW_TRACKING_PASSWORD=YOUR_TOKEN
  ```

## Architecture
```
GitHub ↔ DagHub (code, data, MLflow)
Local → docker-compose → dvc-runner → stage containers (ingest, preprocess, train, evaluate)
```

## Run & Restore
```bash
make build           # build stage images
make run             # run pipeline
make run-push        # run + push data/model to DagHub
make restore         # pull exact data per dvc.lock
```

## Reproduce an Experiment
- Show recorded params/metrics/data/git commit from the registry:
  ```bash
  make reproduce MODEL=iris-classifier VERSION=<n|alias> ARGS=--update-params
  ```
- Follow the printed instructions (git checkout the commit → `make restore` → `make run` → return to your branch).
- Data lineage captured in each run: git commit, combined data MD5, per-file MD5 tags, and DagHub URLs to the exact files.

## Model Promotion
- Training compares new accuracy to the production alias; if higher, it updates the `production` alias, otherwise `staging`.
- Each version is tagged with `test_accuracy`, `promoted`, and `promotion_reason` in MLflow / DagHub.

## Docker Socket Note
- The dvc-runner mounts `/var/run/docker.sock` to launch sibling stage containers. Treat it as privileged; drop the mount if nested Docker is not required.

## Guardrails
- Configure `.env` and `.dvc/config.local` before running.
- Run commands from repo root so Docker volume mounts resolve correctly.
- Commit `params.yaml` with `dvc.lock` to keep code/parameter/data versions aligned.
- Prefer `docker-compose run --rm dvc-runner dvc repro` for isolation; rotate DagHub tokens regularly.

## Troubleshooting
- Auth errors: recheck `.env` and `.dvc/config.local` values.
- Data mismatch: ensure you are on the commit shown by `make reproduce`, then rerun `make restore`.
- Socket concerns: remove the Docker socket volume if you do not need container-in-container.
