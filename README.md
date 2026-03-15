# 🌤️ Distributed Weather Streaming System

A fault-tolerant, real-time weather data streaming pipeline built with **Kafka**, **gRPC**, and **Docker**. Processes **10 messages/sec** across **4 partitions** using Protobuf serialization and offset checkpointing to achieve exactly-once processing with crash recovery.

![Kafka](https://img.shields.io/badge/Kafka-231F20?style=flat&logo=apachekafka&logoColor=white)
![gRPC](https://img.shields.io/badge/gRPC-244c5a?style=flat&logo=google&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-2496ED?style=flat&logo=docker&logoColor=white)
![Python](https://img.shields.io/badge/Python-3776AB?style=flat&logo=python&logoColor=white)
![Protobuf](https://img.shields.io/badge/Protobuf-4285F4?style=flat&logo=google&logoColor=white)

## Features

- **High-throughput ingestion** — 10 messages/sec across 4 Kafka partitions
- **Protobuf serialization** — compact binary encoding via Protocol Buffers
- **Exactly-once processing** — offset checkpointing ensures no duplicates on crash recovery
- **gRPC API** — typed, low-latency service interface for weather data queries
- **Dockerized** — fully containerized with Docker Compose for local dev and deployment
- **Fault tolerance** — consumer groups with automatic partition rebalancing

## Architecture

```
Weather Sources (simulated)
        │
        ▼
┌───────────────────┐
│  Kafka Producer   │  Protobuf serialization
│  4 partitions     │  offset tracking
└────────┬──────────┘
         │
    ┌────▼────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐
    │ Part. 0 │  │ Part. 1 │  │ Part. 2 │  │ Part. 3 │
    └────┬────┘  └────┬────┘  └────┬────┘  └────┬────┘
         └────────────┴────────────┴─────────────┘
                           │
                  ┌────────▼────────┐
                  │  Kafka Consumer │  exactly-once
                  │  (consumer grp) │  crash recovery
                  └────────┬────────┘
                           │
                  ┌────────▼────────┐
                  │   gRPC Server   │  typed API
                  │  WeatherService │
                  └─────────────────┘
```

## Tech Stack

| Component | Technology |
|---|---|
| Message broker | Apache Kafka |
| Serialization | Protocol Buffers (Protobuf) |
| API layer | gRPC |
| Containerization | Docker, Docker Compose |
| Language | Python 3.11 |
| Consumer | confluent-kafka |

## Getting Started

### Prerequisites
- Docker & Docker Compose
- Python 3.11+

### Run with Docker Compose

```bash
docker-compose up
```

This starts Zookeeper, Kafka (4 partitions), the producer, consumer, and gRPC server.

### Run locally

```bash
pip install -r requirements.txt
python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. weather.proto

# Terminal 1 — Producer
python producer.py

# Terminal 2 — Consumer
python consumer.py

# Terminal 3 — gRPC server
python server.py
```

### Query via gRPC client

```bash
python client.py --city "Madison" --limit 10
```

## Kafka Configuration

```python
KAFKA_TOPIC = 'weather-events'
NUM_PARTITIONS = 4
REPLICATION_FACTOR = 1
MESSAGES_PER_SEC = 10
```

## Protobuf Schema

```protobuf
message WeatherEvent {
  string city = 1;
  float temperature = 2;
  float humidity = 3;
  float wind_speed = 4;
  string condition = 5;
  string timestamp = 6;
  int32 partition = 7;
  int64 offset = 8;
}
```

## Exactly-Once Semantics

Offset checkpointing is implemented by committing offsets only after successful processing:

```python
consumer.commit(asynchronous=False)  # synchronous commit after processing
```

On crash recovery, the consumer resumes from the last committed offset — ensuring no message is processed twice.

## Author

**Rakshith Sriraman Krishnaraj** · [LinkedIn](https://www.linkedin.com/in/rakshith-s-k-95b550151/) · [Google Scholar](https://scholar.google.com/citations?user=ErVb3bEAAAAJ&hl=en)