"""
infer.py
─────────
File anomaly inference using trained Isolation Forest.
Loads model from file_model/models/
"""

import joblib
import numpy as np
import pandas as pd
from pathlib import Path

BASE_DIR    = Path(__file__).resolve().parent
MODEL_DIR   = BASE_DIR / "models"
MODEL_PATH  = MODEL_DIR / "isolation_forest.pkl"
SCALER_PATH = MODEL_DIR / "scaler.pkl"

FEATURE_COLUMNS = [
    "modifications_per_minute",
    "unique_processes_writing",
    "extension_change_rate",
    "file_size_change_ratio",
    "sensitive_dir_access_rate",
    "hour_of_day"
]

# Rule-based override thresholds — these ALWAYS fire regardless of IF score
RANSOMWARE_RULES = {
    "mass_modification":    ("modifications_per_minute",  50),
    "bulk_extension_change":("extension_change_rate",     0.5),
    "sensitive_dir_access": ("sensitive_dir_access_rate", 0.4),
}


class FileAnomalyPredictor:

    def __init__(self):
        if not MODEL_PATH.exists():
            raise FileNotFoundError(
                f"Model not found: {MODEL_PATH}\n"
                "Run: python file_model/train_isolation_forest.py"
            )
        self.model  = joblib.load(MODEL_PATH)
        self.scaler = joblib.load(SCALER_PATH)

        self._score_history = []
        self._warmup        = 10   # reduced so demo calibrates quickly

    def predict(self, feature_vector: list) -> dict:
        df     = pd.DataFrame([feature_vector], columns=FEATURE_COLUMNS)
        scaled = self.scaler.transform(df)

        decision_score = float(self.model.decision_function(scaled)[0])
        prediction     = self.model.predict(scaled)[0]

        # ── Rule-based score (always works, no warmup needed) ──────────────
        rule_score = self._rule_score(feature_vector)

        # ── ML score ──────────────────────────────────────────────────────
        ml_score = self._normalize(decision_score)

        # ── Final: take the higher of rule-based or ML score ──────────────
        # This ensures obvious ransomware patterns always score high
        # even before the ML warmup completes
        final_score = max(rule_score, ml_score)

        return {
            "is_anomaly":         prediction == -1 or final_score >= 40,
            "anomaly_score":      round(final_score, 2),
            "raw_decision_score": decision_score,
            "rule_score":         round(rule_score, 2),
            "ml_score":           round(ml_score, 2),
        }

    def _rule_score(self, features: list) -> float:
        """
        Direct rule-based scoring — no warmup needed.
        Maps feature values to 0-100 based on how extreme they are.
        """
        mpm  = features[0]   # modifications_per_minute
        ecr  = features[2]   # extension_change_rate
        sdar = features[4]   # sensitive_dir_access_rate
        hour = features[5]   # hour_of_day

        score = 0.0

        # Modifications per minute: normal ~2, ransomware ~150
        # Scale: 0→0, 10→20, 50→60, 100→85, 150+→100
        if mpm > 0:
            score = max(score, min(100, (mpm / 150) * 100))

        # Extension change rate: normal ~0.01, ransomware ~0.8
        # Scale: 0→0, 0.1→20, 0.5→70, 0.8→100
        if ecr > 0:
            score = max(score, min(100, ecr * 120))

        # Sensitive directory access: normal ~0.03, attack ~0.7
        if sdar > 0.1:
            score = max(score, min(100, sdar * 100))

        # After hours penalty (1-5 AM)
        if 1 <= hour <= 5:
            score = min(100, score * 1.3)

        return float(score)

    def _normalize(self, decision_score: float) -> float:
        """
        Dynamic percentile normalization.
        Falls back to sigmoid mapping pre-warmup.
        """
        raw = -decision_score   # flip: more negative = more anomalous
        self._score_history.append(raw)

        if len(self._score_history) < self._warmup:
            # Sigmoid-like mapping that actually spreads scores well
            # decision_score=0 (boundary) → 50
            # decision_score=-0.1         → ~67
            # decision_score=-0.3         → ~88
            # decision_score=+0.2 (normal)→ ~27
            sigmoid = 1 / (1 + np.exp(-raw * 10))
            return float(np.clip(sigmoid * 100, 0, 100))

        # Post-warmup: percentile normalization
        recent = self._score_history[-500:]
        p5  = float(np.percentile(recent, 5))
        p95 = float(np.percentile(recent, 95))
        if abs(p95 - p5) < 1e-9:
            return 50.0
        return float(np.clip((raw - p5) / (p95 - p5) * 100, 0, 100))


if __name__ == "__main__":
    predictor = FileAnomalyPredictor()

    print("\n========= NORMAL FILE ACTIVITY =========\n")
    for s in [[1,1,0.01,1.02,0.03,10],[3,2,0.02,0.98,0.05,14],[2,1,0.00,1.00,0.02,16]]:
        r = predictor.predict(s)
        print(f"  {s}")
        print(f"  → score={r['anomaly_score']:6.2f}  rule={r['rule_score']:6.2f}  ml={r['ml_score']:6.2f}  anomaly={r['is_anomaly']}\n")

    print("========= SUSPICIOUS ACTIVITY =========\n")
    for s in [[15,2,0.15,0.85,0.20,6],[25,2,0.25,0.75,0.30,4]]:
        r = predictor.predict(s)
        print(f"  {s}")
        print(f"  → score={r['anomaly_score']:6.2f}  rule={r['rule_score']:6.2f}  ml={r['ml_score']:6.2f}  anomaly={r['is_anomaly']}\n")

    print("========= RANSOMWARE-LIKE ACTIVITY =========\n")
    for s in [[140,1,0.80,0.40,0.70,2],[165,1,0.90,0.30,0.85,1]]:
        r = predictor.predict(s)
        print(f"  {s}")
        print(f"  → score={r['anomaly_score']:6.2f}  rule={r['rule_score']:6.2f}  ml={r['ml_score']:6.2f}  anomaly={r['is_anomaly']}\n")