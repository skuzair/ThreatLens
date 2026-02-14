import pandas as pd
from sklearn.ensemble import IsolationForest
import joblib
import os

DATA_PATH = r"C:\Users\Samagra\Documents\ThreatLens\data\processed\network_features.csv"
MODEL_PATH = r"C:\Users\Samagra\Documents\ThreatLens\network_model\models\network\isolation_forest.pkl"

def train_if():

    df = pd.read_csv(DATA_PATH)

    model = IsolationForest(
        n_estimators=200,
        contamination=0.02,
        random_state=42
    )

    model.fit(df)

    os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
    joblib.dump(model, MODEL_PATH)

    print("Isolation Forest saved ✔")

if __name__ == "__main__":
    train_if()
