from ultralytics import YOLO
from config import YOLO_MODEL_PATH, MIN_CONFIDENCE

class PersonDetector:
    def __init__(self):
        self.model = YOLO(YOLO_MODEL_PATH)

    def detect(self, frame):
        results = self.model(frame, classes=[0])
        detections = []

        for box in results[0].boxes:
            conf = float(box.conf[0])
            if conf < MIN_CONFIDENCE:
                continue

            x1, y1, x2, y2 = box.xyxy[0].tolist()
            detections.append([x1, y1, x2, y2, conf])

        return detections
