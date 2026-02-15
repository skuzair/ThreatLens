import joblib
import pandas as pd
from pathlib import Path
from sklearn.metrics import classification_report

BASE_DIR = Path(__file__).resolve().parents[2]
DATA_PATH = BASE_DIR / "data" / "processed" / "file_features.csv"
MODEL_DIR = BASE_DIR / "models" / "file"

MODEL_PATH = MODEL_DIR / "isolation_forest.pkl"
SCALER_PATH = MODEL_DIR / "scaler.pkl"

def evaluate():
    print("Loading model and dataset...")
    model = joblib.load(MODEL_PATH)
    scaler = joblib.load(SCALER_PATH)

    df = pd.read_csv(DATA_PATH)

    if "label" not in df.columns:
        print("No labels found. Evaluation skipped.")
        return

    X = df.drop(columns=["label"])
    y = df["label"]

    X_scaled = scaler.transform(X)

    preds = model.predict(X_scaled)
    preds = [1 if p == -1 else 0 for p in preds]  # convert IF output

    print("Classification Report:")
    print(classification_report(y, preds))

if __name__ == "__main__":
    evaluate()
