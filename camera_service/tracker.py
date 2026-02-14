from deep_sort_realtime.deepsort_tracker import DeepSort

class PersonTracker:
    def __init__(self):
        self.tracker = DeepSort(max_age=30)

    def update(self, detections, frame):
        formatted_detections = []

        for det in detections:
            x1, y1, x2, y2, conf = det
            w = x2 - x1
            h = y2 - y1

            formatted_detections.append(
                ([x1, y1, w, h], conf, 0)
            )

        tracks = self.tracker.update_tracks(
            formatted_detections,
            frame=frame
        )

        tracked_objects = []

        for track in tracks:
            # REMOVE is_confirmed() check for testing
            l, t, r, b = track.to_ltrb()
            tracked_objects.append([
                int(l), int(t), int(r), int(b), track.track_id
            ])

        return tracked_objects
