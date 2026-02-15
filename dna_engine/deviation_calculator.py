from .zscore import calculate_z_score

def calculate_deviation_score(metrics):
    """
    metrics format:
    {
        "bytes_sent": {"value": 1000, "mean": 500, "std": 100}
    }
    """

    anomalous_metrics = []
    total_sigma = 0

    for metric, data in metrics.items():
        sigma = calculate_z_score(data["value"], data["mean"], data["std"])
        total_sigma += sigma

        if sigma > 3:  # threshold for anomaly
            anomalous_metrics.append({
                "metric": metric,
                "current": data["value"],
                "baseline_mean": data["mean"],
                "baseline_std": data["std"],
                "sigma": round(sigma, 2)
            })

    overall_score = min(100, total_sigma * 10)

    return {
        "deviation_sigma": round(total_sigma, 2),
        "anomalous_metrics": anomalous_metrics,
        "overall_dna_deviation_score": round(overall_score, 2)
    }
