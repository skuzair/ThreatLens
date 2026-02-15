class MITREMapper:

    MITRE_MAP = {
        "DATA_EXFILTRATION": [
            "T1078 (Valid Accounts)",
            "T1041 (Exfiltration Over C2)",
            "T1048 (Exfiltration Over Alternative Protocol)",
        ],
        "RANSOMWARE": [
            "T1486 (Data Encrypted for Impact)",
            "T1490 (Inhibit System Recovery)",
            "T1070 (Indicator Removal)",
        ],
        "LATERAL_MOVEMENT": [
            "T1021 (Remote Services)",
            "T1075 (Pass the Hash)",
        ],
        "PRIVILEGE_ESCALATION": [
            "T1078 (Valid Accounts)",
            "T1068 (Exploitation for Privilege Escalation)",
        ],
        # lowercase variants (correlation engine uses these)
        "data_exfiltration": [
            "T1078 (Valid Accounts)",
            "T1041 (Exfiltration Over C2)",
            "T1048 (Exfiltration Over Alternative Protocol)",
        ],
        "ransomware": [
            "T1486 (Data Encrypted for Impact)",
            "T1490 (Inhibit System Recovery)",
            "T1070 (Indicator Removal)",
        ],
    }

    def map_intent(self, intent: str) -> str:
        techniques = self.MITRE_MAP.get(intent, [])
        if not techniques:
            return f"No MITRE mapping available for intent '{intent}'."
        return "Matches " + " + ".join(techniques) + "."