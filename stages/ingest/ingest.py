"""
Ingest stage: Download raw data
"""

import logging
from pathlib import Path

import pandas as pd
from sklearn.datasets import load_iris

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def main():
    logger.info("Starting data ingestion")

    # Load iris dataset
    iris = load_iris()
    df = pd.DataFrame(data=iris.data, columns=iris.feature_names)
    df["target"] = iris.target
    df["target_name"] = df["target"].map(
        {i: name for i, name in enumerate(iris.target_names)}
    )

    # Save to data/raw
    output_dir = Path("/data/raw")
    output_dir.mkdir(parents=True, exist_ok=True)

    output_path = output_dir / "iris.csv"
    df.to_csv(output_path, index=False)

    logger.info(f"Data saved: {output_path}")
    logger.info(f"Shape: {df.shape}")
    logger.info(f"Classes: {df['target_name'].unique().tolist()}")


if __name__ == "__main__":
    main()
