"""
Evaluate stage: Load model from DagsHub and evaluate
"""
import json
from pathlib import Path
import pandas as pd
from sklearn.metrics import accuracy_score, precision_recall_fscore_support, confusion_matrix
import mlflow
import mlflow.sklearn

def main():
    print("📊 Evaluating model...")
    
    # Load metadata to get run_id
    metadata_path = Path("/models/model_metadata.json")
    with open(metadata_path) as f:
        metadata = json.load(f)
    
    run_id = metadata["run_id"]
    print(f"📦 Loading model from run: {run_id}")
    
    # Load model from MLflow/DagsHub (not from local file!)
    model_uri = f"runs:/{run_id}/model"
    model = mlflow.sklearn.load_model(model_uri)
    
    # Load test data
    test_df = pd.read_csv("/data/processed/test.csv")
    X_test = test_df.drop('target', axis=1)
    y_test = test_df['target']
    
    # Predictions
    y_pred = model.predict(X_test)
    
    # Metrics
    accuracy = accuracy_score(y_test, y_pred)
    precision, recall, f1, _ = precision_recall_fscore_support(
        y_test, y_pred, average='weighted'
    )
    
    metrics = {
        "accuracy": float(accuracy),
        "precision": float(precision),
        "recall": float(recall),
        "f1_score": float(f1)
    }
    
    print(f"📈 Evaluation Results:")
    print(f"   Accuracy:  {accuracy:.4f}")
    print(f"   Precision: {precision:.4f}")
    print(f"   Recall:    {recall:.4f}")
    print(f"   F1 Score:  {f1:.4f}")
    
    # Confusion matrix
    cm = confusion_matrix(y_test, y_pred)
    cm_dict = {
        "data": cm.tolist(),
        "labels": ["setosa", "versicolor", "virginica"]
    }
    
    # Save metrics
    output_dir = Path("/metrics")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    metrics_path = output_dir / "metrics.json"
    cm_path = output_dir / "confusion_matrix.json"
    
    with open(metrics_path, 'w') as f:
        json.dump(metrics, f, indent=2)
    
    with open(cm_path, 'w') as f:
        json.dump(cm_dict, f, indent=2)
    
    # Log to MLflow (link to same run)
    with mlflow.start_run(run_id=run_id):
        mlflow.log_metrics({
            "eval_accuracy": accuracy,
            "eval_precision": precision,
            "eval_recall": recall,
            "eval_f1": f1
        })
    
    print(f"✅ Metrics saved: {metrics_path}")
    print(f"✅ Confusion matrix saved: {cm_path}")
    print(f"✅ Logged to MLflow run: {run_id}")

if __name__ == "__main__":
    main()
