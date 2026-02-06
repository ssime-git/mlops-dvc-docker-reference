#!/usr/bin/env python3
"""
Exemple d'accès au data lineage via l'API MLflow
Montre comment récupérer programmatiquement les informations de lineage
"""

import os
from typing import Dict

import mlflow
from mlflow.tracking import MlflowClient


def setup_mlflow():
    """Configure MLflow avec les credentials DagHub"""
    tracking_uri = os.getenv("MLFLOW_TRACKING_URI")
    username = os.getenv("MLFLOW_TRACKING_USERNAME")
    password = os.getenv("MLFLOW_TRACKING_PASSWORD")

    if not all([tracking_uri, username, password]):
        print("⚠️  Variables d'environnement MLflow non définies:")
        print("   - MLFLOW_TRACKING_URI")
        print("   - MLFLOW_TRACKING_USERNAME")
        print("   - MLFLOW_TRACKING_PASSWORD")
        print("\nDéfinissez-les avec:")
        print('export MLFLOW_TRACKING_URI="https://dagshub.com/user/repo.mlflow"')
        return None

    mlflow.set_tracking_uri(tracking_uri)
    return MlflowClient()


def get_latest_run(client: MlflowClient, experiment_name: str = "iris-rf-train"):
    """Récupère le run le plus récent d'une expérience"""
    try:
        experiment = client.get_experiment_by_name(experiment_name)
        if not experiment:
            print(f"Expérience '{experiment_name}' non trouvée")
            return None

        runs = client.search_runs(
            experiment_ids=[experiment.experiment_id],
            order_by=["start_time DESC"],
            max_results=1,
        )

        return runs[0] if runs else None
    except Exception as e:
        print(f"Erreur lors de la récupération du run: {e}")
        return None


def extract_lineage_info(run) -> Dict:
    """Extrait toutes les informations de lineage d'un run"""
    lineage = {
        "run_id": run.info.run_id,
        "run_name": run.data.tags.get("mlflow.runName", "N/A"),
        "start_time": run.info.start_time,
        "data_version": run.data.params.get("data_version", "N/A"),
        "datasets": [],
        "dvc_metadata": {},
        "dagshub_info": {},
        "metrics": dict(run.data.metrics),
    }

    # Extraire les datasets (MLflow 2.x+)
    try:
        if hasattr(run, "inputs") and run.inputs.dataset_inputs:
            for dataset_input in run.inputs.dataset_inputs:
                lineage["datasets"].append(
                    {
                        "name": dataset_input.dataset.name,
                        "source": dataset_input.dataset.source,
                        "digest": dataset_input.dataset.digest,
                        "context": getattr(dataset_input, "context", "N/A"),
                    }
                )
    except AttributeError:
        lineage["datasets"] = "Feature non disponible (MLflow < 2.8)"

    # Extraire les métadonnées DVC des tags
    for tag_key, tag_value in run.data.tags.items():
        if tag_key.startswith("dvc_"):
            lineage["dvc_metadata"][tag_key] = tag_value

    # Extraire les infos DagHub
    lineage["dagshub_info"]["repo"] = run.data.tags.get("dagshub_repo", "N/A")
    lineage["dagshub_info"]["repo_url"] = run.data.tags.get("dagshub_repo_url", "N/A")
    lineage["dagshub_info"]["data_urls"] = {}

    for tag_key, tag_value in run.data.tags.items():
        if tag_key.startswith("dagshub_url_"):
            dataset_name = tag_key.replace("dagshub_url_", "").replace("_", "/")
            lineage["dagshub_info"]["data_urls"][dataset_name] = tag_value

    return lineage


def display_lineage(lineage: Dict):
    """Affiche les informations de lineage de manière formatée"""
    print("\n" + "=" * 80)
    print(f"📊 Data Lineage pour Run: {lineage['run_id']}")
    print("=" * 80)

    print(f"\n🏷️  Run Name: {lineage['run_name']}")
    print(f"📅 Start Time: {lineage['start_time']}")
    print(f"🔖 Data Version: {lineage['data_version']}")

    # Métriques
    print("\n📈 Métriques:")
    for metric_name, metric_value in lineage["metrics"].items():
        print(f"   • {metric_name}: {metric_value:.4f}")

    # Datasets
    print("\n📦 Datasets utilisés:")
    if isinstance(lineage["datasets"], list) and lineage["datasets"]:
        for dataset in lineage["datasets"]:
            print(f"\n   Dataset: {dataset['name']}")
            print(f"   ├─ Source: {dataset['source']}")
            print(f"   ├─ Digest (MD5): {dataset['digest']}")
            print(f"   └─ Context: {dataset['context']}")
    else:
        print(f"   {lineage['datasets']}")

    # Métadonnées DVC
    print("\n🔐 Métadonnées DVC:")
    if lineage["dvc_metadata"]:
        for key, value in lineage["dvc_metadata"].items():
            print(f"   • {key}: {value}")
    else:
        print("   Aucune métadonnée DVC trouvée")

    # Infos DagHub
    print("\n🌐 DagHub Information:")
    print(f"   Repository: {lineage['dagshub_info']['repo']}")
    print(f"   URL: {lineage['dagshub_info']['repo_url']}")

    if lineage["dagshub_info"]["data_urls"]:
        print("\n   📍 URLs vers les versions de données:")
        for dataset_name, url in lineage["dagshub_info"]["data_urls"].items():
            print(f"\n   {dataset_name}:")
            print(f"   └─ {url}")

    print("\n" + "=" * 80 + "\n")


def compare_data_versions(
    client: MlflowClient, experiment_name: str = "iris-rf-train", limit: int = 5
):
    """Compare les versions de données entre plusieurs runs"""
    try:
        experiment = client.get_experiment_by_name(experiment_name)
        if not experiment:
            print(f"Expérience '{experiment_name}' non trouvée")
            return

        runs = client.search_runs(
            experiment_ids=[experiment.experiment_id],
            order_by=["start_time DESC"],
            max_results=limit,
        )

        print("\n" + "=" * 80)
        print(f"🔄 Comparaison des versions de données (derniers {len(runs)} runs)")
        print("=" * 80)

        for i, run in enumerate(runs, 1):
            data_version = run.data.params.get("data_version", "N/A")
            test_acc = run.data.metrics.get("test_accuracy", 0.0)
            run_name = run.data.tags.get("mlflow.runName", "N/A")

            print(f"\n{i}. Run: {run.info.run_id[:8]}... ({run_name})")
            print(f"   Data Version: {data_version}")
            print(f"   Test Accuracy: {test_acc:.4f}")

            # Comparer avec le run précédent
            if i > 1:
                prev_version = runs[i - 2].data.params.get("data_version", "N/A")
                if data_version != prev_version:
                    print(
                        "   ⚠️  Changement de données détecté "
                        f"(précédent: {prev_version})"
                    )
                else:
                    print("   ✓ Même version de données que le run précédent")

        print("\n" + "=" * 80 + "\n")

    except Exception as e:
        print(f"Erreur lors de la comparaison: {e}")


def main():
    """Exemple d'utilisation de l'API de lineage"""
    print("🔍 Accès au Data Lineage via l'API MLflow\n")

    # Setup
    client = setup_mlflow()
    if not client:
        return 1

    # Récupérer le run le plus récent
    print("📥 Récupération du run le plus récent...")
    run = get_latest_run(client)

    if not run:
        print("❌ Aucun run trouvé")
        return 1

    # Extraire et afficher le lineage
    lineage = extract_lineage_info(run)
    display_lineage(lineage)

    # Comparer les versions de données
    compare_data_versions(client)

    # Exemple d'utilisation programmatique
    print("💡 Utilisation programmatique:")
    print("\n# Accéder à la version des données")
    print(f"data_version = '{lineage['data_version']}'")

    print("\n# Récupérer les URLs DagHub")
    print("dagshub_urls = {")
    for name, url in lineage["dagshub_info"]["data_urls"].items():
        print(f"    '{name}': '{url}',")
    print("}")

    print("\n# Vérifier si les données ont changé depuis le dernier run")
    print("# (utile pour l'automatisation)")
    print("if data_version != previous_data_version:")
    print("    print('⚠️  Données modifiées, réentraînement nécessaire')")

    return 0


if __name__ == "__main__":
    exit(main())
