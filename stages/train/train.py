"""
Train stage: Train model and log to MLflow/DagsHub with promotion logic
"""

import json
import logging
from pathlib import Path

import mlflow
import mlflow.sklearn
import pandas as pd
import yaml
from mlflow.tracking import MlflowClient
from sklearn.ensemble import RandomForestClassifier

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


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
            f"New model better ({current_accuracy:.4f} > {prod_accuracy:.4f}), promoting to production"
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
            f"New model not better ({current_accuracy:.4f} <= {prod_accuracy:.4f}), keeping in staging"
        )
        set_model_alias(client, model_name, version, "staging")
        tags["promotion_reason"] = "insufficient_accuracy"
        tag_model(client, model_name, version, tags)
        return False


def main():
    logger.info("Starting model training")

    # Load parameters
    params = load_params()
    n_estimators = params.get("n_estimators", 100)
    max_depth = params.get("max_depth", 5)
    random_state = params.get("random_state", 42)

    logger.info(
        f"Hyperparameters: n_estimators={n_estimators}, max_depth={max_depth}, random_state={random_state}"
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
        # Log parameters
        mlflow.log_params(
            {
                "n_estimators": n_estimators,
                "max_depth": max_depth,
                "random_state": random_state,
                "model_type": "RandomForest",
            }
        )

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

    # Get the model version that was just created
    model_versions = client.search_model_versions(f"name='{model_name}'")
    latest_version = max([int(mv.version) for mv in model_versions])

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
