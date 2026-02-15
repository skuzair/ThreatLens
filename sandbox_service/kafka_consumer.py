from kafka import KafkaConsumer
import json
from config import BOOTSTRAP_SERVERS, SANDBOX_TOPIC_IN

def safe_json_deserializer(message):
    try:
        return json.loads(message.decode("utf-8"))
    except Exception:
        return None

def create_consumer():
    return KafkaConsumer(
        SANDBOX_TOPIC_IN,
        bootstrap_servers=BOOTSTRAP_SERVERS,
        value_deserializer=safe_json_deserializer,
        auto_offset_reset="earliest",
        enable_auto_commit=True
    )
