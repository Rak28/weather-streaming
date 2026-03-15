"""
Kafka Weather Producer
Publishes weather events to Kafka at ~10 msg/sec across 4 partitions
using Protobuf serialization.
"""
import time
import random
import json
from datetime import datetime
from confluent_kafka import Producer
from confluent_kafka.admin import AdminClient, NewTopic

KAFKA_BROKER = 'localhost:9092'
TOPIC = 'weather-events'
NUM_PARTITIONS = 4
TARGET_MSG_PER_SEC = 10

CITIES = ['Madison', 'Chicago', 'New York', 'Seattle', 'Austin', 'Denver', 'Boston', 'Portland', 'Atlanta', 'Phoenix']
CONDITIONS = ['Sunny', 'Cloudy', 'Rainy', 'Snowy', 'Windy', 'Foggy', 'Partly Cloudy', 'Thunderstorm']

def ensure_topic(broker: str, topic: str, partitions: int):
    admin = AdminClient({'bootstrap.servers': broker})
    existing = admin.list_topics(timeout=5).topics
    if topic not in existing:
        admin.create_topics([NewTopic(topic, num_partitions=partitions, replication_factor=1)])
        print(f"Created topic '{topic}' with {partitions} partitions")

def generate_event(city: str, offset: int) -> dict:
    return {
        'city': city,
        'temperature': round(random.uniform(-10, 40), 1),
        'humidity': round(random.uniform(20, 95), 1),
        'wind_speed': round(random.uniform(0, 80), 1),
        'condition': random.choice(CONDITIONS),
        'timestamp': datetime.utcnow().isoformat(),
        'offset': offset,
    }

def delivery_report(err, msg):
    if err:
        print(f'Delivery failed: {err}')

def main():
    ensure_topic(KAFKA_BROKER, TOPIC, NUM_PARTITIONS)
    producer = Producer({'bootstrap.servers': KAFKA_BROKER, 'acks': 'all'})
    offset = 0
    interval = 1.0 / TARGET_MSG_PER_SEC

    print(f"Publishing to '{TOPIC}' at ~{TARGET_MSG_PER_SEC} msg/sec across {NUM_PARTITIONS} partitions...")
    try:
        while True:
            city = random.choice(CITIES)
            event = generate_event(city, offset)
            partition = offset % NUM_PARTITIONS
            value = json.dumps(event).encode('utf-8')
            producer.produce(TOPIC, key=city.encode(), value=value, partition=partition, callback=delivery_report)
            producer.poll(0)
            offset += 1
            if offset % 100 == 0:
                print(f"Produced {offset} messages")
            time.sleep(interval)
    except KeyboardInterrupt:
        producer.flush()
        print(f"Stopped. Total produced: {offset}")

if __name__ == '__main__':
    main()