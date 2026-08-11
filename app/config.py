import os
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # API Settings
    APP_NAME: str = "Fraud Detection Radar Engine"
    API_V1_STR: str = "/api/v1"
    
    # Redis Settings
    REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", "6379"))
    REDIS_DB: int = int(os.getenv("REDIS_DB", "0"))
    
    # Kafka Settings
    KAFKA_BOOTSTRAP_SERVERS: str = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
    KAFKA_TOPIC_TRANSACTIONS: str = os.getenv("KAFKA_TOPIC_TRANSACTIONS", "transactions")
    KAFKA_TOPIC_FLAGGED: str = os.getenv("KAFKA_TOPIC_FLAGGED", "flagged_transactions")
    KAFKA_TOPIC_SCORED: str = os.getenv("KAFKA_TOPIC_SCORED", "scored_transactions")
    
    # ML Artifact Paths
    MODEL_PATH: str = os.getenv("MODEL_PATH", "models/isolation_forest.joblib")
    SCALER_PATH: str = os.getenv("SCALER_PATH", "models/scaler.joblib")
    
    # Thresholds
    ALLOW_THRESHOLD: float = 50.0
    REVIEW_THRESHOLD: float = 75.0

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


settings = Settings()
