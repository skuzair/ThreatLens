"""
train_isolation_forest.py
──────────────────────────
Trains Isolation Forest on file activity data.
Saves model + scaler to file_model/models/

Run from file_model directory:
    python train_isolation_forest.py
"""

import joblib
import pandas as pd
from pathlib import Path
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import MinMaxScaler

# ── Paths ──────────────────────────────────────────────────────────────────
BASE_DIR    = Path(__file__).resolve().parent        # file_model/
DATA_PATH   = BASE_DIR / "data" / "file_features.csv"
MODEL_DIR   = BASE_DIR / "models"
MODEL_PATH  = MODEL_DIR / "isolation_forest.pkl"
SCALER_PATH = MODEL_DIR / "scaler.pkl"


def train():
    # ── Check data exists ──────────────────────────────────────────────────
    if not DATA_PATH.exists():
        print(f"❌ Data not found at: {DATA_PATH}")
        print("   Run generate_synthetic_file_data.py first")
        return

    print(f"Loading dataset from: {DATA_PATH}")
    df = pd.read_csv(DATA_PATH)
    print(f"   Total rows: {len(df)}")

    # Train only on normal samples
    if "label" in df.columns:
        df_train = df[df["label"] == 0]
        print(f"   Training on normal samples only: {len(df_train)}")
        X = df_train.drop(columns=["label"])
    else:
        X = df

    # ── Scale ──────────────────────────────────────────────────────────────
    print("Scaling features...")
    scaler   = MinMaxScaler()
    X_scaled = scaler.fit_transform(X)

    # ── Train ──────────────────────────────────────────────────────────────
    print("Training Isolation Forest...")
    model = IsolationForest(
        n_estimators=100,
        contamination=0.05,
        random_state=42
    )
    model.fit(X_scaled)

    # ── Save ───────────────────────────────────────────────────────────────
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, MODEL_PATH)
    joblib.dump(scaler, SCALER_PATH)

    print(f"✅ Model saved  : {MODEL_PATH}")
    print(f"✅ Scaler saved : {SCALER_PATH}")
    print("File model training complete.")


if __name__ == "__main__":
    train()