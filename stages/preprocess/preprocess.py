"""
Preprocess stage: Split and prepare data
"""

import logging
from pathlib import Path

import pandas as pd
import yaml
from sklearn.model_selection import train_test_split

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def load_params():
    """Load parameters from params.yaml"""
    params_path = Path("/workspace/params.yaml")
    if not params_path.exists():
        return {"test_size": 0.2, "random_state": 42}

    with open(params_path) as f:
        params = yaml.safe_load(f)
    return params.get("preprocess", {})


def main():
    logger.info("Starting data preprocessing")

    # Load parameters
    params = load_params()
    test_size = params.get("test_size", 0.2)
    random_state = params.get("random_state", 42)

    # Load raw data
    input_path = Path("/data/raw/iris.csv")
    df = pd.read_csv(input_path)

    logger.info(f"Loaded data: {df.shape}")

    # Split features and target
    X = df.drop(["target", "target_name"], axis=1)
    y = df["target"]

    # Train/test split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=random_state, stratify=y
    )

    # Combine for saving
    train_df = X_train.copy()
    train_df["target"] = y_train.values

    test_df = X_test.copy()
    test_df["target"] = y_test.values

    # Save processed data
    output_dir = Path("/data/processed")
    output_dir.mkdir(parents=True, exist_ok=True)

    train_path = output_dir / "train.csv"
    test_path = output_dir / "test.csv"

    train_df.to_csv(train_path, index=False)
    test_df.to_csv(test_path, index=False)

    logger.info(f"Train data saved: {train_path} {train_df.shape}")
    logger.info(f"Test data saved: {test_path} {test_df.shape}")


if __name__ == "__main__":
    main()
