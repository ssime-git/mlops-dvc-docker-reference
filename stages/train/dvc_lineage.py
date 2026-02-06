"""
DVC Data Lineage Utilities for DagHub Integration
Provides functions to link DVC data versions with MLflow experiments
"""

import logging
from pathlib import Path
from typing import Dict, Optional, Tuple

logger = logging.getLogger(__name__)


def get_dagshub_repo_info() -> Tuple[Optional[str], Optional[str]]:
    """
    Extract DagHub repository owner and name from DVC config

    Returns:
        Tuple of (owner, repo_name) or (None, None) if not found
    """
    # Try multiple possible locations for DVC config
    possible_paths = [
        Path("/workspace/.dvc/config"),
        Path.cwd() / ".dvc" / "config",
        Path(__file__).parent.parent.parent / ".dvc" / "config",
    ]

    dvc_config_path = None
    for path in possible_paths:
        if path.exists():
            dvc_config_path = path
            break

    if not dvc_config_path:
        logger.warning("DVC config not found")
        return None, None

    try:
        with open(dvc_config_path) as f:
            config = f.read()

        # Parse URL like: https://dagshub.com/ssime-git/mlops-dvc-docker-reference.dvc
        for line in config.split("\n"):
            if "url = https://dagshub.com/" in line:
                # Extract owner/repo from URL
                url_part = line.split("https://dagshub.com/")[1]
                parts = url_part.split("/")
                if len(parts) >= 2:
                    owner = parts[0]
                    repo = parts[1].replace(".dvc", "")
                    return owner, repo

        return None, None
    except Exception as e:
        logger.warning(f"Could not parse DVC config: {e}")
        return None, None


def get_dagshub_data_url(file_path: str, md5_hash: str) -> Optional[str]:
    """
    Generate DagHub URL for a specific data version

    Args:
        file_path: Path to the data file (e.g., "data/processed/train.csv")
        md5_hash: MD5 hash of the file from DVC

    Returns:
        DagHub URL to view the file at that specific version
    """
    owner, repo = get_dagshub_repo_info()

    if not owner or not repo:
        return None

    # DagHub data URL format: https://dagshub.com/{owner}/{repo}/src/{hash}/{path}
    url = f"https://dagshub.com/{owner}/{repo}/src/{md5_hash}/{file_path}"
    return url


def get_all_data_urls(data_metadata: Dict) -> Dict[str, str]:
    """
    Generate DagHub URLs for all datasets in metadata

    Args:
        data_metadata: Dictionary with file paths as keys and metadata dicts as values

    Returns:
        Dictionary mapping file paths to DagHub URLs
    """
    urls = {}

    for path, metadata in data_metadata.items():
        md5_hash = metadata.get("md5")
        if md5_hash:
            url = get_dagshub_data_url(path, md5_hash)
            if url:
                urls[path] = url

    return urls


def log_dagshub_lineage_tags(mlflow_instance, data_metadata: Dict):
    """
    Log DagHub data URLs as MLflow tags for easy access

    Args:
        mlflow_instance: MLflow module instance
        data_metadata: Dictionary with file paths as keys and metadata dicts as values
    """
    owner, repo = get_dagshub_repo_info()

    if not owner or not repo:
        logger.warning("Could not determine DagHub repository info")
        return

    # Log repository info
    mlflow_instance.set_tag("dagshub_repo", f"{owner}/{repo}")
    mlflow_instance.set_tag("dagshub_repo_url", f"https://dagshub.com/{owner}/{repo}")

    # Log URLs for each dataset
    urls = get_all_data_urls(data_metadata)
    for path, url in urls.items():
        tag_name = f"dagshub_url_{path.replace('/', '_').replace('.', '_')}"
        mlflow_instance.set_tag(tag_name, url)
        logger.info(f"Logged DagHub URL for {path}: {url}")


def format_lineage_info(data_version: str, data_metadata: Dict) -> str:
    """
    Format data lineage information as a markdown string

    Args:
        data_version: Combined data version hash
        data_metadata: Dictionary with file paths and metadata

    Returns:
        Formatted markdown string with lineage information
    """
    lines = [
        "# Data Lineage Information\n",
        f"**Data Version:** `{data_version}`\n",
        "\n## Datasets Used\n",
    ]

    owner, repo = get_dagshub_repo_info()

    for path, metadata in data_metadata.items():
        md5 = metadata.get("md5", "unknown")
        size = metadata.get("size", 0)
        stage = metadata.get("stage", "unknown")

        lines.append(f"\n### {path}")
        lines.append(f"- **Stage:** {stage}")
        lines.append(f"- **MD5:** `{md5}`")
        lines.append(f"- **Size:** {size:,} bytes")

        if owner and repo:
            url = get_dagshub_data_url(path, md5)
            if url:
                lines.append(f"- **DagHub URL:** [{path}@{md5[:8]}]({url})")

    return "\n".join(lines)
