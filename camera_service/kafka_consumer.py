from kafka import KafkaConsumer
import json
from config import KAFKA_BOOTSTRAP_SERVERS, RAW_CAMERA_FRAMES_TOPIC
from main import process_event
from kafka_producer import send_result

consumer = KafkaConsumer(
    RAW_CAMERA_FRAMES_TOPIC,
    bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
    value_deserializer=lambda m: json.loads(m.decode('utf-8'))
)

for message in consumer:
    result = process_event(message.value)
    if result is not None:
        send_result(result)
