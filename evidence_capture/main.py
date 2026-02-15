import os
import time
import json
from kafka import KafkaConsumer
from kafka.errors import NoBrokersAvailable
from orchestrator import process_incident
import asyncio

BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")

def get_consumer():
    retries = 15
    for i in range(retries):
        try:
            print(f"[Evidence] Connecting consumer to Kafka (attempt {i+1})...")
            consumer = KafkaConsumer(
                "correlated-incidents",
                bootstrap_servers=BOOTSTRAP_SERVERS,
                value_deserializer=lambda m: json.loads(m.decode("utf-8")),
                auto_offset_reset="earliest",
                enable_auto_commit=True,
                group_id="evidence-capture-group"
            )
            print("[Evidence] Consumer connected to Kafka")
            return consumer
        except NoBrokersAvailable:
            print("[Evidence] Kafka not ready for consumer, retrying...")
            time.sleep(3)

    raise Exception("Kafka not available after retries")

async def main():
    consumer = get_consumer()
    print("[Evidence] Service started. Listening for incidents...")

    for message in consumer:
        incident = message.value
        print(f"[Evidence] Received incident: {incident['incident_id']}")
        await process_incident(incident)

if __name__ == "__main__":
    asyncio.run(main())
