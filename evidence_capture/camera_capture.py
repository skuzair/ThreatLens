import os
from datetime import datetime


async def capture_camera(incident, base_folder):

    camera_folder = os.path.join(base_folder, "camera")
    os.makedirs(camera_folder, exist_ok=True)

    clip_path = os.path.join(camera_folder, "clip.mp4")

    # Create a dummy video file placeholder
    with open(clip_path, "w") as f:
        f.write("Mock video clip content")

    annotated_frame_path = os.path.join(camera_folder, "frame_mock_annotated.jpg")

    with open(annotated_frame_path, "w") as f:
        f.write("Mock annotated frame")

    return {
        "video_clip": clip_path,
        "annotated_frames": [annotated_frame_path],
        "clip_duration_seconds": 10
    }
