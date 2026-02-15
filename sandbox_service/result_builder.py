"""
Result Builder
==============
Assembles the final sandbox result dict from all pipeline components.
"""

from datetime import datetime


def build_result(
    input_data: dict,
    verdict: str,
    score: int,
    log: dict,
    iocs: dict,
    screenshots: list,
) -> dict:
    return {
        "incident_id":           input_data["incident_id"],
        "file_hash":             input_data.get("file_hash", "sha256:unknown"),
        "attack_type":           input_data.get("attack_type", "unknown"),
        "verdict":               verdict,
        "confidence_score":      score,
        "detonation_timestamp":  datetime.utcnow().isoformat() + "Z",
        "behavioral_summary":    log,
        "extracted_iocs":        iocs,
        "screenshot_sequence":   screenshots,
    }