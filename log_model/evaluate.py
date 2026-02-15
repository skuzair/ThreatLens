"""
evaluate.py
────────────
Run from ThreatLens root:
    python log_model/evaluate.py
"""

import pandas as pd
from pathlib import Path
from log_model.infer import LogInference

BASE_DIR  = Path(__file__).resolve().parent
DATA_PATH = BASE_DIR / "data" / "log_features.csv"


def evaluate():
    if not DATA_PATH.exists():
        print(f"❌ Data not found: {DATA_PATH}")
        return

    df     = pd.read_csv(DATA_PATH)
    y_true = df["label"].values
    X      = df.drop(columns=["label"]).values

    model  = LogInference()
    buffer = []
    scores = []

    for row in X:
        result = model.predict(row.tolist(), buffer)
        scores.append(result["final_anomaly_score"])

    avg = sum(scores) / len(scores)
    print(f"✅ Evaluation complete")
    print(f"   Samples: {len(scores)}")
    print(f"   Average anomaly score: {avg:.2f}")
    print(f"   Scores > 50 (anomalous): {sum(s > 50 for s in scores)}")


if __name__ == "__main__":
    evaluate()