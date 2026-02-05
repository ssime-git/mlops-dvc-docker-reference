#!/usr/bin/env python3
"""
View data lineage for MLflow experiments
Shows the connection between DVC data versions and MLflow runs
"""

import os
import sys
from pathlib import Path

import mlflow
from mlflow.tracking import MlflowClient
from tabulate import tabulate


def get_run_lineage(run):
    """Extract lineage information from an MLflow run"""
    data = run.data
    info = run.info

    # Extract DVC data version
    data_version = data.params.get("data_version", "N/A")

    # Extract DagHub URLs from tags
    dagshub_urls = {}
    for tag_key, tag_value in data.tags.items():
        if tag_key.startswith("dagshub_url_"):
            dataset_name = tag_key.replace("dagshub_url_", "").replace("_", "/")
            dagshub_urls[dataset_name] = tag_value

    # Extract dataset information
    datasets = []
    try:
        # MLflow 2.x+ has datasets attribute
        if hasattr(run, "inputs"):
            for dataset_input in run.inputs.dataset_inputs:
                datasets.append(
                    {
                        "name": dataset_input.dataset.name,
                        "digest": dataset_input.dataset.digest,
                        "source": dataset_input.dataset.source,
                    }
                )
    except AttributeError:
        pass

    return {
        "run_id": info.run_id,
        "run_name": data.tags.get("mlflow.runName", "N/A"),
        "data_version": data_version,
        "test_accuracy": data.metrics.get("test_accuracy", 0.0),
        "dagshub_urls": dagshub_urls,
        "datasets": datasets,
        "start_time": info.start_time,
    }


def display_lineage_table(runs_lineage):
    """Display lineage information as a table"""
    table_data = []

    for lineage in runs_lineage:
        table_data.append(
            [
                lineage["run_id"][:8],
                lineage["run_name"],
                lineage["data_version"],
                f"{lineage['test_accuracy']:.4f}",
                len(lineage["datasets"]),
                len(lineage["dagshub_urls"]),
            ]
        )

    headers = [
        "Run ID",
        "Run Name",
        "Data Version",
        "Test Acc",
        "Datasets",
        "DagHub URLs",
    ]
    print("\n" + "=" * 80)
    print("MLflow Experiments Data Lineage")
    print("=" * 80)
    print(tabulate(table_data, headers=headers, tablefmt="grid"))
    print()


def display_detailed_lineage(lineage):
    """Display detailed lineage for a specific run"""
    print("\n" + "=" * 80)
    print(f"Detailed Lineage for Run: {lineage['run_id']}")
    print("=" * 80)
    print(f"\nRun Name: {lineage['run_name']}")
    print(f"Data Version: {lineage['data_version']}")
    print(f"Test Accuracy: {lineage['test_accuracy']:.4f}")

    print("\n--- Datasets Used ---")
    if lineage["datasets"]:
        for dataset in lineage["datasets"]:
            print(f"\nDataset: {dataset['name']}")
            print(f"  Source: {dataset['source']}")
            print(f"  Digest: {dataset['digest']}")
    else:
        print("No dataset information logged")

    print("\n--- DagHub Data URLs ---")
    if lineage["dagshub_urls"]:
        for name, url in lineage["dagshub_urls"].items():
            print(f"\n{name}:")
            print(f"  {url}")
    else:
        print("No DagHub URLs logged")

    print("\n" + "=" * 80 + "\n")


def main():
    # Setup MLflow
    tracking_uri = os.getenv("MLFLOW_TRACKING_URI")
    if not tracking_uri:
        print("Error: MLFLOW_TRACKING_URI environment variable not set")
        sys.exit(1)

    mlflow.set_tracking_uri(tracking_uri)
    client = MlflowClient()

    # Get experiment
    experiment_name = "iris-rf-train"
    try:
        experiment = client.get_experiment_by_name(experiment_name)
        if not experiment:
            print(f"Experiment '{experiment_name}' not found")
            sys.exit(1)
    except Exception as e:
        print(f"Error getting experiment: {e}")
        sys.exit(1)

    # Get all runs
    runs = client.search_runs(
        experiment_ids=[experiment.experiment_id],
        order_by=["start_time DESC"],
        max_results=20,
    )

    if not runs:
        print(f"No runs found for experiment '{experiment_name}'")
        sys.exit(0)

    # Extract lineage information
    runs_lineage = [get_run_lineage(run) for run in runs]

    # Display table
    display_lineage_table(runs_lineage)

    # Ask user if they want details
    if len(sys.argv) > 1:
        run_index = int(sys.argv[1])
        if 0 <= run_index < len(runs_lineage):
            display_detailed_lineage(runs_lineage[run_index])
        else:
            print(f"Invalid run index. Please use 0-{len(runs_lineage) - 1}")
    else:
        print("To view detailed lineage for a specific run:")
        print(f"  python {sys.argv[0]} <run_index>")
        print(f"\nExample: python {sys.argv[0]} 0")


if __name__ == "__main__":
    main()
