class SHAPProcessor:

    def extract_top_factors(self, shap_values, top_n=3):
        """
        Accept two formats:
          1. List of {"feature": str, "impact": float}  ← NLG native
          2. List of {"feature": str, "impact": float, "direction": str}
             ← from correlation_engine.infer shap_top_features
        Returns list of feature name strings.
        """
        if not shap_values:
            return []

        sorted_features = sorted(
            shap_values,
            key=lambda x: abs(x.get("impact", 0)),
            reverse=True,
        )
        return [f["feature"] for f in sorted_features[:top_n]]

    def compute_confidence(self, shap_values):
        """
        Derive a confidence % from cumulative SHAP magnitude.
        Clipped to [1, 99].
        """
        if not shap_values:
            return 50

        total = sum(abs(f.get("impact", 0)) for f in shap_values)
        return max(1, min(int(total * 100), 99))

    def top_feature_directions(self, shap_values, top_n=3):
        """
        Return list of (feature, direction) tuples for richer NLG text.
        direction is 'increase' | 'decrease' (falls back to sign of impact).
        """
        if not shap_values:
            return []

        sorted_features = sorted(
            shap_values,
            key=lambda x: abs(x.get("impact", 0)),
            reverse=True,
        )[:top_n]

        result = []
        for f in sorted_features:
            direction = f.get("direction") or (
                "increase" if f.get("impact", 0) > 0 else "decrease"
            )
            result.append((f["feature"], direction))
        return result