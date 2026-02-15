def update_ema(old_mean, new_value, alpha=0.1):
    """
    Exponential Moving Average update
    """
    if old_mean is None:
        return new_value
    return alpha * new_value + (1 - alpha) * old_mean


def update_std(old_std, old_mean, new_value, alpha=0.1):
    """
    Simple adaptive std update (approximation)
    """
    if old_std is None:
        return 1.0

    deviation = abs(new_value - old_mean)
    return alpha * deviation + (1 - alpha) * old_std
