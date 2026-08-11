# 🛡️ Real-Time Fraud Detection Engine (Stripe Radar Architecture)

An end-to-end, production-grade microservices system designed for real-time credit card transaction anomaly detection and risk scoring. Replays transaction events through Apache Kafka, computes stateful sliding-window velocity metrics in Redis, scores feature vectors using a calibrated Scikit-Learn `IsolationForest` model via FastAPI, and yields actionable decisions (`ALLOW`, `MANUAL_REVIEW`, `BLOCK`).

---

## 📐 System Architecture

```text
                               ┌─────────────────────────────┐
                               │ Kaggle / Replay Producer    │
                               └──────────────┬──────────────┘
                                              │ (TPS Stream)
                                              ▼
                                   ┌────────────────────┐
                                   │ Kafka: transactions│
                                   └──────────┬─────────┘
                                              │
                                              ▼
                                   ┌────────────────────┐
                                   │ Consumer Worker    │
                                   └──────────┬─────────┘
                                              │
                    ┌─────────────────────────┴─────────────────────────┐
                    ▼                                                   ▼
      ┌──────────────────────────┐                        ┌──────────────────────────┐
      │ Redis Velocity Engine    │                        │ FastAPI Anomaly Engine   │
      │ (Sliding Window ZSETs)   │                        │ (Isolation Forest Model) │
      └─────────────┬────────────┘                        └─────────────┬────────────┘
                    │ (0-30 Penalty Points)                             │ (0-100 Base Score)
                    └─────────────────────────┬─────────────────────────┘
                                              ▼
                                 ┌──────────────────────────┐
                                 │ Calibrated Risk Score    │
                                 │  - <50: ALLOW            │
                                 │  - 50-75: MANUAL_REVIEW  │
                                 │  - >75: BLOCK            │
                                 └────────────┬─────────────┘
                                              │
                                              ▼
                                 ┌──────────────────────────┐
                                 │ Kafka: scored / flagged  │
                                 └──────────────────────────┘
```

---

## 🛠️ Tech Stack

- **API & Scoring Microservice:** Python 3.11+, FastAPI, Pydantic v2, Uvicorn
- **State & Velocity Engine:** Redis (sliding-window `ZSET` sorted sets: 10-min count & 1-hr spend volume)
- **Streaming & Messaging:** Apache Kafka, Zookeeper, `kafka-python-ng`, `aiokafka`, `httpx`
- **ML / Anomaly Detection:** Scikit-Learn (`IsolationForest`), `StandardScaler`, `joblib`, `numpy`, `pandas`
- **Containerization & Orchestration:** Docker, Docker Compose
- **Testing:** `pytest`, `pytest-asyncio`, `fakeredis`

---

## 📁 Directory Structure

```text
fraud-detection-radar/
├── docker-compose.yml           # Microservice orchestration (Kafka, Redis, API, Consumer)
├── Dockerfile                   # Service container definition
├── requirements.txt             # Python dependencies
├── README.md                    # Project documentation
├── scripts/
│   ├── download_dataset.py      # Dataset loader & synthetic fallback generator
│   └── train_model.py           # Trains StandardScaler + IsolationForest, exports artifacts
├── models/                      # Saved ML artifacts
│   ├── scaler.joblib
│   └── isolation_forest.joblib
├── app/                         # FastAPI Scoring Microservice
│   ├── config.py                # Environment configurations
│   ├── schemas.py               # Pydantic request & response models
│   ├── main.py                  # FastAPI app entrypoint & health checks
│   ├── services/
│   │   ├── anomaly_detector.py  # Model inference & 0-100 score calibration
│   │   └── velocity_checker.py  # Redis sliding-window velocity rules (ZSET)
│   └── routers/
│       └── score.py             # POST /api/v1/score endpoint
├── pipeline/                    # Streaming Infrastructure
│   ├── producer.py              # Kafka replay producer (configurable TPS)
│   └── consumer.py              # Kafka consumer worker invoking scoring API
└── tests/                       # Automated Test Suite
    ├── test_api.py              # API endpoint unit tests
    └── test_velocity.py         # Velocity sliding window unit tests
```

---

## 🚀 Quickstart Guide

### 1. Environment Setup & Dependency Installation

Create a virtual environment and install dependencies:

```bash
python -m venv venv
# On Windows:
venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate

pip install -r requirements.txt
```

### 2. Download Dataset & Train the Anomaly Model

Run the training pipeline script to fit `StandardScaler` and `IsolationForest` on normal credit card transactions and export artifacts to `models/`:

```bash
python scripts/download_dataset.py
python scripts/train_model.py
```

### 3. Run Automated Tests

Execute the test suite verifying API endpoints and Redis sliding window logic:

```bash
pytest -v
```

---

## 🐳 Running with Docker Compose

Spin up all infrastructure components (Zookeeper, Kafka, Redis, Scoring API, Stream Consumer) in background containers:

```bash
docker compose up --build -d
```

Check the health status of the services:

```bash
curl http://localhost:8000/health
```

Expected output:
```json
{
  "status": "ok",
  "redis_connected": true,
  "model_loaded": true
}
```

---

## 📊 Live Transaction Streaming & Scoring

Start the Kafka Producer to stream replayed transactions at a rate of 20 events/sec:

```bash
python pipeline/producer.py --tps 20
```

Inspect live risk scoring in the consumer logs:

```bash
docker compose logs -f stream-consumer
# Or locally:
python pipeline/consumer.py
```

Sample output:
```text
[Consumer] Txn: txn_8a7d10e2 | Card: card_0012 | $45.20 | Risk Score: 12/100 | Action: [ALLOW] | Reasons: [] | Latency: 2.14ms
[Consumer] Txn: txn_3b9c02d1 | Card: card_9999_burst | $3200.00 | Risk Score: 88/100 | Action: [BLOCK] | Reasons: ['HIGH_ANOMALY_INDEX', 'HIGH_VELOCITY_BURST', 'HIGH_VOLUME_SPEND'] | Latency: 3.45ms
```

---

## 🧪 Manual API Testing

Submit a test score request using `curl`:

```bash
curl -X POST "http://localhost:8000/api/v1/score" \
     -H "Content-Type: application/json" \
     -d '{
           "transaction_id": "txn_manual_101",
           "card_id": "card_manual_001",
           "amount": 1500.0,
           "features": {
             "V1": -1.35, "V2": 0.42, "V3": 1.11, "V4": 0.12, "V5": -0.5, "V6": 0.2, "V7": 0.1,
             "V8": -0.1, "V9": 0.4, "V10": -0.2, "V11": 0.3, "V12": -0.4, "V13": 0.1, "V14": -0.1,
             "V15": 0.2, "V16": -0.3, "V17": 0.1, "V18": 0.0, "V19": -0.1, "V20": 0.2, "V21": 0.1,
             "V22": -0.2, "V23": 0.05, "V24": -0.1, "V25": 0.2, "V26": -0.05, "V27": 0.01, "V28": 0.02
           }
         }'
```

Response:
```json
{
  "transaction_id": "txn_manual_101",
  "card_id": "card_manual_001",
  "risk_score": 18,
  "action": "ALLOW",
  "reasons": [],
  "model_score": 18.25,
  "velocity_score": 0.0,
  "latency_ms": 2.85
}
```
