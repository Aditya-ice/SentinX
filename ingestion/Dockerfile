FROM python:3.10-slim

WORKDIR /app

# Install uv for fast dependency resolution
RUN pip install uv

COPY requirements.txt .

# Install dependencies using uv into the system environment
RUN uv pip install --system -r requirements.txt

COPY . .

# Run the producer to generate traffic
CMD ["python", "producer.py", "--eps", "5000", "--broker", "kafka-service:9092"]
