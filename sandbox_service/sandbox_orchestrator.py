"""
Sandbox Orchestrator
====================
Main pipeline: Docker execution → classification → screenshots → result.
"""

from pathlib import Path

from docker_runner      import run_sandbox
from behavior_classifier import classify_sandbox_verdict
from ioc_extractor      import extract_iocs
from screenshot_loop    import capture_screenshots
from result_builder     import build_result


def execute_sandbox(input_data: dict) -> dict:
    """
    Full detonation pipeline for one sandbox request.

    input_data keys:
        incident_id  – str
        file_hash    – str
        attack_type  – str  (optional, defaults to "ransomware")
    """
    incident_id = input_data["incident_id"]
    attack_type = input_data.get("attack_type", "ransomware")
    file_hash   = input_data.get("file_hash", "sha256:unknown")

    print(f"\n[Sandbox] Starting detonation: {incident_id} ({attack_type})")

    # 1. Execute in Docker
    execution = run_sandbox(incident_id, attack_type)
    output_lines   = execution["output_lines"]
    behavioral_log = execution["behavioral_log"]

    # 2. Classify behaviour
    verdict, score, indicators = classify_sandbox_verdict(behavioral_log)
    print(f"  [Classifier] Verdict: {verdict}  Score: {score}  "
          f"Indicators: {indicators}")

    # 3. Extract IOCs
    iocs = extract_iocs(behavioral_log, file_hash)

    # 4. Generate PIL screenshots
    screenshots = capture_screenshots(
        incident_id  = incident_id,
        attack_type  = attack_type,
        output_lines = output_lines,
        behavioral_log = behavioral_log,
        verdict      = verdict,
        confidence   = score,
    )

    # 5. Build result
    result = build_result(
        input_data   = input_data,
        verdict      = verdict,
        score        = score,
        log          = behavioral_log,
        iocs         = iocs,
        screenshots  = screenshots,
    )

    # Enrich with execution metadata
    result["docker_used"]     = execution["docker_used"]
    result["exit_code"]       = execution["exit_code"]
    result["duration_sec"]    = execution["duration_sec"]
    result["output_lines"]    = output_lines
    result["indicators"]      = indicators
    result["screenshot_count"] = len(screenshots)

    print(f"[Sandbox] ✅ Complete — {verdict} ({score}) | "
          f"{len(screenshots)} frames | Docker={execution['docker_used']}")
    return result