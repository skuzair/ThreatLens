import json
import os


def _safe_deserializer(x):
    try:
        return json.loads(x.decode("utf-8"))
    except Exception:
        return None


def create_consumer(topic="correlated-incidents"):
    from kafka import KafkaConsumer
    return KafkaConsumer(
        topic,
        bootstrap_servers=os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092"),
        auto_offset_reset="earliest",
        enable_auto_commit=True,
        group_id="nlg-service-group",
        value_deserializer=_safe_deserializer,
    )