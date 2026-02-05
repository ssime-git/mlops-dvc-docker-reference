# Docker Socket Pattern

## The Problem

**We want:** DVC running in a container to spawn other containers (stages).

**Options:**
1. **Docker-in-Docker (DinD)** - Run Docker daemon inside container ❌
2. **Docker Socket Sharing** - Share host's Docker daemon ✅

## What is `/var/run/docker.sock`?

The Docker daemon socket. When you run `docker run`, your CLI talks to this socket.

```bash
# On your host
ls -l /var/run/docker.sock
# srw-rw---- 1 root docker 0 Jan 30 10:00 /var/run/docker.sock
```

## How It Works

```
┌─────────────────────────────────────┐
│   Host Machine                      │
│                                     │
│   Docker Daemon                     │
│   (listening on socket)             │
│        ↑                            │
│        │                            │
│   /var/run/docker.sock              │
│        │                            │
│        │ mounted into               │
│        ↓                            │
│   ┌──────────────────────────────┐ │
│   │ DVC Container                │ │
│   │                              │ │
│   │ docker run ... ────────────┐ │ │
│   └──────────────────────────────┘ │
│                                  │  │
│        spawns sibling            │  │
│        (NOT nested)              ↓  │
│   ┌──────────────────────────────┐ │
│   │ Stage Container              │ │
│   │ (runs alongside DVC)         │ │
│   └──────────────────────────────┘ │
└─────────────────────────────────────┘
```

## Implementation

### In docker-compose.yml

```yaml
services:
  dvc-runner:
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock  # ← Share socket
```

### What This Enables

When DVC container runs:
```bash
docker run -v $(pwd)/data:/data mlops-ingest python ingest.py
```

It's actually calling the **host's Docker daemon**, which spawns a **sibling container**.

## Security Implications

⚠️ **CRITICAL:** Container with socket access has root-equivalent power.

**It can:**
- Spawn any container (including privileged ones)
- Access all host Docker resources
- Potentially escape to host

**Safe in:**
- Development environments ✅
- CI/CD with trusted code ✅
- Your own laptop ✅

**Dangerous in:**
- Production with untrusted code ❌
- Multi-tenant systems ❌

## Why Not Docker-in-Docker?

**Docker-in-Docker (DinD):**
```dockerfile
FROM docker:dind
# Runs its OWN Docker daemon inside
```

**Problems:**
- Requires `--privileged` flag (even worse security)
- Nested filesystems = performance issues
- Complex networking
- Cache inefficiency

**Socket sharing is simpler and standard practice.**

## Alternative: Kubernetes

In production (Phase 3+), you'd use Kubernetes which handles this differently:
- Pods with multiple containers
- Kubernetes API (not Docker socket)
- Proper RBAC and security

## Verification

Check if socket works:
```bash
# Inside dvc-runner container
docker ps  # Should show host's containers

# Should NOT show DVC container running "inside" DVC container
# They run as siblings on the host
```

## Research Questions

1. What's the difference between `docker run --rm` in the socket pattern vs DinD?
2. How do sibling containers share volumes?
3. Why does Jenkins/GitLab CI use this pattern?
4. What's a rootless Docker socket?
5. How would you secure this in production?
