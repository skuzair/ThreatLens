from .infer import DNAEngine
import random
import time

engine = DNAEngine()

entity_type = "device"
entity_id = "192.168.1.157"

for i in range(20):
    event = {
        "bytes_sent": random.randint(1000, 5000),
        "packets_sent": random.randint(10, 100),
        "hour_of_day": random.randint(0, 23)
    }

    result = engine.process_event(entity_type, entity_id, event)
    print(result)
    time.sleep(1)
