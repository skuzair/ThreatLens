"""
ThreatLens AI - Elasticsearch Client
Handles event indexing, search, and retrieval for LLM copilot RAG
"""

from elasticsearch import Elasticsearch, helpers
from elasticsearch.exceptions import ConnectionError, NotFoundError
import os
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ElasticsearchClient:
    """Wrapper for Elasticsearch operations"""
    
    # Index mappings for different event types
    INDEX_MAPPINGS = {
        'events': {
            'mappings': {
                'properties': {
                    'event_id': {'type': 'keyword'},
                    'timestamp': {'type': 'date'},
                    'source_type': {'type': 'keyword'},
                    'zone': {'type': 'keyword'},
                    'host': {'type': 'keyword'},
                    'anomaly_score': {'type': 'float'},
                    'severity': {'type': 'keyword'},
                    'dna_deviation_score': {'type': 'float'},
                    'raw_data': {'type': 'object', 'enabled': False},
                    'message': {'type': 'text', 'analyzer': 'standard'},
                    'entity_id': {'type': 'keyword'},
                    'entity_type': {'type': 'keyword'}
                }
            },
            'settings': {
                'number_of_shards': 2,
                'number_of_replicas': 0,
                'index.lifecycle.name': 'threatlens-events-policy',
                'index.lifecycle.rollover_alias': 'threatlens-events'
            }
        },
        'incidents': {
            'mappings': {
                'properties': {
                    'incident_id': {'type': 'keyword'},
                    'timestamp': {'type': 'date'},
                    'risk_score': {'type': 'float'},
                    'severity': {'type': 'keyword'},
                    'intent': {'type': 'keyword'},
                    'mitre_ttps': {'type': 'keyword'},
                    'affected_entities': {'type': 'keyword'},
                    'zones': {'type': 'keyword'},
                    'correlated_events': {'type': 'nested'},
                    'evidence_links': {'type': 'keyword'},
                    'description': {'type': 'text'},
                    'status': {'type': 'keyword'},  # open, investigating, resolved
                    'assigned_to': {'type': 'keyword'}
                }
            },
            'settings': {
                'number_of_shards': 1,
                'number_of_replicas': 0
            }
        },
        'anomalies': {
            'mappings': {
                'properties': {
                    'event_id': {'type': 'keyword'},
                    'timestamp': {'type': 'date'},
                    'source_type': {'type': 'keyword'},
                    'anomaly_score': {'type': 'float'},
                    'model_type': {'type': 'keyword'},
                    'features': {'type': 'object'},
                    'zone': {'type': 'keyword'},
                    'explanation': {'type': 'text'}
                }
            }
        }
    }
    
    def __init__(self, host=None, user=None, password=None, index_prefix=None):
        """
        Initialize Elasticsearch client
        
        Args:
            host: Elasticsearch host (default from env)
            user: Username (default from env)
            password: Password (default from env)
            index_prefix: Prefix for all indices (default from env)
        """
        self.host = host or os.getenv('ELASTICSEARCH_HOST', 'localhost:9200')
        self.user = user or os.getenv('ELASTICSEARCH_USER', 'elastic')
        self.password = password or os.getenv('ELASTICSEARCH_PASSWORD', 'changeme')
        self.index_prefix = index_prefix or os.getenv('ELASTICSEARCH_INDEX_PREFIX', 'threatlens')
        
        self.client = None
        self._connect()
    
    def _connect(self):
        """Establish connection to Elasticsearch"""
        try:
            # Try with authentication first
            self.client = Elasticsearch(
                [f'http://{self.host}'],
                basic_auth=(self.user, self.password),
                verify_certs=False,
                request_timeout=30
            )
            
            # Test connection
            if self.client.ping():
                logger.info(f"Connected to Elasticsearch at {self.host}")
                info = self.client.info()
                logger.info(f"Elasticsearch version: {info['version']['number']}")
            else:
                # Try without auth
                self.client = Elasticsearch([f'http://{self.host}'], verify_certs=False)
                if self.client.ping():
                    logger.info(f"Connected to Elasticsearch (no auth) at {self.host}")
                else:
                    raise ConnectionError("Cannot connect to Elasticsearch")
                    
        except Exception as e:
            logger.error(f"Failed to connect to Elasticsearch: {e}")
            # Create a dummy client for graceful degradation
            self.client = None
    
    def create_index(self, index_type: str) -> bool:
        """
        Create an index with predefined mapping
        
        Args:
            index_type: Type of index (events, incidents, anomalies)
            
        Returns:
            True if successful
        """
        if not self.client:
            return False
        
        index_name = f"{self.index_prefix}-{index_type}"
        
        try:
            if self.client.indices.exists(index=index_name):
                logger.info(f"Index {index_name} already exists")
                return True
            
            mapping = self.INDEX_MAPPINGS.get(index_type)
            if not mapping:
                logger.error(f"No mapping defined for index type: {index_type}")
                return False
            
            self.client.indices.create(index=index_name, body=mapping)
            logger.info(f"Created index: {index_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create index {index_name}: {e}")
            return False
    
    def create_all_indices(self) -> bool:
        """Create all predefined indices"""
        success = True
        for index_type in self.INDEX_MAPPINGS.keys():
            if not self.create_index(index_type):
                success = False
        return success
    
    def index_event(self, event: Dict, index_type: str = 'events') -> bool:
        """
        Index a single event
        
        Args:
            event: Event dictionary
            index_type: Index to use (events, incidents, anomalies)
            
        Returns:
            True if successful
        """
        if not self.client:
            return False
        
        index_name = f"{self.index_prefix}-{index_type}"
        
        try:
            # Ensure timestamp is in ISO format
            if 'timestamp' in event and isinstance(event['timestamp'], str):
                event['timestamp'] = event['timestamp']
            elif 'timestamp' not in event:
                event['timestamp'] = datetime.utcnow().isoformat()
            
            response = self.client.index(
                index=index_name,
                id=event.get('event_id') or event.get('incident_id'),
                document=event
            )
            
            return response['result'] in ['created', 'updated']
            
        except Exception as e:
            logger.error(f"Failed to index event: {e}")
            return False
    
    def bulk_index_events(self, events: List[Dict], index_type: str = 'events') -> int:
        """
        Bulk index multiple events for performance
        
        Args:
            events: List of event dictionaries
            index_type: Index to use
            
        Returns:
            Number of successfully indexed events
        """
        if not self.client or not events:
            return 0
        
        index_name = f"{self.index_prefix}-{index_type}"
        
        # Prepare bulk actions
        actions = []
        for event in events:
            # Ensure timestamp
            if 'timestamp' not in event:
                event['timestamp'] = datetime.utcnow().isoformat()
            
            action = {
                '_index': index_name,
                '_id': event.get('event_id') or event.get('incident_id'),
                '_source': event
            }
            actions.append(action)
        
        try:
            success, failed = helpers.bulk(
                self.client,
                actions,
                raise_on_error=False,
                stats_only=True
            )
            
            logger.info(f"Bulk indexed {success} events to {index_name} ({failed} failed)")
            return success
            
        except Exception as e:
            logger.error(f"Bulk index failed: {e}")
            return 0
    
    def search_events(self, 
                     query: Optional[Dict] = None,
                     index_type: str = 'events',
                     start_time: Optional[datetime] = None,
                     end_time: Optional[datetime] = None,
                     size: int = 100,
                     sort_by: str = 'timestamp',
                     sort_order: str = 'desc') -> List[Dict]:
        """
        Search for events with optional filters
        
        Args:
            query: Elasticsearch query DSL (None = match all)
            index_type: Index to search
            start_time: Filter events after this time
            end_time: Filter events before this time
            size: Maximum results to return
            sort_by: Field to sort by
            sort_order: 'asc' or 'desc'
            
        Returns:
            List of matching events
        """
        if not self.client:
            return []
        
        index_name = f"{self.index_prefix}-{index_type}"
        
        # Build query
        if query is None:
            query = {'match_all': {}}
        
        # Add time range filter if specified
        filters = []
        if start_time or end_time:
            time_range = {}
            if start_time:
                time_range['gte'] = start_time.isoformat()
            if end_time:
                time_range['lte'] = end_time.isoformat()
            filters.append({'range': {'timestamp': time_range}})
        
        # Combine query with filters
        search_body = {
            'query': {
                'bool': {
                    'must': [query],
                    'filter': filters
                }
            },
            'size': size,
            'sort': [{sort_by: {'order': sort_order}}]
        }
        
        try:
            response = self.client.search(index=index_name, body=search_body)
            events = [hit['_source'] for hit in response['hits']['hits']]
            logger.info(f"Found {len(events)} events in {index_name}")
            return events
            
        except NotFoundError:
            logger.warning(f"Index {index_name} not found")
            return []
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []
    
    def search_by_zone(self, zone: str, hours: int = 24, index_type: str = 'events') -> List[Dict]:
        """
        Search events by zone within time window
        
        Args:
            zone: Zone identifier (e.g., 'server_room')
            hours: Hours to look back
            index_type: Index to search
            
        Returns:
            List of events in that zone
        """
        start_time = datetime.utcnow() - timedelta(hours=hours)
        query = {'term': {'zone.keyword': zone}}
        return self.search_events(query=query, index_type=index_type, start_time=start_time)
    
    def search_by_entity(self, entity_id: str, hours: int = 24) -> List[Dict]:
        """
        Search all events for a specific entity (device/user/zone)
        
        Args:
            entity_id: Entity identifier
            hours: Hours to look back
            
        Returns:
            List of events related to entity
        """
        start_time = datetime.utcnow() - timedelta(hours=hours)
        query = {'term': {'entity_id.keyword': entity_id}}
        return self.search_events(query=query, start_time=start_time)
    
    def get_high_risk_incidents(self, threshold: float = 70.0, limit: int = 50) -> List[Dict]:
        """
        Get recent high-risk incidents for SOC dashboard
        
        Args:
            threshold: Minimum risk score
            limit: Maximum incidents to return
            
        Returns:
            List of high-risk incidents
        """
        query = {'range': {'risk_score': {'gte': threshold}}}
        return self.search_events(
            query=query,
            index_type='incidents',
            size=limit,
            sort_by='risk_score',
            sort_order='desc'
        )
    
    def aggregate_by_source(self, hours: int = 24) -> Dict:
        """
        Get event counts by source type
        
        Args:
            hours: Time window in hours
            
        Returns:
            Dictionary with counts per source type
        """
        if not self.client:
            return {}
        
        index_name = f"{self.index_prefix}-events"
        start_time = datetime.utcnow() - timedelta(hours=hours)
        
        agg_body = {
            'query': {
                'range': {
                    'timestamp': {'gte': start_time.isoformat()}
                }
            },
            'aggs': {
                'sources': {
                    'terms': {
                        'field': 'source_type.keyword',
                        'size': 10
                    }
                }
            },
            'size': 0
        }
        
        try:
            response = self.client.search(index=index_name, body=agg_body)
            buckets = response['aggregations']['sources']['buckets']
            return {b['key']: b['doc_count'] for b in buckets}
        except Exception as e:
            logger.error(f"Aggregation failed: {e}")
            return {}
    
    def get_context_for_llm(self, question: str, limit: int = 10) -> List[Dict]:
        """
        Get relevant context for LLM copilot (RAG)
        
        Args:
            question: User's natural language question
            limit: Maximum context documents
            
        Returns:
            List of relevant events/incidents
        """
        if not self.client:
            return []
        
        # Simple text search across events and incidents
        # In production, use vector embeddings for better retrieval
        query = {
            'multi_match': {
                'query': question,
                'fields': ['message', 'description', 'zone', 'entity_id'],
                'type': 'best_fields'
            }
        }
        
        # Search both events and incidents
        events = self.search_events(query=query, index_type='events', size=limit//2)
        incidents = self.search_events(query=query, index_type='incidents', size=limit//2)
        
        return events + incidents
    
    def delete_old_events(self, days: int = 90, index_type: str = 'events') -> int:
        """
        Delete events older than specified days (for compliance)
        
        Args:
            days: Age threshold in days
            index_type: Index to clean
            
        Returns:
            Number of deleted documents
        """
        if not self.client:
            return 0
        
        index_name = f"{self.index_prefix}-{index_type}"
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        delete_query = {
            'query': {
                'range': {
                    'timestamp': {'lt': cutoff_date.isoformat()}
                }
            }
        }
        
        try:
            response = self.client.delete_by_query(index=index_name, body=delete_query)
            deleted = response.get('deleted', 0)
            logger.info(f"Deleted {deleted} events older than {days} days from {index_name}")
            return deleted
        except Exception as e:
            logger.error(f"Delete failed: {e}")
            return 0


# Singleton instance
_elasticsearch_client_instance = None


def get_elasticsearch_client() -> ElasticsearchClient:
    """Get singleton Elasticsearch client instance"""
    global _elasticsearch_client_instance
    if _elasticsearch_client_instance is None:
        _elasticsearch_client_instance = ElasticsearchClient()
    return _elasticsearch_client_instance


if __name__ == '__main__':
    """Test Elasticsearch client"""
    
    client = get_elasticsearch_client()
    
    if not client.client:
        print("✗ Cannot connect to Elasticsearch - is it running?")
        print("  Run: docker-compose up -d")
        exit(1)
    
    # Create indices
    print("Creating indices...")
    client.create_all_indices()
    
    # Index test event
    test_event = {
        'event_id': 'test-001',
        'timestamp': datetime.utcnow().isoformat(),
        'source_type': 'network',
        'zone': 'server_room',
        'host': '192.168.1.157',
        'anomaly_score': 85.5,
        'severity': 'high',
        'message': 'Unusual network traffic detected' 
    }
    
    if client.index_event(test_event):
        print("✓ Indexed test event")
    
    # Search test
    events = client.search_events(size=5)
    print(f"✓ Found {len(events)} recent events")
    
    # Aggregation test
    counts = client.aggregate_by_source(hours=24)
    print(f"✓ Event counts by source: {counts}")
    
    print("\n✅ Elasticsearch client tests passed!")