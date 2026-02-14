import cv2
from detector import PersonDetector
from tracker import PersonTracker
from zone_engine import get_zone
from rule_engine import check_violations
from scorer import calculate_score

# Initialize models
detector = PersonDetector()
tracker = PersonTracker()

# Load image
frame = cv2.imread("test.png")  # change if your image name differs
timestamp = "2024-01-15T02:03:12"  # 2 AM (after hours)

# Run detection
detections = detector.detect(frame)
tracked = tracker.update(detections, frame)

print("Detections:", detections)
print("Tracked:", tracked)
print("--------------------------------------------------")

for obj in tracked:
    x1, y1, x2, y2, track_id = obj

    # Calculate person center
    center = ((x1 + x2) / 2, (y1 + y2) / 2)

    # Step 1: Zone detection
    zone_name, zone_config = get_zone(center)

    if zone_name:
        print("ZONE DETECTED:", zone_name)

        # Step 2: Check violations
        violations, duration = check_violations(
            track_id,
            zone_name,
            zone_config,
            timestamp
        )

        print("VIOLATIONS:", violations)

        # Step 3: Score calculation
        confidence = detections[0][4] if detections else 0
        score = calculate_score(violations, confidence)

        print("ANOMALY SCORE:", score)
        print("TIME IN ZONE (minutes):", round(duration, 2))
    else:
        print("Person not inside any defined zone.")

    print("--------------------------------------------------")
