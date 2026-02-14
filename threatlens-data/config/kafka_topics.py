"""
ThreatLens AI - Kafka Topics Configuration
Defines all topics used in the data pipeline with their settings
"""

from kafka.admin import KafkaAdminClient, NewTopic
from kafka.errors import TopicAlreadyExistsError
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Topic name constants for imports (e.g. rf_detector, ingestion)
RAW_NETWORK_EVENTS_TOPIC = "raw-network-events"
RAW_CAMERA_FRAMES_TOPIC = "raw-camera-frames"
RAW_RF_SIGNALS_TOPIC = "raw-rf-signals"
RAW_LOG_EVENTS_TOPIC = "raw-log-events"
RAW_FILE_EVENTS_TOPIC = "raw-file-events"
NETWORK_ANOMALY_SCORES_TOPIC = "network-anomaly-scores"
CAMERA_ANOMALY_SCORES_TOPIC = "camera-anomaly-scores"
RF_ANOMALY_SCORES_TOPIC = "rf-anomaly-scores"
LOG_ANOMALY_SCORES_TOPIC = "log-anomaly-scores"
FILE_ANOMALY_SCORES_TOPIC = "file-anomaly-scores"


class KafkaTopicManager:
    """Manages Kafka topic creation and configuration"""

    # Topic definitions with (name, partitions, replication_factor)
    TOPICS = {
        # ============================================
        # RAW INGESTION TOPICS (Stage 1)
        # ============================================
        'raw-network-events': {
            'partitions': 3,
            'replication_factor': 1,
            'retention_ms': 604800000,  # 7 days
            'description': 'Raw network flow data from switches/firewalls'
        },
        'raw-camera-frames': {
            'partitions': 2,
            'replication_factor': 1,
            'retention_ms': 86400000,  # 1 day (large video data)
            'description': 'Raw camera frames (base64 encoded)'
        },
        'raw-rf-signals': {
            'partitions': 2,
            'replication_factor': 1,
            'retention_ms': 604800000,  # 7 days
            'description': 'RF device detections (WiFi/BLE beacons)'
        },
        'raw-log-events': {
            'partitions': 3,
            'replication_factor': 1,
            'retention_ms': 2592000000,  # 30 days
            'description': 'System/application logs (Syslog, Windows Event)'
        },
        'raw-file-events': {
            'partitions': 2,
            'replication_factor': 1,
            'retention_ms': 604800000,  # 7 days
            'description': 'File system change events (watchdog)'
        },
        
        # ============================================
        # DNA-ENRICHED EVENTS (Stage 2)
        # ============================================
        'dna-enriched-events': {
            'partitions': 4,
            'replication_factor': 1,
            'retention_ms': 604800000,  # 7 days
            'description': 'Events with behavioral DNA deviation scores'
        },
        
        # ============================================
        # ANOMALY DETECTION OUTPUTS (Stage 3A-E)
        # ============================================
        'network-anomaly-scores': {
            'partitions': 3,
            'replication_factor': 1,
            'retention_ms': 2592000000,  # 30 days
            'description': 'Network anomalies (Isolation Forest + Autoencoder)'
        },
        'camera-anomaly-scores': {
            'partitions': 2,
            'replication_factor': 1,
            'retention_ms': 2592000000,  # 30 days
            'description': 'Camera anomalies (YOLOv8 + DeepSORT + rules)'
        },
        'rf-anomaly-scores': {
            'partitions': 2,
            'replication_factor': 1,
            'retention_ms': 2592000000,  # 30 days
            'description': 'RF anomalies (whitelist + z-score)'
        },
        'log-anomaly-scores': {
            'partitions': 3,
            'replication_factor': 1,
            'retention_ms': 2592000000,  # 30 days
            'description': 'Log anomalies (Random Forest + LSTM)'
        },
        'file-anomaly-scores': {
            'partitions': 2,
            'replication_factor': 1,
            'retention_ms': 2592000000,  # 30 days
            'description': 'File integrity anomalies (hash + rules)'
        },
        
        # ============================================
        # CORRELATION & INCIDENTS (Stage 4)
        # ============================================
        'correlated-incidents': {
            'partitions': 2,
            'replication_factor': 1,
            'retention_ms': 7776000000,  # 90 days
            'description': 'Cross-domain correlated security incidents'
        },
        'attack-graphs': {
            'partitions': 2,
            'replication_factor': 1,
            'retention_ms': 7776000000,  # 90 days
            'description': 'Causal attack graphs (for Neo4j ingestion)'
        },
        
        # ============================================
        # EVIDENCE & FORENSICS (Stage 5-6)
        # ============================================
        'evidence-manifest': {
            'partitions': 2,
            'replication_factor': 1,
            'retention_ms': 31536000000,  # 365 days (compliance)
            'description': 'Evidence collection manifests with MinIO paths'
        },
        'sandbox-queue': {
            'partitions': 1,
            'replication_factor': 1,
            'retention_ms': 604800000,  # 7 days
            'description': 'Files queued for sandbox detonation'
        },
        'sandbox-results': {
            'partitions': 2,
            'replication_factor': 1,
            'retention_ms': 7776000000,  # 90 days
            'description': 'Sandbox analysis results (malware verdicts)'
        },
        
        # ============================================
        # BLOCKCHAIN & EXPLANATIONS (Stage 7)
        # ============================================
        'blockchain-anchors': {
            'partitions': 1,
            'replication_factor': 1,
            'retention_ms': -1,  # Infinite retention (audit trail)
            'description': 'Evidence hash anchors on Polygon blockchain'
        },
        'nlg-explanations': {
            'partitions': 2,
            'replication_factor': 1,
            'retention_ms': 7776000000,  # 90 days
            'description': 'Natural language incident explanations (XAI + NLG)'
        },
        
        # ============================================
        # CONTROL & ALERTS
        # ============================================
        'soc-alerts': {
            'partitions': 2,
            'replication_factor': 1,
            'retention_ms': 2592000000,  # 30 days
            'description': 'Real-time SOC alerts for dashboard'
        },
        'system-health': {
            'partitions': 1,
            'replication_factor': 1,
            'retention_ms': 604800000,  # 7 days
            'description': 'Component health/metrics for monitoring'
        }
    }
    
    def __init__(self, bootstrap_servers=None):
        """Initialize Kafka admin client"""
        self.bootstrap_servers = bootstrap_servers or os.getenv('KAFKA_BROKER', 'localhost:9092')
        self.admin_client = None
    
    def connect(self):
        """Establish connection to Kafka cluster"""
        try:
            self.admin_client = KafkaAdminClient(
                bootstrap_servers=self.bootstrap_servers,
                client_id='threatlens-topic-manager'
            )
            logger.info(f"Connected to Kafka at {self.bootstrap_servers}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to Kafka: {e}")
            return False
    
    def create_all_topics(self):
        """Create all required topics"""
        if not self.admin_client:
            if not self.connect():
                return False
        
        topics_to_create = []
        for topic_name, config in self.TOPICS.items():
            topic = NewTopic(
                name=topic_name,
                num_partitions=config['partitions'],
                replication_factor=config['replication_factor'],
                topic_configs={
                    'retention.ms': str(config['retention_ms']),
                    'compression.type': 'lz4',
                    'max.message.bytes': '10485760'  # 10MB
                }
            )
            topics_to_create.append(topic)
        
        try:
            result = self.admin_client.create_topics(
                new_topics=topics_to_create,
                validate_only=False
            )
            logger.info(f"Successfully created {len(topics_to_create)} topics")
            return True
        except TopicAlreadyExistsError:
            logger.warning("Some topics already exist, skipping...")
            return True
        except Exception as e:
            logger.error(f"Failed to create topics: {e}")
            return False
    
    def list_topics(self):
        """List all existing topics"""
        if not self.admin_client:
            if not self.connect():
                return []
        
        try:
            topics = self.admin_client.list_topics()
            logger.info(f"Found {len(topics)} existing topics")
            return topics
        except Exception as e:
            logger.error(f"Failed to list topics: {e}")
            return []
    
    def delete_all_topics(self):
        """Delete all ThreatLens topics (use with caution!)"""
        if not self.admin_client:
            if not self.connect():
                return False
        
        topic_names = list(self.TOPICS.keys())
        try:
            self.admin_client.delete_topics(topics=topic_names)
            logger.warning(f"Deleted {len(topic_names)} topics")
            return True
        except Exception as e:
            logger.error(f"Failed to delete topics: {e}")
            return False
    
    def close(self):
        """Close admin client connection"""
        if self.admin_client:
            self.admin_client.close()
            logger.info("Closed Kafka admin client")


def get_topic_schema(topic_name):
    """
    Get the expected message schema for a given topic.
    Used for validation and documentation.
    """
    schemas = {
        'raw-network-events': {
            'event_id': 'str (uuid)',
            'timestamp': 'str (ISO8601)',
            'source_ip': 'str',
            'dest_ip': 'str',
            'source_port': 'int',
            'dest_port': 'int',
            'protocol': 'str (TCP/UDP/ICMP)',
            'bytes_sent': 'int',
            'bytes_received': 'int',
            'duration_seconds': 'float',
            'flags': 'str (TCP flags)',
            'host': 'str (device hostname)'
        },
        'raw-camera-frames': {
            'event_id': 'str (uuid)',
            'timestamp': 'str (ISO8601)',
            'camera_id': 'str',
            'zone': 'str',
            'frame_base64': 'str (base64 encoded)',
            'resolution': 'str (WIDTHxHEIGHT)',
            'fps': 'float'
        },
        'correlated-incidents': {
            'incident_id': 'str',
            'timestamp': 'str (ISO8601)',
            'risk_score': 'float (0-100)',
            'intent': 'str',
            'severity': 'str (low|medium|high|critical)',
            'correlated_events': 'list[dict]',
            'mitre_ttps': 'list[str]',
            'affected_entities': 'list[str]',
            'zones': 'list[str]'
        }
        # Add more schemas as needed...
    }
    return schemas.get(topic_name, {})


if __name__ == '__main__':
    """
    Standalone script to initialize all Kafka topics
    Usage: python kafka_topics.py
    """
    import argparse
    
    parser = argparse.ArgumentParser(description='Manage ThreatLens Kafka topics')
    parser.add_argument('--create', action='store_true', help='Create all topics')
    parser.add_argument('--list', action='store_true', help='List all topics')
    parser.add_argument('--delete', action='store_true', help='Delete all topics (DANGEROUS)')
    parser.add_argument('--broker', type=str, default='localhost:9092', help='Kafka broker address')
    
    args = parser.parse_args()
    
    manager = KafkaTopicManager(bootstrap_servers=args.broker)
    
    if args.create:
        manager.create_all_topics()
    elif args.list:
        topics = manager.list_topics()
        print(f"\nExisting topics: {topics}")
    elif args.delete:
        confirm = input("Are you sure you want to delete all topics? (yes/no): ")
        if confirm.lower() == 'yes':
            manager.delete_all_topics()
    else:
        print("No action specified. Use --create, --list, or --delete")
    
    manager.close()