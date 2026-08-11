from typing import Dict, List, Optional, Union
from enum import Enum
from pydantic import BaseModel, Field, field_validator


class ActionEnum(str, Enum):
    ALLOW = "ALLOW"
    MANUAL_REVIEW = "MANUAL_REVIEW"
    BLOCK = "BLOCK"


class TransactionPayload(BaseModel):
    transaction_id: str = Field(..., description="Unique transaction ID", json_schema_extra={"example": "txn_1029384"})
    card_id: str = Field(..., description="Unique card or account ID", json_schema_extra={"example": "card_881923"})
    amount: float = Field(..., description="Transaction amount in USD", json_schema_extra={"example": 149.99}, ge=0.0)
    features: Union[List[float], Dict[str, float]] = Field(
        ...,
        description="28 PCA feature values (V1..V28) as a list of 28 floats or a dictionary",
        json_schema_extra={"example": {"V1": -1.35, "V2": 0.42, "V3": 1.11}}
    )
    timestamp: Optional[float] = Field(None, description="Unix timestamp of transaction (seconds)")

    @field_validator("features")
    def validate_features(cls, v):
        if isinstance(v, list):
            if len(v) != 28:
                raise ValueError(f"Expected 28 feature values for V1..V28, got {len(v)}")
        elif isinstance(v, dict):
            missing = [f"V{i}" for i in range(1, 29) if f"V{i}" not in v]
            if missing:
                raise ValueError(f"Missing required PCA feature keys: {missing[:5]}...")
        else:
            raise ValueError("Features must be a list of 28 floats or a dictionary containing V1..V28")
        return v


class ScoreResponse(BaseModel):
    transaction_id: str
    card_id: str
    risk_score: int = Field(..., description="Calibrated risk score between 0 (Safe) and 100 (High Risk)")
    action: ActionEnum
    reasons: List[str]
    model_score: float = Field(..., description="Base ML model anomaly score (0-100)")
    velocity_score: float = Field(..., description="Velocity penalty score (0-30)")
    latency_ms: float = Field(..., description="Processing time in milliseconds")


class HealthResponse(BaseModel):
    status: str
    redis_connected: bool
    model_loaded: bool
