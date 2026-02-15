"""
Risk Calculator (Updated - No RF Sensor)

Calculates final incident risk score using:
- Weighted anomaly scores by source (network, logs, camera, file)
- Correlation multiplier (based on number of sources)
- Rule risk multiplier
- MITRE severity weighting
- Capped final score

Returns:
    final_score,
    breakdown_dict
"""

from typing import Dict, List


class RiskCalculator:

    def __init__(self):
        # Source importance weights (redistributed without RF)
        # Total weight sums to 1.0
        self.source_weights = {
            "network": 0.35,
            "logs": 0.30,
            "camera": 0.20,
            "file": 0.15
        }

        # Correlation multiplier based on number of sources involved
        self.correlation_multipliers = {
            1: 1.0,
            2: 1.3,
            3: 1.6,
            4: 2.0
        }

        # MITRE severity weights
        self.mitre_severity_weights = {
            "low": 1.0,
            "medium": 1.3,
            "high": 1.6,
            "critical": 2.0
        }

    def calculate(self, events: List[Dict], rule: Dict):
        """
        Args:
            events: filtered correlated events
            rule: matched rule dictionary

        Returns:
            tuple: (final_score, breakdown_dict)
        """
        if not events:
            return 0.0, {}

        # 1. Weighted base score
        base_score = 0.0
        for event in events:
            source = event["source"]
            score = event["score"]
            weight = self.source_weights.get(source, 0.1)
            base_score += score * weight

        # 2. Correlation multiplier
        unique_sources = len(set(e["source"] for e in events))
        correlation_multiplier = self.correlation_multipliers.get(
            min(unique_sources, 4),
            1.0
        )

        # 3. Rule multiplier
        rule_multiplier = rule.get("risk_multiplier", 1.0)

        # 4. MITRE severity weighting
        mitre_ttps = rule.get("mitre_ttps", [])
        mitre_severity = self._infer_mitre_severity(mitre_ttps)
        mitre_weight = self.mitre_severity_weights.get(mitre_severity, 1.0)

        # 5. Final score calculation
        raw_score = (
            base_score *
            correlation_multiplier *
            rule_multiplier *
            mitre_weight
        )

        final_score = min(100.0, round(raw_score, 2))

        breakdown = {
            "base_weighted_score": round(base_score, 2),
            "correlation_multiplier": correlation_multiplier,
            "rule_multiplier": rule_multiplier,
            "mitre_severity": mitre_severity,
            "mitre_weight": mitre_weight,
            "final_capped_score": final_score
        }

        return final_score, breakdown

    def _infer_mitre_severity(self, ttps: List[str]) -> str:
        """Simple heuristic for MITRE severity"""
        if not ttps:
            return "low"

        critical_ttps = {"T1486", "T1490", "T1498"}
        high_ttps = {"T1041", "T1071", "T1021", "T1068"}
        medium_ttps = {"T1078", "T1110", "T1595"}

        if any(t in critical_ttps for t in ttps):
            return "critical"
        elif any(t in high_ttps for t in ttps):
            return "high"
        elif any(t in medium_ttps for t in ttps):
            return "medium"
        else:
            return "low"