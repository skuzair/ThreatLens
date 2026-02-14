"""
ThreatLens AI - Camera/Video Ingestion (Stage 1)
P2 Component: Captures camera frames and sends to Kafka

Supports THREE modes:
1. RTSP stream (IP camera)
2. Video file (mp4/avi)
3. Webcam (laptop camera for testing)

Author: P2 Team
Handoff: Sends to P3's camera_service (YOLOv8 + DeepSORT + zone rules)
"""

import os
import sys
import json
import cv2
import base64
import time
import uuid
from datetime import datetime
from kafka import KafkaProducer
from typing import Dict, Optional
import logging
import numpy as np

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CameraIngestion:
    """Ingestion service for camera/video streams"""
    
    def __init__(self,
                 kafka_broker: str = None,
                 camera_source: str = None,
                 camera_id: str = 'cam-001',
                 zone: str = 'server_room',
                 fps: int = 5,
                 resolution: tuple = (1280, 720)):
        """
        Initialize camera ingestion
        
        Args:
            kafka_broker: Kafka broker address
            camera_source: Video source:
                - RTSP URL: 'rtsp://192.168.1.101:554/stream'
                - Video file: 'path/to/video.mp4'
                - Webcam: '0' or '1' (device index)
                - Test mode: 'test' (generates synthetic frames)
            camera_id: Camera identifier
            zone: Physical zone (server_room, lobby, etc.)
            fps: Frames per second to capture
            resolution: Target resolution (width, height)
        """
        self.kafka_broker = kafka_broker or os.getenv('KAFKA_BROKER', 'localhost:9092')
        self.camera_source = camera_source or '0'  # Default to webcam
        self.camera_id = camera_id
        self.zone = zone
        self.target_fps = fps
        self.resolution = resolution
        
        # Initialize Kafka producer
        self.producer = self._create_producer()
        
        # Video capture object
        self.cap = None
        self.is_test_mode = (camera_source == 'test')
    
    def _create_producer(self) -> KafkaProducer:
        """Create Kafka producer for video frames"""
        return KafkaProducer(
            bootstrap_servers=self.kafka_broker,
            value_serializer=lambda v: json.dumps(v).encode('utf-8'),
            key_serializer=lambda k: k.encode('utf-8') if k else None,
            max_request_size=10485760,  # 10MB for large frames
            acks='all',
            compression_type='gzip'  # Compress frames
        )
    
    def open_camera(self) -> bool:
        """Open video source (camera/file/stream)"""
        if self.is_test_mode:
            logger.info("Running in TEST mode - generating synthetic frames")
            return True
        
        try:
            # Determine source type
            if self.camera_source.startswith('rtsp://'):
                logger.info(f"Opening RTSP stream: {self.camera_source}")
                self.cap = cv2.VideoCapture(self.camera_source)
            
            elif self.camera_source.isdigit():
                # Webcam
                camera_index = int(self.camera_source)
                logger.info(f"Opening webcam {camera_index}")
                self.cap = cv2.VideoCapture(camera_index)
            
            elif os.path.isfile(self.camera_source):
                # Video file
                logger.info(f"Opening video file: {self.camera_source}")
                self.cap = cv2.VideoCapture(self.camera_source)
            
            else:
                logger.error(f"Invalid camera source: {self.camera_source}")
                return False
            
            # Verify camera opened
            if not self.cap.isOpened():
                logger.error("Failed to open camera/video source")
                return False
            
            # Set resolution
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.resolution[0])
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.resolution[1])
            
            logger.info(f"Camera opened successfully (Resolution: {self.resolution})")
            return True
            
        except Exception as e:
            logger.error(f"Error opening camera: {e}")
            return False
    
    def generate_test_frame(self, frame_number: int) -> np.ndarray:
        """Generate a synthetic test frame with overlay text"""
        # Create blank frame
        frame = np.zeros((self.resolution[1], self.resolution[0], 3), dtype=np.uint8)
        
        # Add gradient background
        gradient = np.linspace(0, 255, self.resolution[1], dtype=np.uint8)
        frame[:, :, 0] = gradient[:, np.newaxis]  # Blue channel
        frame[:, :, 1] = gradient[:, np.newaxis] // 2  # Green channel
        
        # Add text overlay
        timestamp = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
        cv2.putText(frame, f"ThreatLens AI - Test Mode", (50, 60),
                   cv2.FONT_HERSHEY_SIMPLEX, 1.5, (255, 255, 255), 2)
        cv2.putText(frame, f"Camera: {self.camera_id}", (50, 120),
                   cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 2)
        cv2.putText(frame, f"Zone: {self.zone}", (50, 170),
                   cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 2)
        cv2.putText(frame, f"Frame: {frame_number}", (50, 220),
                   cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 2)
        cv2.putText(frame, f"Time: {timestamp}", (50, 270),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, (200, 200, 200), 2)
        
        # Simulate "person" detection (random rectangles)
        if frame_number % 10 < 7:  # 70% chance of "detection"
            x, y = np.random.randint(100, 800), np.random.randint(100, 500)
            w, h = 200, 400
            cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 3)
            cv2.putText(frame, "Person (TEST)", (x, y-10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        
        return frame
    
    def read_frame(self, frame_number: int = 0) -> Optional[np.ndarray]:
        """Read a frame from camera/video"""
        if self.is_test_mode:
            return self.generate_test_frame(frame_number)
        
        if not self.cap:
            logger.error("Camera not opened")
            return None
        
        ret, frame = self.cap.read()
        
        if not ret:
            logger.warning("Failed to read frame (end of video?)")
            return None
        
        # Resize if needed
        if frame.shape[1] != self.resolution[0] or frame.shape[0] != self.resolution[1]:
            frame = cv2.resize(frame, self.resolution)
        
        return frame
    
    def frame_to_base64(self, frame: np.ndarray) -> str:
        """Convert OpenCV frame to base64 string"""
        # Encode frame to JPEG
        _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
        
        # Convert to base64
        base64_str = base64.b64encode(buffer).decode('utf-8')
        return base64_str
    
    def create_event(self, frame: np.ndarray, frame_number: int) -> Dict:
        """Create normalized camera event"""
        # Convert frame to base64
        frame_base64 = self.frame_to_base64(frame)
        
        return {
            'event_id': str(uuid.uuid4()),
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'source_type': 'camera',
            'host': self.camera_id,
            'zone': self.zone,
            'raw_data': {
                'camera_id': self.camera_id,
                'frame_number': frame_number,
                'frame_base64': frame_base64,
                'resolution': f"{self.resolution[0]}x{self.resolution[1]}",
                'fps': self.target_fps
            },
            'anomaly_score': 0.0,  # Will be set by P3's camera_service
            'severity': 'low',
            'dna_deviation_score': 0.0
        }
    
    def send_to_kafka(self, event: Dict, topic: str = 'raw-camera-frames'):
        """Send frame event to Kafka"""
        try:
            self.producer.send(
                topic,
                key=event['event_id'],
                value=event
            )
            self.producer.flush()
            return True
        except Exception as e:
            logger.error(f"Failed to send frame to Kafka: {e}")
            return False
    
    def run(self, max_frames: int = None, show_preview: bool = False):
        """
        Run continuous frame capture and ingestion
        
        Args:
            max_frames: Maximum frames to capture (None = infinite)
            show_preview: Display frames in window (requires GUI)
        """
        if not self.is_test_mode and not self.open_camera():
            logger.error("Failed to open camera")
            return
        
        logger.info(f"Starting camera ingestion: {self.camera_id} @ {self.target_fps} FPS")
        logger.info(f"Zone: {self.zone}, Resolution: {self.resolution}")
        
        frame_count = 0
        total_sent = 0
        start_time = time.time()
        
        # Calculate delay between frames
        frame_delay = 1.0 / self.target_fps
        
        try:
            while True:
                if max_frames and frame_count >= max_frames:
                    break
                
                frame_start = time.time()
                
                # Read frame
                frame = self.read_frame(frame_count)
                
                if frame is None:
                    if not self.is_test_mode:
                        logger.info("End of video or camera disconnected")
                        break
                    else:
                        continue
                
                # Create and send event
                event = self.create_event(frame, frame_count)
                if self.send_to_kafka(event):
                    total_sent += 1
                
                frame_count += 1
                
                # Show preview if requested
                if show_preview:
                    cv2.imshow(f"ThreatLens Camera: {self.camera_id}", frame)
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        logger.info("User requested quit")
                        break
                
                # Log progress
                if frame_count % 50 == 0:
                    elapsed = time.time() - start_time
                    actual_fps = frame_count / elapsed if elapsed > 0 else 0
                    logger.info(f"Frames: {frame_count}, Sent: {total_sent}, "
                               f"FPS: {actual_fps:.2f}")
                
                # Maintain target FPS
                frame_elapsed = time.time() - frame_start
                if frame_elapsed < frame_delay:
                    time.sleep(frame_delay - frame_elapsed)
        
        except KeyboardInterrupt:
            logger.info("\nStopped by user")
        
        finally:
            # Cleanup
            elapsed = time.time() - start_time
            avg_fps = frame_count / elapsed if elapsed > 0 else 0
            
            logger.info(f"\nIngestion Summary:")
            logger.info(f"  Total frames: {frame_count}")
            logger.info(f"  Frames sent: {total_sent}")
            logger.info(f"  Duration: {elapsed:.2f}s")
            logger.info(f"  Average FPS: {avg_fps:.2f}")
            
            if not self.is_test_mode and self.cap:
                self.cap.release()
            
            if show_preview:
                cv2.destroyAllWindows()
            
            self.producer.close()


def main():
    """
    Main entry point for camera ingestion
    
    Usage:
        # Test mode (synthetic frames)
        python camera_ingestion.py --source test --camera cam-001 --zone server_room
        
        # Webcam
        python camera_ingestion.py --source 0 --camera cam-webcam --zone lobby
        
        # Video file
        python camera_ingestion.py --source /path/to/video.mp4 --camera cam-video
        
        # RTSP stream
        python camera_ingestion.py --source rtsp://192.168.1.101:554/stream --camera cam-srv-001
    """
    import argparse
    
    parser = argparse.ArgumentParser(description='ThreatLens Camera Ingestion (P2)')
    parser.add_argument('--source', type=str, default='test',
                       help='Camera source: test/0/video.mp4/rtsp://...')
    parser.add_argument('--camera', type=str, default='cam-001',
                       help='Camera ID')
    parser.add_argument('--zone', type=str, default='server_room',
                       help='Physical zone')
    parser.add_argument('--kafka', type=str, default='localhost:9092',
                       help='Kafka broker')
    parser.add_argument('--fps', type=int, default=5,
                       help='Target frames per second')
    parser.add_argument('--width', type=int, default=1280,
                       help='Frame width')
    parser.add_argument('--height', type=int, default=720,
                       help='Frame height')
    parser.add_argument('--max-frames', type=int, default=None,
                       help='Maximum frames to capture')
    parser.add_argument('--preview', action='store_true',
                       help='Show frame preview window')
    
    args = parser.parse_args()
    
    # Create ingestion service
    ingestion = CameraIngestion(
        kafka_broker=args.kafka,
        camera_source=args.source,
        camera_id=args.camera,
        zone=args.zone,
        fps=args.fps,
        resolution=(args.width, args.height)
    )
    
    # Run ingestion
    ingestion.run(max_frames=args.max_frames, show_preview=args.preview)


if __name__ == '__main__':
    main()