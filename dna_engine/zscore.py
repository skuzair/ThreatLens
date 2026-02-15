def calculate_z_score(value, mean, std):
    if std == 0:
        return 0
    return abs((value - mean) / std)
