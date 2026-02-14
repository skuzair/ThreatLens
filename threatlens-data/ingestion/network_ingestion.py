"""
ThreatLens AI - Network Traffic Ingestion (Stage 1)
P2 Component: Reads network data and sends to Kafka

Supports TWO modes:
1. Real data: NSL-KDD dataset
2. Synthetic: Generated network flows

Author: P2 Team
Handoff: Sends to P4's network anomaly detection models
"""

import os
import sys
import json
import csv
import time
import random
import uuid
from datetime import datetime, timedelta
from kafka import KafkaProducer
from typing import Dict, Optional, List
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class NetworkDataGenerator:
    """Generates synthetic network flows for testing"""
    
    PROTOCOLS = ['TCP', 'UDP', 'ICMP']
    SERVICES = ['http', 'https', 'ssh', 'ftp', 'dns', 'smtp', 'rdp']
    FLAGS = ['S', 'SA', 'SF', 'R', 'PA', 'F']
    
    NORMAL_IPS = [
        '192.168.1.10', '192.168.1.15', '192.168.1.20',
        '192.168.1.25', '192.168.1.30', '192.168.1.157'
    ]
    
    ATTACK_IPS = [
        '203.0.113.5',  # C2 server
        '198.51.100.42',  # Scanner
        '192.0.2.99'  # Attacker
    ]
    
    def generate_normal_flow(self) -> Dict:
        """Generate a benign network flow"""
        src_ip = random.choice(self.NORMAL_IPS)
        dst_ip = random.choice(self.NORMAL_IPS)
        
        return {
            'source_ip': src_ip,
            'dest_ip': dst_ip,
            'source_port': random.randint(49152, 65535),  # Ephemeral ports
            'dest_port': random.choice([80, 443, 22, 53]),
            'protocol': random.choice(['TCP', 'UDP']),
            'bytes_sent': random.randint(100, 5000),
            'bytes_received': random.randint(100, 5000),
            'duration_seconds': round(random.uniform(0.1, 30.0), 2),
            'flags': random.choice(['SF', 'SA']),
            'service': random.choice(self.SERVICES)
        }
    
    def generate_attack_flow(self, attack_type: str = 'random') -> Dict:
        """Generate malicious network flow"""
        if attack_type == 'random':
            attack_type = random.choice(['port_scan', 'dos', 'exfiltration', 'c2'])
        
        if attack_type == 'port_scan':
            # Port scanning: many connections, small bytes
            return {
                'source_ip': random.choice(self.ATTACK_IPS),
                'dest_ip': random.choice(self.NORMAL_IPS),
                'source_port': random.randint(49152, 65535),
                'dest_port': random.randint(1, 1024),  # Scanning low ports
                'protocol': 'TCP',
                'bytes_sent': random.randint(40, 100),
                'bytes_received': 0,
                'duration_seconds': 0.01,
                'flags': 'S',  # SYN scan
                'service': 'other'
            }
        
        elif attack_type == 'dos':
            # DoS attack: high volume
            return {
                'source_ip': random.choice(self.ATTACK_IPS),
                'dest_ip': random.choice(self.NORMAL_IPS),
                'source_port': random.randint(1024, 65535),
                'dest_port': 80,
                'protocol': 'TCP',
                'bytes_sent': random.randint(50000, 200000),
                'bytes_received': random.randint(0, 100),
                'duration_seconds': round(random.uniform(0.1, 1.0), 2),
                'flags': 'S',
                'service': 'http'
            }
        
        elif attack_type == 'exfiltration':
            # Data exfiltration: large outbound bytes
            return {
                'source_ip': random.choice(self.NORMAL_IPS),
                'dest_ip': random.choice(self.ATTACK_IPS),
                'source_port': random.randint(49152, 65535),
                'dest_port': 443,
                'protocol': 'TCP',
                'bytes_sent': random.randint(100000, 500000),  # Large upload
                'bytes_received': random.randint(100, 1000),
                'duration_seconds': round(random.uniform(30.0, 120.0), 2),
                'flags': 'SF',
                'service': 'https'
            }
        
        else:  # c2 communication
            return {
                'source_ip': random.choice(self.NORMAL_IPS),
                'dest_ip': random.choice(self.ATTACK_IPS),
                'source_port': random.randint(49152, 65535),
                'dest_port': random.choice([8080, 4444, 31337]),
                'protocol': 'TCP',
                'bytes_sent': random.randint(500, 2000),
                'bytes_received': random.randint(500, 2000),
                'duration_seconds': round(random.uniform(1.0, 10.0), 2),
                'flags': 'SF',
                'service': 'other'
            }


class NSLKDDReader:
    """Reads NSL-KDD dataset and converts to our format"""
    
    # NSL-KDD column names (41 features + label)
    COLUMNS = [
        'duration', 'protocol_type', 'service', 'flag', 'src_bytes', 'dst_bytes',
        'land', 'wrong_fragment', 'urgent', 'hot', 'num_failed_logins', 'logged_in',
        'num_compromised', 'root_shell', 'su_attempted', 'num_root', 'num_file_creations',
        'num_shells', 'num_access_files', 'num_outbound_cmds', 'is_host_login',
        'is_guest_login', 'count', 'srv_count', 'serror_rate', 'srv_serror_rate',
        'rerror_rate', 'srv_rerror_rate', 'same_srv_rate', 'diff_srv_rate',
        'srv_diff_host_rate', 'dst_host_count', 'dst_host_srv_count',
        'dst_host_same_srv_rate', 'dst_host_diff_srv_rate', 'dst_host_same_src_port_rate',
        'dst_host_srv_diff_host_rate', 'dst_host_serror_rate', 'dst_host_srv_serror_rate',
        'dst_host_rerror_rate', 'dst_host_srv_rerror_rate', 'label', 'difficulty'
    ]
    
    def __init__(self, file_path: str):
        self.file_path = file_path
    
    def read_batch(self, batch_size: int = 100) -> List[Dict]:
        """Read a batch of records from NSL-KDD dataset"""
        events = []
        
        try:
            with open(self.file_path, 'r') as f:
                reader = csv.reader(f)
                for i, row in enumerate(reader):
                    if i >= batch_size:
                        break
                    
                    # Convert NSL-KDD row to our network event format
                    event = self._convert_nsl_kdd_row(row)
                    if event:
                        events.append(event)
            
            logger.info(f"Read {len(events)} events from NSL-KDD dataset")
            return events
            
        except FileNotFoundError:
            logger.error(f"Dataset not found: {self.file_path}")
            return []
        except Exception as e:
            logger.error(f"Error reading dataset: {e}")
            return []
    
    def _convert_nsl_kdd_row(self, row: List[str]) -> Optional[Dict]:
        """Convert NSL-KDD row to normalized event format"""
        try:
            # Map NSL-KDD features to our schema
            protocol_map = {'tcp': 'TCP', 'udp': 'UDP', 'icmp': 'ICMP'}
            
            return {
                'source_ip': f"192.168.1.{random.randint(1, 254)}",  # Simulated (not in NSL-KDD)
                'dest_ip': f"192.168.1.{random.randint(1, 254)}",
                'source_port': random.randint(1024, 65535),
                'dest_port': random.randint(1, 1024),
                'protocol': protocol_map.get(row[1].lower(), 'TCP'),
                'bytes_sent': int(float(row[4])),  # src_bytes
                'bytes_received': int(float(row[5])),  # dst_bytes
                'duration_seconds': float(row[0]),
                'flags': row[3],  # TCP flags
                'service': row[2],
                'is_attack': 0 if row[41] == 'normal' else 1,  # Label
                'attack_type': row[41]
            }
        except (IndexError, ValueError) as e:
            logger.warning(f"Failed to parse row: {e}")
            return None


class NetworkIngestion:
    """Main ingestion service for network traffic"""
    
    def __init__(self, 
                 kafka_broker: str = None,
                 dataset_path: str = None,
                 use_synthetic: bool = False):
        """
        Initialize network ingestion
        
        Args:
            kafka_broker: Kafka broker address
            dataset_path: Path to NSL-KDD dataset (if using real data)
            use_synthetic: Use synthetic data generator
        """
        self.kafka_broker = kafka_broker or os.getenv('KAFKA_BROKER', 'localhost:9092')
        self.dataset_path = dataset_path
        self.use_synthetic = use_synthetic
        
        # Initialize Kafka producer
        self.producer = self._create_producer()
        
        # Initialize data source
        if use_synthetic:
            self.data_generator = NetworkDataGenerator()
            logger.info("Using synthetic network data generator")
        elif dataset_path:
            self.dataset_reader = NSLKDDReader(dataset_path)
            logger.info(f"Using NSL-KDD dataset: {dataset_path}")
        else:
            logger.error("No data source configured! Set dataset_path or use_synthetic=True")
            sys.exit(1)
    
    def _create_producer(self) -> KafkaProducer:
        """Create Kafka producer with JSON serialization"""
        return KafkaProducer(
            bootstrap_servers=self.kafka_broker,
            value_serializer=lambda v: json.dumps(v).encode('utf-8'),
            key_serializer=lambda k: k.encode('utf-8') if k else None,
            acks='all',
            retries=3
        )
    
    def create_event(self, flow_data: Dict) -> Dict:
        """Create normalized network event"""
        return {
            'event_id': str(uuid.uuid4()),
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'source_type': 'network',
            'host': flow_data.get('source_ip'),
            'zone': 'network',  # Will be enriched by P4's detection layer
            'raw_data': flow_data,
            'anomaly_score': 0.0,  # Will be set by P4's models
            'severity': 'low',
            'dna_deviation_score': 0.0
        }
    
    def send_to_kafka(self, event: Dict, topic: str = 'raw-network-events'):
        """Send event to Kafka topic"""
        try:
            self.producer.send(
                topic,
                key=event['event_id'],
                value=event
            )
            self.producer.flush()
            return True
        except Exception as e:
            logger.error(f"Failed to send to Kafka: {e}")
            return False
    
    def run_synthetic_mode(self, events_per_batch: int = 10, 
                          attack_ratio: float = 0.2,
                          interval_seconds: float = 1.0):
        """
        Run continuous synthetic data generation
        
        Args:
            events_per_batch: Number of events per batch
            attack_ratio: Percentage of attack traffic (0.0 to 1.0)
            interval_seconds: Delay between batches
        """
        logger.info(f"Starting synthetic mode: {events_per_batch} events/batch, "
                   f"{attack_ratio*100}% attacks, {interval_seconds}s interval")
        
        batch_count = 0
        total_sent = 0
        
        try:
            while True:
                batch_count += 1
                
                for i in range(events_per_batch):
                    # Generate attack or normal flow
                    if random.random() < attack_ratio:
                        flow_data = self.data_generator.generate_attack_flow()
                    else:
                        flow_data = self.data_generator.generate_normal_flow()
                    
                    # Create and send event
                    event = self.create_event(flow_data)
                    if self.send_to_kafka(event):
                        total_sent += 1
                
                logger.info(f"Batch {batch_count}: Sent {events_per_batch} events "
                           f"(Total: {total_sent})")
                
                time.sleep(interval_seconds)
                
        except KeyboardInterrupt:
            logger.info(f"\nStopped. Total events sent: {total_sent}")
            self.producer.close()
    
    def run_dataset_mode(self, batch_size: int = 100, 
                        batches: int = 10,
                        interval_seconds: float = 1.0):
        """
        Run batch ingestion from NSL-KDD dataset
        
        Args:
            batch_size: Events per batch
            batches: Number of batches to send
            interval_seconds: Delay between batches
        """
        logger.info(f"Starting dataset mode: {batch_size} events/batch, "
                   f"{batches} batches, {interval_seconds}s interval")
        
        total_sent = 0
        
        try:
            for batch_num in range(batches):
                # Read batch from dataset
                flows = self.dataset_reader.read_batch(batch_size)
                
                if not flows:
                    logger.warning("No more data in dataset")
                    break
                
                # Send each flow
                for flow_data in flows:
                    event = self.create_event(flow_data)
                    if self.send_to_kafka(event):
                        total_sent += 1
                
                logger.info(f"Batch {batch_num + 1}/{batches}: Sent {len(flows)} events "
                           f"(Total: {total_sent})")
                
                time.sleep(interval_seconds)
        
        except KeyboardInterrupt:
            logger.info(f"\nStopped. Total events sent: {total_sent}")
        finally:
            self.producer.close()


def main():
    """
    Main entry point for network ingestion
    
    Usage:
        # Synthetic mode (no dataset needed)
        python network_ingestion.py --mode synthetic --events 20 --attacks 0.3
        
        # Dataset mode (requires NSL-KDD)
        python network_ingestion.py --mode dataset --path datasets/network/nsl-kdd/KDDTrain.txt
    """
    import argparse
    
    parser = argparse.ArgumentParser(description='ThreatLens Network Ingestion (P2)')
    parser.add_argument('--mode', choices=['synthetic', 'dataset'], required=True,
                       help='Data source mode')
    parser.add_argument('--path', type=str, help='Path to NSL-KDD dataset file')
    parser.add_argument('--kafka', type=str, default='localhost:9092',
                       help='Kafka broker address')
    parser.add_argument('--events', type=int, default=10,
                       help='Events per batch (synthetic mode)')
    parser.add_argument('--attacks', type=float, default=0.2,
                       help='Attack ratio 0.0-1.0 (synthetic mode)')
    parser.add_argument('--batches', type=int, default=10,
                       help='Number of batches (dataset mode)')
    parser.add_argument('--interval', type=float, default=1.0,
                       help='Seconds between batches')
    
    args = parser.parse_args()
    
    # Validate arguments
    if args.mode == 'dataset' and not args.path:
        parser.error("--path required for dataset mode")
    
    # Create ingestion service
    ingestion = NetworkIngestion(
        kafka_broker=args.kafka,
        dataset_path=args.path,
        use_synthetic=(args.mode == 'synthetic')
    )
    
    # Run appropriate mode
    if args.mode == 'synthetic':
        ingestion.run_synthetic_mode(
            events_per_batch=args.events,
            attack_ratio=args.attacks,
            interval_seconds=args.interval
        )
    else:
        ingestion.run_dataset_mode(
            batch_size=args.events,
            batches=args.batches,
            interval_seconds=args.interval
        )


if __name__ == '__main__':
    main()