"""
NLG Service — Full Incident Simulation Demo
============================================
Exercises every path of the NLG pipeline without Kafka.
Tests both the legacy NLG-native format AND real outputs
from the correlation engine + sandbox service.

Run from ThreatLens root:
    python nlg_service/simulate_full_incident.py
"""

import sys
import json
from pathlib import Path

# Always resolve relative to this file so it works from any CWD
sys.path.insert(0, str(Path(__file__).resolve().parent))

from explanation_builder   import ExplanationBuilder
from recommendation_engine import RecommendationEngine
from incident_validator    import IncidentValidator
from main                  import build_output


builder    = ExplanationBuilder()
recommender = RecommendationEngine()
validator  = IncidentValidator()


# ═══════════════════════════════════════════════════════════════════════════
# INCIDENT 1 — NLG-native format (matches original simulate_full_incident.py)
# ═══════════════════════════════════════════════════════════════════════════

INCIDENT_EXFIL = {
    "incident_id": "INC-2024-001",
    "risk_score":  94,
    "severity":    "CRITICAL",
    "intent":      "DATA_EXFILTRATION",

    # SHAP from correlation engine (shap_top_features format)
    "shap_explanations": [
        {"feature": "after_hours",    "impact": 0.42, "direction": "increase"},
        {"feature": "zone_violation", "impact": 0.33, "direction": "increase"},
        {"feature": "volume_spike",   "impact": 0.29, "direction": "increase"},
    ],

    # DNA baseline deviation (from dna_engine)
    "dna_deviations": {
        "entity":             "user_svc_backup",
        "zscore":             4.7,
        "threshold":          3.0,
        "anomalous_features": ["login_hour", "data_volume_outbound", "command_sequence"],
        "magnitude":          2.3,
    },

    # Markov next-stage prediction (from correlation_engine.infer)
    "attack_progression": {
        "next_stage":              "log deletion",
        "time_estimate_minutes":   15,
        "confidence":              "87%",
    },

    "camera_event": {
        "zone":            "Server Room",
        "timestamp":       "02:00",
        "permitted_start": "08:00",
        "permitted_end":   "18:00",
        "reid_token":      7743,
        "score":           92,
    },

    "logs_event": {
        "src_ip":           "192.168.1.157",
        "timestamp":        "02:04",
        "ip_history":       "has never previously authenticated on this subnet",
        "failure_count":    7,
        "privilege_level":  "root",
        "time_after_login": 53,
        "score":            76,
    },

    "network_event": {
        "transfer_size":   2.3,
        "dst_ip":          "203.0.113.5",
        "timestamp":       "02:06",
        "dst_history":     "no prior history in network baseline",
        "volume_multiple": 53,
        "traffic_pattern": "data exfiltration",
        "score":           87,
    },

    "file_event": {
        "timestamp":                  "02:05",
        "file_count":                 847,
        "directory":                  "/var/db/",
        "modification_type":          "modified",
        "time_window":                60,
        "process_name":               "unknown_binary.exe",
        "process_status":             "not whitelisted",
        "extension_change_statement": (
            "File extensions changed from .sql to .encrypted "
            "— ransomware encryption pattern confirmed"
        ),
        "score": 91,
    },

    # NLG-native sandbox format
    "sandbox_result": {
        "filename":        "unknown_binary.exe",
        "verdict":         "MALICIOUS",
        "sandbox_actions": "performed mass encryption activity",
        "c2_domains":      "evil-c2.ru",
        "ioc_count":       12,
    },
}


# ═══════════════════════════════════════════════════════════════════════════
# INCIDENT 2 — Real sandbox output format (from demo_sandbox_evidence.py)
# ═══════════════════════════════════════════════════════════════════════════

INCIDENT_RANSOMWARE = {
    "incident_id": "INC-TEST-RANSOMWARE",
    "risk_score":  95.0,
    "severity":    "CRITICAL",
    "intent":      "ransomware",

    # SHAP in correlation engine output format
    "shap_explanations": [
        {"feature": "has_ransomware_pattern", "impact": 0.312, "direction": "increase"},
        {"feature": "has_file_source",        "impact": 0.201, "direction": "increase"},
        {"feature": "privilege_escalation",   "impact": 0.118, "direction": "increase"},
        {"feature": "time_of_day",            "impact": -0.041,"direction": "decrease"},
        {"feature": "avg_score",              "impact": 0.038, "direction": "increase"},
    ],

    "dna_deviations": {
        "entity":             "host_SRV-DC01",
        "zscore":             5.1,
        "threshold":          3.0,
        "anomalous_features": ["file_write_rate", "shadow_delete_attempt", "c2_beacon"],
        "magnitude":          3.2,
    },

    "attack_progression": {
        "next_stage":            "lateral movement",
        "time_estimate_minutes": 10,
        "confidence":            "91%",
    },

    "file_event": {
        "timestamp":                  "2026-02-15T14:30:00Z",
        "file_count":                 160,
        "directory":                  "/sandbox/victim_files/",
        "modification_type":          "encrypted",
        "time_window":                45,
        "process_name":               "payload.py",
        "process_status":             "sandboxed — MALICIOUS",
        "extension_change_statement": (
            "160 files renamed with .locked extension "
            "— AES-256 encryption confirmed by sandbox"
        ),
        "score": 95,
    },

    "network_event": {
        "transfer_size":   0.5,
        "dst_ip":          "185.220.101.47",
        "timestamp":       "2026-02-15T14:31:00Z",
        "dst_history":     "known Tor exit node — threat intel match",
        "volume_multiple": 12,
        "traffic_pattern": "C2 beacon + key exchange",
        "score":           78,
    },

    # Real sandbox output format (what demo_sandbox_evidence.py produces)
    "sandbox_result": {
        "incident_id":    "INC-TEST-RANSOMWARE",
        "attack_type":    "ransomware",
        "verdict":        "MALICIOUS",
        "confidence_score": 100,
        "file_hash":      "sha256:4a8b2c1d9e3f0a7b",
        "behavioral_summary": {
            "files_encrypted":                160,
            "ransom_note_created":            True,
            "shadow_copies_deleted":          True,
            "c2_callbacks":                   3,
            "registry_modified":              ["HKCU\\Run\\persist_malware"],
            "processes_spawned_suspicious":   ["cmd.exe", "vssadmin.exe"],
            "network_connections_attempted":  [
                {"ip": "185.220.101.47", "port": 443, "domain": "secure-payments.xyz"},
                {"ip": "91.108.4.200",   "port": 8080},
            ],
            "records_exfiltrated": 0,
            "exfil_size_kb":       0,
        },
        "extracted_iocs": {
            "ips":           ["185.220.101.47", "91.108.4.200"],
            "domains":       ["secure-payments.xyz"],
            "registry_keys": ["HKCU\\Run\\persist_malware"],
            "processes":     ["cmd.exe", "vssadmin.exe"],
            "mitre_behaviors": ["T1486", "T1490", "T1071", "T1547"],
        },
        "indicators": [
            "mass_file_encryption", "ransom_note_dropped",
            "backup_destruction",   "c2_callback",
            "known_c2_domain",      "persistence",
        ],
    },
}


# ═══════════════════════════════════════════════════════════════════════════
# RUNNER
# ═══════════════════════════════════════════════════════════════════════════

def run_incident(incident: dict, label: str):
    print(f"\n{'═'*80}")
    print(f"  {label}")
    print(f"  {incident['incident_id']}  |  {incident['severity']}  "
          f"|  Risk: {incident['risk_score']}")
    print(f"{'═'*80}")

    is_valid, missing = validator.validate(incident)
    if not is_valid:
        print(f"  ❌ Validation failed: {missing}")
        return None

    output = build_output(incident, builder, recommender)

    print(f"\n  SUMMARY\n  {output['summary']}\n")

    for s in output["sections"]:
        print(f"  [{s['source'].upper()}]  score={s['score']}")
        print(f"  {s['text']}")
        if s["key_factors"]:
            print(f"  Key factors: {', '.join(s['key_factors'])}")
        print()

    print(f"  CORRELATION\n  {output['correlation_statement']}\n")
    print(f"  MITRE\n  {output['mitre_statement']}\n")

    if output.get("dna_statement"):
        print(f"  DNA BASELINE\n  {output['dna_statement']}\n")

    if output.get("sandbox_statement"):
        print(f"  SANDBOX\n  {output['sandbox_statement']}\n")

    print(f"  PREDICTION\n  {output['prediction_statement']}\n")

    print(f"  RECOMMENDED ACTIONS")
    for i, action in enumerate(output["recommended_actions"], 1):
        print(f"    {i}. {action}")

    if output.get("shap_top_features"):
        print(f"\n  SHAP TOP FEATURES")
        for f in output["shap_top_features"]:
            direction = "↑" if f.get("direction") == "increase" else "↓"
            print(f"    {direction} {f['feature']:35} {f['impact']:+.4f}")

    return output


def main():
    print("\n" + "═"*80)
    print("  THREATLENS NLG SERVICE — FULL INCIDENT SIMULATION")
    print("═"*80)

    results = []

    out1 = run_incident(INCIDENT_EXFIL,      "INCIDENT 1: DATA EXFILTRATION (NLG-native format)")
    results.append(("INC-2024-001",      out1 is not None))

    out2 = run_incident(INCIDENT_RANSOMWARE, "INCIDENT 2: RANSOMWARE (real sandbox output format)")
    results.append(("INC-TEST-RANSOMWARE", out2 is not None))

    print(f"\n{'═'*80}")
    print("  SUMMARY")
    print(f"{'═'*80}")
    for inc_id, ok in results:
        print(f"  {'✅' if ok else '❌'}  {inc_id}")

    # Write last output to file for inspection
    if out2:
        out_path = Path(__file__).resolve().parent / "last_nlg_output.json"
        out_path.write_text(
            json.dumps(out2, indent=2, default=str), encoding="utf-8"
        )
        print(f"\n  Full JSON output → {out_path}")

    print(f"{'═'*80}\n")


if __name__ == "__main__":
    main()