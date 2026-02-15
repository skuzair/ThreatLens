"""
Screenshot Loop
===============
Generates a sequence of PIL frames that visually represent the sandbox
detonation progressing over time. Uses real terminal output captured
from Docker to populate the frames.
"""

from datetime import datetime
from pathlib import Path

from config import EVIDENCE_ROOT, NUM_FRAMES
from screenshot_engine import generate_frame


# MITRE ATT&CK mappings per attack type
MITRE_MAP = {
    "ransomware": [
        ("Discovery",    "T1083"),
        ("DefenseEva",   "T1490"),
        ("ServiceStop",  "T1489"),
        ("Encryption",   "T1486"),
        ("C2",           "T1071"),
    ],
    "data_exfiltration": [
        ("ValidAccts",   "T1078"),
        ("Collection",   "T1560"),
        ("Exfil-C2",     "T1041"),
        ("DNS-Tunnel",   "T1048"),
        ("LogClear",     "T1070"),
    ],
}


def capture_screenshots(
    incident_id: str,
    attack_type: str,
    output_lines: list,
    behavioral_log: dict,
    verdict: str,
    confidence: int,
) -> list:
    """
    Generate NUM_FRAMES annotated sandbox frames.

    Parameters
    ----------
    incident_id    : e.g. "INC-TEST-RANSOMWARE"
    attack_type    : "ransomware" | "data_exfiltration"
    output_lines   : terminal lines captured from Docker
    behavioral_log : structured result dict from the attack script
    verdict        : "MALICIOUS" | "SUSPICIOUS" | "BENIGN"
    confidence     : 0–100

    Returns list of absolute path strings.
    """
    folder = EVIDENCE_ROOT / incident_id / "sandbox"
    folder.mkdir(parents=True, exist_ok=True)

    base_ts = datetime.utcnow()

    # Build metrics that animate over the frames
    enc_total   = behavioral_log.get("files_encrypted",    0)
    exfil_kb    = behavioral_log.get("exfil_size_kb",      0)
    c2_total    = behavioral_log.get("c2_callbacks",        0)
    ioc_list    = _extract_ioc_strings(behavioral_log)
    mitre       = MITRE_MAP.get(attack_type, MITRE_MAP["ransomware"])

    metrics = {
        "files_encrypted": enc_total,
        "exfil_kb":        exfil_kb,
        "c2_hits":         c2_total,
        "iocs":            ioc_list,
        "mitre":           mitre,
        "verdict":         verdict if confidence >= 70 else None,
        "confidence":      f"{confidence}%" if confidence >= 70 else None,
    }

    screenshots = []
    for i in range(NUM_FRAMES):
        path = folder / f"frame_{i:04d}.jpg"

        generate_frame(
            frame_idx    = i,
            total_frames = NUM_FRAMES,
            all_lines    = output_lines,
            incident_id  = incident_id,
            attack_type  = attack_type,
            base_ts      = base_ts,
            out_path     = path,
            metrics      = metrics,
        )
        screenshots.append(str(path))

    print(f"  [Screenshots] ✓ {NUM_FRAMES} frames → {folder}")
    return screenshots


def _extract_ioc_strings(log: dict) -> list:
    iocs = []
    for conn in log.get("network_connections_attempted", []):
        ip     = conn.get("ip",     "")
        domain = conn.get("domain", "")
        if ip:
            iocs.append(f"IP: {ip}")
        if domain:
            iocs.append(f"Domain: {domain}")
    for rk in log.get("registry_modified", []):
        iocs.append(f"Reg: {rk}")
    for proc in log.get("processes_spawned_suspicious", []):
        iocs.append(f"Proc: {proc}")
    return iocs