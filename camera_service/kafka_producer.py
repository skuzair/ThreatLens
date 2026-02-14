from kafka import KafkaProducer
import json
from config import KAFKA_BOOTSTRAP_SERVERS, CAMERA_ANOMALY_SCORES_TOPIC

producer = KafkaProducer(
    bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

def send_result(message):
    producer.send(CAMERA_ANOMALY_SCORES_TOPIC, message)
    producer.flush()
