"""
Synthetic Incident Generator for Intent Classifier

Generates structured correlated incidents for 6 attack types:

1. ransomware
2. data_exfiltration
3. insider_threat
4. apt_infiltration
5. ddos
6. reconnaissance

IMPORTANT:
Uses IntentFeatureBuilder from correlation_engine.intent_predictor
to guarantee feature consistency WITHOUT loading model.
"""

import os
import random
import pandas as pd

from correlation_engine.intent_predictor import (
    IntentFeatureBuilder,
    FEATURE_ORDER
)

OUTPUT_PATH = "data/processed/intent_training_data.csv"

ATTACK_TYPES = [
    "ransomware",
    "data_exfiltration",
    "insider_threat",
    "apt_infiltration",
    "ddos",
    "reconnaissance"
]


# ============================================================
# Incident Templates
# ============================================================

def generate_incident(attack_type: str) -> dict:

    time_of_day = random.randint(0, 23)

    if attack_type == "ransomware":
        return {
            "sources_involved": ["file", "logs"],
            "correlated_events": [
                {
                    "source": "file",
                    "score": random.randint(85, 100),
                    "ransomware_pattern": True
                },
                {
                    "source": "logs",
                    "score": random.randint(60, 90),
                    "privilege_escalation_flag": True
                }
            ],
            "time_of_day": time_of_day
        }

    elif attack_type == "data_exfiltration":
        return {
            "sources_involved": ["network"],
            "correlated_events": [
                {
                    "source": "network",
                    "score": random.randint(80, 100),
                    "large_transfer_flag": True
                }
            ],
            "time_of_day": time_of_day
        }

    elif attack_type == "insider_threat":
        return {
            "sources_involved": ["logs"],
            "correlated_events": [
                {
                    "source": "logs",
                    "score": random.randint(70, 95),
                    "privilege_escalation_flag": True
                }
            ],
            "time_of_day": time_of_day
        }

    elif attack_type == "apt_infiltration":
        return {
            "sources_involved": ["camera", "logs", "network"],
            "correlated_events": [
                {
                    "source": "camera",
                    "score": random.randint(70, 90)
                },
                {
                    "source": "logs",
                    "score": random.randint(65, 85),
                    "privilege_escalation_flag": True
                },
                {
                    "source": "network",
                    "score": random.randint(60, 80)
                }
            ],
            "time_of_day": time_of_day
        }

    elif attack_type == "ddos":
        return {
            "sources_involved": ["network"],
            "correlated_events": [
                {
                    "source": "network",
                    "score": random.randint(85, 100)
                }
            ],
            "time_of_day": time_of_day
        }

    elif attack_type == "reconnaissance":
        return {
            "sources_involved": ["network"],
            "correlated_events": [
                {
                    "source": "network",
                    "score": random.randint(50, 70)
                }
            ],
            "time_of_day": time_of_day
        }

    else:
        raise ValueError("Unknown attack type")


# ============================================================
# Noise Injection
# ============================================================

def inject_noise(incident: dict, noise_probability=0.1):

    if random.random() < noise_probability:
        incident["sources_involved"].append("rf")
        incident["correlated_events"].append({
            "source": "rf",
            "score": random.randint(30, 50)
        })

    for event in incident["correlated_events"]:
        event["score"] = max(
            0,
            min(100, event["score"] + random.randint(-5, 5))
        )

    return incident


# ============================================================
# Dataset Generation
# ============================================================

def generate_dataset(samples_per_class=1500):

    rows = []
    labels = []

    for attack in ATTACK_TYPES:
        for _ in range(samples_per_class):

            incident = generate_incident(attack)
            incident = inject_noise(incident)

            features = IntentFeatureBuilder.build_features(incident)

            rows.append(features)
            labels.append(attack)

    df = pd.DataFrame(rows, columns=FEATURE_ORDER)
    df["label"] = labels

    os.makedirs("data/processed", exist_ok=True)
    df.to_csv(OUTPUT_PATH, index=False)

    print(f"Dataset saved to {OUTPUT_PATH}")
    print(f"Total samples: {len(df)}")
    print("Class distribution:")
    print(df["label"].value_counts())


# ============================================================
# Entry Point
# ============================================================

if __name__ == "__main__":
    generate_dataset(samples_per_class=1500)
