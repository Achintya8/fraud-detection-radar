import os
import joblib
import numpy as np
from typing import Dict, List, Tuple, Union
from app.config import settings


class AnomalyDetector:
    def __init__(self, model_path: str = settings.MODEL_PATH, scaler_path: str = settings.SCALER_PATH):
        self.model_path = model_path
        self.scaler_path = scaler_path
        self.model = None
        self.scaler = None
        self.is_loaded = False
        self.load_artifacts()

    def load_artifacts(self) -> bool:
        """Loads trained IsolationForest model and StandardScaler artifacts."""
        try:
            if os.path.exists(self.model_path) and os.path.exists(self.scaler_path):
                self.model = joblib.load(self.model_path)
                self.scaler = joblib.load(self.scaler_path)
                self.is_loaded = True
                return True
            else:
                print(f"[AnomalyDetector] Artifacts not found at {self.model_path} or {self.scaler_path}")
                self.is_loaded = False
                return False
        except Exception as e:
            print(f"[AnomalyDetector] Error loading model artifacts: {e}")
            self.is_loaded = False
            return False

    def predict(self, features: Union[List[float], Dict[str, float]], amount: float) -> Tuple[float, List[str]]:
        """
        Extracts feature vector, applies StandardScaler, runs IsolationForest decision function,
        and converts to a calibrated 0-100 base risk score along with reason flags.
        """
        reasons = []

        # Convert features dict to 28-element list if necessary
        if isinstance(features, dict):
            feature_vector = [float(features[f"V{i}"]) for i in range(1, 29)]
        else:
            feature_vector = [float(x) for x in features]

        # Full feature vector: 28 PCA features + Amount
        full_vector = np.array(feature_vector + [float(amount)], dtype=np.float64).reshape(1, -1)

        if not self.is_loaded:
            # Fallback if model isn't loaded yet
            print("[AnomalyDetector] Model not loaded, using fallback heuristic score")
            base_score = 10.0
            if amount > 5000:
                base_score += 40.0
                reasons.append("HIGH_TRANSACTION_AMOUNT")
            return min(100.0, base_score), reasons

        # Standardize feature vector
        scaled_vector = self.scaler.transform(full_vector)

        # Check feature deviation thresholds (|scaled_val| > 3.5)
        extreme_features = np.where(np.abs(scaled_vector[0][:-1]) > 3.5)[0]
        if len(extreme_features) > 0:
            reasons.append("ANOMALOUS_FEATURE_VECTOR")

        # IsolationForest decision_function: higher = normal (~0.1 to 0.2), lower/negative = anomalous (~ -0.1 to -0.3)
        raw_score = float(self.model.decision_function(scaled_vector)[0])

        # Calibrate raw score to 0-100 risk score using smooth sigmoid transformation
        # Centered around s = 0.02 where score = 50
        risk_score = 100.0 / (1.0 + np.exp(14.0 * (raw_score - 0.01)))
        risk_score = float(np.clip(risk_score, 0.0, 100.0))

        if risk_score > 60.0 and "ANOMALOUS_FEATURE_VECTOR" not in reasons:
            reasons.append("HIGH_ANOMALY_INDEX")

        return round(risk_score, 2), reasons


# Global singleton instance
anomaly_detector = AnomalyDetector()
