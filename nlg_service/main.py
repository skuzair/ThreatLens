"""
NLG Service — Kafka Consumer
=============================
Reads from: correlated-incidents
Writes to:  nlg-explanations

Accepts the full enriched incident format:
    {incident, shap_explanations, sandbox_result, dna_deviations, attack_progression}
"""

import sys
import json
from pathlib import Path

# Ensure sibling modules resolve regardless of working directory
sys.path.insert(0, str(Path(__file__).resolve().parent))

from kafka_consumer      import create_consumer
from kafka_producer      import create_producer
from explanation_builder import ExplanationBuilder
from recommendation_engine import RecommendationEngine
from incident_validator  import IncidentValidator
from safe_extract        import safe_get


def build_output(incident: dict, builder: ExplanationBuilder,
                 recommender: RecommendationEngine) -> dict:

    shap_values = incident.get("shap_explanations", [])
    sections    = []

    # ── Per-source sections ───────────────────────────────────────────────
    if "camera_event" in incident:
        text, factors = builder.build_camera_section(
            incident["camera_event"], shap_values)
        sections.append({
            "source":      "Camera",
            "icon":        "camera",
            "score":       incident["camera_event"].get("score", 0),
            "text":        text,
            "key_factors": factors,
        })

    if "logs_event" in incident:
        text, factors = builder.build_logs_section(
            incident["logs_event"], shap_values)
        sections.append({
            "source":      "System Logs",
            "icon":        "terminal",
            "score":       incident["logs_event"].get("score", 0),
            "text":        text,
            "key_factors": factors,
        })

    if "file_event" in incident:
        text, factors = builder.build_file_section(
            incident["file_event"], shap_values)
        sections.append({
            "source":      "File Integrity",
            "icon":        "file-warning",
            "score":       incident["file_event"].get("score", 0),
            "text":        text,
            "key_factors": factors,
        })

    if "network_event" in incident:
        text, factors = builder.build_network_section(
            incident["network_event"], shap_values)
        sections.append({
            "source":      "Network",
            "icon":        "network",
            "score":       incident["network_event"].get("score", 0),
            "text":        text,
            "key_factors": factors,
        })

    severity = incident.get("severity", "UNKNOWN")
    risk     = incident.get("risk_score", 0)

    output = {
        "incident_id":           incident["incident_id"],
        "risk_score":            risk,
        "severity":              severity,
        "intent":                incident["intent"],
        "summary":               (
            f"{severity}: Coordinated {incident['intent'].lower().replace('_',' ')} "
            f"attack detected. Risk score {risk}/100."
        ),
        "sections":              sections,
        "correlation_statement": builder.build_correlation_statement(incident),
        "mitre_statement":       builder.build_mitre_statement(incident["intent"]),
        "sandbox_statement":     builder.build_sandbox_section(
                                     incident.get("sandbox_result")),
        "dna_statement":         builder.build_dna_section(
                                     incident.get("dna_deviations")),
        "prediction_statement":  builder.build_prediction_statement(
                                     incident, shap_values),
        "recommended_actions":   recommender.generate(incident),
        "shap_top_features":     shap_values[:5],
    }

    return output


def run():
    builder    = ExplanationBuilder()
    recommender = RecommendationEngine()
    validator  = IncidentValidator()
    consumer   = create_consumer()
    producer   = create_producer()

    print("[NLG] Service started. Listening on 'correlated-incidents'...")

    for message in consumer:
        incident = message.value
        if incident is None:
            continue

        is_valid, missing = validator.validate(incident)
        if not is_valid:
            producer.send("nlg-explanations", {
                "incident_id": incident.get("incident_id", "UNKNOWN"),
                "error":       f"Missing required fields: {missing}",
            })
            producer.flush()
            continue

        try:
            output = build_output(incident, builder, recommender)
            producer.send("nlg-explanations", output)
            producer.flush()
            print(f"[NLG] Published explanation for {incident['incident_id']}")

        except Exception as exc:
            producer.send("nlg-explanations", {
                "incident_id": incident.get("incident_id", "UNKNOWN"),
                "error":       str(exc),
            })
            producer.flush()


if __name__ == "__main__":
    run()