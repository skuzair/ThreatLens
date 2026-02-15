import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).resolve().parent))

from template_engine    import TemplateEngine
from shap_processor     import SHAPProcessor
from correlation_engine import CorrelationEngine
from mitre_mapper       import MITREMapper
from safe_extract       import safe_get


class ExplanationBuilder:

    def __init__(self):
        self.engine     = TemplateEngine()
        self.shap       = SHAPProcessor()
        self.corr       = CorrelationEngine()
        self.mitre      = MITREMapper()

    # ── Internal helpers ──────────────────────────────────────────────────

    def _hours_outside(self, timestamp, permitted_start, permitted_end):
        try:
            fmt = "%H:%M"
            t   = datetime.strptime(timestamp, fmt)
            s   = datetime.strptime(permitted_start, fmt)
            e   = datetime.strptime(permitted_end, fmt)
            if t < s:
                return int((s - t).seconds / 3600)
            if t > e:
                return int((t - e).seconds / 3600)
        except Exception:
            pass
        return 0

    def _key_factors(self, shap_values):
        return self.shap.extract_top_factors(shap_values or [])

    # ── Per-source section builders ───────────────────────────────────────

    def build_camera_section(self, event: dict, shap_values=None):
        try:
            hours_outside = self._hours_outside(
                safe_get(event, "timestamp",       "00:00"),
                safe_get(event, "permitted_start", "08:00"),
                safe_get(event, "permitted_end",   "18:00"),
            )
            text = self.engine.render("camera", {
                "zone":            safe_get(event, "zone",            "Unknown Zone"),
                "timestamp":       safe_get(event, "timestamp",       "Unknown Time"),
                "hours_outside":   hours_outside,
                "permitted_start": safe_get(event, "permitted_start", "08:00"),
                "permitted_end":   safe_get(event, "permitted_end",   "18:00"),
                "reid_token":      safe_get(event, "reid_token",      "N/A"),
            })
            return text, self._key_factors(shap_values)
        except Exception:
            return "Camera analysis unavailable.", []

    def build_logs_section(self, event: dict, shap_values=None):
        try:
            text = self.engine.render("logs", {
                "src_ip":          safe_get(event, "src_ip",          "unknown IP"),
                "timestamp":       safe_get(event, "timestamp",       "unknown time"),
                "ip_history":      safe_get(event, "ip_history",      "has no prior history"),
                "failure_count":   safe_get(event, "failure_count",   0),
                "privilege_level": safe_get(event, "privilege_level", "unknown"),
                "time_after_login":safe_get(event, "time_after_login",0),
            })
            return text, self._key_factors(shap_values)
        except Exception:
            return "Log analysis unavailable.", []

    def build_network_section(self, event: dict, shap_values=None):
        try:
            text = self.engine.render("network", {
                "transfer_size":   safe_get(event, "transfer_size",  0),
                "dst_ip":          safe_get(event, "dst_ip",         "unknown"),
                "timestamp":       safe_get(event, "timestamp",      "unknown"),
                "dst_history":     safe_get(event, "dst_history",    "no prior history"),
                "volume_multiple": safe_get(event, "volume_multiple", 1),
                "traffic_pattern": safe_get(event, "traffic_pattern","unknown pattern"),
            })
            return text, self._key_factors(shap_values)
        except Exception:
            return "Network analysis unavailable.", []

    def build_file_section(self, event: dict, shap_values=None):
        try:
            text = self.engine.render("file", {
                "file_count":                safe_get(event, "file_count",     0),
                "directory":                 safe_get(event, "directory",      "unknown"),
                "modification_type":         safe_get(event, "modification_type", "modified"),
                "time_window":               safe_get(event, "time_window",    60),
                "process_name":              safe_get(event, "process_name",   "unknown"),
                "process_status":            safe_get(event, "process_status", "unknown"),
                "extension_change_statement":safe_get(event, "extension_change_statement", ""),
            })
            return text, self._key_factors(shap_values)
        except Exception:
            return "File integrity analysis unavailable.", []

    def build_sandbox_section(self, sandbox_result: dict):
        """
        Accepts both:
          - NLG-native format:  {filename, verdict, sandbox_actions, c2_domains, ioc_count}
          - Real sandbox output: {verdict, confidence_score, behavioral_summary,
                                  extracted_iocs, indicators, attack_type, ...}
        """
        if not sandbox_result:
            return None
        try:
            # Normalise real sandbox output → template variables
            filename = (
                sandbox_result.get("filename")
                or sandbox_result.get("file_hash", "unknown_sample")
            )

            verdict = sandbox_result.get("verdict", "UNKNOWN")

            # sandbox_actions: build from behavioral_summary if present
            beh = sandbox_result.get("behavioral_summary") or {}
            if beh:
                parts = []
                enc = beh.get("files_encrypted", 0)
                if enc:
                    parts.append(f"encrypted {enc} files")
                rec = beh.get("records_exfiltrated", 0)
                if rec:
                    parts.append(f"exfiltrated {rec} records")
                if beh.get("shadow_copies_deleted"):
                    parts.append("deleted shadow copies")
                if beh.get("ransom_note_created"):
                    parts.append("dropped a ransom note")
                sandbox_actions = ", ".join(parts) if parts else "performed malicious activity"
            else:
                sandbox_actions = sandbox_result.get(
                    "sandbox_actions", "performed malicious activity"
                )

            # c2_domains: from extracted_iocs or direct field
            iocs = sandbox_result.get("extracted_iocs") or {}
            domains = iocs.get("domains") if isinstance(iocs, dict) else []
            c2_domains = (
                ", ".join(domains) if domains
                else sandbox_result.get("c2_domains", "unknown")
            )

            # ioc_count
            if isinstance(iocs, dict):
                ioc_count = (
                    len(iocs.get("ips", [])) +
                    len(iocs.get("domains", [])) +
                    len(iocs.get("registry_keys", [])) +
                    len(iocs.get("processes", []))
                )
            else:
                ioc_count = sandbox_result.get("ioc_count", 0)

            return self.engine.render("sandbox", {
                "filename":       filename,
                "verdict":        verdict,
                "sandbox_actions":sandbox_actions,
                "c2_domains":     c2_domains,
                "ioc_count":      ioc_count,
            })
        except Exception as exc:
            return f"Sandbox analysis unavailable. ({exc})"

    def build_dna_section(self, dna_deviations: dict):
        """
        dna_deviations format (from dna_engine):
        {
            "entity":            "user_42",
            "zscore":            4.2,
            "threshold":         3.0,
            "anomalous_features": ["login_hour", "data_volume", "command_sequence"],
            "magnitude":         2.1
        }
        """
        if not dna_deviations:
            return None
        try:
            features = dna_deviations.get("anomalous_features", [])
            return self.engine.render("dna", {
                "entity":            dna_deviations.get("entity",    "unknown"),
                "zscore":            float(dna_deviations.get("zscore",    0)),
                "threshold":         float(dna_deviations.get("threshold", 3.0)),
                "anomalous_features":
                    ", ".join(features) if isinstance(features, list)
                    else str(features),
                "magnitude":         round(float(dna_deviations.get("magnitude", 1.0)), 1),
            })
        except Exception as exc:
            return f"DNA analysis unavailable. ({exc})"

    # ── Cross-cutting statements ──────────────────────────────────────────

    def build_correlation_statement(self, incident: dict) -> str:
        try:
            events = [
                incident[k]
                for k in ("camera_event","logs_event","file_event","network_event")
                if k in incident
            ]
            return self.engine.render("correlation", {
                "source_count":    len(events),
                "window_minutes":  self.corr.calculate_window(events),
                "sequence":        self.corr.build_sequence(incident),
                "attack_pattern":  self.corr.infer_attack_pattern(
                                       safe_get(incident, "intent", "")),
            })
        except Exception:
            return "Correlation analysis unavailable."

    def build_mitre_statement(self, intent: str) -> str:
        try:
            return self.mitre.map_intent(intent)
        except Exception:
            return "MITRE mapping unavailable."

    def build_prediction_statement(self, incident: dict, shap_values: list) -> str:
        try:
            # Use Markov next-stage if available, else fallback
            attack_prog = incident.get("attack_progression") or {}
            next_stage  = attack_prog.get("next_stage", "log deletion")
            time_est    = attack_prog.get("time_estimate_minutes", 15)
            confidence  = self.shap.compute_confidence(shap_values or [])

            return self.engine.render("prediction", {
                "current_stage":  safe_get(incident, "intent", "unknown"),
                "next_stage":     next_stage,
                "time_estimate":  time_est,
                "confidence":     confidence,
                "recommendation": "Immediate containment and host isolation",
            })
        except Exception:
            return "Prediction unavailable."