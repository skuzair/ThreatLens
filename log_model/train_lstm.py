"""
train_lstm.py
──────────────
Run from ThreatLens root:
    python log_model/train_lstm.py
"""

import os
import torch
import torch.nn as nn
import torch.optim as optim
import pandas as pd
import numpy as np
from pathlib import Path
from torch.utils.data import DataLoader, TensorDataset
from sklearn.model_selection import train_test_split

BASE_DIR    = Path(__file__).resolve().parent
DATA_PATH   = BASE_DIR / "data" / "log_features.csv"
MODEL_DIR   = BASE_DIR / "models"
MODEL_PATH  = MODEL_DIR / "lstm.pt"

DEVICE          = torch.device("cuda" if torch.cuda.is_available() else "cpu")
SEQUENCE_LENGTH = 10


class LogLSTM(nn.Module):
    def __init__(self, input_dim=15):
        super().__init__()
        self.lstm1    = nn.LSTM(input_dim, 64, batch_first=True)
        self.dropout1 = nn.Dropout(0.2)
        self.lstm2    = nn.LSTM(64, 32, batch_first=True)
        self.dropout2 = nn.Dropout(0.2)
        self.fc1      = nn.Linear(32, 16)
        self.relu     = nn.ReLU()
        self.output   = nn.Linear(16, 1)
        self.sigmoid  = nn.Sigmoid()

    def forward(self, x):
        x, _ = self.lstm1(x)
        x     = self.dropout1(x)
        x, _ = self.lstm2(x)
        x     = self.dropout2(x)
        x     = x[:, -1, :]
        x     = self.relu(self.fc1(x))
        return self.sigmoid(self.output(x))


def build_sequences(X, y, seq_len=10):
    seqs, labels = [], []
    for i in range(len(X) - seq_len):
        seqs.append(X[i:i + seq_len])
        labels.append(y[i + seq_len - 1])
    return np.array(seqs), np.array(labels)


def train_lstm():
    if not DATA_PATH.exists():
        print(f"❌ Data not found: {DATA_PATH}")
        return

    print(f"Loading data: {DATA_PATH}")
    df   = pd.read_csv(DATA_PATH)
    y    = df["label"].values
    X    = df.drop(columns=["label"]).values.astype(np.float32)

    X_seq, y_seq = build_sequences(X, y, SEQUENCE_LENGTH)
    X_train, X_val, y_train, y_val = train_test_split(X_seq, y_seq, test_size=0.2, random_state=42)

    loader = DataLoader(
        TensorDataset(
            torch.tensor(X_train),
            torch.tensor(y_train).float().unsqueeze(1)
        ),
        batch_size=64, shuffle=True
    )

    model     = LogLSTM(input_dim=X.shape[1]).to(DEVICE)
    criterion = nn.BCELoss()
    optimizer = optim.Adam(model.parameters(), lr=0.001)

    print(f"Training LSTM on {DEVICE}...")
    for epoch in range(30):
        model.train()
        total_loss = 0
        for xb, yb in loader:
            xb, yb = xb.to(DEVICE), yb.to(DEVICE)
            loss = criterion(model(xb), yb)
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
            total_loss += loss.item()
        print(f"  Epoch {epoch+1:02d}/30 | Loss: {total_loss/len(loader):.6f}")

    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    torch.save(model.state_dict(), MODEL_PATH)
    print(f"✅ LSTM saved: {MODEL_PATH}")


if __name__ == "__main__":
    train_lstm()