"""
NLG Service — Local Unit Tests
Run from nlg_service/ directory or project root.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from explanation_builder import ExplanationBuilder

builder = ExplanationBuilder()

# ── Camera ────────────────────────────────────────────────────────────────
print("\n--- CAMERA ---")
text, factors = builder.build_camera_section({
    "zone": "Server Room", "timestamp": "02:00",
    "permitted_start": "08:00", "permitted_end": "18:00",
    "reid_token": 7743, "score": 92,
})
print(text)
print("Factors:", factors)

# ── Logs ──────────────────────────────────────────────────────────────────
print("\n--- LOGS ---")
text, factors = builder.build_logs_section({
    "src_ip": "192.168.1.157", "timestamp": "02:04",
    "ip_history": "has never previously authenticated on this subnet",
    "failure_count": 7, "privilege_level": "root", "time_after_login": 53,
})
print(text)

# ── Network ───────────────────────────────────────────────────────────────
print("\n--- NETWORK ---")
text, factors = builder.build_network_section({
    "transfer_size": 2.3, "dst_ip": "203.0.113.5", "timestamp": "02:06",
    "dst_history": "no prior history in network baseline",
    "volume_multiple": 53, "traffic_pattern": "data exfiltration",
})
print(text)

# ── File ──────────────────────────────────────────────────────────────────
print("\n--- FILE ---")
text, factors = builder.build_file_section({
    "file_count": 847, "directory": "/var/db/", "modification_type": "modified",
    "time_window": 60, "process_name": "unknown_binary.exe",
    "process_status": "not whitelisted",
    "extension_change_statement":
        "File extensions changed from .sql to .encrypted — ransomware encryption pattern confirmed",
})
print(text)

# ── Sandbox (NLG-native) ──────────────────────────────────────────────────
print("\n--- SANDBOX (native format) ---")
print(builder.build_sandbox_section({
    "filename": "unknown_binary.exe", "verdict": "MALICIOUS",
    "sandbox_actions": "performed mass encryption activity",
    "c2_domains": "evil-c2.ru", "ioc_count": 12,
}))

# ── Sandbox (real output format) ──────────────────────────────────────────
print("\n--- SANDBOX (real sandbox output) ---")
print(builder.build_sandbox_section({
    "verdict": "MALICIOUS", "file_hash": "sha256:abc123",
    "behavioral_summary": {
        "files_encrypted": 160, "ransom_note_created": True,
        "shadow_copies_deleted": True, "c2_callbacks": 3,
    },
    "extracted_iocs": {
        "ips": ["185.220.101.47"], "domains": ["secure-payments.xyz"],
        "registry_keys": [], "processes": ["cmd.exe"],
    },
}))

# ── DNA ───────────────────────────────────────────────────────────────────
print("\n--- DNA DEVIATION ---")
print(builder.build_dna_section({
    "entity": "user_svc_backup", "zscore": 4.7, "threshold": 3.0,
    "anomalous_features": ["login_hour", "data_volume_outbound", "command_sequence"],
    "magnitude": 2.3,
}))

print("\n✅ All unit tests passed\n")