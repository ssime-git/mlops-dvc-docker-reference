#!/usr/bin/env bash
set -euo pipefail

if [ -z "${FILE:-}" ]; then
  echo "Usage: make reproduce-json FILE=experiment_<run>.json [WORKTREE=/tmp/repro-<hash>]" >&2
  exit 1
fi

if [ ! -f "$FILE" ]; then
  echo "File not found: $FILE" >&2
  exit 1
fi

FILE_PATH=$(cd "$(dirname "$FILE")" && pwd)/$(basename "$FILE")
SOURCE_REPO_ROOT=$(pwd)

# Load repository environment if present.
if [ -f "$SOURCE_REPO_ROOT/.env" ]; then
  set -a
  . "$SOURCE_REPO_ROOT/.env"
  set +a
fi

if command -v uvx >/dev/null 2>&1; then
  DVC_HOST_CMD=(uvx dvc)
elif command -v dvc >/dev/null 2>&1; then
  DVC_HOST_CMD=(dvc)
else
  echo "Neither 'uvx' nor 'dvc' is available on host" >&2
  exit 1
fi

commit=$(FILE="$FILE_PATH" python3 - <<'PY'
import json, os
from pathlib import Path
p = Path(os.environ["FILE"])
data = json.loads(p.read_text())
value = data.get("git_commit")
print(value or "")
PY
)

if [ -z "$commit" ]; then
  echo "git_commit missing in $FILE_PATH; cannot create worktree" >&2
  exit 1
fi

run_id=$(FILE="$FILE_PATH" python3 - <<'PY'
import json, os
from pathlib import Path
p = Path(os.environ["FILE"])
data = json.loads(p.read_text())
print(data.get("run_id", ""))
PY
)

data_version=$(FILE="$FILE_PATH" python3 - <<'PY'
import json, os
from pathlib import Path
p = Path(os.environ["FILE"])
data = json.loads(p.read_text())
print(data.get("data_version", ""))
PY
)

worktree_default="/tmp/repro-${commit:0:7}"
worktree_dir=${WORKTREE:-$worktree_default}

if [ -d "$worktree_dir" ]; then
  echo "Worktree already exists: $worktree_dir" >&2
  echo "Remove it or set WORKTREE to another path" >&2
  exit 1
fi

echo "📂 Creating worktree at $worktree_dir for commit $commit"
git worktree add "$worktree_dir" "$commit" >/dev/null

cd "$worktree_dir"

if [ ! -f params.yaml ]; then
  echo "params.yaml missing in worktree" >&2
  exit 1
fi

# Older commits may contain absolute host paths in dvc.yaml.
# Rewrite them to the current worktree path for reproducible execution.
if [ -f dvc.yaml ]; then
  SOURCE_ROOT="$SOURCE_REPO_ROOT" WORKTREE_ROOT="$(pwd)" python3 - <<'PY'
import os
from pathlib import Path

dvc_path = Path("dvc.yaml")
text = dvc_path.read_text()
source = os.environ["SOURCE_ROOT"]
target = os.environ["WORKTREE_ROOT"]
if source in text:
    text = text.replace(source, target)

# Historical commits may miss uid/gid mapping in docker run commands.
# Inject host user mapping to avoid root-owned artifacts during host-mode dvc repro.
if "docker run --rm -u $HOST_UID:$HOST_GID" not in text:
    text = text.replace("docker run --rm", "docker run --rm -u $HOST_UID:$HOST_GID")

dvc_path.write_text(text)
PY
fi

FILE_ENV="$FILE_PATH" python3 - <<'PY'
import json, os, yaml
from pathlib import Path

data = json.loads(Path(os.environ["FILE_ENV"]).read_text())
params_path = Path("params.yaml")
params = yaml.safe_load(params_path.read_text()) or {}
params.setdefault("train", {})
for key in ["n_estimators", "max_depth", "random_state"]:
    if key in data.get("params", {}):
        params["train"][key] = int(data["params"][key])
params_path.write_text(yaml.dump(params, default_flow_style=False))
PY

if [ -z "${DAGSHUB_USER_NAME:-}" ] || [ -z "${DAGSHUB_TOKEN:-}" ]; then
  echo "❌ DAGSHUB_USER_NAME / DAGSHUB_TOKEN must be set for dvc pull" >&2
  exit 1
fi

echo "🔄 Restoring data for data_version=${data_version:-unknown}"
PROJECT_PATH=$(pwd) HOST_UID=$(id -u) HOST_GID=$(id -g) "${DVC_HOST_CMD[@]}" remote modify origin --local auth basic
PROJECT_PATH=$(pwd) HOST_UID=$(id -u) HOST_GID=$(id -g) "${DVC_HOST_CMD[@]}" remote modify origin --local user "$DAGSHUB_USER_NAME"
PROJECT_PATH=$(pwd) HOST_UID=$(id -u) HOST_GID=$(id -g) "${DVC_HOST_CMD[@]}" remote modify origin --local password "$DAGSHUB_TOKEN"
PROJECT_PATH=$(pwd) HOST_UID=$(id -u) HOST_GID=$(id -g) "${DVC_HOST_CMD[@]}" config cache.type copy --local
PROJECT_PATH=$(pwd) HOST_UID=$(id -u) HOST_GID=$(id -g) "${DVC_HOST_CMD[@]}" pull
mkdir -p data models metrics
docker run --rm -v "$(pwd):/workspace" alpine:3.20 sh -c \
  "chown -R $(id -u):$(id -g) /workspace/data /workspace/models /workspace/metrics"
PROJECT_PATH=$(pwd) HOST_UID=$(id -u) HOST_GID=$(id -g) "${DVC_HOST_CMD[@]}" unprotect data models metrics >/dev/null 2>&1 || true

echo "▶️  Reproducing pipeline"
PROJECT_PATH=$(pwd) HOST_UID=$(id -u) HOST_GID=$(id -g) "${DVC_HOST_CMD[@]}" repro

echo "✅ Reproduction complete in $worktree_dir (run_id=${run_id:-unknown})"
echo "To inspect artifacts: ls $worktree_dir/data $worktree_dir/models $worktree_dir/metrics"
