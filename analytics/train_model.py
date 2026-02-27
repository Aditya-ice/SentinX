import json
import random
import joblib
from sklearn.ensemble import RandomForestClassifier
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score

def synthesize_training_data(num_samples=10000):
    """
    Generate synthetic network features.
    Features we aim to use in our PySpark streaming job:
    1. response_size
    2. latency_ms
    3. is_error_status (0 or 1)
    """
    data = []
    labels = []
    
    for _ in range(num_samples):
        # 80% normal, 20% anomaly
        is_anomaly = random.random() < 0.2
        
        if not is_anomaly:
            # Normal distribution
            response_size = random.randint(100, 5000)
            latency = random.randint(10, 100)
            is_error = 0 if random.random() < 0.95 else 1 # 5% error rate naturally
            label = 0
        else:
            # Anomalous distribution (spikes, high error rates)
            anomaly_type = random.choice(['spike', 'error_flood'])
            if anomaly_type == 'spike':
                response_size = random.randint(8000, 20000)
                latency = random.randint(150, 500)
                is_error = 0
            else:
                response_size = random.randint(100, 1000)
                latency = random.randint(20, 200)
                is_error = 1
            label = 1
            
        data.append([response_size, latency, is_error])
        labels.append(label)
        
    return pd.DataFrame(data, columns=['response_size', 'latency_ms', 'is_error']), pd.Series(labels)

def train_and_save_model():
    print("Generating synthetic dataset...")
    X, y = synthesize_training_data(20000)
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    print("Training Random Forest model...")
    model = RandomForestClassifier(n_estimators=100, max_depth=3, random_state=42)
    model.fit(X_train, y_train)
    
    # Evaluate
    preds = model.predict(X_test)
    acc = accuracy_score(y_test, preds)
    print(f"Model accuracy on synthetic test set: {acc * 100:.2f}%")
    
    # Save model
    model_path = 'sentinx_rf_model.pkl'
    joblib.dump(model, model_path)
    print(f"Model saved to {model_path}")

if __name__ == '__main__':
    train_and_save_model()
