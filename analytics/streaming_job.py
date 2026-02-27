import os
import json
import redis
import joblib
import pandas as pd
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, from_json, current_timestamp, window, avg, max as spark_max, when
from pyspark.sql.types import StructType, StructField, StringType, IntegerType, LongType

# Setup Spark
spark = SparkSession.builder \
    .appName("SentinX-Analytics-Brain") \
    .config("spark.jars.packages", "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0") \
    .getOrCreate()

spark.sparkContext.setLogLevel("WARN")

# Define Schema coming from Kafka
schema = StructType([
    StructField("timestamp", StringType(), True),
    StructField("source_ip", StringType(), True),
    StructField("destination_ip", StringType(), True),
    StructField("http_method", StringType(), True),
    StructField("url_path", StringType(), True),
    StructField("user_agent", StringType(), True),
    StructField("response_status", IntegerType(), True),
    StructField("response_size", IntegerType(), True),
    StructField("latency_ms", IntegerType(), True),
    StructField("attack_type", StringType(), True)
])

# Load Random Forest Model
model_path = "sentinx_rf_model.pkl"
model = joblib.load(model_path)

# Redis client
redis_host = os.environ.get('REDIS_HOST', 'localhost')
r = redis.Redis(host=redis_host, port=6379, db=0, decode_responses=True)

def process_batch(df, epoch_id):
    """
    Micro-batch processing logic where we apply our XGBoost inference.
    """
    if df.isEmpty():
        return
        
    print(f"--- Processing Batch {epoch_id} ({df.count()} records) ---")
    
    # We collect the batch to Pandas for efficient bulk prediction with XGBoost.
    # In a fully distributed setting, we'd use a Pandas UDF.
    pandas_df = df.toPandas()
    
    # Extract features matching training script: response_size, latency_ms, is_error (0 or 1)
    # is_error = 1 if status >= 400
    pandas_df['is_error'] = pandas_df['response_status'].apply(lambda x: 1 if x >= 400 else 0)
    
    features = pandas_df[['response_size', 'latency_ms', 'is_error']]
    
    # Predict
    preds = model.predict_proba(features)[:, 1]
    # Binary threshold 0.5
    pandas_df['is_threat'] = (preds > 0.5).astype(int)
    pandas_df['ml_score'] = preds
    
    # Identify threats
    threats = pandas_df[pandas_df['is_threat'] == 1]
    
    if len(threats) > 0:
        print(f"⚠️ THREAT DETECTED ⚠️ | Blocks applied: {len(threats)}")
        # Sink to Redis for FastAPI immediate consumption
        for idx, row in threats.iterrows():
            # Key format: threat:source_ip
            r.setex(f"threat:{row['source_ip']}", 300, json.dumps(row.to_dict()))
            print(f"  [BLOCKED] IP: {row['source_ip']} | Type: {row['attack_type']} | Score: {preds[idx]:.2f}")
    else:
        print("✅ No threats detected in this batch.")

kafka_broker = os.environ.get('KAFKA_BROKER', 'localhost:9092')
print(f"Connecting to Kafka topic 'network-raw-logs' at {kafka_broker}...")

# Read stream from Kafka
df_kafka = spark \
    .readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", kafka_broker) \
    .option("subscribe", "network-raw-logs") \
    .option("startingOffsets", "latest") \
    .load()

# Parse JSON values
parsed_df = df_kafka.selectExpr("CAST(value AS STRING)") \
    .select(from_json(col("value"), schema).alias("data")) \
    .select("data.*")

# Add a processing timestamp for windowing
timestamped_df = parsed_df.withColumn("processing_time", current_timestamp())

# Example aggregation: 10 second rolling average of traffic size and max latency per IP
aggregated_df = timestamped_df \
    .withWatermark("processing_time", "10 seconds") \
    .groupBy(
        window(col("processing_time"), "10 seconds", "5 seconds"),
        col("source_ip")
    ).agg(
        avg("response_size").alias("avg_response_size"),
        spark_max("latency_ms").alias("max_latency_ms")
    )

# Write aggregation to console for debugging
query_agg = aggregated_df.writeStream \
    .outputMode("update") \
    .format("console") \
    .option("truncate", "false") \
    .start()

# Write raw parsed events to ML inference (ForeachBatch)
query_ml = parsed_df.writeStream \
    .outputMode("append") \
    .foreachBatch(process_batch) \
    .start()

query_agg.awaitTermination()
query_ml.awaitTermination()
