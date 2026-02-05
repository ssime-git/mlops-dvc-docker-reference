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


def get_production_model_accuracy(client, model_name):
    """Get accuracy of current production model"""
    try:
        # Get production version
        prod_versions = client.get_latest_versions(model_name, stages=["Production"])
        if not prod_versions:
            logger.info("No production model found")
            return None

        prod_version = prod_versions[0]
        # Get run that created this model version
        run = client.get_run(prod_version.run_id)
        prod_accuracy = run.data.metrics.get("test_accuracy")

        logger.info(
            f"Production model (v{prod_version.version}): test_accuracy={prod_accuracy:.4f}"
        )
        return prod_accuracy
    except Exception as e:
        logger.warning(f"Could not retrieve production model: {e}")
        return None


def promote_model(client, model_name, version, current_accuracy, prod_accuracy):
    """Decide if model should be promoted to production"""
    if prod_accuracy is None:
        # No production model exists, promote this one
        logger.info("No existing production model, promoting new model")
        client.transition_model_version_stage(
            name=model_name, version=version, stage="Production"
        )
        return True

    if current_accuracy > prod_accuracy:
        # New model is better, promote it
        logger.info(
            f"New model better ({current_accuracy:.4f} > {prod_accuracy:.4f}), promoting to production"
        )
        # Archive old production model
        client.transition_model_version_stage(
            name=model_name,
            version=version,
            stage="Production",
            archive_existing_versions=True,
        )
        return True
    else:
        # Keep in staging
        logger.info(
            f"New model not better ({current_accuracy:.4f} <= {prod_accuracy:.4f}), keeping in staging"
        )
        client.transition_model_version_stage(
            name=model_name, version=version, stage="Staging"
        )
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

    # Get current production model accuracy
    prod_accuracy = get_production_model_accuracy(client, model_name)

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
        client, model_name, latest_version, test_score, prod_accuracy
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

    logger.info(f"Model logged to MLflow/DagsHub, run_id: {run_id}")
    logger.info(f"Model registered as: {model_name} v{latest_version}")
    logger.info(f"Stage: {'Production' if promoted else 'Staging'}")
    logger.info(f"Metadata saved: {metadata_path}")


if __name__ == "__main__":
    main()
