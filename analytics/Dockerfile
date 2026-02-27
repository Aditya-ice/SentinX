FROM apache/spark:3.5.0

USER root

# Install uv, Java (if needed), and build tools for python packages
RUN apt-get update && apt-get install -y python3-pip && rm -rf /var/lib/apt/lists/*
RUN pip3 install uv

WORKDIR /app

COPY requirements.txt .
RUN uv pip install --system -r requirements.txt

COPY . .

# Assume the model is pre-trained and included, or run train_model.py before startup
# We start the streaming job connected to Kafka and Redis
CMD ["python3", "streaming_job.py"]
