"""
Markov Predictor

Responsibilities:
- Map classified intent to attack stage
- Predict next likely stage
- Provide transition confidence
- Attach MITRE mapping if available

This module runs AFTER intent classification.
"""
import random
from typing import Dict, Tuple


class MarkovPredictor:

    def __init__(self):
        self.stage_mapping = self._build_stage_mapping()
        self.transition_matrix = self._build_transition_matrix()

    # --------------------------------------------------------
    # Stage Mapping (Intent → Attack Stage)
    # --------------------------------------------------------

    def _build_stage_mapping(self) -> Dict[str, str]:
        """
        Maps intent label to current attack stage.
        """

        return {
            "reconnaissance": "reconnaissance",
            "credential_attack": "initial_access",
            "privilege_escalation": "execution",
            "lateral_movement": "lateral_movement",
            "data_staging": "collection",
            "data_exfiltration": "exfiltration",
            "ransomware": "impact",
            "ddos": "impact",
            "c2_activity": "command_and_control",
            "insider_threat": "execution",
            "apt_infiltration": "lateral_movement",
            "physical_intrusion": "initial_access"
        }

    # --------------------------------------------------------
    # Transition Matrix (Markov Chain)
    # --------------------------------------------------------

    def _build_transition_matrix(self) -> Dict[str, Dict[str, float]]:
        """
        Transition probabilities between attack stages.
        Probabilities should sum to 1 per stage.
        """

        return {

            "reconnaissance": {
                "initial_access": 0.70,
                "reconnaissance": 0.20,
                "none": 0.10
            },

            "initial_access": {
                "execution": 0.40,
                "persistence": 0.30,
                "lateral_movement": 0.20,
                "none": 0.10
            },

            "execution": {
                "persistence": 0.30,
                "lateral_movement": 0.30,
                "exfiltration": 0.20,
                "impact": 0.10,
                "none": 0.10
            },

            "lateral_movement": {
                "collection": 0.40,
                "exfiltration": 0.30,
                "impact": 0.20,
                "none": 0.10
            },

            "collection": {
                "exfiltration": 0.60,
                "impact": 0.20,
                "none": 0.20
            },

            "exfiltration": {
                "log_deletion": 0.50,
                "impact": 0.30,
                "none": 0.20
            },

            "command_and_control": {
                "execution": 0.40,
                "lateral_movement": 0.30,
                "exfiltration": 0.20,
                "none": 0.10
            },

            "impact": {
                "none": 1.0
            },

            "persistence": {
                "execution": 0.40,
                "lateral_movement": 0.30,
                "none": 0.30
            },

            "log_deletion": {
                "none": 1.0
            }
        }

    # --------------------------------------------------------
    # Prediction Logic
    # --------------------------------------------------------

    def predict_next_stage(self,
                           primary_intent: str) -> Dict:
        """
        Returns structured prediction:
        {
            current_stage,
            predicted_next_stage,
            confidence,
            warning_message
        }
        """

        current_stage = self.stage_mapping.get(
            primary_intent,
            "execution"
        )

        transitions = self.transition_matrix.get(
            current_stage,
            {"none": 1.0}
        )

        # This is what makes it a Stochastic attack progression simulator. picks the next attack, but using weighted probabilities.
    
        stages = list(transitions.keys())
        probabilities = list(transitions.values())

        next_stage = random.choices(stages, weights=probabilities)[0]
        confidence = transitions[next_stage]

        result = {
            "current_stage": current_stage,
            "predicted_next_stage": next_stage,
            "confidence": round(confidence, 3)
        }

        # Optional human-readable warning
        if next_stage == "initial_access":
            result["warning"] = "Attacker likely to gain initial system access."
        elif next_stage == "execution":
            result["warning"] = "Malicious code execution likely."
        elif next_stage == "lateral_movement":
            result["warning"] = "Attacker may spread across systems."
        elif next_stage == "exfiltration":
            result["warning"] = "Potential data exfiltration likely."
        elif next_stage == "impact":
            result["warning"] = "System impact or destruction likely."
        elif next_stage == "log_deletion":
            result["warning"] = "Attacker may attempt to cover tracks."
        elif next_stage == "reconnaissance":
            result["warning"] = "Ongoing reconnaissance activity detected."
        else:
            result["warning"] = None


        return result
