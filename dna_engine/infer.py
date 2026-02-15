from .profile_store import DNAProfileStore
from .profile_manager import create_new_profile, update_profile
from .deviation_calculator import calculate_deviation_score


class DNAEngine:
    def __init__(self):
        self.store = DNAProfileStore()

    def process_event(self, entity_type, entity_id, event_features):
        profile = self.store.get_profile(entity_type, entity_id)

        if not profile:
            profile = create_new_profile(event_features)
        else:
            profile = update_profile(profile, event_features)

        self.store.save_profile(entity_type, entity_id, profile)

        # Prepare metrics for deviation calculation
        metric_input = {}
        for key, value in event_features.items():
            metric_input[key] = {
                "value": value,
                "mean": profile["metrics"][key]["mean"],
                "std": profile["metrics"][key]["std"]
            }

        deviation = calculate_deviation_score(metric_input)

        return {
            "entity_id": entity_id,
            "entity_type": entity_type,
            "dna": deviation
        }
