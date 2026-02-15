from .ema_engine import update_ema, update_std

def create_new_profile(event_features):
    profile = {"metrics": {}}

    for key, value in event_features.items():
        profile["metrics"][key] = {
            "mean": value,
            "std": 1.0,
            "sample_count": 1,
            "ema_alpha": 0.1
        }

    return profile


def update_profile(profile, event_features):
    metrics = profile["metrics"]

    for key, value in event_features.items():
        if key not in metrics:
            metrics[key] = {
                "mean": value,
                "std": 1.0,
                "sample_count": 1,
                "ema_alpha": 0.1
            }
            continue

        alpha = metrics[key]["ema_alpha"]
        old_mean = metrics[key]["mean"]
        old_std = metrics[key]["std"]

        new_mean = update_ema(old_mean, value, alpha)
        new_std = update_std(old_std, old_mean, value, alpha)

        metrics[key]["mean"] = new_mean
        metrics[key]["std"] = new_std
        metrics[key]["sample_count"] += 1

    return profile
