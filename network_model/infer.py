"""
infer.py — Dynamic calibration version
────────────────────────────────────────
Fixes the "everything scores 87" problem by using percentile-based
dynamic normalization that self-calibrates to whatever data it sees.

The root cause was: synthetic data has very different byte/load ranges
vs UNSW-NB15 training data, so the autoencoder MSE is always high
(everything looks anomalous). Dynamic calibration fixes this by
normalizing relative to the observed data distribution, not fixed constants.
"""

import os
import torch
import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import mean_squared_error

from network_model.model_architecture import load_autoencoder

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

MODEL_DIR = os.path.join(os.path.dirname(__file__), "models", "network")

FEATURE_NAMES = [
    "dur", "spkts", "dpkts", "sbytes", "dbytes",
    "sttl", "dttl", "sload", "dload", "sloss",
    "dloss", "sinpkt", "dinpkt", "sjit", "djit",
    "swin", "dwin", "tcprtt", "synack", "ackdat"
]


class NetworkInference:

    def __init__(self):
        self.scaler      = joblib.load(os.path.join(MODEL_DIR, "scaler.pkl"))
        self.if_model    = joblib.load(os.path.join(MODEL_DIR, "isolation_forest.pkl"))
        self.autoencoder = load_autoencoder(
            os.path.join(MODEL_DIR, "autoencoder.pt"), device=DEVICE
        )

        # Running history for dynamic normalization
        self._ae_history = []
        self._if_history = []
        self._warmup     = 50   # events before dynamic normalization kicks in

    def _dynamic_normalize(self, value: float, history: list) -> float:
        """
        Before warmup: simple clamp to 0-100.
        After warmup:  percentile-based normalization so full 0-100
                       range is used regardless of data distribution.
        """
        history.append(value)

        if len(history) < self._warmup:
            # Fixed normalization during warmup
            return float(np.clip(abs(value) * 80, 0, 100))

        # Use last 500 values, 5th-95th percentile as the range
        recent = history[-500:]
        p5     = float(np.percentile(recent, 5))
        p95    = float(np.percentile(recent, 95))

        if abs(p95 - p5) < 1e-9:
            return 50.0

        normalized = (value - p5) / (p95 - p5) * 100
        return float(np.clip(normalized, 0, 100))

    def predict(self, feature_vector: list) -> float:
        """
        Takes list of 20 floats in FEATURE_NAMES order.
        Returns float anomaly score 0-100.
        """
        # Named DataFrame so sklearn does not warn
        df         = pd.DataFrame([feature_vector], columns=FEATURE_NAMES)
        X_scaled   = self.scaler.transform(df)
        X_scaled_df = pd.DataFrame(X_scaled, columns=FEATURE_NAMES)

        # Isolation Forest (trained on scaled data; use scaled DataFrame for feature names)
        # decision_function: negative = anomalous, positive = normal
        if_raw   = float(self.if_model.decision_function(X_scaled_df)[0])
        if_score = self._dynamic_normalize(-if_raw, self._if_history)

        # Autoencoder reconstruction error
        self.autoencoder.eval()
        with torch.no_grad():
            tensor        = torch.tensor(X_scaled).float().to(DEVICE)
            reconstructed = self.autoencoder(tensor)
            ae_error      = float(mean_squared_error(
                tensor.cpu().numpy().flatten(),
                reconstructed.cpu().numpy().flatten()
            ))

        ae_score = self._dynamic_normalize(ae_error, self._ae_history)

        # Weighted ensemble
        final = (0.4 * if_score) + (0.6 * ae_score)
        return round(float(np.clip(final, 0, 100)), 2)