"""
generate_synthetic_file_data.py
────────────────────────────────
Generates synthetic file activity dataset for training.
Saves to file_model/data/file_features.csv

Run from file_model directory:
    python generate_synthetic_file_data.py
"""

import os
import numpy as np
import pandas as pd
from pathlib import Path

# ── Paths ──────────────────────────────────────────────────────────────────
BASE_DIR    = Path(__file__).resolve().parent   # file_model/
OUTPUT_DIR  = BASE_DIR / "data"
OUTPUT_PATH = OUTPUT_DIR / "file_features.csv"


def generate_file_data(n_normal=8000, n_attack=2000):
    np.random.seed(42)

    # Normal file activity
    normal = pd.DataFrame({
        "modifications_per_minute":  np.random.poisson(2, n_normal),
        "unique_processes_writing":  np.random.randint(1, 3, n_normal),
        "extension_change_rate":     np.random.uniform(0, 0.05, n_normal),
        "file_size_change_ratio":    np.random.uniform(0.9, 1.1, n_normal),
        "sensitive_dir_access_rate": np.random.uniform(0, 0.1, n_normal),
        "hour_of_day":               np.random.randint(8, 20, n_normal),
        "label": 0
    })

    # Ransomware-like activity
    attack = pd.DataFrame({
        "modifications_per_minute":  np.random.poisson(150, n_attack),
        "unique_processes_writing":  np.random.randint(1, 2, n_attack),
        "extension_change_rate":     np.random.uniform(0.6, 1.0, n_attack),
        "file_size_change_ratio":    np.random.uniform(0.2, 0.5, n_attack),
        "sensitive_dir_access_rate": np.random.uniform(0.5, 1.0, n_attack),
        "hour_of_day":               np.random.randint(0, 5, n_attack),
        "label": 1
    })

    df = pd.concat([normal, attack]).sample(frac=1).reset_index(drop=True)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUTPUT_PATH, index=False)

    print(f"✅ Dataset saved to: {OUTPUT_PATH}")
    print(f"   Normal samples : {n_normal}")
    print(f"   Attack samples : {n_attack}")
    print(f"   Total rows     : {len(df)}")


if __name__ == "__main__":
    generate_file_data()