from config import SCORE_WEIGHTS, CONFIDENCE_THRESHOLD, CONFIDENCE_MULTIPLIER

def calculate_score(violations, confidence):
    score = 0

    for v in violations:
        if v in SCORE_WEIGHTS:
            score += SCORE_WEIGHTS[v]

    if confidence > CONFIDENCE_THRESHOLD:
        score *= CONFIDENCE_MULTIPLIER

    return min(100, int(score))
