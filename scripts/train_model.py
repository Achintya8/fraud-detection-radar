import os
import joblib
import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import classification_report, roc_auc_score
from download_dataset import setup_dataset


def train():
    # 1. Ensure dataset exists
    dataset_path = setup_dataset()
    print(f"[Train] Loading dataset from {dataset_path}...")
    df = pd.read_csv(dataset_path)

    feature_cols = [f"V{i}" for i in range(1, 29)] + ["Amount"]
    X = df[feature_cols].values
    y = df["Class"].values

    print(f"[Train] Dataset shape: {df.shape}. Total transactions: {len(df)}, Normal: {(y == 0).sum()}, Fraud: {(y == 1).sum()}")

    # 2. Separate normal transactions for unsupervised training
    normal_mask = (y == 0)
    X_normal = X[normal_mask]

    # 3. Fit StandardScaler on normal transactions
    print("[Train] Fitting StandardScaler on normal transactions...")
    scaler = StandardScaler()
    X_normal_scaled = scaler.fit_transform(X_normal)

    # 4. Train IsolationForest model strictly on normal transactions
    print("[Train] Training IsolationForest model...")
    # Standard contamination roughly matching dataset fraud ratio ~0.17%
    model = IsolationForest(
        n_estimators=100,
        contamination=0.0017,
        max_samples="auto",
        random_state=42,
        n_jobs=-1
    )
    model.fit(X_normal_scaled)

    # 5. Evaluate model performance on full dataset
    X_all_scaled = scaler.transform(X)
    raw_scores = model.decision_function(X_all_scaled)
    
    # Calibrate risk score (0 to 100)
    risk_scores = 100.0 / (1.0 + np.exp(14.0 * (raw_scores - 0.01)))
    
    # Predict binary fraud if risk score > 50
    preds_binary = (risk_scores > 50.0).astype(int)

    auc = roc_auc_score(y, risk_scores)
    print(f"\n--- Model Evaluation ---")
    print(f"ROC AUC Score: {auc:.4f}")
    print("\nClassification Report (Risk Score > 50 vs Actual Class):")
    print(classification_report(y, preds_binary, target_names=["Normal", "Fraud"], zero_division=0))

    # 6. Export artifacts to models/
    output_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "models"))
    os.makedirs(output_dir, exist_ok=True)

    scaler_path = os.path.join(output_dir, "scaler.joblib")
    model_path = os.path.join(output_dir, "isolation_forest.joblib")

    joblib.dump(scaler, scaler_path)
    joblib.dump(model, model_path)

    print(f"\n[Train] Saved scaler artifact to: {scaler_path}")
    print(f"[Train] Saved model artifact to: {model_path}")
    print("[Train] Training pipeline complete successfully.")


if __name__ == "__main__":
    train()
