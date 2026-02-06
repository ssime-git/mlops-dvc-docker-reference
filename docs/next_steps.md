# Next Steps to Raise Production Readiness

Target: move from strong reference project to production-grade reliability and operations.

## A) Reliability/Operations Hardening

1. Wrap external service calls (MLflow/DagHub) in retry with bounded backoff.
2. Standardize JSON logs (or key-value logs) for ingestion by observability tools.
3. Record stage runtime and outcome in a simple machine-readable artifact.
4. Add explicit timeout policy for long-running reproduce commands.

Success criteria:
- Transient network failures are retried safely.
- Runs are diagnosable from logs alone.
- Basic reliability metrics are visible in CI and local runs.

## B) Release Discipline

1. Define versioning policy (`vX.Y.Z` tags).
2. Add `CHANGELOG.md` and release checklist.
3. Pin and regularly review dependency versions.

Success criteria:
- Every release is reproducible and documented.
- Dependency drift is controlled.

## C) Phase 3A (Airflow `DockerOperator`)

1. Create an Airflow DAG with one task per stage image.
2. Reuse the same image tags and container entrypoints from Phase 2.
3. Mount/pass volumes, secrets, and env consistently with current DVC runs.
4. Encode stage ordering in DAG dependencies to mirror DVC graph.
5. Keep Docker daemon access only in Airflow worker/executor context.

Success criteria:
- Airflow executes the same stage images with equivalent outputs.
- Orchestrator changes, container contracts stay stable.

## D) Phase 3B (Optional `KubernetesPodOperator`)

1. Reuse same stage images in Kubernetes pods.
2. Replace Docker-specific mounts with Kubernetes volumes/secrets/configs.
3. Keep env/params interface stable so stage code is unchanged.
4. Map resource requests/limits per stage for teachable scheduling behavior.

Success criteria:
- Same stage image contracts run under Kubernetes.
- Team learns portability of containerized stages across orchestrators.

## E) Cross-Phase Contract Checklist

- Inputs/outputs paths are stable across DVC, DockerOperator, and KubernetesPodOperator.
- Environment variable names are stable (`MLFLOW_*`, DagHub credentials, project paths).
- Artifact formats remain unchanged (`model_metadata.json`, `metrics.json`, confusion matrix JSON).
- Stage exit codes and logging behavior are deterministic.

## Suggested implementation order

1. Retry + resilient MLflow/DagHub calls.
2. Structured logging and run correlation IDs.
3. Operational KPI artifacts and CI surfacing.
4. Airflow DAG (Phase 3A, `DockerOperator`).
5. Optional Kubernetes DAG migration (Phase 3B).
6. Release process formalization (tags/changelog/version policy).
