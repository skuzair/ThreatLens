"""
Correlation Rules Configuration (Updated - No RF Sensor)
Each rule defines:
- Required sources
- Optional sources
- Minimum anomaly scores
- Time window constraints
- Risk multiplier
- MITRE ATT&CK mappings
- Intent label

Available sources: network, logs, file, camera
"""

CORRELATION_RULES = [

    # -----------------------------------------------------------
    # 1. Insider Data Exfiltration
    # -----------------------------------------------------------
    {
        "rule_id": "RULE_001",
        "name": "Insider Data Exfiltration",
        "required_sources": ["camera", "logs", "network"],
        "optional_sources": ["file"],
        "min_scores": {"camera": 70, "logs": 60, "network": 70},
        "time_window_minutes": 10,
        "zone_match_required": True,
        "risk_multiplier": 1.8,
        "mitre_ttps": ["T1078", "T1041"],
        "intent_label": "data_exfiltration"
    },

    # -----------------------------------------------------------
    # 2. Ransomware Deployment
    # -----------------------------------------------------------
    {
        "rule_id": "RULE_002",
        "name": "Ransomware Deployment",
        "required_sources": ["file"],
        "optional_sources": ["network", "logs"],
        "min_scores": {"file": 80},
        "ransomware_pattern_required": True,
        "time_window_minutes": 5,
        "risk_multiplier": 2.0,
        "mitre_ttps": ["T1486", "T1490"],
        "intent_label": "ransomware"
    },

    # -----------------------------------------------------------
    # 3. Physical + Cyber Coordinated Attack
    # -----------------------------------------------------------
    {
        "rule_id": "RULE_003",
        "name": "Physical + Cyber Coordinated",
        "required_sources": ["camera", "logs"],
        "optional_sources": ["network"],
        "time_window_minutes": 5,
        "risk_multiplier": 1.6,
        "mitre_ttps": ["T1078", "T1098"],
        "intent_label": "apt_infiltration"
    },

    # -----------------------------------------------------------
    # 4. Credential Stuffing / Brute Force
    # -----------------------------------------------------------
    {
        "rule_id": "RULE_004",
        "name": "Credential Stuffing Attack",
        "required_sources": ["logs"],
        "optional_sources": ["network"],
        "min_scores": {"logs": 65},
        "time_window_minutes": 5,
        "risk_multiplier": 1.5,
        "mitre_ttps": ["T1110"],
        "intent_label": "credential_attack"
    },

    # -----------------------------------------------------------
    # 5. Command & Control (C2) Beaconing
    # -----------------------------------------------------------
    {
        "rule_id": "RULE_005",
        "name": "C2 Beaconing Detected",
        "required_sources": ["network"],
        "optional_sources": ["logs"],
        "min_scores": {"network": 70},
        "time_window_minutes": 15,
        "risk_multiplier": 1.7,
        "mitre_ttps": ["T1071"],
        "intent_label": "c2_activity"
    },

    # -----------------------------------------------------------
    # 6. Data Staging Before Exfiltration
    # -----------------------------------------------------------
    {
        "rule_id": "RULE_006",
        "name": "Data Staging Before Exfiltration",
        "required_sources": ["file"],
        "optional_sources": ["network"],
        "min_scores": {"file": 75},
        "time_window_minutes": 10,
        "risk_multiplier": 1.6,
        "mitre_ttps": ["T1074"],
        "intent_label": "data_staging"
    },

    # -----------------------------------------------------------
    # 7. Lateral Movement
    # -----------------------------------------------------------
    {
        "rule_id": "RULE_007",
        "name": "Lateral Movement Detected",
        "required_sources": ["logs", "network"],
        "optional_sources": [],
        "min_scores": {"logs": 60, "network": 60},
        "time_window_minutes": 8,
        "risk_multiplier": 1.7,
        "mitre_ttps": ["T1021"],
        "intent_label": "lateral_movement"
    },

    # -----------------------------------------------------------
    # 8. Reconnaissance Activity
    # -----------------------------------------------------------
    {
        "rule_id": "RULE_008",
        "name": "Internal Reconnaissance",
        "required_sources": ["network"],
        "optional_sources": [],
        "min_scores": {"network": 55},
        "time_window_minutes": 15,
        "risk_multiplier": 1.4,
        "mitre_ttps": ["T1595"],
        "intent_label": "reconnaissance"
    },

    # -----------------------------------------------------------
    # 9. Unauthorized After-Hours Access
    # -----------------------------------------------------------
    {
        "rule_id": "RULE_009",
        "name": "After Hours Access Anomaly",
        "required_sources": ["logs"],
        "optional_sources": ["camera"],
        "min_scores": {"logs": 65},
        "time_window_minutes": 5,
        "risk_multiplier": 1.5,
        "mitre_ttps": ["T1078"],
        "intent_label": "insider_threat"
    },

    # -----------------------------------------------------------
    # 10. Privilege Escalation Attempt
    # -----------------------------------------------------------
    {
        "rule_id": "RULE_010",
        "name": "Privilege Escalation",
        "required_sources": ["logs"],
        "optional_sources": ["file"],
        "min_scores": {"logs": 75},
        "time_window_minutes": 5,
        "risk_multiplier": 1.8,
        "mitre_ttps": ["T1068"],
        "intent_label": "privilege_escalation"
    },

    # -----------------------------------------------------------
    # 11. Distributed Denial of Service (DDoS)
    # -----------------------------------------------------------
    {
        "rule_id": "RULE_011",
        "name": "DDoS Attack Pattern",
        "required_sources": ["network"],
        "optional_sources": [],
        "min_scores": {"network": 80},
        "time_window_minutes": 3,
        "risk_multiplier": 1.9,
        "mitre_ttps": ["T1498"],
        "intent_label": "ddos"
    },

    # -----------------------------------------------------------
    # 12. Suspicious File Activity + Network Traffic
    # -----------------------------------------------------------
    {
        "rule_id": "RULE_012",
        "name": "Malware Execution Pattern",
        "required_sources": ["file", "network"],
        "optional_sources": ["logs"],
        "min_scores": {"file": 70, "network": 65},
        "time_window_minutes": 8,
        "risk_multiplier": 1.7,
        "mitre_ttps": ["T1059", "T1071"],
        "intent_label": "apt_infiltration"
    },

    # -----------------------------------------------------------
    # 13. Camera + File Anomaly (Physical + Data)
    # -----------------------------------------------------------
    {
        "rule_id": "RULE_013",
        "name": "Physical Access with Data Manipulation",
        "required_sources": ["camera", "file"],
        "optional_sources": ["logs"],
        "min_scores": {"camera": 65, "file": 70},
        "time_window_minutes": 10,
        "zone_match_required": True,
        "risk_multiplier": 1.6,
        "mitre_ttps": ["T1078", "T1565"],
        "intent_label": "insider_threat"
    },
]