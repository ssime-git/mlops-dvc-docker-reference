# Docker Socket Pattern

## Why Mount Docker Socket?

DVC runner needs to spawn sibling containers to execute pipeline stages.

## How It Works

```
Host Docker Daemon
    ↑ (via /var/run/docker.sock)
DVC Runner Container
    ↓ (spawns via socket)
Stage Containers (siblings, not children)
```

## Configuration

In `docker-compose.yml`:
```yaml
volumes:
  - /var/run/docker.sock:/var/run/docker.sock
```

In `dvc.yaml`:
```yaml
cmd: docker run --rm -v $PROJECT_PATH/data:/data mlops-ingest
```

## Key Points

- Sibling containers run at host level
- All containers share host Docker daemon
- Requires absolute host paths for volume mounts
- More efficient than Docker-in-Docker

## Security Note

Mounting Docker socket gives container control over host Docker daemon.
Only use in trusted environments.
