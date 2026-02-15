"""
generate_synthetic_logs.py
───────────────────────────
Generates synthetic log features as fallback if HDFS data is not available.
Saves to log_model/data/log_features.csv

Run from ThreatLens root:
    python log_model/generate_synthetic_logs.py
"""

import numpy as np
import pandas as pd
from pathlib import Path

BASE_DIR    = Path(__file__).resolve().parent
OUTPUT_DIR  = BASE_DIR / "data"
OUTPUT_PATH = OUTPUT_DIR / "log_features.csv"


def generate_logs(n_normal=10000, n_attack=2000):
    np.random.seed(42)

    normal = pd.DataFrame({
        "event_type_encoded":         np.random.uniform(0, 0.5, n_normal),
        "hour_of_day":                np.random.randint(8, 18, n_normal),
        "day_of_week":                np.random.randint(0, 5, n_normal),
        "failed_logins_last_5min":    np.random.poisson(0.5, n_normal),
        "is_new_source_ip":           0,
        "privilege_level":            0,
        "command_risk_score":         np.random.uniform(0, 0.2, n_normal),
        "is_first_time_user_host":    0,
        "time_since_last_event_sec":  np.random.randint(10, 300, n_normal),
        "process_whitelisted":        1,
        "destination_ip_internal":    1,
        "auth_method_encoded":        0,
        "dna_deviation_score":        np.random.uniform(0, 20, n_normal),
        "consecutive_failures":       np.random.poisson(0.3, n_normal),
        "session_duration_seconds":   np.random.randint(60, 3600, n_normal),
        "label": 0
    })

    attack = pd.DataFrame({
        "event_type_encoded":         np.random.uniform(1.5, 3.0, n_attack),
        "hour_of_day":                np.random.randint(0, 5, n_attack),
        "day_of_week":                np.random.randint(0, 6, n_attack),
        "failed_logins_last_5min":    np.random.poisson(5, n_attack),
        "is_new_source_ip":           1,
        "privilege_level":            2,
        "command_risk_score":         np.random.uniform(0.6, 1.0, n_attack),
        "is_first_time_user_host":    1,
        "time_since_last_event_sec":  np.random.randint(1, 20, n_attack),
        "process_whitelisted":        0,
        "destination_ip_internal":    0,
        "auth_method_encoded":        0,
        "dna_deviation_score":        np.random.uniform(50, 100, n_attack),
        "consecutive_failures":       np.random.poisson(6, n_attack),
        "session_duration_seconds":   np.random.randint(10, 300, n_attack),
        "label": 1
    })

    df = pd.concat([normal, attack]).sample(frac=1).reset_index(drop=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUTPUT_PATH, index=False)

    print(f"✅ Synthetic log dataset saved to: {OUTPUT_PATH}")
    print(f"   Normal: {n_normal} | Attack: {n_attack} | Total: {len(df)}")


if __name__ == "__main__":
    generate_logs()