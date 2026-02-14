"""
ThreatLens AI - File Integrity Monitoring (Stage 1)
P2 Component: Monitors file system changes and sends to Kafka

Monitors:
- Critical system files (/etc/shadow, /etc/passwd)
- Web server directories (/var/www)
- Application configs
- Detects: modifications, creations, deletions, permission changes

Author: P2 Team
Handoff: Sends to P3's file_detector (hash check + sandbox trigger)
"""

import os
import sys
import json
import time
import hashlib
import uuid
from datetime import datetime
from pathlib import Path
from kafka import KafkaProducer
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileSystemEvent
from typing import Dict, List, Set
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FileEventHandler(FileSystemEventHandler):
    """Handles file system events and sends to Kafka"""
    
    CRITICAL_EXTENSIONS = {
        '.exe', '.dll', '.so', '.sh', '.bat', '.ps1', '.py', '.php',
        '.jsp', '.asp', '.conf', '.config', '.ini', '.yaml', '.yml'
    }
    
    SUSPICIOUS_PATTERNS = [
        'shadow', 'passwd', 'sudoers', 'authorized_keys', 'id_rsa',
        'wallet', 'password', 'secret', 'token', 'credential'
    ]
    
    def __init__(self, kafka_producer: KafkaProducer, 
                 monitored_paths: List[str],
                 send_to_sandbox: bool = True):
        """
        Initialize file event handler
        
        Args:
            kafka_producer: Kafka producer instance
            monitored_paths: List of paths being monitored
            send_to_sandbox: Send suspicious files to sandbox
        """
        super().__init__()
        self.producer = kafka_producer
        self.monitored_paths = monitored_paths
        self.send_to_sandbox = send_to_sandbox
        self.event_count = 0
        
        # Rate limiting: ignore rapid duplicate events
        self.recent_events: Set[str] = set()
        self.last_cleanup = time.time()
    
    def _should_ignore(self, file_path: str) -> bool:
        """Check if file should be ignored"""
        # Ignore hidden files, temp files, logs
        ignore_patterns = [
            '.git/', '__pycache__/', '.pyc', '.swp', '.tmp',
            '.log', '.cache', 'node_modules/'
        ]
        
        for pattern in ignore_patterns:
            if pattern in file_path:
                return True
        
        return False
    
    def _calculate_file_hash(self, file_path: str) -> str:
        """Calculate SHA256 hash of file"""
        try:
            sha256_hash = hashlib.sha256()
            with open(file_path, "rb") as f:
                for byte_block in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(byte_block)
            return sha256_hash.hexdigest()
        except Exception as e:
            logger.warning(f"Failed to hash {file_path}: {e}")
            return "unknown"
    
    def _is_suspicious_file(self, file_path: str) -> bool:
        """Check if file is suspicious (for sandbox)"""
        file_path_lower = file_path.lower()
        file_ext = Path(file_path).suffix.lower()
        
        # Check extension
        if file_ext in self.CRITICAL_EXTENSIONS:
            return True
        
        # Check filename patterns
        for pattern in self.SUSPICIOUS_PATTERNS:
            if pattern in file_path_lower:
                return True
        
        return False
    
    def _get_file_info(self, file_path: str) -> Dict:
        """Get detailed file information"""
        try:
            stat = os.stat(file_path)
            return {
                'size_bytes': stat.st_size,
                'permissions': oct(stat.st_mode)[-3:],
                'owner_uid': stat.st_uid,
                'modified_time': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                'created_time': datetime.fromtimestamp(stat.st_ctime).isoformat()
            }
        except Exception as e:
            logger.warning(f"Failed to get file info for {file_path}: {e}")
            return {}
    
    def _create_event(self, event: FileSystemEvent, event_type: str) -> Dict:
        """Create normalized file event"""
        file_path = event.src_path
        file_hash = "unknown"
        file_info = {}
        
        # Get file hash and info for created/modified files
        if event_type in ['created', 'modified'] and os.path.isfile(file_path):
            file_hash = self._calculate_file_hash(file_path)
            file_info = self._get_file_info(file_path)
        
        # Determine severity
        is_suspicious = self._is_suspicious_file(file_path)
        severity = 'high' if is_suspicious else 'medium' if event_type == 'modified' else 'low'
        
        return {
            'event_id': str(uuid.uuid4()),
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'source_type': 'file',
            'host': os.uname().nodename,
            'zone': 'file_system',
            'raw_data': {
                'file_path': file_path,
                'event_type': event_type,  # created, modified, deleted, moved
                'file_hash': file_hash,
                'file_extension': Path(file_path).suffix,
                'file_name': Path(file_path).name,
                'directory': str(Path(file_path).parent),
                'is_suspicious': is_suspicious,
                **file_info
            },
            'anomaly_score': 0.0,  # Will be set by P3's file_detector
            'severity': severity,
            'dna_deviation_score': 0.0
        }
    
    def _send_to_kafka(self, event: Dict):
        """Send file event to Kafka"""
        try:
            # Send to raw file events topic
            self.producer.send(
                'raw-file-events',
                key=event['event_id'],
                value=event
            )
            
            # If suspicious, also send to sandbox queue
            if self.send_to_sandbox and event['raw_data'].get('is_suspicious', False):
                sandbox_event = {
                    'event_id': event['event_id'],
                    'file_path': event['raw_data']['file_path'],
                    'file_hash': event['raw_data']['file_hash'],
                    'trigger_reason': f"Suspicious {event['raw_data']['event_type']}: {Path(event['raw_data']['file_path']).name}",
                    'timestamp': event['timestamp']
                }
                self.producer.send('sandbox-queue', value=sandbox_event)
                logger.warning(f"🔥 Sent to sandbox: {event['raw_data']['file_path']}")
            
            self.producer.flush()
            self.event_count += 1
            
        except Exception as e:
            logger.error(f"Failed to send to Kafka: {e}")
    
    def _rate_limit_check(self, file_path: str) -> bool:
        """
        Check if event should be rate-limited
        Returns True if event should be processed
        """
        # Clean old events every 60 seconds
        if time.time() - self.last_cleanup > 60:
            self.recent_events.clear()
            self.last_cleanup = time.time()
        
        # Check if this file was recently processed
        if file_path in self.recent_events:
            return False
        
        self.recent_events.add(file_path)
        return True
    
    def on_created(self, event: FileSystemEvent):
        """Called when a file or directory is created"""
        if event.is_directory or self._should_ignore(event.src_path):
            return
        
        if not self._rate_limit_check(event.src_path):
            return
        
        logger.info(f"➕ Created: {event.src_path}")
        kafka_event = self._create_event(event, 'created')
        self._send_to_kafka(kafka_event)
    
    def on_modified(self, event: FileSystemEvent):
        """Called when a file is modified"""
        if event.is_directory or self._should_ignore(event.src_path):
            return
        
        if not self._rate_limit_check(event.src_path):
            return
        
        logger.info(f"✏️  Modified: {event.src_path}")
        kafka_event = self._create_event(event, 'modified')
        self._send_to_kafka(kafka_event)
    
    def on_deleted(self, event: FileSystemEvent):
        """Called when a file or directory is deleted"""
        if event.is_directory or self._should_ignore(event.src_path):
            return
        
        logger.warning(f"🗑️  Deleted: {event.src_path}")
        kafka_event = self._create_event(event, 'deleted')
        self._send_to_kafka(kafka_event)
    
    def on_moved(self, event: FileSystemEvent):
        """Called when a file or directory is moved"""
        if event.is_directory or self._should_ignore(event.src_path):
            return
        
        logger.info(f"📦 Moved: {event.src_path} → {event.dest_path}")
        kafka_event = self._create_event(event, 'moved')
        kafka_event['raw_data']['dest_path'] = event.dest_path
        self._send_to_kafka(kafka_event)


class FileIngestion:
    """Main ingestion service for file integrity monitoring"""
    
    DEFAULT_WATCH_PATHS = [
        '/tmp',  # Temporary files (common malware staging area)
        # Add more paths as needed:
        # '/etc',  # System configs (requires root)
        # '/var/www',  # Web server
        # '/opt',  # Applications
    ]
    
    def __init__(self,
                 kafka_broker: str = None,
                 watch_paths: List[str] = None,
                 recursive: bool = True,
                 send_to_sandbox: bool = True):
        """
        Initialize file integrity monitoring
        
        Args:
            kafka_broker: Kafka broker address
            watch_paths: Directories to monitor
            recursive: Monitor subdirectories
            send_to_sandbox: Send suspicious files to sandbox
        """
        self.kafka_broker = kafka_broker or os.getenv('KAFKA_BROKER', 'localhost:9092')
        self.watch_paths = watch_paths or self.DEFAULT_WATCH_PATHS
        self.recursive = recursive
        self.send_to_sandbox = send_to_sandbox
        
        # Initialize Kafka producer
        self.producer = self._create_producer()
        
        # Initialize observer and event handler
        self.observer = Observer()
        self.event_handler = FileEventHandler(
            self.producer,
            self.watch_paths,
            send_to_sandbox
        )
        
        logger.info(f"Initialized file monitoring for {len(self.watch_paths)} paths")
    
    def _create_producer(self) -> KafkaProducer:
        """Create Kafka producer"""
        return KafkaProducer(
            bootstrap_servers=self.kafka_broker,
            value_serializer=lambda v: json.dumps(v, default=str).encode('utf-8'),
            key_serializer=lambda k: k.encode('utf-8') if k else None,
            acks='all',
            retries=3
        )
    
    def run(self):
        """Start file monitoring"""
        logger.info("Starting file integrity monitoring...")
        logger.info(f"Monitored paths: {self.watch_paths}")
        logger.info(f"Recursive: {self.recursive}")
        logger.info(f"Send to sandbox: {self.send_to_sandbox}")
        
        # Schedule monitoring for each path
        for path in self.watch_paths:
            if not os.path.exists(path):
                logger.warning(f"Path does not exist: {path}")
                continue
            
            self.observer.schedule(
                self.event_handler,
                path,
                recursive=self.recursive
            )
            logger.info(f"✓ Monitoring: {path}")
        
        # Start observer
        self.observer.start()
        logger.info("File monitoring active. Press Ctrl+C to stop.")
        
        try:
            while True:
                time.sleep(10)
                # Log periodic stats
                logger.info(f"Events processed: {self.event_handler.event_count}")
        
        except KeyboardInterrupt:
            logger.info("\nStopping file monitoring...")
            self.observer.stop()
        
        self.observer.join()
        self.producer.close()
        logger.info(f"Total events processed: {self.event_handler.event_count}")


def main():
    """
    Main entry point for file monitoring
    
    Usage:
        # Monitor default paths (/tmp)
        python file_ingestion.py
        
        # Monitor custom paths
        python file_ingestion.py --paths /opt/app /var/www/html
        
        # Monitor without recursive
        python file_ingestion.py --paths /etc --no-recursive
    """
    import argparse
    
    parser = argparse.ArgumentParser(description='ThreatLens File Ingestion (P2)')
    parser.add_argument('--kafka', type=str, default='localhost:9092',
                       help='Kafka broker')
    parser.add_argument('--paths', nargs='+', 
                       help='Paths to monitor (default: /tmp)')
    parser.add_argument('--no-recursive', action='store_true',
                       help='Do not monitor subdirectories')
    parser.add_argument('--no-sandbox', action='store_true',
                       help='Do not send suspicious files to sandbox')
    
    args = parser.parse_args()
    
    # Validate paths
    watch_paths = args.paths or ['/tmp']
    for path in watch_paths:
        if not os.path.exists(path):
            logger.error(f"Path does not exist: {path}")
            sys.exit(1)
        if not os.access(path, os.R_OK):
            logger.error(f"No read permission for: {path}")
            sys.exit(1)
    
    # Create ingestion service
    ingestion = FileIngestion(
        kafka_broker=args.kafka,
        watch_paths=watch_paths,
        recursive=not args.no_recursive,
        send_to_sandbox=not args.no_sandbox
    )
    
    # Run monitoring
    ingestion.run()


if __name__ == '__main__':
    main()