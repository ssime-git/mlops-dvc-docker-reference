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

commit=$(FILE="$FILE_PATH" python3 - <<'PY'
import json, os
from pathlib import Path
p = Path(os.environ["FILE"])
data = json.loads(p.read_text())
print(data.get("git_commit", ""))
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
PROJECT_PATH=$(pwd) docker-compose run --rm dvc-runner dvc pull

echo "▶️  Reproducing pipeline"
PROJECT_PATH=$(pwd) docker-compose run --rm dvc-runner dvc repro

echo "✅ Reproduction complete in $worktree_dir (run_id=${run_id:-unknown})"
echo "To inspect artifacts: ls $worktree_dir/data $worktree_dir/models $worktree_dir/metrics"
