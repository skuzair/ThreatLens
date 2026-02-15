"""
Intent Model Evaluation Script

Responsibilities:
- Load trained model + encoder
- Load dataset
- Evaluate performance
- Print detailed metrics
- Show confusion matrix
- Show feature importance
- Save evaluation report
"""

import os
import joblib
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    accuracy_score
)

# ============================================================
# CONFIG
# ============================================================

DATA_PATH = "data/processed/intent_training_data.csv"
MODEL_DIR = "models/intent"
MODEL_PATH = os.path.join(MODEL_DIR, "random_forest.pkl")
ENCODER_PATH = os.path.join(MODEL_DIR, "label_encoder.pkl")
METADATA_PATH = os.path.join(MODEL_DIR, "training_metadata.pkl")

REPORT_PATH = os.path.join(MODEL_DIR, "evaluation_report.txt")


# ============================================================
# Evaluation
# ============================================================

def evaluate():

    # --------------------------------------------------------
    # Load artifacts
    # --------------------------------------------------------
    model = joblib.load(MODEL_PATH)
    encoder = joblib.load(ENCODER_PATH)
    metadata = joblib.load(METADATA_PATH)

    df = pd.read_csv(DATA_PATH)

    X = df.drop("label", axis=1)
    y = df["label"]

    y_encoded = encoder.transform(y)

    # --------------------------------------------------------
    # Predictions
    # --------------------------------------------------------
    y_pred = model.predict(X)

    accuracy = accuracy_score(y_encoded, y_pred)

    report = classification_report(
        y_encoded,
        y_pred,
        target_names=encoder.classes_,
        digits=4
    )

    cm = confusion_matrix(y_encoded, y_pred)

    # --------------------------------------------------------
    # Print Metrics
    # --------------------------------------------------------
    print("\n===== MODEL EVALUATION =====")
    print(f"Accuracy: {accuracy:.4f}")
    print("\nClassification Report:\n")
    print(report)

    print("Confusion Matrix:")
    print(cm)

    # --------------------------------------------------------
    # Feature Importance
    # --------------------------------------------------------
    feature_importances = model.feature_importances_
    feature_names = metadata["feature_names"]

    importance_df = pd.DataFrame({
        "feature": feature_names,
        "importance": feature_importances
    }).sort_values(by="importance", ascending=False)

    print("\nTop Feature Importances:")
    print(importance_df)

    # --------------------------------------------------------
    # Save Report
    # --------------------------------------------------------
    with open(REPORT_PATH, "w") as f:
        f.write("Intent Model Evaluation Report\n")
        f.write("=" * 40 + "\n\n")
        f.write(f"Accuracy: {accuracy:.4f}\n\n")
        f.write("Classification Report:\n")
        f.write(report)
        f.write("\nConfusion Matrix:\n")
        f.write(str(cm))
        f.write("\n\nFeature Importances:\n")
        f.write(str(importance_df))

    print(f"\nEvaluation report saved to {REPORT_PATH}")

    # --------------------------------------------------------
    # Optional: Plot Confusion Matrix
    # --------------------------------------------------------
    plot_confusion_matrix(cm, encoder.classes_)

    # --------------------------------------------------------
    # Optional: Plot Feature Importance
    # --------------------------------------------------------
    plot_feature_importance(importance_df)


# ============================================================
# Visualization
# ============================================================

def plot_confusion_matrix(cm, labels):

    plt.figure()
    plt.imshow(cm)
    plt.title("Confusion Matrix")
    plt.xticks(range(len(labels)), labels, rotation=45)
    plt.yticks(range(len(labels)), labels)

    for i in range(len(labels)):
        for j in range(len(labels)):
            plt.text(j, i, cm[i, j],
                     ha="center", va="center")

    plt.xlabel("Predicted")
    plt.ylabel("True")
    plt.tight_layout()
    plt.show()


def plot_feature_importance(importance_df):

    plt.figure()
    plt.bar(importance_df["feature"], importance_df["importance"])
    plt.xticks(rotation=45)
    plt.title("Feature Importance")
    plt.tight_layout()
    plt.show()


# ============================================================
# Entry Point
# ============================================================

if __name__ == "__main__":
    evaluate()
