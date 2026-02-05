"""
Ingest stage: Download raw data
"""
import os
from pathlib import Path
from sklearn.datasets import load_iris
import pandas as pd

def main():
    print("🔽 Ingesting data...")
    
    # Load iris dataset
    iris = load_iris()
    df = pd.DataFrame(
        data=iris.data,
        columns=iris.feature_names
    )
    df['target'] = iris.target
    df['target_name'] = df['target'].map(
        {i: name for i, name in enumerate(iris.target_names)}
    )
    
    # Save to data/raw
    output_dir = Path("/data/raw")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    output_path = output_dir / "iris.csv"
    df.to_csv(output_path, index=False)
    
    print(f"✅ Data saved: {output_path}")
    print(f"   Shape: {df.shape}")
    print(f"   Classes: {df['target_name'].unique().tolist()}")

if __name__ == "__main__":
    main()
