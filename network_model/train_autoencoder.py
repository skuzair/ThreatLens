import torch
import torch.nn as nn
import torch.optim as optim
import pandas as pd
import numpy as np
import os
import joblib
from sklearn.model_selection import train_test_split
from torch.utils.data import DataLoader, TensorDataset
from model_architecture import NetworkAutoencoder

DATA_PATH = r"C:\Users\Samagra\Documents\ThreatLens\data\processed\network_features.csv"
MODEL_DIR = r"C:\Users\Samagra\Documents\ThreatLens\network_model\models\network"

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

def train_autoencoder():

    df = pd.read_csv(DATA_PATH)
    X = df.values.astype(np.float32)

    os.makedirs(MODEL_DIR, exist_ok=True)

    X_train, _ = train_test_split(X, test_size=0.2, random_state=42)

    train_loader = DataLoader(
        TensorDataset(torch.tensor(X_train)),
        batch_size=256,
        shuffle=True
    )

    model = NetworkAutoencoder(input_dim=X.shape[1]).to(DEVICE)

    criterion = nn.MSELoss()
    optimizer = optim.Adam(model.parameters(), lr=0.001)

    for epoch in range(30):
        total_loss = 0
        for batch in train_loader:
            inputs = batch[0].to(DEVICE)
            outputs = model(inputs)
            loss = criterion(outputs, inputs)

            optimizer.zero_grad()
            loss.backward()
            optimizer.step()

            total_loss += loss.item()

        print(f"Epoch {epoch+1} Loss: {total_loss/len(train_loader):.6f}")

    torch.save(model.state_dict(), f"{MODEL_DIR}/autoencoder.pt")
    print("Autoencoder saved ✔")

if __name__ == "__main__":
    train_autoencoder()
