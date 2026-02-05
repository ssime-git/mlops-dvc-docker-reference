# Architecture

## System Overview

```
GitHub ←→ DagsHub (webhook sync)
           ├── DVC Storage
           ├── MLflow Server
           └── Model Registry

Local:
  Docker Compose
    └── DVC Runner
        └── Spawns stage containers via Docker socket
            ├── Ingest
            ├── Preprocess
            ├── Train
            └── Evaluate
```

## Data Flow

1. Code changes pushed to GitHub
2. DagsHub syncs via webhook
3. Run pipeline: `make run`
4. DVC orchestrates Docker containers
5. Stages read/write to shared volumes
6. MLflow logs experiments to DagsHub
7. Models registered in DagsHub registry
8. Data pushed to DagsHub storage

## Components

- **Git**: Code versioning
- **DVC**: Pipeline + data versioning
- **Docker**: Container isolation
- **MLflow**: Experiment tracking
- **DagsHub**: Centralized storage and UI
