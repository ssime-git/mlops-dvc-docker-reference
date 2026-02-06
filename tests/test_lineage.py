import importlib
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "stages" / "train"))
dvc_lineage = importlib.import_module("dvc_lineage")


@pytest.fixture
def sample_metadata():
    return {
        "data/processed/train.csv": {
            "md5": "47fd89ce6c52daa555a94670836c67a2",
            "size": 2237,
            "stage": "preprocess",
        },
        "data/processed/test.csv": {
            "md5": "12633f6b7b7282fb932761e33b24d21d",
            "size": 617,
            "stage": "preprocess",
        },
    }


def test_get_dagshub_repo_info_from_cwd_config(tmp_path, monkeypatch):
    dvc_dir = tmp_path / ".dvc"
    dvc_dir.mkdir(parents=True)
    (dvc_dir / "config").write_text(
        '[remote "origin"]\n    url = https://dagshub.com/acme/mlops-demo.dvc\n',
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)

    owner, repo = dvc_lineage.get_dagshub_repo_info()

    assert owner == "acme"
    assert repo == "mlops-demo"


def test_get_dagshub_repo_info_missing_config_returns_none(monkeypatch):
    monkeypatch.setattr(dvc_lineage.Path, "exists", lambda _self: False)

    owner, repo = dvc_lineage.get_dagshub_repo_info()

    assert owner is None
    assert repo is None


def test_get_dagshub_repo_info_malformed_url_returns_none(tmp_path, monkeypatch):
    dvc_dir = tmp_path / ".dvc"
    dvc_dir.mkdir(parents=True)
    (dvc_dir / "config").write_text(
        '[remote "origin"]\n    url = https://example.com/not-dagshub\n',
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)

    owner, repo = dvc_lineage.get_dagshub_repo_info()

    assert owner is None
    assert repo is None


def test_get_dagshub_data_url(monkeypatch):
    monkeypatch.setattr(dvc_lineage, "get_dagshub_repo_info", lambda: ("acme", "mlops"))

    url = dvc_lineage.get_dagshub_data_url(
        "data/processed/train.csv", "47fd89ce6c52daa555a94670836c67a2"
    )

    assert url == (
        "https://dagshub.com/acme/mlops/src/"
        "47fd89ce6c52daa555a94670836c67a2/data/processed/train.csv"
    )


def test_get_all_data_urls_ignores_items_without_md5(monkeypatch):
    monkeypatch.setattr(dvc_lineage, "get_dagshub_repo_info", lambda: ("acme", "mlops"))

    urls = dvc_lineage.get_all_data_urls(
        {
            "data/processed/train.csv": {
                "md5": "abc",
                "size": 1,
                "stage": "preprocess",
            },
            "data/processed/invalid.csv": {"size": 2, "stage": "preprocess"},
        }
    )

    assert "data/processed/train.csv" in urls
    assert "data/processed/invalid.csv" not in urls


def test_format_lineage_info_contains_expected_fields(sample_metadata, monkeypatch):
    monkeypatch.setattr(dvc_lineage, "get_dagshub_repo_info", lambda: ("acme", "mlops"))

    rendered = dvc_lineage.format_lineage_info("a7f3c82e", sample_metadata)

    assert "Data Version" in rendered
    assert "a7f3c82e" in rendered
    assert "data/processed/train.csv" in rendered
    assert "data/processed/test.csv" in rendered
    assert "MD5" in rendered
    assert "https://dagshub.com/acme/mlops/src/" in rendered
