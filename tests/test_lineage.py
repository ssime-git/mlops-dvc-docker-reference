#!/usr/bin/env python3
"""
Quick test script for data lineage functionality
"""

import sys
from pathlib import Path

# Add stages/train to path to import dvc_lineage
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "stages" / "train"))

from dvc_lineage import (
    format_lineage_info,
    get_all_data_urls,
    get_dagshub_data_url,
    get_dagshub_repo_info,
)


def test_dagshub_repo_info():
    """Test extracting DagHub repository information"""
    print("\n=== Testing DagHub Repo Info ===")
    owner, repo = get_dagshub_repo_info()
    print(f"Owner: {owner}")
    print(f"Repo: {repo}")

    if owner and repo:
        print("✓ Successfully extracted repository info")
        return True
    else:
        print("✗ Failed to extract repository info")
        return False


def test_dagshub_url_generation():
    """Test generating DagHub URLs"""
    print("\n=== Testing DagHub URL Generation ===")

    test_cases = [
        ("data/processed/train.csv", "47fd89ce6c52daa555a94670836c67a2"),
        ("data/processed/test.csv", "12633f6b7b7282fb932761e33b24d21d"),
    ]

    success = True
    for path, md5 in test_cases:
        url = get_dagshub_data_url(path, md5)
        if url:
            print(f"✓ {path}")
            print(f"  URL: {url}")
        else:
            print(f"✗ Failed to generate URL for {path}")
            success = False

    return success


def test_all_data_urls():
    """Test generating URLs for multiple datasets"""
    print("\n=== Testing All Data URLs ===")

    # Sample metadata like what get_data_version() returns
    data_metadata = {
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

    urls = get_all_data_urls(data_metadata)

    if len(urls) == 2:
        print(f"✓ Generated {len(urls)} URLs")
        for path, url in urls.items():
            print(f"  {path}: {url}")
        return True
    else:
        print(f"✗ Expected 2 URLs, got {len(urls)}")
        return False


def test_lineage_formatting():
    """Test formatting lineage information"""
    print("\n=== Testing Lineage Formatting ===")

    data_version = "a7f3c82e"
    data_metadata = {
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

    lineage_info = format_lineage_info(data_version, data_metadata)

    # Check that key elements are present
    checks = [
        ("Data Version" in lineage_info, "Data Version header"),
        (data_version in lineage_info, "Version hash"),
        ("train.csv" in lineage_info, "Train dataset"),
        ("test.csv" in lineage_info, "Test dataset"),
        ("MD5" in lineage_info, "MD5 hashes"),
    ]

    success = True
    for check, desc in checks:
        if check:
            print(f"✓ {desc} present")
        else:
            print(f"✗ {desc} missing")
            success = False

    print("\nGenerated lineage info:")
    print("-" * 80)
    print(lineage_info)
    print("-" * 80)

    return success


def main():
    """Run all tests"""
    print("=" * 80)
    print("Data Lineage Functionality Tests")
    print("=" * 80)

    tests = [
        test_dagshub_repo_info,
        test_dagshub_url_generation,
        test_all_data_urls,
        test_lineage_formatting,
    ]

    results = []
    for test_func in tests:
        try:
            result = test_func()
            results.append((test_func.__name__, result))
        except Exception as e:
            print(f"\n✗ {test_func.__name__} raised exception: {e}")
            results.append((test_func.__name__, False))

    # Summary
    print("\n" + "=" * 80)
    print("Test Summary")
    print("=" * 80)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {test_name}")

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\n✓ All tests passed!")
        return 0
    else:
        print(f"\n✗ {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
