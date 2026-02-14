import cv2

def annotate_frame(frame, tracked_objects, violations_map):
    for obj in tracked_objects:
        x1, y1, x2, y2, track_id = obj

        color = (0, 255, 0)
        if violations_map.get(track_id):
            color = (0, 0, 255)

        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
        cv2.putText(frame, f"ID:{track_id}", (x1, y1 - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

    return frame
