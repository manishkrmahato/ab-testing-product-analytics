"""
Data loading and provenance verification module.

Handles automated downloading, checksum verification, and structured
DataFrame loading for experiment and segment data.
"""

import hashlib
import os
import urllib.request
from typing import Optional, Tuple
import pandas as pd

RAW_DATA_URLS = {
    "ab_data.csv": "https://raw.githubusercontent.com/beery4010/Analyze-AB-Test-Results/master/ab_data.csv",
    "countries.csv": "https://raw.githubusercontent.com/beery4010/Analyze-AB-Test-Results/master/countries.csv",
}

EXPECTED_SHA256 = {
    "ab_data.csv": "d56e2accec25e99ac21cb3d76c5df516dd19cc7a77c14c9014f94e1ea1301beb",
    "countries.csv": "c011d0503d305c295327cd9dff9c37bb62a5f9ef4b356bcdaf7deca20d55e45b",
}


def calculate_sha256(file_path: str) -> str:
    """Calculates SHA256 hex digest for a local file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(65536), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def verify_file_checksum(file_path: str, expected_hash: str) -> bool:
    """Verifies that a local file matches its expected SHA256 hash."""
    if not os.path.exists(file_path):
        return False
    actual_hash = calculate_sha256(file_path)
    return actual_hash.lower() == expected_hash.lower()


def download_file(url: str, target_path: str, timeout: int = 30) -> None:
    """Downloads a file from a URL using a standard browser user-agent."""
    os.makedirs(os.path.dirname(os.path.abspath(target_path)), exist_ok=True)
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) ExperimentationDataDownloader/1.0"}
    )
    with urllib.request.urlopen(req, timeout=timeout) as response, open(target_path, "wb") as out_file:
        out_file.write(response.read())


def ensure_data_downloaded(data_dir: str = "data/raw") -> Tuple[str, str]:
    """
    Ensures both ab_data.csv and countries.csv exist and pass checksum validation.
    Downloads them if missing or invalid.
    """
    os.makedirs(data_dir, exist_ok=True)
    ab_path = os.path.join(data_dir, "ab_data.csv")
    countries_path = os.path.join(data_dir, "countries.csv")

    for filename, path in [("ab_data.csv", ab_path), ("countries.csv", countries_path)]:
        expected_hash = EXPECTED_SHA256[filename]
        if not os.path.exists(path) or not verify_file_checksum(path, expected_hash):
            url = RAW_DATA_URLS[filename]
            print(f"Downloading {filename} from {url}...")
            download_file(url, path)
            if not verify_file_checksum(path, expected_hash):
                actual = calculate_sha256(path)
                raise ValueError(
                    f"Checksum mismatch for {filename}! Expected {expected_hash}, got {actual}"
                )
            print(f"Successfully verified {filename} checksum.")

    return ab_path, countries_path


def load_raw_experiment_data(file_path: str = "data/raw/ab_data.csv") -> pd.DataFrame:
    """
    Loads raw experiment data from CSV into a pandas DataFrame.
    """
    if not os.path.exists(file_path):
        ensure_data_downloaded(os.path.dirname(file_path))

    df = pd.read_csv(
        file_path,
        dtype={
            "user_id": "int64",
            "group": "category",
            "landing_page": "category",
            "converted": "int64",
        },
        parse_dates=["timestamp"],
    )
    return df


def load_countries_data(file_path: str = "data/raw/countries.csv") -> pd.DataFrame:
    """
    Loads user-country mapping data from CSV into a pandas DataFrame.
    """
    if not os.path.exists(file_path):
        ensure_data_downloaded(os.path.dirname(file_path))

    df = pd.read_csv(
        file_path,
        dtype={
            "user_id": "int64",
            "country": "category",
        },
    )
    return df
