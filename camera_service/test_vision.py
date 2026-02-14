import cv2
from detector import PersonDetector
from tracker import PersonTracker
from annotator import annotate_frame

detector = PersonDetector()
tracker = PersonTracker()

frame = cv2.imread("test.png")

detections = detector.detect(frame)
tracked = tracker.update(detections, frame)

annotated = annotate_frame(frame, tracked, {})
cv2.imwrite("output.jpg", annotated)

print("Vision test completed")
