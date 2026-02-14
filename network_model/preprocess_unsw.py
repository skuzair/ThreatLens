import os
import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler
import joblib

# =========================
# HARDCODED PATHS (STABLE)
# =========================
RAW_PATH = r"C:\Users\Samagra\Documents\ThreatLens\data\raw\unsw_nb15\UNSW_NB15_training-set.csv"
PROCESSED_PATH = r"C:\Users\Samagra\Documents\ThreatLens\data\processed\network_features.csv"
SCALER_PATH = r"C:\Users\Samagra\Documents\ThreatLens\network_model\models\network\scaler.pkl"

SELECTED_FEATURES = [
    "dur", "spkts", "dpkts", "sbytes", "dbytes",
    "sttl", "dttl", "sload", "dload", "sloss",
    "dloss", "sinpkt", "dinpkt", "sjit", "djit",
    "swin", "dwin", "tcprtt", "synack", "ackdat"
]

def preprocess_unsw():
    print("Loading UNSW dataset...")
    df = pd.read_csv(RAW_PATH)

    df = df[df["label"] == 0]
    df = df.fillna(0)

    df = df[SELECTED_FEATURES]

    scaler = MinMaxScaler()
    scaled = scaler.fit_transform(df)

    os.makedirs(os.path.dirname(PROCESSED_PATH), exist_ok=True)
    os.makedirs(os.path.dirname(SCALER_PATH), exist_ok=True)

    pd.DataFrame(scaled, columns=SELECTED_FEATURES).to_csv(PROCESSED_PATH, index=False)
    joblib.dump(scaler, SCALER_PATH)

    print("Preprocessing complete ✔")

# =========================
# RUNTIME EVENT CONVERTER
# =========================
def preprocess_single_event(event):

    duration = float(event.get("duration_seconds", event.get("duration", 0)))
    bytes_sent = float(event.get("bytes_sent", event.get("src_bytes", 0)))
    bytes_received = float(event.get("bytes_received", event.get("dst_bytes", 0)))

    feature_map = {
        "dur": duration,
        "spkts": bytes_sent / 500 if bytes_sent else 0,
        "dpkts": bytes_received / 500 if bytes_received else 0,
        "sbytes": bytes_sent,
        "dbytes": bytes_received,
        "sttl": 64,
        "dttl": 64,
        "sload": bytes_sent / max(duration, 1),
        "dload": bytes_received / max(duration, 1),
        "sloss": 0,
        "dloss": 0,
        "sinpkt": duration / max(bytes_sent / 1000, 1),
        "dinpkt": duration / max(bytes_received / 1000, 1),
        "sjit": 0,
        "djit": 0,
        "swin": 8192,
        "dwin": 8192,
        "tcprtt": duration / 10 if duration else 0,
        "synack": duration / 20 if duration else 0,
        "ackdat": duration / 30 if duration else 0
    }

    vector = [feature_map[f] for f in SELECTED_FEATURES]
    print("FEATURE VECTOR:", vector)
    return vector


if __name__ == "__main__":
    preprocess_unsw()
