import json
import os


def create_producer():
    from kafka import KafkaProducer
    return KafkaProducer(
        bootstrap_servers=os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092"),
        value_serializer=lambda x: json.dumps(x).encode("utf-8"),
    )