from confluent_kafka import Consumer, KafkaError
from typing import Callable, List
import json
import asyncio
from config import settings


class BaseConsumer:
    """Base Kafka consumer class"""
    
    def __init__(self, topics: List[str], group_id: str = None):
        self.topics = topics
        self.consumer = Consumer({
            "bootstrap.servers": settings.KAFKA_BOOTSTRAP_SERVERS,
            "group.id": group_id or settings.KAFKA_GROUP_ID,
            "auto.offset.reset": "latest",
            "enable.auto.commit": True
        })
        self.consumer.subscribe(topics)
        self.running = False
    
    async def run(self):
        """Main consumer loop"""
        self.running = True
        print(f"🎧 Kafka consumer started for topics: {self.topics}")
        
        while self.running:
            try:
                msg = self.consumer.poll(timeout=0.1)
                
                if msg is None:
                    await asyncio.sleep(0.01)
                    continue
                
                if msg.error():
                    if msg.error().code() == KafkaError._PARTITION_EOF:
                        continue
                    else:
                        print(f"❌ Kafka error: {msg.error()}")
                        continue
                
                # Parse message
                try:
                    data = json.loads(msg.value().decode('utf-8'))
                    topic = msg.topic()
                    
                    # Route to appropriate handler
                    await self.handle_message(topic, data)
                    
                except json.JSONDecodeError as e:
                    print(f"❌ Failed to decode JSON from {msg.topic()}: {e}")
                except Exception as e:
                    print(f"❌ Error handling message from {msg.topic()}: {e}")
            
            except Exception as e:
                print(f"❌ Consumer loop error: {e}")
                await asyncio.sleep(1)
    
    async def handle_message(self, topic: str, data: dict):
        """Override this method in subclasses"""
        raise NotImplementedError("Subclasses must implement handle_message")
    
    def stop(self):
        """Stop the consumer"""
        self.running = False
        self.consumer.close()
        print(f"🛑 Kafka consumer stopped for topics: {self.topics}")
