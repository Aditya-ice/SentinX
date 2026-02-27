# SentinX: Real-Time Network Threat Defense

SentinX is a cloud-native, real-time network threat detection and response engine powered by **Apache Kafka**, **PySpark Structured Streaming**, **Scikit-Learn**, and **React**. 

It analyzes high-velocity network traffic using machine learning to instantly detect malicious payloads (DDoS, SQLi, Brute Force) and distributes the actionable threat intelligence to a headless **FastAPI** backend and dynamic **Glassmorphism dashboard** via **Redis** sub-50ms caching.

---

## 🏗 Architecture

The platform is divided into decoupling microservices that can be deployed individually into Kubernetes:

1. **Ingestion Engine (`/ingestion`)**: A Python-based high-throughput Kafka producer generating simulated multi-vector network traffic at 5,000+ EPS.
2. **Analytics Brain (`/analytics`)**: A PySpark ML application processing Kafka streams, applying a Random Forest model, and sinking threats to Redis.
3. **Headless API (`/api`)**: A FastAPI microservice offering sub-50ms queries for blocked IP addresses and live network entropy.
4. **Dashboard (`/frontend`)**: A React/Vite UI visualizing active threats and probabilities in real-time.
5. **Infrastructure (`/k8s`)**: Kubernetes deployments, services, and Bitnami Helm charts for the message brokers and caching layers.

## 🚀 Quick Start (Local Development)

### 1. Start Core Infrastructure
Ensure Docker Desktop is running. It will spin up Zookeeper, Kafka, Redis, and Elasticsearch.
```bash
docker compose up -d
```

### 2. Start Services (in parallel terminals)

**Terminal 1: Ingestion Generator**
```bash
cd ingestion
uv run python producer.py --eps 5000
```

**Terminal 2: Analytics PySpark Engine**
```bash
cd analytics
# Export Java 17 home if running natively on Mac
export JAVA_HOME=/Library/Java/JavaVirtualMachines/temurin-17.jdk/Contents/Home
uv run python train_model.py # Optional: Only if you need to retrain the RF model
uv run python streaming_job.py
```

**Terminal 3: FastAPI Backend**
```bash
cd api
uv run python main.py
```

**Terminal 4: React Dashboard**
```bash
cd frontend
npm run dev
```

Navigate to [http://localhost:5173](http://localhost:5173) to view the live dashboard.

## 🚢 Kubernetes Deployment
The repository includes automated CI/CD via **GitHub Actions**, building containers for each service.

1. Install Bitnami Helm dependencies:
```bash
cat k8s/helm-instructions.txt
```
2. Apply the custom services mapping:
```bash
kubectl apply -f k8s/sentinx-services.yaml
```
