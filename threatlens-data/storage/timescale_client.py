"""
ThreatLens AI - TimescaleDB Client
Handles behavioral DNA baselines and time-series anomaly detection (Stage 2)
"""
from dotenv import load_dotenv
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


import psycopg2
from psycopg2.extras import RealDictCursor, execute_values
import os
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TimescaleDBClient:
    """Wrapper for TimescaleDB operations (PostgreSQL + time-series extension)"""
    
    # SQL table schemas
    TABLE_SCHEMAS = {
        'behavioral_baselines': """
            CREATE TABLE IF NOT EXISTS behavioral_baselines (
                time TIMESTAMPTZ NOT NULL,
                entity_id VARCHAR(255) NOT NULL,
                entity_type VARCHAR(50) NOT NULL,
                metric_name VARCHAR(100) NOT NULL,
                metric_value DOUBLE PRECISION NOT NULL,
                rolling_mean DOUBLE PRECISION,
                rolling_stddev DOUBLE PRECISION,
                sample_count INTEGER DEFAULT 1,
                PRIMARY KEY (time, entity_id, metric_name)
            );
            
            -- Convert to hypertable (time-series optimized)
            SELECT create_hypertable('behavioral_baselines', 'time', 
                                     if_not_exists => TRUE,
                                     chunk_time_interval => INTERVAL '1 day');
            
            -- Create indices for fast queries
            CREATE INDEX IF NOT EXISTS idx_baselines_entity 
                ON behavioral_baselines (entity_id, metric_name, time DESC);
            CREATE INDEX IF NOT EXISTS idx_baselines_type 
                ON behavioral_baselines (entity_type, time DESC);
        """,
        
        'dna_deviations': """
            CREATE TABLE IF NOT EXISTS dna_deviations (
                time TIMESTAMPTZ NOT NULL,
                event_id VARCHAR(255) NOT NULL,
                entity_id VARCHAR(255) NOT NULL,
                entity_type VARCHAR(50) NOT NULL,
                metric_name VARCHAR(100) NOT NULL,
                current_value DOUBLE PRECISION NOT NULL,
                baseline_mean DOUBLE PRECISION,
                baseline_stddev DOUBLE PRECISION,
                z_score DOUBLE PRECISION,
                deviation_severity VARCHAR(20),
                PRIMARY KEY (time, event_id, metric_name)
            );
            
            SELECT create_hypertable('dna_deviations', 'time',
                                     if_not_exists => TRUE,
                                     chunk_time_interval => INTERVAL '1 day');
            
            CREATE INDEX IF NOT EXISTS idx_deviations_entity
                ON dna_deviations (entity_id, time DESC);
            CREATE INDEX IF NOT EXISTS idx_deviations_severity
                ON dna_deviations (deviation_severity, time DESC);
        """,
        
        'entity_profiles': """
            CREATE TABLE IF NOT EXISTS entity_profiles (
                entity_id VARCHAR(255) PRIMARY KEY,
                entity_type VARCHAR(50) NOT NULL,
                first_seen TIMESTAMPTZ NOT NULL,
                last_seen TIMESTAMPTZ NOT NULL,
                total_events INTEGER DEFAULT 0,
                total_anomalies INTEGER DEFAULT 0,
                risk_score DOUBLE PRECISION DEFAULT 0.0,
                metadata JSONB,
                created_at TIMESTAMPTZ DEFAULT NOW(),
                updated_at TIMESTAMPTZ DEFAULT NOW()
            );
            
            CREATE INDEX IF NOT EXISTS idx_profiles_type
                ON entity_profiles (entity_type);
            CREATE INDEX IF NOT EXISTS idx_profiles_risk
                ON entity_profiles (risk_score DESC);
        """
    }
    
    def __init__(self, host=None, port=None, dbname=None, user=None, password=None):
        """
        Initialize TimescaleDB client
        
        Args:
            host: PostgreSQL host (default from env)
            port: PostgreSQL port (default from env)
            dbname: Database name (default from env)
            user: Username (default from env)
            password: Password (default from env)
        """
        self.host = host or os.getenv('TIMESCALE_HOST', 'localhost')
        self.port = port or os.getenv('TIMESCALE_PORT', '5432')
        self.dbname = dbname or os.getenv('TIMESCALE_DB', 'threatlens_dna')
        self.user = user or os.getenv('TIMESCALE_USER', 'postgres')
        self.password = password or os.getenv('TIMESCALE_PASSWORD', 'postgres')
        
        self.conn = None
        self._connect()
    
    def _connect(self):
        """Establish connection to TimescaleDB"""
        try:
            self.conn = psycopg2.connect(
                host=self.host,
                port=self.port,
                dbname=self.dbname,
                user=self.user,
                password=self.password
            )
            self.conn.autocommit = False
            logger.info(f"Connected to TimescaleDB at {self.host}:{self.port}/{self.dbname}")
            
            # Verify TimescaleDB extension
            with self.conn.cursor() as cur:
                cur.execute("SELECT extversion FROM pg_extension WHERE extname='timescaledb';")
                version = cur.fetchone()
                if version:
                    logger.info(f"TimescaleDB version: {version[0]}")
                else:
                    logger.warning("TimescaleDB extension not found - installing...")
                    cur.execute("CREATE EXTENSION IF NOT EXISTS timescaledb;")
                    self.conn.commit()
                    
        except psycopg2.Error as e:
            logger.error(f"Failed to connect to TimescaleDB: {e}")
            self.conn = None
    
    def initialize_schema(self) -> bool:
        """Create all tables and hypertables"""
        if not self.conn:
            return False
        
        try:
            with self.conn.cursor() as cur:
                for table_name, schema_sql in self.TABLE_SCHEMAS.items():
                    logger.info(f"Creating table: {table_name}")
                    cur.execute(schema_sql)
                self.conn.commit()
            logger.info("Schema initialization complete")
            return True
            
        except psycopg2.Error as e:
            logger.error(f"Schema initialization failed: {e}")
            self.conn.rollback()
            return False
    
    def insert_baseline(self, entity_id: str, entity_type: str, metric_name: str,
                       metric_value: float, timestamp: Optional[datetime] = None) -> bool:
        """
        Insert a behavioral baseline measurement
        
        Args:
            entity_id: Entity identifier (IP, user_id, zone_id)
            entity_type: Type (device, user, zone)
            metric_name: Metric being measured (e.g., 'bytes_per_min', 'login_count')
            metric_value: Current metric value
            timestamp: Measurement time (default: now)
            
        Returns:
            True if successful
        """
        if not self.conn:
            return False
        
        timestamp = timestamp or datetime.utcnow()
        
        sql = """
            INSERT INTO behavioral_baselines 
                (time, entity_id, entity_type, metric_name, metric_value)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (time, entity_id, metric_name) DO UPDATE
                SET metric_value = EXCLUDED.metric_value;
        """
        
        try:
            with self.conn.cursor() as cur:
                cur.execute(sql, (timestamp, entity_id, entity_type, metric_name, metric_value))
                self.conn.commit()
            return True
            
        except psycopg2.Error as e:
            logger.error(f"Failed to insert baseline: {e}")
            self.conn.rollback()
            return False
    
    def bulk_insert_baselines(self, baselines: List[Dict]) -> int:
        """
        Bulk insert multiple baseline measurements
        
        Args:
            baselines: List of dicts with keys: entity_id, entity_type, metric_name, metric_value, timestamp
            
        Returns:
            Number of inserted rows
        """
        if not self.conn or not baselines:
            return 0
        
        sql = """
            INSERT INTO behavioral_baselines 
                (time, entity_id, entity_type, metric_name, metric_value)
            VALUES %s
            ON CONFLICT (time, entity_id, metric_name) DO NOTHING;
        """
        
        values = [
            (
                b.get('timestamp', datetime.utcnow()),
                b['entity_id'],
                b['entity_type'],
                b['metric_name'],
                b['metric_value']
            )
            for b in baselines
        ]
        
        try:
            with self.conn.cursor() as cur:
                execute_values(cur, sql, values)
                self.conn.commit()
            logger.info(f"Bulk inserted {len(baselines)} baselines")
            return len(baselines)
            
        except psycopg2.Error as e:
            logger.error(f"Bulk insert failed: {e}")
            self.conn.rollback()
            return 0
    
    def calculate_rolling_baseline(self, entity_id: str, metric_name: str,
                                   window_hours: int = 168) -> Tuple[float, float]:
        """
        Calculate rolling mean and stddev for an entity's metric (DNA baseline)
        
        Args:
            entity_id: Entity to analyze
            metric_name: Metric to analyze
            window_hours: Rolling window size (default: 168 = 1 week)
            
        Returns:
            Tuple of (mean, stddev)
        """
        if not self.conn:
            return (0.0, 0.0)
        
        sql = """
            SELECT 
                AVG(metric_value) as mean,
                STDDEV(metric_value) as stddev
            FROM behavioral_baselines
            WHERE entity_id = %s
                AND metric_name = %s
                AND time > NOW() - INTERVAL '%s hours'
            GROUP BY entity_id, metric_name;
        """
        
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(sql, (entity_id, metric_name, window_hours))
                result = cur.fetchone()
                
                if result and result['mean'] is not None:
                    mean = float(result['mean'])
                    stddev = float(result['stddev']) if result['stddev'] else 0.1
                    return (mean, stddev)
                else:
                    return (0.0, 0.1)  # Default if no baseline exists
                    
        except psycopg2.Error as e:
            logger.error(f"Failed to calculate baseline: {e}")
            return (0.0, 0.1)
    
    def calculate_dna_deviation(self, entity_id: str, entity_type: str, metric_name: str,
                               current_value: float, window_hours: int = 168) -> float:
        """
        Calculate DNA deviation score (z-score) for current metric value
        
        Args:
            entity_id: Entity being measured
            entity_type: Entity type
            metric_name: Metric name
            current_value: Current measurement
            window_hours: Baseline window
            
        Returns:
            Z-score (number of standard deviations from mean)
        """
        mean, stddev = self.calculate_rolling_baseline(entity_id, metric_name, window_hours)
        
        if stddev == 0:
            stddev = 0.1  # Avoid division by zero
        
        z_score = abs((current_value - mean) / stddev)
        return z_score
    
    def insert_dna_deviation(self, event_id: str, entity_id: str, entity_type: str,
                            metric_name: str, current_value: float,
                            baseline_mean: float, baseline_stddev: float,
                            z_score: float, timestamp: Optional[datetime] = None) -> bool:
        """
        Record a DNA deviation event
        
        Args:
            event_id: Associated event ID
            entity_id: Entity identifier
            entity_type: Entity type
            metric_name: Metric that deviated
            current_value: Current metric value
            baseline_mean: Baseline mean
            baseline_stddev: Baseline stddev
            z_score: Calculated z-score
            timestamp: Event time
            
        Returns:
            True if successful
        """
        if not self.conn:
            return False
        
        timestamp = timestamp or datetime.utcnow()
        
        # Classify severity based on z-score
        if z_score < 2:
            severity = 'low'
        elif z_score < 3:
            severity = 'medium'
        elif z_score < 4:
            severity = 'high'
        else:
            severity = 'critical'
        
        sql = """
            INSERT INTO dna_deviations
                (time, event_id, entity_id, entity_type, metric_name,
                 current_value, baseline_mean, baseline_stddev, z_score, deviation_severity)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT DO NOTHING;
        """
        
        try:
            with self.conn.cursor() as cur:
                cur.execute(sql, (
                    timestamp, event_id, entity_id, entity_type, metric_name,
                    current_value, baseline_mean, baseline_stddev, z_score, severity
                ))
                self.conn.commit()
            return True
            
        except psycopg2.Error as e:
            logger.error(f"Failed to insert deviation: {e}")
            self.conn.rollback()
            return False
    
    def get_entity_deviations(self, entity_id: str, hours: int = 24) -> List[Dict]:
        """
        Get recent DNA deviations for an entity
        
        Args:
            entity_id: Entity to query
            hours: Time window
            
        Returns:
            List of deviation records
        """
        if not self.conn:
            return []
        
        sql = """
            SELECT * FROM dna_deviations
            WHERE entity_id = %s
                AND time > NOW() - INTERVAL '%s hours'
            ORDER BY time DESC;
        """
        
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(sql, (entity_id, hours))
                results = cur.fetchall()
                return [dict(row) for row in results]
                
        except psycopg2.Error as e:
            logger.error(f"Failed to get deviations: {e}")
            return []
    
    def upsert_entity_profile(self, entity_id: str, entity_type: str,
                             metadata: Optional[Dict] = None) -> bool:
        """
        Create or update an entity profile
        
        Args:
            entity_id: Entity identifier
            entity_type: Entity type
            metadata: Additional metadata (JSON)
            
        Returns:
            True if successful
        """
        if not self.conn:
            return False
        
        sql = """
            INSERT INTO entity_profiles (entity_id, entity_type, first_seen, last_seen, metadata)
            VALUES (%s, %s, NOW(), NOW(), %s)
            ON CONFLICT (entity_id) DO UPDATE SET
                last_seen = NOW(),
                total_events = entity_profiles.total_events + 1,
                metadata = EXCLUDED.metadata,
                updated_at = NOW();
        """
        
        try:
            with self.conn.cursor() as cur:
                cur.execute(sql, (entity_id, entity_type, json.dumps(metadata or {})))
                self.conn.commit()
            return True
            
        except psycopg2.Error as e:
            logger.error(f"Failed to upsert entity profile: {e}")
            self.conn.rollback()
            return False
    
    def get_high_risk_entities(self, limit: int = 20) -> List[Dict]:
        """
        Get entities with highest risk scores
        
        Args:
            limit: Maximum entities to return
            
        Returns:
            List of entity profiles
        """
        if not self.conn:
            return []
        
        sql = """
            SELECT * FROM entity_profiles
            ORDER BY risk_score DESC, total_anomalies DESC
            LIMIT %s;
        """
        
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(sql, (limit,))
                results = cur.fetchall()
                return [dict(row) for row in results]
                
        except psycopg2.Error as e:
            logger.error(f"Failed to get high-risk entities: {e}")
            return []
    
    def cleanup_old_data(self, days: int = 90) -> int:
        """
        Delete old baseline and deviation data (retention policy)
        
        Args:
            days: Age threshold in days
            
        Returns:
            Total rows deleted
        """
        if not self.conn:
            return 0
        
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        deleted_count = 0
        
        for table in ['behavioral_baselines', 'dna_deviations']:
            sql = f"DELETE FROM {table} WHERE time < %s;"
            
            try:
                with self.conn.cursor() as cur:
                    cur.execute(sql, (cutoff_date,))
                    deleted = cur.rowcount
                    deleted_count += deleted
                    logger.info(f"Deleted {deleted} rows from {table}")
                self.conn.commit()
                
            except psycopg2.Error as e:
                logger.error(f"Cleanup failed for {table}: {e}")
                self.conn.rollback()
        
        return deleted_count
    
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            logger.info("Closed TimescaleDB connection")


# Singleton instance
_timescale_client_instance = None


def get_timescale_client() -> TimescaleDBClient:
    """Get singleton TimescaleDB client instance"""
    global _timescale_client_instance
    if _timescale_client_instance is None:
        _timescale_client_instance = TimescaleDBClient()
    return _timescale_client_instance


if __name__ == '__main__':
    """Test TimescaleDB client"""
    
    client = get_timescale_client()
    
    if not client.conn:
        print("✗ Cannot connect to TimescaleDB - is it running?")
        print("  Run: docker-compose up -d")
        exit(1)
    
    # Initialize schema
    print("Initializing schema...")
    client.initialize_schema()
    
    # Insert test baselines
    print("Inserting test baselines...")
    for i in range(10):
        timestamp = datetime.utcnow() - timedelta(hours=i)
        client.insert_baseline(
            entity_id='192.168.1.157',
            entity_type='device',
            metric_name='bytes_per_min',
            metric_value=1500.0 + (i * 100),  # Simulated increasing traffic
            timestamp=timestamp
        )
    
    # Calculate baseline
    mean, stddev = client.calculate_rolling_baseline('192.168.1.157', 'bytes_per_min')
    print(f"✓ Calculated baseline: mean={mean:.2f}, stddev={stddev:.2f}")
    
    # Calculate deviation
    z_score = client.calculate_dna_deviation(
        '192.168.1.157', 'device', 'bytes_per_min', 3500.0
    )
    print(f"✓ DNA deviation z-score: {z_score:.2f}")
    
    # Insert deviation
    client.insert_dna_deviation(
        event_id='test-dev-001',
        entity_id='192.168.1.157',
        entity_type='device',
        metric_name='bytes_per_min',
        current_value=3500.0,
        baseline_mean=mean,
        baseline_stddev=stddev,
        z_score=z_score
    )
    
    # Get entity deviations
    deviations = client.get_entity_deviations('192.168.1.157', hours=24)
    print(f"✓ Found {len(deviations)} deviations for entity")
    
    # Upsert entity profile
    client.upsert_entity_profile(
        '192.168.1.157',
        'device',
        metadata={'hostname': 'workstation-01', 'department': 'IT'}
    )
    print("✓ Updated entity profile")
    
    print("\n✅ TimescaleDB client tests passed!")
    
    client.close()