"""
Correlation Engine Diagnostic Tool

Run this to check if files are properly installed.
Usage: python check_correlation_engine.py
"""

import sys
from pathlib import Path

def check_file(filepath, required_content=None):
    """Check if file exists and optionally contains required content"""
    path = Path(filepath)
    
    if not path.exists():
        print(f"  ❌ MISSING: {filepath}")
        return False
    
    if required_content:
        try:
            content = path.read_text()
            if required_content in content:
                print(f"  ✅ OK: {filepath} (contains {required_content})")
                return True
            else:
                print(f"  ⚠️  WARNING: {filepath} exists but missing '{required_content}'")
                return False
        except Exception as e:
            print(f"  ❌ ERROR reading {filepath}: {e}")
            return False
    else:
        print(f"  ✅ OK: {filepath}")
        return True

def main():
    print("\n" + "="*80)
    print("  🔍 CORRELATION ENGINE DIAGNOSTIC")
    print("="*80 + "\n")
    
    # Check directory structure
    print("📁 Checking directory structure...")
    base_dir = Path("correlation_engine")
    
    if not base_dir.exists():
        print(f"  ❌ CRITICAL: correlation_engine/ directory not found!")
        print(f"  Current directory: {Path.cwd()}")
        print(f"  Make sure you're in the ThreatLens root directory")
        return False
    
    print(f"  ✅ correlation_engine/ directory exists\n")
    
    # Check required files
    print("📄 Checking required files...")
    
    required_files = {
        "correlation_engine/__init__.py": None,
        "correlation_engine/infer.py": "class CorrelationEngine",
        "correlation_engine/correlation_window.py": "class CorrelationWindowManager",
        "correlation_engine/rules_config.py": "CORRELATION_RULES",
        "correlation_engine/rule_engine.py": "class RuleEngine",
        "correlation_engine/risk_calculator.py": "class RiskCalculator",
        "correlation_engine/intent_predictor.py": "class IntentPredictor",
        "correlation_engine/markov_predictor.py": "class MarkovPredictor",
    }
    
    all_ok = True
    for file, content in required_files.items():
        if not check_file(file, content):
            all_ok = False
    
    print()
    
    # Check for RF references (should be removed)
    print("🔍 Checking for RF sensor references (should be removed)...")
    
    files_to_check = [
        "correlation_engine/rules_config.py",
        "correlation_engine/risk_calculator.py",
        "correlation_engine/intent_predictor.py",
    ]
    
    rf_found = False
    for file in files_to_check:
        path = Path(file)
        if path.exists():
            content = path.read_text()
            if '"rf"' in content.lower() or 'rf_triggered' in content:
                print(f"  ⚠️  WARNING: Found RF references in {file}")
                rf_found = True
    
    if not rf_found:
        print(f"  ✅ No RF references found (good!)\n")
    else:
        print(f"  ❌ RF references found - files may not be updated\n")
        all_ok = False
    
    # Test imports
    print("📦 Testing imports...")
    
    try:
        sys.path.insert(0, str(Path.cwd()))
        
        print("  Testing: from correlation_engine.risk_calculator import RiskCalculator")
        from correlation_engine.risk_calculator import RiskCalculator
        print("  ✅ RiskCalculator imported successfully")
        
        print("  Testing: from correlation_engine.intent_predictor import IntentPredictor")
        from correlation_engine.intent_predictor import IntentPredictor
        print("  ✅ IntentPredictor imported successfully")
        
        print("  Testing: from correlation_engine.infer import CorrelationEngine")
        from correlation_engine.infer import CorrelationEngine
        print("  ✅ CorrelationEngine imported successfully")
        
        # Try to instantiate
        print("\n  Testing instantiation...")
        engine = CorrelationEngine()
        print("  ✅ CorrelationEngine() instantiated successfully")

        # ── SHAP explanation smoke test ────────────────────────────────────
        print("\n🧠 Testing SHAP explanation...")
        try:
            import pandas as pd
            from correlation_engine.intent_predictor import IntentFeatureBuilder, FEATURE_ORDER

            sample_incident = {
                "sources_involved": ["file", "logs"],
                "correlated_events": [
                    {"source": "file", "score": 95, "ransomware_pattern": True},
                    {"source": "logs", "score": 80, "privilege_escalation_flag": True},
                ],
                "time_of_day": 2,
            }

            # Build feature vector (same path as production code)
            builder = IntentFeatureBuilder()
            features = builder.build_features(sample_incident)
            features_df = pd.DataFrame([features], columns=FEATURE_ORDER)

            # Run SHAP via the already-initialised explainer on the engine
            shap_values = engine.shap_explainer.shap_values(features_df)

            # Predict so we know which class index to explain
            intent = engine.intent_predictor.predict(sample_incident)
            primary_class_idx = list(
                engine.intent_predictor.encoder.classes_
            ).index(intent["primary_intent"])

            primary_shap = shap_values[primary_class_idx][0]
            feature_impacts = sorted(
                zip(FEATURE_ORDER, primary_shap),
                key=lambda x: abs(x[1]),
                reverse=True
            )[:5]

            print(f"\n  Predicted intent : {intent['primary_intent']}")
            print(f"  Confidence       : {intent['primary_confidence']:.1%}")
            if intent.get("secondary_intent"):
                print(f"  Secondary intent : {intent['secondary_intent']} "
                      f"({intent['secondary_confidence']:.1%})")

            print()
            print(f"  {'Feature':<32} {'SHAP Impact':>12}  Direction")
            print(f"  {'-'*32} {'-'*12}  {'-'*28}")
            for name, impact in feature_impacts:
                direction = "↑ increases intent probability" if impact > 0 else "↓ decreases intent probability"
                print(f"  {name:<32} {impact:>+12.4f}  {direction}")

            print()
            print("  ✅ SHAP explainer working correctly")

        except Exception as shap_err:
            print(f"  ❌ SHAP test failed: {shap_err}")
            import traceback
            traceback.print_exc()
            all_ok = False
        # ──────────────────────────────────────────────────────────────────

    except ImportError as e:
        print(f"  ❌ Import error: {e}")
        all_ok = False
        
        # Provide specific guidance
        print("\n  💡 Fix suggestions:")
        print("  1. Copy updated files:")
        print("     cp correlation_engine_updated/*.py correlation_engine/")
        print("  2. Make sure __init__.py exists:")
        print("     touch correlation_engine/__init__.py")
        print("  3. Check Python path:")
        print(f"     Current: {sys.path[:3]}")
        
    except Exception as e:
        print(f"  ❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        all_ok = False
    
    # Check source weights
    print("\n🎯 Checking source weight configuration...")
    try:
        from correlation_engine.risk_calculator import RiskCalculator
        calc = RiskCalculator()
        weights = calc.source_weights
        
        expected = {"network": 0.35, "logs": 0.30, "camera": 0.20, "file": 0.15}
        
        if weights == expected:
            print(f"  ✅ Source weights correct: {weights}")
        else:
            print(f"  ⚠️  WARNING: Unexpected weights")
            print(f"     Expected: {expected}")
            print(f"     Got:      {weights}")
            
        if "rf" in weights:
            print(f"  ❌ ERROR: RF sensor still in weights!")
            all_ok = False
            
    except Exception as e:
        print(f"  ❌ Could not check weights: {e}")
        all_ok = False
    
    # Final verdict
    print("\n" + "="*80)
    if all_ok:
        print("  ✅ ALL CHECKS PASSED")
        print("  Ready to run: python test_correlation.py")
    else:
        print("  ❌ ISSUES FOUND")
        print("  Fix the errors above before running tests")
    print("="*80 + "\n")
    
    return all_ok

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)