import argparse
import json
import os
import random
import sys
import time
import uuid
import pandas as pd
from kafka import KafkaProducer
from kafka.errors import KafkaError

# Add parent directory to path for app configs
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from app.config import settings


def json_serializer(data):
    return json.dumps(data).encode("utf-8")


def run_producer(tps: int = 20, bootstrap_servers: str = settings.KAFKA_BOOTSTRAP_SERVERS, topic: str = settings.KAFKA_TOPIC_TRANSACTIONS):
    data_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "creditcard.csv"))

    if os.path.exists(data_path):
        print(f"[Producer] Replaying dataset from {data_path}")
        df = pd.read_csv(data_path)
    else:
        print("[Producer] Dataset not found, generating live synthetic transactions")
        df = None

    print(f"[Producer] Connecting to Kafka at {bootstrap_servers}...")
    try:
        producer = KafkaProducer(
            bootstrap_servers=bootstrap_servers,
            value_serializer=json_serializer,
            acks=1,
            retries=3
        )
        print(f"[Producer] Connected! Publishing to topic '{topic}' at ~{tps} TPS...")
    except KafkaError as e:
        print(f"[Producer] Error connecting to Kafka broker: {e}")
        sys.exit(1)

    cards_pool = [f"card_{i:04d}" for i in range(1, 101)]
    # Hot card designated for generating velocity bursts
    burst_card = "card_9999_burst"

    delay = 1.0 / max(1, tps)
    counter = 0

    try:
        while True:
            counter += 1
            txn_id = f"txn_{uuid.uuid4().hex[:10]}"
            now = time.time()

            # Every 15 transactions, inject a velocity burst from burst_card
            if counter % 15 == 0:
                card_id = burst_card
            else:
                card_id = random.choice(cards_pool)

            if df is not None and len(df) > 0:
                sample = df.sample(n=1).iloc[0]
                amount = float(sample["Amount"])
                features = {f"V{i}": float(sample[f"V{i}"]) for i in range(1, 29)}
            else:
                amount = round(random.exponential(100.0), 2)
                features = {f"V{i}": round(random.normal(0.0, 1.0), 4) for i in range(1, 29)}

            payload = {
                "transaction_id": txn_id,
                "card_id": card_id,
                "amount": amount,
                "features": features,
                "timestamp": now
            }

            producer.send(topic, value=payload)

            if counter % 50 == 0:
                print(f"[Producer] Sent {counter} transactions. Latest: {txn_id} ({card_id}, ${amount:.2f})")

            time.sleep(delay)

    except KeyboardInterrupt:
        print(f"\n[Producer] Stopping producer after {counter} messages sent.")
    finally:
        producer.flush()
        producer.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Kafka Fraud Transaction Producer")
    parser.add_argument("--tps", type=int, default=20, help="Transactions per second")
    parser.add_argument("--bootstrap-servers", type=str, default=settings.KAFKA_BOOTSTRAP_SERVERS, help="Kafka bootstrap servers")
    parser.add_argument("--topic", type=str, default=settings.KAFKA_TOPIC_TRANSACTIONS, help="Kafka topic")
    args = parser.parse_args()

    run_producer(tps=args.tps, bootstrap_servers=args.bootstrap_servers, topic=args.topic)
