"""
train_random_forest.py
───────────────────────
Run from ThreatLens root:
    python log_model/train_random_forest.py
"""

import joblib
import pandas as pd
from pathlib import Path
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split

BASE_DIR    = Path(__file__).resolve().parent
DATA_PATH   = BASE_DIR / "data" / "log_features.csv"
MODEL_DIR   = BASE_DIR / "models"
MODEL_PATH  = MODEL_DIR / "random_forest.pkl"


def train_random_forest():
    if not DATA_PATH.exists():
        print(f"❌ Data not found: {DATA_PATH}")
        print("   Run parse_hdfs_logs.py or generate_synthetic_logs.py first")
        return

    print(f"Loading data: {DATA_PATH}")
    df = pd.read_csv(DATA_PATH)
    print(f"   Rows: {len(df)} | Anomaly rate: {df['label'].mean():.2%}")

    y = df["label"].values
    X = df.drop(columns=["label"]).values

    X_train, X_val, y_train, y_val = train_test_split(X, y, test_size=0.2, random_state=42)

    print("Training Random Forest...")
    model = RandomForestClassifier(
        n_estimators=200,
        max_depth=15,
        random_state=42,
        n_jobs=-1
    )
    model.fit(X_train, y_train)

    val_acc = model.score(X_val, y_val)
    print(f"   Validation accuracy: {val_acc:.4f}")

    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, MODEL_PATH)
    print(f"✅ Random Forest saved: {MODEL_PATH}")


if __name__ == "__main__":
    train_random_forest()