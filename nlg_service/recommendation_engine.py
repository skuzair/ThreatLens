class RecommendationEngine:

    def generate(self, incident: dict) -> list:
        actions = []
        severity = incident.get("severity", "")
        intent   = incident.get("intent",   "")

        # ── Severity-based baseline ───────────────────────────────────────
        if severity == "CRITICAL":
            actions += [
                "Isolate affected host immediately from all network segments",
                "Block malicious IPs at perimeter firewall and SIEM",
                "Revoke all active sessions for compromised credentials",
            ]
        elif severity == "HIGH":
            actions += [
                "Quarantine affected system pending investigation",
                "Reset credentials for accounts involved in the incident",
            ]

        # ── Intent-specific ───────────────────────────────────────────────
        if intent in ("DATA_EXFILTRATION", "data_exfiltration"):
            actions += [
                "Audit all outbound traffic logs for the past 24 hours",
                "Notify data protection officer — potential data breach",
                "Preserve network capture before log rotation",
            ]

        if intent in ("RANSOMWARE", "ransomware"):
            actions += [
                "Disconnect all storage volumes and NAS shares immediately",
                "Do NOT pay ransom — contact incident response team",
                "Restore from last known-good offline backup",
            ]

        # ── Sandbox confirmed malicious ───────────────────────────────────
        sandbox = incident.get("sandbox_result") or {}
        if sandbox.get("verdict") == "MALICIOUS":
            actions += [
                f"Hash {sandbox.get('filename','unknown file')} and submit to VirusTotal",
                "Blacklist all IOCs extracted from sandbox detonation",
            ]
            for domain in (sandbox.get("c2_domains") or "").split(","):
                d = domain.strip()
                if d:
                    actions.append(f"Block C2 domain at DNS layer: {d}")

        # ── DNA deviation ─────────────────────────────────────────────────
        dna = incident.get("dna_deviations") or {}
        if dna.get("zscore", 0) > 3.0:
            actions.append(
                f"Initiate behavioural review for entity '{dna.get('entity','unknown')}'"
                " — z-score exceeds 3σ threshold"
            )

        # ── Markov next-stage prediction ─────────────────────────────────
        attack_prog = incident.get("attack_progression") or {}
        next_stage  = attack_prog.get("next_stage")
        if next_stage:
            actions.append(
                f"Pre-emptively monitor for '{next_stage}' "
                f"(predicted next attack stage, "
                f"confidence: {attack_prog.get('confidence', '?')})"
            )

        # Always end with log preservation
        actions.append("Preserve all logs and evidence before any remediation")

        # Deduplicate while preserving order
        seen = set()
        deduped = []
        for a in actions:
            if a not in seen:
                seen.add(a)
                deduped.append(a)

        return deduped