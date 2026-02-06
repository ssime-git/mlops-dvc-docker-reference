#!/usr/bin/env python3
"""
Reproduce an experiment from a model in the registry
Shows exact parameters and data used - just copy and run
"""

import argparse
import json
from pathlib import Path

import yaml
from mlflow.tracking import MlflowClient


def get_experiment_info(model_name, version_or_alias):
    """Get experiment parameters and metadata"""
    client = MlflowClient()

    # Get model version
    try:
        # Try as alias first
        mv = client.get_model_version_by_alias(model_name, version_or_alias)
    except Exception:
        # Otherwise treat as version number
        mv = client.get_model_version(model_name, version_or_alias)

    # Get run
    run = client.get_run(mv.run_id)

    # Extract info
    data_version = run.data.params.get("data_version") or run.data.tags.get(
        "dvc_data_version"
    )
    git_commit = run.data.tags.get("git_commit")

    return {
        "run_id": run.info.run_id,
        "model_version": mv.version,
        "params": run.data.params,
        "metrics": run.data.metrics,
        "data_version": data_version,
        "git_commit": git_commit,
    }


def update_params_yaml(params, output_file="params.yaml"):
    """Update params.yaml with experiment parameters"""
    with open(output_file) as f:
        current_params = yaml.safe_load(f)

    if "train" not in current_params:
        current_params["train"] = {}

    # Update from MLflow params
    for key, value in params.items():
        if key in ["n_estimators", "max_depth", "random_state"]:
            current_params["train"][key] = int(value)

    with open(output_file, "w") as f:
        yaml.dump(current_params, f, default_flow_style=False)

    print(f"✅ Updated {output_file}")


def main():
    parser = argparse.ArgumentParser(
        description="Reproduce experiment from model registry"
    )
    parser.add_argument("model_name", help="Model name (e.g., iris-classifier)")
    parser.add_argument(
        "version", help="Version number or alias (e.g., 5, production, staging)"
    )
    parser.add_argument(
        "--update-params", action="store_true", help="Update params.yaml automatically"
    )

    args = parser.parse_args()

    # Get experiment info
    print(f"🔍 Retrieving {args.model_name} @ {args.version}...\n")
    info = get_experiment_info(args.model_name, args.version)

    # Display info
    print("📊 Experiment Details:")
    print(f"   Run ID: {info['run_id']}")
    print(f"   Model Version: {info['model_version']}")
    print(f"   Data Version: {info['data_version']}")
    if info.get("git_commit"):
        print(f"   Git Commit: {info['git_commit'][:7]}")

    print("\n⚙️  Parameters:")
    for key, value in info["params"].items():
        if key in ["n_estimators", "max_depth", "random_state"]:
            print(f"   {key}: {value}")

    print("\n📈 Metrics:")
    for key, value in info["metrics"].items():
        if "accuracy" in key:
            print(f"   {key}: {value:.4f}")

    # Save
    output_file = Path(f"experiment_{info['run_id']}.json")
    try:
        output_file.write_text(json.dumps(info, indent=2) + "\n", encoding="utf-8")
    except PermissionError:
        fallback_dir = Path("/tmp")
        output_file = fallback_dir / output_file.name
        output_file.write_text(json.dumps(info, indent=2) + "\n", encoding="utf-8")
        print(f"⚠️  Default output path not writable, saved to {output_file}")

    # Update params
    if args.update_params:
        update_params_yaml(info["params"])

    # Instructions
    print("\n🔄 To reproduce:")
    if info.get("git_commit"):
        print(f"   1. git checkout {info['git_commit'][:7]}  # Get correct dvc.lock")
        print("   2. make restore                          # Pull exact data")
        print("   3. make run                              # Reproduce")
        print("   4. git checkout main                     # Return to main")
    else:
        print("   ⚠️  No git commit found in this run")
        print("   1. make restore  # Pull current data")
        print("   2. make run      # Reproduce (may differ if data changed)")

    if not args.update_params:
        print("\n💡 Tip: Use --update-params to auto-update params.yaml")


if __name__ == "__main__":
    main()
