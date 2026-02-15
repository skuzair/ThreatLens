"""
Behaviour Classifier
====================
Scores the behavioral log from Docker execution and returns a verdict.
Works with the structured JSON emitted by the attack scripts as well as
the legacy simulate_behavior() dict.
"""


def classify_sandbox_verdict(log: dict):
    score      = 0
    indicators = []

    # ── Ransomware indicators ──────────────────────────────────────────────
    enc = log.get("files_encrypted", 0)
    if enc > 100:
        score += 40; indicators.append("mass_file_encryption")
    elif enc > 10:
        score += 25; indicators.append("file_encryption_detected")

    if log.get("ransom_note_created"):
        score += 30; indicators.append("ransom_note_dropped")

    if log.get("shadow_copies_deleted"):
        score += 25; indicators.append("backup_destruction")

    # ── Network / C2 indicators ────────────────────────────────────────────
    conns = log.get("network_connections_attempted", [])
    if conns:
        score += 20; indicators.append("c2_callback_attempted")
        # Bonus for known-bad domains/IPs
        bad_domains = {"evil-c2.ru", "secure-payments.xyz",
                       "update.microsofft-cdn.com"}
        for c in conns:
            if c.get("domain") in bad_domains:
                score += 10; indicators.append("known_c2_domain")
                break

    # ── Persistence / defence evasion ─────────────────────────────────────
    if log.get("registry_modified"):
        score += 15; indicators.append("persistence_established")

    procs = log.get("processes_spawned_suspicious", [])
    if procs:
        score += 10; indicators.append("suspicious_child_process")
    if "vssadmin.exe" in procs:
        score += 10; indicators.append("shadow_copy_deletion_tool")

    # ── Exfiltration indicators ────────────────────────────────────────────
    if log.get("records_exfiltrated", 0) > 0:
        score += 35; indicators.append("data_exfiltration_detected")
    if log.get("exfil_size_kb", 0) > 0:
        score += 10; indicators.append("large_data_transfer")

    # ── Verdict ───────────────────────────────────────────────────────────
    score = min(score, 100)

    if score >= 70:
        verdict = "MALICIOUS"
    elif score >= 40:
        verdict = "SUSPICIOUS"
    else:
        verdict = "BENIGN"

    return verdict, score, indicators