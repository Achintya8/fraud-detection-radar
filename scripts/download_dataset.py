import os
import shutil
import numpy as np
import pandas as pd


def setup_dataset():
    target_dir = os.path.join(os.path.dirname(__file__), "..", "data")
    os.makedirs(target_dir, exist_ok=True)
    target_path = os.path.join(target_dir, "creditcard.csv")

    if os.path.exists(target_path):
        print(f"[Dataset] Found dataset at {target_path} ({os.path.getsize(target_path)} bytes)")
        return target_path

    # Check parent directory (e.g. c:\Users\achin\Desktop\Fintech\creditcard.csv)
    parent_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "creditcard.csv"))
    if os.path.exists(parent_path):
        print(f"[Dataset] Copying existing creditcard.csv from {parent_path} to {target_path}...")
        shutil.copyfile(parent_path, target_path)
        print(f"[Dataset] Successfully copied ({os.path.getsize(target_path)} bytes)")
        return target_path

    # Attempt synthetic generation if dataset file is completely absent
    print("[Dataset] creditcard.csv not found locally. Generating synthetic dataset with 10,000 samples...")
    np.random.seed(42)
    n_samples = 10000
    n_fraud = 50

    # Normal transactions (V1..V28 drawn from standard normal N(0, 1))
    normal_v = np.random.normal(loc=0.0, scale=1.0, size=(n_samples - n_fraud, 28))
    normal_amt = np.random.exponential(scale=80.0, size=(n_samples - n_fraud, 1))
    normal_class = np.zeros((n_samples - n_fraud, 1))

    # Fraudulent transactions (V1..V28 with extreme shifts N(3.5, 2.0))
    fraud_v = np.random.normal(loc=3.5, scale=2.0, size=(n_fraud, 28))
    fraud_amt = np.random.uniform(low=500.0, high=4000.0, size=(n_fraud, 1))
    fraud_class = np.ones((n_fraud, 1))

    v_features = np.vstack([normal_v, fraud_v])
    amounts = np.vstack([normal_amt, fraud_amt])
    classes = np.vstack([normal_class, fraud_class])
    times = np.arange(n_samples).reshape(-1, 1)

    all_data = np.hstack([times, v_features, amounts, classes])
    cols = ["Time"] + [f"V{i}" for i in range(1, 29)] + ["Amount", "Class"]

    df = pd.DataFrame(all_data, columns=cols)
    df = df.sample(frac=1.0, random_state=42).reset_index(drop=True)
    df.to_csv(target_path, index=False)
    print(f"[Dataset] Synthetic creditcard.csv created at {target_path} ({len(df)} rows)")
    return target_path


if __name__ == "__main__":
    setup_dataset()
