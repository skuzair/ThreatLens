from kafka_consumer import create_consumer
from kafka_producer import publish_result
from sandbox_orchestrator import execute_sandbox

def run():
    consumer = create_consumer()

    for message in consumer:
        input_data = message.value

        if input_data is None:
            continue

        result = execute_sandbox(input_data)
        publish_result(result)


if __name__ == "__main__":
    run()
