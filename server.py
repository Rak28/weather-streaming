"""
gRPC WeatherService server
Serves processed weather events over a typed gRPC interface.
"""
import grpc
import json
import time
from concurrent import futures
from confluent_kafka import Consumer, KafkaError
import weather_pb2
import weather_pb2_grpc

KAFKA_BROKER = 'localhost:9092'
TOPIC = 'weather-events'
PORT = 50051
MAX_BUFFER = 1000

# In-memory buffer of recent events
event_buffer: list[dict] = []

class WeatherServiceServicer(weather_pb2_grpc.WeatherServiceServicer):
    def GetLatestWeather(self, request, context):
        city_filter = request.city.lower() if request.city else None
        limit = request.limit if request.limit > 0 else 20

        filtered = [e for e in reversed(event_buffer) if not city_filter or e['city'].lower() == city_filter][:limit]
        events = [weather_pb2.WeatherEvent(**{k: v for k, v in e.items() if k != 'offset'}, offset=e.get('offset', 0)) for e in filtered]
        return weather_pb2.WeatherResponse(events=events, total=len(events))

    def StreamWeather(self, request, context):
        city_filter = request.city.lower() if request.city else None
        consumer = Consumer({'bootstrap.servers': KAFKA_BROKER, 'group.id': f'grpc-stream-{time.time()}', 'auto.offset.reset': 'latest'})
        consumer.subscribe([TOPIC])
        try:
            while context.is_active():
                msg = consumer.poll(1.0)
                if msg is None or msg.error():
                    continue
                event = json.loads(msg.value().decode())
                if city_filter and event['city'].lower() != city_filter:
                    continue
                yield weather_pb2.WeatherEvent(city=event['city'], temperature=event['temperature'], humidity=event['humidity'], wind_speed=event['wind_speed'], condition=event['condition'], timestamp=event['timestamp'], partition=msg.partition(), offset=msg.offset())
        finally:
            consumer.close()

def kafka_buffer_worker():
    """Background thread: keeps event_buffer updated from Kafka."""
    consumer = Consumer({'bootstrap.servers': KAFKA_BROKER, 'group.id': 'grpc-buffer', 'auto.offset.reset': 'latest'})
    consumer.subscribe([TOPIC])
    while True:
        msg = consumer.poll(0.5)
        if msg and not msg.error():
            event = json.loads(msg.value().decode())
            event_buffer.append(event)
            if len(event_buffer) > MAX_BUFFER:
                event_buffer.pop(0)

def serve():
    import threading
    threading.Thread(target=kafka_buffer_worker, daemon=True).start()
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    weather_pb2_grpc.add_WeatherServiceServicer_to_server(WeatherServiceServicer(), server)
    server.add_insecure_port(f'[::]:{PORT}')
    server.start()
    print(f"gRPC WeatherService listening on port {PORT}")
    server.wait_for_termination()

if __name__ == '__main__':
    serve()