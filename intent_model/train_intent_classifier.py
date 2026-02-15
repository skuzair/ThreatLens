"""
Train RandomForest Intent Classifier

Responsibilities:
- Load incident-level dataset
- Validate feature schema
- Encode labels
- Perform stratified train/test split
- Cross-validation scoring
- Save trained model + encoder
- Output performance metrics
"""

import os
import joblib
import pandas as pd
import numpy as np

from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import classification_report, confusion_matrix


# ============================================================
# CONFIG
# ============================================================

DATA_PATH = "C:/Users/Samagra/Documents/ThreatLens/data/processed/intent_training_data.csv"
MODEL_DIR = "models/"
MODEL_PATH = os.path.join(MODEL_DIR, "random_forest.pkl")
ENCODER_PATH = os.path.join(MODEL_DIR, "label_encoder.pkl")
METADATA_PATH = os.path.join(MODEL_DIR, "training_metadata.pkl")

RANDOM_STATE = 42


# ============================================================
# Training Function
# ============================================================

def train():

    # --------------------------------------------------------
    # 1️⃣ Load Dataset
    # --------------------------------------------------------
    if not os.path.exists(DATA_PATH):
        raise FileNotFoundError(f"Dataset not found at {DATA_PATH}")

    df = pd.read_csv(DATA_PATH)

    if "label" not in df.columns:
        raise ValueError("Dataset must contain 'label' column")

    X = df.drop("label", axis=1)
    y = df["label"]

    print(f"\nDataset loaded: {len(df)} samples")
    print("Class distribution:")
    print(y.value_counts())
    print()

    # --------------------------------------------------------
    # 2️⃣ Encode Labels
    # --------------------------------------------------------
    label_encoder = LabelEncoder()
    y_encoded = label_encoder.fit_transform(y)

    # --------------------------------------------------------
    # 3️⃣ Train/Test Split (Stratified)
    # --------------------------------------------------------
    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y_encoded,
        test_size=0.2,
        stratify=y_encoded,
        random_state=RANDOM_STATE
    )

    # --------------------------------------------------------
    # 4️⃣ Model Definition
    # --------------------------------------------------------
    model = RandomForestClassifier(
        n_estimators=300,
        max_depth=15,
        min_samples_split=2,
        min_samples_leaf=1,
        class_weight="balanced",
        random_state=RANDOM_STATE,
        n_jobs=-1
    )

    # --------------------------------------------------------
    # 5️⃣ Cross Validation
    # --------------------------------------------------------
    cv_scores = cross_val_score(
        model,
        X_train,
        y_train,
        cv=5,
        scoring="accuracy",
        n_jobs=-1
    )

    print("Cross-validation accuracy:")
    print(f"Mean: {cv_scores.mean():.4f}")
    print(f"Std:  {cv_scores.std():.4f}")
    print()

    # --------------------------------------------------------
    # 6️⃣ Train Model
    # --------------------------------------------------------
    model.fit(X_train, y_train)

    # --------------------------------------------------------
    # 7️⃣ Evaluation
    # --------------------------------------------------------
    y_pred = model.predict(X_test)

    print("Test Classification Report:")
    print(
        classification_report(
            y_test,
            y_pred,
            target_names=label_encoder.classes_
        )
    )

    print("Confusion Matrix:")
    print(confusion_matrix(y_test, y_pred))
    print()

    test_accuracy = np.mean(y_pred == y_test)
    print(f"Final Test Accuracy: {test_accuracy:.4f}")

    # --------------------------------------------------------
    # 8️⃣ Save Artifacts
    # --------------------------------------------------------
    os.makedirs(MODEL_DIR, exist_ok=True)

    joblib.dump(model, MODEL_PATH)
    joblib.dump(label_encoder, ENCODER_PATH)

    metadata = {
        "feature_count": X.shape[1],
        "feature_names": list(X.columns),
        "classes": list(label_encoder.classes_),
        "cv_mean_accuracy": float(cv_scores.mean()),
        "cv_std": float(cv_scores.std()),
        "test_accuracy": float(test_accuracy)
    }

    joblib.dump(metadata, METADATA_PATH)

    print("\nModel saved to:", MODEL_PATH)
    print("Label encoder saved to:", ENCODER_PATH)
    print("Metadata saved to:", METADATA_PATH)


# ============================================================
# Entry Point
# ============================================================

if __name__ == "__main__":
    train()
