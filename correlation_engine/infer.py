"""
Full Correlation Pipeline

Window -> RuleEngine -> RiskCalculator -> IntentPredictor -> Markov Predictor
"""

from datetime import datetime
import uuid

import shap
import pandas as pd

from .rule_engine import RuleEngine
from .risk_calculator import RiskCalculator
from .intent_predictor import IntentPredictor, IntentFeatureBuilder, FEATURE_ORDER
from .markov_predictor import MarkovPredictor


class CorrelationEngine:

    def __init__(self):
        self.rule_engine = RuleEngine()
        self.risk_calculator = RiskCalculator()
        self.intent_predictor = IntentPredictor()
        self.markov_predictor = MarkovPredictor()
        self.feature_builder = IntentFeatureBuilder()

        # SHAP TreeExplainer — initialised once at startup against the
        # underlying sklearn RandomForest so explanations are fast & exact
        self.shap_explainer = shap.TreeExplainer(self.intent_predictor.model)

    def process(self, window):
        """Process a correlation window and generate incident"""

        rule, filtered_events = self.rule_engine.evaluate(window)

        if not rule:
            return None

        # 1. Risk Calculation
        risk_score, breakdown = self.risk_calculator.calculate(
            filtered_events,
            rule
        )

        # 2. Intent Classification
        intent_input = {
            "sources_involved": list(
                set(e["source"] for e in filtered_events)
            ),
            "correlated_events": filtered_events,
            "time_of_day": datetime.utcnow().hour
        }

        intent = self.intent_predictor.predict(intent_input)

        # 3. SHAP Explanation for the predicted intent class
        shap_explanation = self._explain_intent(intent_input, intent)
        intent["shap_top_features"] = shap_explanation

        # 4. Markov Stage Prediction
        markov_output = self.markov_predictor.predict_next_stage(
            intent["primary_intent"]
        )

        # 5. Final Structured Output
        result = {
            "incident_id": f"INC-{uuid.uuid4().hex[:8]}",
            "risk_score": risk_score,
            "severity": self._severity(risk_score),
            "intent": intent,               # now includes shap_top_features
            "attack_progression": markov_output,
        }

        return result

    # ------------------------------------------------------------------
    # SHAP helpers
    # ------------------------------------------------------------------

    def _explain_intent(self, intent_input: dict, intent: dict) -> list:
        """
        Run SHAP on the same feature vector used for prediction and return
        the top-5 most influential features for the winning intent class.

        Returns a list of dicts, each with:
            feature   – feature name
            impact    – raw SHAP value (float)
            direction – "increase" | "decrease"
        """
        features = self.feature_builder.build_features(intent_input)
        features_df = pd.DataFrame([features], columns=FEATURE_ORDER)

        # shap_values shape: [n_classes][n_samples, n_features]
        shap_values = self.shap_explainer.shap_values(features_df)

        # Resolve the class index for the primary predicted intent
        primary_class_idx = list(
            self.intent_predictor.encoder.classes_
        ).index(intent["primary_intent"])

        primary_shap = shap_values[primary_class_idx][0]   # 1-D array

        # Rank by absolute impact, take top 5
        feature_impacts = sorted(
            zip(FEATURE_ORDER, primary_shap),
            key=lambda x: abs(x[1]),
            reverse=True
        )[:5]

        self._log_shap(feature_impacts)

        return [
            {
                "feature":   name,
                "impact":    round(float(val), 4),
                "direction": "increase" if val > 0 else "decrease",
            }
            for name, val in feature_impacts
        ]

    @staticmethod
    def _log_shap(feature_impacts: list):
        """Print a readable SHAP summary to stdout (mirrors original behaviour)."""
        print("\n--- SHAP Explanation (Intent Model) ---")
        for name, impact in feature_impacts:
            direction = (
                "↑ increases intent probability"
                if impact > 0
                else "↓ decreases intent probability"
            )
            print(f"  {name:30} {impact:+.4f}  {direction}")
        print("----------------------------------------\n")

    def _severity(self, score):
        """Convert risk score to severity level"""
        if score >= 90:
            return "CRITICAL"
        elif score >= 75:
            return "HIGH"
        elif score >= 50:
            return "MEDIUM"
        elif score >= 30:
            return "LOW"
        return "INFO"