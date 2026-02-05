#!/usr/bin/env python3
"""
Reproduce an experiment from a model in the registry
"""

import argparse
import json

import mlflow
import yaml
from mlflow.tracking import MlflowClient


def get_experiment_info(model_name, version_or_alias):
    """Get experiment parameters and metadata"""
    client = MlflowClient()

    # Get model version
    try:
        # Try as alias first
        mv = client.get_model_version_by_alias(model_name, version_or_alias)
    except:
        # Otherwise treat as version number
        mv = client.get_registered_model_version(model_name, version_or_alias)

    # Get run
    run = client.get_run(mv.run_id)

    return {
        "run_id": run.info.run_id,
        "model_version": mv.version,
        "params": run.data.params,
        "metrics": run.data.metrics,
        "tags": {k: v for k, v in mv.tags.items()},
        "model_uri": f"models:/{model_name}@{version_or_alias}",
    }


def update_params_yaml(params, output_file="params.yaml"):
    """Update params.yaml with experiment parameters"""

    # Load current params
    with open(output_file) as f:
        current_params = yaml.safe_load(f)

    # Update train section
    if "train" not in current_params:
        current_params["train"] = {}

    # Update from MLflow params
    for key, value in params.items():
        if key in ["n_estimators", "max_depth", "random_state"]:
            # Convert string to int
            current_params["train"][key] = int(value)

    # Write back
    with open(output_file, "w") as f:
        yaml.dump(current_params, f, default_flow_style=False)

    print(f"Updated {output_file}")


def main():
    parser = argparse.ArgumentParser(
        description="Reproduce experiment from model registry"
    )
    parser.add_argument("model_name", help="Model name (e.g., iris-classifier)")
    parser.add_argument(
        "version", help="Version number or alias (e.g., 5, production, staging)"
    )
    parser.add_argument(
        "--update-params", action="store_true", help="Automatically update params.yaml"
    )

    args = parser.parse_args()

    # Get experiment info
    print(f"Retrieving experiment info for {args.model_name} @ {args.version}...")
    info = get_experiment_info(args.model_name, args.version)

    print(f"\nExperiment Details:")
    print(f"  Run ID: {info['run_id']}")
    print(f"  Model Version: {info['model_version']}")

    print(f"\nParameters:")
    for key, value in info["params"].items():
        print(f"  {key}: {value}")

    print(f"\nMetrics:")
    for key, value in info["metrics"].items():
        print(f"  {key}: {value:.4f}")

    print(f"\nTags:")
    for key, value in info["tags"].items():
        print(f"  {key}: {value}")

    # Save to file
    output_file = f"experiment_{info['run_id']}.json"
    with open(output_file, "w") as f:
        json.dump(info, f, indent=2)
    print(f"\nSaved to: {output_file}")

    # Update params if requested
    if args.update_params:
        update_params_yaml(info["params"])
        print("\nTo reproduce:")
        print("  make run")
    else:
        print("\nTo reproduce:")
        print(f"  1. Update params.yaml with the parameters above")
        print(f"  2. make run")
        print(f"\nOr run with --update-params to auto-update params.yaml")


if __name__ == "__main__":
    main()
