import pytest
import numpy as np

# Use httpx AsyncClient or FastAPI TestClient
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "redis_connected" in data
    assert "model_loaded" in data


def test_root_index_html():
    response = client.get("/")
    assert response.status_code == 200
    assert "Radar" in response.text
    assert "Transaction Risk Inspector" in response.text



def test_score_normal_transaction():
    payload = {
        "transaction_id": "test_txn_001",
        "card_id": "test_card_1234",
        "amount": 25.50,
        "features": {f"V{i}": 0.05 for i in range(1, 29)},
        "timestamp": 1700000000.0
    }
    response = client.post("/api/v1/score", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["transaction_id"] == "test_txn_001"
    assert data["card_id"] == "test_card_1234"
    assert 0 <= data["risk_score"] <= 100
    assert data["action"] in ["ALLOW", "MANUAL_REVIEW", "BLOCK"]
    assert "latency_ms" in data


def test_score_anomalous_transaction():
    # Extreme values in V1..V28 and high amount
    anomalous_features = {f"V{i}": (5.0 if i % 2 == 0 else -5.0) for i in range(1, 29)}
    payload = {
        "transaction_id": "test_txn_fraud_999",
        "card_id": "test_card_suspect",
        "amount": 9999.99,
        "features": anomalous_features,
        "timestamp": 1700000005.0
    }
    response = client.post("/api/v1/score", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["risk_score"] >= 50
    assert data["action"] in ["MANUAL_REVIEW", "BLOCK"]
    assert len(data["reasons"]) > 0


def test_score_invalid_features_validation():
    # Only 10 features instead of 28
    payload = {
        "transaction_id": "test_invalid",
        "card_id": "test_card",
        "amount": 100.0,
        "features": [1.0] * 10
    }
    response = client.post("/api/v1/score", json=payload)
    assert response.status_code == 422
