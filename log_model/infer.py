"""
infer.py
─────────
Log anomaly inference using RF + LSTM ensemble.
Loads models from log_model/models/
"""

import torch
import joblib
import numpy as np
from pathlib import Path

BASE_DIR    = Path(__file__).resolve().parent
MODEL_DIR   = BASE_DIR / "models"
RF_PATH     = MODEL_DIR / "random_forest.pkl"
LSTM_PATH   = MODEL_DIR / "lstm.pt"

DEVICE          = torch.device("cuda" if torch.cuda.is_available() else "cpu")
SEQUENCE_LENGTH = 10


class LogLSTM(torch.nn.Module):
    def __init__(self, input_dim=15):
        super().__init__()
        self.lstm1    = torch.nn.LSTM(input_dim, 64, batch_first=True)
        self.dropout1 = torch.nn.Dropout(0.2)
        self.lstm2    = torch.nn.LSTM(64, 32, batch_first=True)
        self.dropout2 = torch.nn.Dropout(0.2)
        self.fc1      = torch.nn.Linear(32, 16)
        self.relu     = torch.nn.ReLU()
        self.output   = torch.nn.Linear(16, 1)
        self.sigmoid  = torch.nn.Sigmoid()

    def forward(self, x):
        x, _ = self.lstm1(x)
        x     = self.dropout1(x)
        x, _ = self.lstm2(x)
        x     = self.dropout2(x)
        x     = x[:, -1, :]
        x     = self.relu(self.fc1(x))
        return self.sigmoid(self.output(x))


class LogInference:

    def __init__(self):
        if not RF_PATH.exists():
            raise FileNotFoundError(f"RF model not found: {RF_PATH}\nRun: python train_random_forest.py")
        if not LSTM_PATH.exists():
            raise FileNotFoundError(f"LSTM not found: {LSTM_PATH}\nRun: python train_lstm.py")

        self.rf   = joblib.load(RF_PATH)
        self.lstm = LogLSTM()
        self.lstm.load_state_dict(torch.load(LSTM_PATH, map_location=DEVICE, weights_only=True))
        self.lstm.to(DEVICE)
        self.lstm.eval()

    def predict(self, feature_vector, sequence_buffer):
        # ── Random Forest ──────────────────────────────────────────────────
        rf_proba = self.rf.predict_proba([feature_vector])[0]
        
        # Handle case where model only learned one class
        if len(rf_proba) == 1:
            # Check which class the model learned
            learned_class = self.rf.classes_[0]
            if learned_class == 1:
                # Model only saw anomalies, assume everything is anomaly
                rf_prob = 1.0
            else:
                # Model only saw normal, assume everything is normal
                rf_prob = 0.0
        else:
            # Normal case: get probability of anomaly class (class 1)
            rf_prob = rf_proba[1] if 1 in self.rf.classes_ else rf_proba[0]
        
        rf_score = float(np.clip(rf_prob * 100, 5, 95))

        # ── LSTM sequence ──────────────────────────────────────────────────
        sequence_buffer.append(feature_vector)

        if len(sequence_buffer) < SEQUENCE_LENGTH:
            lstm_score = 10.0
        else:
            seq    = np.array(sequence_buffer[-SEQUENCE_LENGTH:], dtype=np.float32)
            tensor = torch.tensor(seq).unsqueeze(0).to(DEVICE)
            with torch.no_grad():
                lstm_score = float(np.clip(self.lstm(tensor).item() * 100, 5, 95))

        # ── Ensemble ───────────────────────────────────────────────────────
        final = (0.4 * rf_score) + (0.6 * lstm_score)

        return {
            "rf_score":           round(rf_score, 2),
            "lstm_score":         round(lstm_score, 2),
            "final_anomaly_score": round(final, 2)
        }


if __name__ == "__main__":
    # Initialize the inference engine
    print("Loading models...")
    inference = LogInference()
    
    # Check what classes the RF learned
    print(f"Random Forest learned classes: {inference.rf.classes_}")
    
    # Create a sequence buffer to track history
    sequence_buffer = []
    
    # Test with some sample feature vectors
    # (15 features matching your log_features.csv structure)
    test_cases = [
        {
            "name": "Normal log",
            "features": [0.5, 12.0, 3.0, 0.0, 0.0, 1.0, 0.1, 0.0, 100.0, 1.0, 1.0, 0.5, 0.05, 0.0, 300.0]
        },
        {
            "name": "Potential anomaly - high risk",
            "features": [0.8, 2.0, 6.0, 5.0, 1.0, 3.0, 0.9, 1.0, 10.0, 0.0, 0.0, 0.2, 0.8, 3.0, 50.0]
        },
        {
            "name": "Potential anomaly - failed logins",
            "features": [0.3, 23.0, 5.0, 10.0, 1.0, 2.0, 0.6, 0.0, 5.0, 1.0, 1.0, 0.3, 0.7, 8.0, 20.0]
        }
    ]
    
    print("\n" + "=" * 70)
    print("LOG ANOMALY DETECTION - INFERENCE TEST")
    print("=" * 70)
    
    for i, test in enumerate(test_cases, 1):
        result = inference.predict(test["features"], sequence_buffer)
        
        print(f"\n[Test {i}] {test['name']}")
        print(f"  RF Score:    {result['rf_score']}%")
        print(f"  LSTM Score:  {result['lstm_score']}%")
        print(f"  Final Score: {result['final_anomaly_score']}%")
        
        # Interpret the result
        score = result['final_anomaly_score']
        if score < 30:
            status = "✓ NORMAL"
        elif score < 60:
            status = "⚠ SUSPICIOUS"
        else:
            status = "✗ ANOMALY"
        print(f"  Status: {status}")
    
    print("\n" + "=" * 70)
    print("\nNote: If RF score is always the same, retrain with:")
    print("  python generate_synthetic_logs.py")
    print("  python train_random_forest.py")
    print("  python train_lstm.py")