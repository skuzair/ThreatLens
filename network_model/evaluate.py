import pandas as pd
from infer import NetworkInference

DATA_PATH = "data/processed/network_features.csv"


def evaluate():

    df = pd.read_csv(DATA_PATH)

    if "label" in df.columns:
        y_true = df["label"].values
        X = df.drop(columns=["label"]).values
    else:
        y_true = None
        X = df.values

    model = NetworkInference()

    scores = []
    for row in X:
        result = model.predict(row)
        scores.append(result["final_anomaly_score"])

    print("Evaluation complete.")
    print(f"Average anomaly score: {sum(scores)/len(scores):.2f}")


if __name__ == "__main__":
    evaluate()
