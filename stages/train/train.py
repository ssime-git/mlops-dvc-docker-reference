"""
Train stage: Train model and log to MLflow/DagsHub
"""
import os
import json
from pathlib import Path
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
import mlflow
import mlflow.sklearn
import yaml

def load_params():
    """Load parameters from params.yaml"""
    params_path = Path("/workspace/params.yaml")
    if not params_path.exists():
        return {"n_estimators": 100, "max_depth": 5, "random_state": 42}
    
    with open(params_path) as f:
        params = yaml.safe_load(f)
    return params.get("train", {})

def main():
    print("🎯 Training model...")
    
    # Load parameters
    params = load_params()
    n_estimators = params.get("n_estimators", 100)
    max_depth = params.get("max_depth", 5)
    random_state = params.get("random_state", 42)
    
    print(f"📋 Hyperparameters:")
    print(f"   n_estimators: {n_estimators}")
    print(f"   max_depth: {max_depth}")
    print(f"   random_state: {random_state}")
    
    # Load data
    train_df = pd.read_csv("/data/processed/train.csv")
    test_df = pd.read_csv("/data/processed/test.csv")
    
    X_train = train_df.drop('target', axis=1)
    y_train = train_df['target']
    X_test = test_df.drop('target', axis=1)
    y_test = test_df['target']
    
    # Start MLflow run
    with mlflow.start_run(run_name="iris-rf-train"):
        
        # Log parameters
        mlflow.log_params({
            "n_estimators": n_estimators,
            "max_depth": max_depth,
            "random_state": random_state,
            "model_type": "RandomForest"
        })
        
        # Train model
        model = RandomForestClassifier(
            n_estimators=n_estimators,
            max_depth=max_depth,
            random_state=random_state
        )
        model.fit(X_train, y_train)
        
        # Log metrics
        train_score = model.score(X_train, y_train)
        test_score = model.score(X_test, y_test)
        
        mlflow.log_metrics({
            "train_accuracy": train_score,
            "test_accuracy": test_score
        })
        
        print(f"📈 Train accuracy: {train_score:.4f}")
        print(f"📈 Test accuracy: {test_score:.4f}")
        
        # Log model to MLflow (saved to DagsHub, not locally!)
        mlflow.sklearn.log_model(
            model,
            "model",
            registered_model_name="iris-classifier"  # Auto-register in DagsHub model registry
        )
        
        # Save metadata locally (for DVC tracking)
        run_id = mlflow.active_run().info.run_id
        metadata = {
            "run_id": run_id,
            "train_accuracy": train_score,
            "test_accuracy": test_score,
            "model_type": "RandomForest",
            "params": {
                "n_estimators": n_estimators,
                "max_depth": max_depth
            }
        }
        
        output_dir = Path("/models")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        metadata_path = output_dir / "model_metadata.json"
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        print(f"✅ Model logged to MLflow/DagsHub")
        print(f"   Run ID: {run_id}")
        print(f"   Registered as: iris-classifier")
        print(f"✅ Metadata saved: {metadata_path}")

if __name__ == "__main__":
    main()
