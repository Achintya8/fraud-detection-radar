import argparse
import json
import os
import sys
import time
import httpx
from kafka import KafkaConsumer, KafkaProducer
from kafka.errors import KafkaError

# Add parent directory to path for app configs
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from app.config import settings


def json_deserializer(data):
    return json.loads(data.decode("utf-8"))


def json_serializer(data):
    return json.dumps(data).encode("utf-8")


def run_consumer(
    bootstrap_servers: str = settings.KAFKA_BOOTSTRAP_SERVERS,
    topic: str = settings.KAFKA_TOPIC_TRANSACTIONS,
    api_url: str = os.getenv("SCORING_API_URL", "http://localhost:8000/api/v1/score")
):
    print(f"[Consumer] Connecting to Kafka at {bootstrap_servers}...")
    try:
        consumer = KafkaConsumer(
            topic,
            bootstrap_servers=bootstrap_servers,
            value_deserializer=json_deserializer,
            auto_offset_reset="latest",
            group_id="fraud-radar-consumer-group",
            enable_auto_commit=True
        )
        producer = KafkaProducer(
            bootstrap_servers=bootstrap_servers,
            value_serializer=json_serializer
        )
        print(f"[Consumer] Subscribed to topic '{topic}'. Scoring API: {api_url}")
    except KafkaError as e:
        print(f"[Consumer] Error initializing Kafka consumer/producer: {e}")
        sys.exit(1)

    http_client = httpx.Client(timeout=5.0)

    try:
        for msg in consumer:
            txn = msg.value
            txn_id = txn.get("transaction_id", "unknown")
            card_id = txn.get("card_id", "unknown")
            amount = txn.get("amount", 0.0)

            # Post to FastAPI Scoring Engine
            try:
                response = http_client.post(api_url, json=txn)
                if response.status_code == 200:
                    result = response.json()
                    action = result.get("action")
                    risk_score = result.get("risk_score")
                    reasons = result.get("reasons", [])
                    latency = result.get("latency_ms")

                    # Log formatted status
                    status_flag = f"[{action}]"
                    print(
                        f"[Consumer] Txn: {txn_id} | Card: {card_id} | ${amount:.2f} | "
                        f"Risk Score: {risk_score}/100 | Action: {status_flag} | "
                        f"Reasons: {reasons} | Latency: {latency}ms"
                    )

                    # Publish scored result to scored_transactions topic
                    producer.send(settings.KAFKA_TOPIC_SCORED, value=result)

                    # If flagged for review or block, publish to flagged_transactions topic
                    if action in ["MANUAL_REVIEW", "BLOCK"]:
                        producer.send(settings.KAFKA_TOPIC_FLAGGED, value=result)

                else:
                    print(f"[Consumer] API error {response.status_code}: {response.text}")

            except httpx.RequestError as req_err:
                print(f"[Consumer] HTTP connection error calling scoring API ({api_url}): {req_err}")

    except KeyboardInterrupt:
        print("\n[Consumer] Stopping Kafka consumer service.")
    finally:
        consumer.close()
        producer.close()
        http_client.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Kafka Fraud Transaction Consumer")
    parser.add_argument("--bootstrap-servers", type=str, default=settings.KAFKA_BOOTSTRAP_SERVERS, help="Kafka bootstrap servers")
    parser.add_argument("--topic", type=str, default=settings.KAFKA_TOPIC_TRANSACTIONS, help="Kafka topic")
    parser.add_argument("--api-url", type=str, default=os.getenv("SCORING_API_URL", "http://localhost:8000/api/v1/score"), help="Scoring API endpoint URL")
    args = parser.parse_args()

    run_consumer(bootstrap_servers=args.bootstrap_servers, topic=args.topic, api_url=args.api_url)
