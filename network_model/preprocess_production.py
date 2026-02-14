import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DATA_PATH = os.path.join(BASE_DIR, "data", "processed", "network_features.csv")

import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler
import joblib
import os

SCALER_PATH = "models/network/scaler.pkl"

def encode_protocol(protocol):
    mapping = {"TCP": 1, "UDP": 2, "ICMP": 3}
    return mapping.get(protocol, 0)

def encode_flags(flags):
    return [
        1 if "S" in flags else 0,
        1 if "A" in flags else 0,
        1 if "F" in flags else 0,
        1 if "R" in flags else 0,
    ]

def preprocess_dataframe(df):
    features = []

    for _, row in df.iterrows():
        vector = [
            row["duration_seconds"],
            row["bytes_sent"],
            row["bytes_received"],
            row["source_port"],
            row["dest_port"],
            encode_protocol(row["protocol"]),
        ]

        vector.extend(encode_flags(row.get("flags", "")))
        features.append(vector)

    return np.array(features)

def fit_scaler(data):
    scaler = MinMaxScaler()
    scaled = scaler.fit_transform(data)
    os.makedirs("models/network", exist_ok=True)
    joblib.dump(scaler, SCALER_PATH)
    return scaled

def preprocess_single_event(event):
    # Handle both direct event and nested raw_data structure
    if "raw_data" in event:
        raw = event["raw_data"]
    else:
        raw = event

    duration      = float(raw.get("duration_seconds", 0) or 0)
    bytes_sent    = float(raw.get("bytes_sent", 0) or 0)
    bytes_received = float(raw.get("bytes_received", 0) or 0)
    src_port      = float(raw.get("source_port", 0) or 0)
    dst_port      = float(raw.get("dest_port", 0) or 0)
    protocol      = raw.get("protocol", "TCP").upper()

    # Derive meaningful features from actual values
    proto_encoded = {"TCP": 1.0, "UDP": 0.5, "ICMP": 0.2}.get(protocol, 0.0)
    sload = bytes_sent / (duration + 1e-6)
    dload = bytes_received / (duration + 1e-6)
    
    # Estimate packet counts from byte sizes (avg packet ~512 bytes)
    spkts = max(1, int(bytes_sent / 512))
    dpkts = max(1, int(bytes_received / 512))

    # TTL heuristic based on destination port
    sttl = 64 if dst_port < 1024 else 128
    dttl = 64

    feature_vector = [
        duration,        # dur
        spkts,           # spkts  ← now derived not hardcoded
        dpkts,           # dpkts  ← now derived not hardcoded
        bytes_sent,      # sbytes ← now populated
        bytes_received,  # dbytes ← now populated
        sttl,            # sttl
        dttl,            # dttl
        sload,           # sload  ← now derived
        dload,           # dload  ← now derived
        0,               # sloss
        0,               # dloss
        duration / (spkts + 1),   # sinpkt
        duration / (dpkts + 1),   # dinpkt
        0,               # sjit
        0,               # djit
        8192,            # swin
        8192,            # dwin
        0,               # tcprtt
        0,               # synack
        0                # ackdat
    ]

    return feature_vector