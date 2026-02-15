from kafka import KafkaProducer
import json
from config import BOOTSTRAP_SERVERS, SANDBOX_TOPIC_OUT

producer = KafkaProducer(
    bootstrap_servers=BOOTSTRAP_SERVERS,
    value_serializer=lambda v: json.dumps(v).encode("utf-8")
)

def publish_result(data):
    producer.send(SANDBOX_TOPIC_OUT, data)
    producer.flush()
