"""
ThreatLens AI - RF Signal Ingestion (Stage 1)
P2 Component: Captures WiFi/BLE signals and sends to Kafka

Supports TWO modes:
1. Synthetic: Generated WiFi/BLE beacons (default for testing)
2. Real capture: Using airmon-ng/hcitool (requires hardware)

Author: P2 Team
Handoff: Sends to P3's RF detector (whitelist + z-score analysis)
"""

import os
import sys
import json
import time
import random
import uuid
from datetime import datetime, timedelta
from kafka import KafkaProducer
from typing import Dict, List, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RFSignalGenerator:
    """Generates synthetic RF signals (WiFi/BLE) for testing"""
    
    def __init__(self, whitelist_path: str = None):
        """
        Initialize RF signal generator
        
        Args:
            whitelist_path: Path to rf_whitelist.json
        """
        self.whitelist_path = whitelist_path or 'config/rf_whitelist.json'
        self.authorized_devices = []
        self.rogue_devices = []
        
        self._load_whitelist()
        self._generate_rogue_devices()
    
    def _load_whitelist(self):
        """Load authorized devices from whitelist"""
        try:
            with open(self.whitelist_path, 'r') as f:
                config = json.load(f)
                self.authorized_devices = config.get('authorized_devices', [])
            logger.info(f"Loaded {len(self.authorized_devices)} authorized devices")
        except FileNotFoundError:
            logger.warning(f"Whitelist not found: {self.whitelist_path}")
            # Create default authorized devices
            self.authorized_devices = [
                {
                    'mac_address': 'AA:BB:CC:DD:EE:01',
                    'device_type': 'wifi_ap',
                    'vendor': 'Cisco',
                    'location': 'Floor 1',
                    'expected_signal_range': {'min_dbm': -70, 'max_dbm': -30}
                },
                {
                    'mac_address': '11:22:33:44:55:01',
                    'device_type': 'laptop',
                    'vendor': 'Dell',
                    'location': 'Mobile',
                    'expected_signal_range': {'min_dbm': -75, 'max_dbm': -30}
                }
            ]
    
    def _generate_rogue_devices(self):
        """Generate rogue/unauthorized devices for attack simulation"""
        self.rogue_devices = [
            {
                'mac_address': 'FF:FF:FF:00:00:01',
                'device_type': 'wifi_ap',
                'vendor': 'WiFi Pineapple',
                'ssid': 'Free_WiFi',
                'attack_type': 'rogue_ap'
            },
            {
                'mac_address': 'DE:AD:BE:EF:00:01',
                'device_type': 'laptop',
                'vendor': 'Unknown',
                'ssid': 'Corp_WiFi_Backup',
                'attack_type': 'evil_twin'
            },
            {
                'mac_address': 'BA:DD:CA:FE:00:01',
                'device_type': 'scanner',
                'vendor': 'Unknown',
                'attack_type': 'wifi_scanner'
            }
        ]
    
    def generate_authorized_signal(self) -> Dict:
        """Generate signal from authorized device"""
        device = random.choice(self.authorized_devices)
        signal_range = device.get('expected_signal_range', {'min_dbm': -80, 'max_dbm': -30})
        
        # Normal signal strength within expected range
        signal_dbm = random.uniform(signal_range['min_dbm'], signal_range['max_dbm'])
        
        # Add some noise
        signal_dbm += random.gauss(0, 2)  # ±2dBm noise
        
        return {
            'mac_address': device['mac_address'],
            'device_type': device['device_type'],
            'vendor': device.get('vendor', 'Unknown'),
            'signal_strength_dbm': round(signal_dbm, 1),
            'channel': random.choice([1, 6, 11, 36, 149]),  # Common WiFi channels
            'ssid': device.get('ssid', f"Corp-WiFi-{device['device_type']}"),
            'encryption': random.choice(['WPA2', 'WPA3']),
            'location': device.get('location', 'Unknown'),
            'is_authorized': True,
            'attack_type': None
        }
    
    def generate_rogue_signal(self, attack_type: str = 'random') -> Dict:
        """Generate signal from rogue/attack device"""
        if attack_type == 'random':
            device = random.choice(self.rogue_devices)
        else:
            device = next((d for d in self.rogue_devices if d['attack_type'] == attack_type), 
                         self.rogue_devices[0])
        
        attack_type = device['attack_type']
        
        if attack_type == 'rogue_ap':
            # Rogue access point with suspicious SSID
            signal_dbm = random.uniform(-60, -30)  # Strong signal
            ssid = device.get('ssid', 'Free_WiFi')
            encryption = 'Open'  # No encryption
        
        elif attack_type == 'evil_twin':
            # Evil twin AP (mimics legitimate network)
            signal_dbm = random.uniform(-65, -25)  # Very strong signal
            ssid = 'Corp-WiFi'  # Mimics real SSID
            encryption = 'WPA2'
        
        else:  # wifi_scanner
            # Rapid channel hopping (scanning)
            signal_dbm = random.uniform(-80, -50)
            ssid = ''
            encryption = 'Unknown'
        
        return {
            'mac_address': device['mac_address'],
            'device_type': device['device_type'],
            'vendor': device.get('vendor', 'Unknown'),
            'signal_strength_dbm': round(signal_dbm, 1),
            'channel': random.choice(range(1, 14)),  # Scanning all channels
            'ssid': ssid,
            'encryption': encryption,
            'location': 'Unknown',
            'is_authorized': False,
            'attack_type': attack_type
        }
    
    def generate_deauth_attack(self) -> List[Dict]:
        """Generate deauthentication attack signals"""
        # Deauth attacks send many deauth frames
        signals = []
        target_device = random.choice(self.authorized_devices)
        attacker_mac = random.choice(self.rogue_devices)['mac_address']
        
        for i in range(50):  # 50 deauth frames
            signals.append({
                'mac_address': attacker_mac,
                'device_type': 'attacker',
                'vendor': 'Unknown',
                'signal_strength_dbm': random.uniform(-70, -40),
                'channel': 6,
                'ssid': '',
                'encryption': 'Unknown',
                'location': 'Unknown',
                'is_authorized': False,
                'attack_type': 'deauth_flood',
                'target_mac': target_device['mac_address']
            })
        
        return signals


class RFIngestion:
    """Main ingestion service for RF signals"""
    
    def __init__(self,
                 kafka_broker: str = None,
                 whitelist_path: str = None,
                 use_synthetic: bool = True):
        """
        Initialize RF ingestion
        
        Args:
            kafka_broker: Kafka broker address
            whitelist_path: Path to rf_whitelist.json
            use_synthetic: Use synthetic generator (True = default)
        """
        self.kafka_broker = kafka_broker or os.getenv('KAFKA_BROKER', 'localhost:9092')
        self.use_synthetic = use_synthetic
        
        # Initialize Kafka producer
        self.producer = self._create_producer()
        
        # Initialize data source
        if use_synthetic:
            self.signal_generator = RFSignalGenerator(whitelist_path)
            logger.info("Using synthetic RF signal generator")
        else:
            logger.error("Real RF capture not implemented yet - use --synthetic")
            logger.error("Requires: airmon-ng, airodump-ng, or hcitool")
            sys.exit(1)
    
    def _create_producer(self) -> KafkaProducer:
        """Create Kafka producer"""
        return KafkaProducer(
            bootstrap_servers=self.kafka_broker,
            value_serializer=lambda v: json.dumps(v).encode('utf-8'),
            key_serializer=lambda k: k.encode('utf-8') if k else None,
            acks='all',
            retries=3
        )
    
    def create_event(self, signal_data: Dict) -> Dict:
        """Create normalized RF event"""
        return {
            'event_id': str(uuid.uuid4()),
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'source_type': 'rf',
            'host': signal_data['mac_address'],
            'zone': signal_data.get('location', 'network'),
            'raw_data': signal_data,
            'anomaly_score': 0.0,  # Will be set by P3's RF detector
            'severity': 'high' if not signal_data.get('is_authorized', False) else 'low',
            'dna_deviation_score': 0.0
        }
    
    def send_to_kafka(self, event: Dict, topic: str = 'raw-rf-signals'):
        """Send RF event to Kafka"""
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
    
    def run_synthetic_mode(self,
                          signals_per_batch: int = 20,
                          attack_ratio: float = 0.1,
                          interval_seconds: float = 2.0,
                          deauth_attack_interval: int = 50):
        """
        Run continuous synthetic RF signal generation
        
        Args:
            signals_per_batch: Signals per batch
            attack_ratio: Percentage of rogue signals
            interval_seconds: Delay between batches
            deauth_attack_interval: Trigger deauth attack every N batches
        """
        logger.info(f"Starting synthetic RF mode: {signals_per_batch} signals/batch, "
                   f"{attack_ratio*100}% attacks")
        
        batch_count = 0
        total_sent = 0
        
        try:
            while True:
                batch_count += 1
                batch_signals = []
                
                # Generate normal signals
                for i in range(signals_per_batch):
                    if random.random() < attack_ratio:
                        signal_data = self.signal_generator.generate_rogue_signal()
                    else:
                        signal_data = self.signal_generator.generate_authorized_signal()
                    
                    batch_signals.append(signal_data)
                
                # Occasionally inject deauth attack
                if batch_count % deauth_attack_interval == 0:
                    logger.warning("🚨 Simulating deauth attack!")
                    deauth_signals = self.signal_generator.generate_deauth_attack()
                    batch_signals.extend(deauth_signals)
                
                # Send all signals
                for signal_data in batch_signals:
                    event = self.create_event(signal_data)
                    if self.send_to_kafka(event):
                        total_sent += 1
                
                # Log summary
                authorized_count = sum(1 for s in batch_signals if s.get('is_authorized', False))
                rogue_count = len(batch_signals) - authorized_count
                
                logger.info(f"Batch {batch_count}: Sent {len(batch_signals)} signals "
                           f"(Authorized: {authorized_count}, Rogue: {rogue_count}, "
                           f"Total: {total_sent})")
                
                time.sleep(interval_seconds)
        
        except KeyboardInterrupt:
            logger.info(f"\nStopped. Total signals sent: {total_sent}")
            self.producer.close()


def main():
    """
    Main entry point for RF ingestion
    
    Usage:
        # Synthetic mode (default)
        python rf_ingestion.py --signals 20 --attacks 0.15
        
        # With custom whitelist
        python rf_ingestion.py --whitelist config/rf_whitelist.json
    """
    import argparse
    
    parser = argparse.ArgumentParser(description='ThreatLens RF Ingestion (P2)')
    parser.add_argument('--kafka', type=str, default='localhost:9092',
                       help='Kafka broker')
    parser.add_argument('--whitelist', type=str, default='config/rf_whitelist.json',
                       help='Path to RF whitelist')
    parser.add_argument('--signals', type=int, default=20,
                       help='Signals per batch')
    parser.add_argument('--attacks', type=float, default=0.1,
                       help='Attack ratio (0.0-1.0)')
    parser.add_argument('--interval', type=float, default=2.0,
                       help='Seconds between batches')
    parser.add_argument('--deauth-interval', type=int, default=50,
                       help='Deauth attack every N batches')
    parser.add_argument('--synthetic', action='store_true', default=True,
                       help='Use synthetic generator (default: True)')
    
    args = parser.parse_args()
    
    # Create ingestion service
    ingestion = RFIngestion(
        kafka_broker=args.kafka,
        whitelist_path=args.whitelist,
        use_synthetic=args.synthetic
    )
    
    # Run synthetic mode
    ingestion.run_synthetic_mode(
        signals_per_batch=args.signals,
        attack_ratio=args.attacks,
        interval_seconds=args.interval,
        deauth_attack_interval=args.deauth_interval
    )


if __name__ == '__main__':
    main()