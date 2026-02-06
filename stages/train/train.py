"""
Train stage: Train model and log to MLflow/DagsHub with promotion logic
"""

import json
import logging
import os
import subprocess
from pathlib import Path

import mlflow
import mlflow.sklearn
import pandas as pd
import yaml
from dvc_lineage import format_lineage_info, log_dagshub_lineage_tags
from mlflow.data.pandas_dataset import from_pandas
from mlflow.tracking import MlflowClient
from sklearn.ensemble import RandomForestClassifier

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def get_git_commit():
    """Get current git commit hash from workspace"""
    env_commit = os.getenv("GIT_COMMIT")
    if env_commit:
        return env_commit.strip()

    try:
        commit = (
            subprocess.check_output(
                ["git", "rev-parse", "HEAD"],
                cwd="/workspace",
                stderr=subprocess.DEVNULL,
            )
            .decode()
            .strip()
        )
        return commit
    except Exception as e:
        logger.warning(f"Could not get git commit: {e}")
        return None


def load_params():
    """Load parameters from params.yaml"""
    params_path = Path("/workspace/params.yaml")
    if not params_path.exists():
        return {"n_estimators": 100, "max_depth": 5, "random_state": 42}

    with open(params_path) as f:
        params = yaml.safe_load(f)
    return params.get("train", {})


def get_production_model_version(client, model_name):
    """Get current production model using aliases"""
    try:
        # Try to get model with 'production' alias
        mv = client.get_model_version_by_alias(model_name, "production")
        run = client.get_run(mv.run_id)
        prod_accuracy = run.data.metrics.get("test_accuracy")
        if prod_accuracy is None:
            logger.info(f"Production model (v{mv.version}) has no test_accuracy metric")
        else:
            logger.info(
                f"Production model (v{mv.version}): test_accuracy={prod_accuracy:.4f}"
            )
        return mv.version, prod_accuracy
    except mlflow.exceptions.RestException:
        logger.info("No production model found")
        return None, None


def set_model_alias(client, model_name, version, alias):
    """Set alias for model version"""
    client.set_registered_model_alias(model_name, alias, str(version))
    logger.info(f"Set alias '{alias}' for model v{version}")


def tag_model(client, model_name, version, tags):
    """Add tags to model version"""
    for key, value in tags.items():
        client.set_model_version_tag(model_name, str(version), key, value)


def get_data_version():
    """Get DVC data version from dvc.lock with detailed metadata"""
    import hashlib

    dvc_lock_path = Path("/workspace/dvc.lock")
    if not dvc_lock_path.exists():
        return None, {}

    try:
        with open(dvc_lock_path) as f:
            dvc_lock = yaml.safe_load(f)

        # Get hashes for data outputs
        data_hashes = {}
        data_metadata = {}

        for stage_name, stage_data in dvc_lock.get("stages", {}).items():
            if stage_name in ["ingest", "preprocess"]:
                for out in stage_data.get("outs", []):
                    if "md5" in out:
                        path = out.get("path", "unknown")
                        md5_hash = out["md5"]
                        size = out.get("size", 0)

                        data_hashes[path] = md5_hash
                        data_metadata[path] = {
                            "md5": md5_hash,
                            "size": size,
                            "stage": stage_name,
                        }

        # Create combined hash
        combined = "_".join(f"{k}:{v}" for k, v in sorted(data_hashes.items()))
        version_hash = hashlib.md5(combined.encode()).hexdigest()[:8]

        return version_hash, data_metadata
    except Exception as e:
        logger.warning(f"Could not get data version: {e}")
        return None, {}


def promote_model(
    client, model_name, version, current_accuracy, prod_version, prod_accuracy
):
    """Decide if model should be promoted to production"""
    tags = {"test_accuracy": str(current_accuracy), "promoted": "false"}

    if prod_accuracy is None:
        # No production model exists, promote this one
        logger.info("No existing production model, promoting new model")
        set_model_alias(client, model_name, version, "production")
        tags["promoted"] = "true"
        tags["promotion_reason"] = "first_model"
        tag_model(client, model_name, version, tags)
        return True

    if current_accuracy > prod_accuracy:
        # New model is better, promote it
        logger.info(
            "New model better "
            f"({current_accuracy:.4f} > {prod_accuracy:.4f}), "
            "promoting to production"
        )

        # Archive old production
        if prod_version:
            set_model_alias(client, model_name, prod_version, "archived")
            tag_model(client, model_name, prod_version, {"status": "archived"})

        # Promote new model
        set_model_alias(client, model_name, version, "production")
        tags["promoted"] = "true"
        tags["promotion_reason"] = "better_accuracy"
        tag_model(client, model_name, version, tags)
        return True
    else:
        # Keep in staging
        logger.info(
            "New model not better "
            f"({current_accuracy:.4f} <= {prod_accuracy:.4f}), "
            "keeping in staging"
        )
        set_model_alias(client, model_name, version, "staging")
        tags["promotion_reason"] = "insufficient_accuracy"
        tag_model(client, model_name, version, tags)
        return False


def resolve_registered_model_version(client, model_name, run_id):
    """Resolve the model version created by the current run."""
    query = f"name='{model_name}' and run_id='{run_id}'"
    versions = []

    try:
        versions = client.search_model_versions(query)
    except Exception as e:
        logger.warning(f"Primary model-version lookup failed ({query}): {e}")

    if not versions:
        fallback = client.search_model_versions(f"name='{model_name}'")
        versions = [mv for mv in fallback if mv.run_id == run_id]

    if not versions:
        raise RuntimeError(
            f"Could not resolve model version for model={model_name}, run_id={run_id}"
        )

    return max(int(mv.version) for mv in versions)


def main():
    logger.info("Starting model training")

    # Get data version and metadata
    data_version, data_metadata = get_data_version()
    if data_version:
        logger.info(f"Data version: {data_version}")
        logger.info(f"Data metadata: {data_metadata}")

    # Load parameters
    params = load_params()
    n_estimators = params.get("n_estimators", 100)
    max_depth = params.get("max_depth", 5)
    random_state = params.get("random_state", 42)

    logger.info(
        "Hyperparameters: "
        f"n_estimators={n_estimators}, "
        f"max_depth={max_depth}, "
        f"random_state={random_state}"
    )

    # Load data
    train_df = pd.read_csv("/data/processed/train.csv")
    test_df = pd.read_csv("/data/processed/test.csv")

    X_train = train_df.drop("target", axis=1)
    y_train = train_df["target"]
    X_test = test_df.drop("target", axis=1)
    y_test = test_df["target"]

    model_name = "iris-classifier"
    client = MlflowClient()

    # Get current production model
    prod_version, prod_accuracy = get_production_model_version(client, model_name)

    # Start MLflow run
    with mlflow.start_run(run_name="iris-rf-train") as run:
        # Log git commit for reproducibility
        git_commit = get_git_commit()
        if git_commit:
            mlflow.set_tag("git_commit", git_commit)
            logger.info(f"Git commit: {git_commit}")

        # Log parameters
        mlflow.log_params(
            {
                "n_estimators": n_estimators,
                "max_depth": max_depth,
                "random_state": random_state,
                "model_type": "RandomForest",
            }
        )

        # Log data version for lineage
        if data_version:
            mlflow.log_param("data_version", data_version)
            mlflow.set_tag("dvc_data_version", data_version)

            # Log detailed DVC metadata for each dataset
            for path, metadata in data_metadata.items():
                mlflow.set_tag(f"dvc_{path.replace('/', '_')}_md5", metadata["md5"])
                mlflow.log_param(f"dvc_{path.replace('/', '_')}_size", metadata["size"])

        # Create MLflow datasets with DVC metadata for data lineage
        # Use local paths as source since MLflow doesn't recognize dvc:// protocol
        train_dataset = from_pandas(
            train_df,
            source="/data/processed/train.csv",
            name="train_data",
            targets="target",
        )

        test_dataset = from_pandas(
            test_df,
            source="/data/processed/test.csv",
            name="test_data",
            targets="target",
        )

        # Log datasets to MLflow for lineage tracking
        # DVC metadata is tracked via tags and params above
        mlflow.log_input(train_dataset, context="training")
        mlflow.log_input(test_dataset, context="testing")

        logger.info("Logged datasets to MLflow for lineage tracking")

        # Log DagHub URLs for data lineage
        log_dagshub_lineage_tags(mlflow, data_metadata)

        # Create and log lineage info as artifact
        lineage_info = format_lineage_info(data_version, data_metadata)
        lineage_path = Path("/tmp/data_lineage.md")
        lineage_path.write_text(lineage_info)
        mlflow.log_artifact(str(lineage_path), "lineage")
        logger.info("Logged DagHub lineage information")

        # Train model
        model = RandomForestClassifier(
            n_estimators=n_estimators, max_depth=max_depth, random_state=random_state
        )
        model.fit(X_train, y_train)

        # Log metrics
        train_score = model.score(X_train, y_train)
        test_score = model.score(X_test, y_test)

        mlflow.log_metrics({"train_accuracy": train_score, "test_accuracy": test_score})

        logger.info(f"Train accuracy: {train_score:.4f}")
        logger.info(f"Test accuracy: {test_score:.4f}")

        # Log model to MLflow
        mlflow.sklearn.log_model(model, "model", registered_model_name=model_name)

        run_id = run.info.run_id

    # Resolve the model version created by this exact run to avoid race conditions.
    latest_version = resolve_registered_model_version(client, model_name, run_id)

    # Promote model based on comparison
    promoted = promote_model(
        client, model_name, latest_version, test_score, prod_version, prod_accuracy
    )

    # Save metadata locally
    metadata = {
        "run_id": run_id,
        "model_name": model_name,
        "version": latest_version,
        "train_accuracy": train_score,
        "test_accuracy": test_score,
        "promoted_to_production": promoted,
        "model_type": "RandomForest",
        "params": {"n_estimators": n_estimators, "max_depth": max_depth},
        "data_version": data_version,
    }

    output_dir = Path("/models")
    output_dir.mkdir(parents=True, exist_ok=True)

    metadata_path = output_dir / "model_metadata.json"
    with open(metadata_path, "w") as f:
        json.dump(metadata, f, indent=2)

    alias = "production" if promoted else "staging"
    logger.info(f"Model logged to MLflow/DagsHub, run_id: {run_id}")
    logger.info(f"Model registered as: {model_name} v{latest_version}")
    logger.info(f"Alias: {alias}")
    logger.info(f"Metadata saved: {metadata_path}")


if __name__ == "__main__":
    main()
