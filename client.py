"""
gRPC WeatherService client — example usage
"""
import grpc
import argparse
import weather_pb2
import weather_pb2_grpc

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--city', default='', help='Filter by city')
    parser.add_argument('--limit', type=int, default=10, help='Number of results')
    parser.add_argument('--stream', action='store_true', help='Stream live updates')
    args = parser.parse_args()

    with grpc.insecure_channel('localhost:50051') as channel:
        stub = weather_pb2_grpc.WeatherServiceStub(channel)
        req = weather_pb2.WeatherRequest(city=args.city, limit=args.limit)

        if args.stream:
            print(f"Streaming weather for '{args.city or 'all cities'}'...")
            for event in stub.StreamWeather(req):
                print(f"[P{event.partition}@{event.offset}] {event.city}: {event.temperature}°C, {event.condition}, wind {event.wind_speed}km/h")
        else:
            resp = stub.GetLatestWeather(req)
            print(f"Latest {resp.total} events:")
            for e in resp.events:
                print(f"  {e.city}: {e.temperature}°C, {e.humidity}% humidity, {e.condition}")

if __name__ == '__main__':
    main()