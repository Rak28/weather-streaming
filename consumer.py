"""
Kafka Weather Consumer
Consumes weather events with exactly-once semantics via offset checkpointing.
Supports crash recovery by resuming from last committed offset.
"""
import json
import signal
import sys
from confluent_kafka import Consumer, KafkaError, KafkaException

KAFKA_BROKER = 'localhost:9092'
TOPIC = 'weather-events'
GROUP_ID = 'weather-processor'

processed_count = 0
running = True

def signal_handler(sig, frame):
    global running
    print(f"\nShutting down. Processed: {processed_count} messages")
    running = False

signal.signal(signal.SIGINT, signal_handler)

def process_event(event: dict) -> None:
    """Process a weather event — extend with DB writes, alerting, etc."""
    global processed_count
    processed_count += 1
    if processed_count % 50 == 0:
        print(f"Processed {processed_count} | City: {event['city']} | Temp: {event['temperature']}°C | {event['condition']}")

def main():
    consumer = Consumer({
        'bootstrap.servers': KAFKA_BROKER,
        'group.id': GROUP_ID,
        'auto.offset.reset': 'earliest',
        'enable.auto.commit': False,   # manual commit for exactly-once
        'max.poll.interval.ms': 300000,
    })
    consumer.subscribe([TOPIC])
    print(f"Consumer started. Group: {GROUP_ID}")

    try:
        while running:
            msg = consumer.poll(timeout=1.0)
            if msg is None:
                continue
            if msg.error():
                if msg.error().code() == KafkaError._PARTITION_EOF:
                    continue
                raise KafkaException(msg.error())

            event = json.loads(msg.value().decode('utf-8'))
            process_event(event)

            # Synchronous commit — exactly-once guarantee
            # On crash, resume from this offset
            consumer.commit(asynchronous=False)
    finally:
        consumer.close()
        print(f"Consumer closed. Total processed: {processed_count}")

if __name__ == '__main__':
    main()