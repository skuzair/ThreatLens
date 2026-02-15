"""
Intent Predictor Module (Updated - No RF Sensor)
Production-ready version

- Proper label decoding
- Clean separation of feature builder
- No numeric class leakage
- Updated for 4 sources: network, logs, file, camera
"""
import pandas as pd
import os
import joblib
import numpy as np
from typing import Dict, List


# ============================================================
# CONFIG
# ============================================================

MODEL_PATH = "models/intent/random_forest.pkl"
ENCODER_PATH = "models/intent/label_encoder.pkl"

# Updated feature order without RF
FEATURE_ORDER = [
    "camera_triggered",
    "network_triggered",
    "logs_triggered",
    "file_triggered",
    "has_mass_encryption",
    "has_large_transfer",
    "has_privilege_escalation",
    "time_of_day",
    "sources_count",
    "max_anomaly_score"
]


# ============================================================
# FEATURE BUILDER
# ============================================================

class IntentFeatureBuilder:

    @staticmethod
    def build_features(incident: Dict) -> List[float]:

        sources = incident.get("sources_involved", [])
        events = incident.get("correlated_events", [])
        time_of_day = incident.get("time_of_day", 0)

        def any_flag(flag):
            return any(e.get(flag, False) for e in events)

        feature_dict = {
            "camera_triggered": int("camera" in sources),
            "network_triggered": int("network" in sources),
            "logs_triggered": int("logs" in sources),
            "file_triggered": int("file" in sources),

            "has_mass_encryption": int(any_flag("ransomware_pattern")),
            "has_large_transfer": int(any_flag("large_transfer_flag")),
            "has_privilege_escalation": int(any_flag("privilege_escalation_flag")),

            "time_of_day": int(time_of_day),
            "sources_count": len(set(sources)),

            "max_anomaly_score": max(
                (e.get("score", 0) for e in events),
                default=0
            )
        }

        return [feature_dict[f] for f in FEATURE_ORDER]


# ============================================================
# INTENT PREDICTOR
# ============================================================

class IntentPredictor:

    def __init__(self,
                 model_path: str = MODEL_PATH,
                 encoder_path: str = ENCODER_PATH):

        self.model = self._load(model_path, "Intent model")
        self.encoder = self._load(encoder_path, "Label encoder")
        self.feature_builder = IntentFeatureBuilder()

    # --------------------------------------------------------

    def _load(self, path: str, name: str):
        if not os.path.exists(path):
            raise FileNotFoundError(f"{name} not found at {path}")
        return joblib.load(path)

    # --------------------------------------------------------

    def predict(self, incident: Dict) -> Dict:

        features = self.feature_builder.build_features(incident)

        features_df = pd.DataFrame([features], columns=FEATURE_ORDER)
        probs = self.model.predict_proba(features_df)[0]
        class_indices = self.model.classes_

        sorted_idx = np.argsort(probs)[::-1]

        primary_class = class_indices[sorted_idx[0]]
        secondary_class = class_indices[sorted_idx[1]]

        # 🔥 Proper decoding
        primary_label = self.encoder.inverse_transform([primary_class])[0]
        secondary_label = self.encoder.inverse_transform([secondary_class])[0]

        return {
            "primary_intent": primary_label,
            "primary_confidence": round(float(probs[sorted_idx[0]]), 3),
            "secondary_intent": secondary_label,
            "secondary_confidence": round(float(probs[sorted_idx[1]]), 3)
        }