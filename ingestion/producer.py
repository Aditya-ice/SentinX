import json
import time
import argparse
from confluent_kafka import Producer
from traffic_generator import TrafficGenerator

def delivery_report(err, msg):
    """ Called once for each message produced to indicate delivery result. """
    if err is not None:
        print(f'Message delivery failed: {err}')

def run_producer(broker, topic, target_eps):
    # Setup Kafka Producer with high throughput configurations
    conf = {
        'bootstrap.servers': broker,
        'queue.buffering.max.messages': 500000,
        'queue.buffering.max.kbytes': 1048576,
        'batch.num.messages': 10000,
        'linger.ms': 5, # Wait briefly to collect a batch
        'compression.type': 'snappy', # Trade CPU for network bandwidth
        'acks': 1 # Fast acknowledgment for high throughput
    }
    
    producer = Producer(conf)
    generator = TrafficGenerator()
    
    print(f"Starting ingestion to topic: {topic} at ~{target_eps} EPS")
    
    batch_size = 1000
    sleep_time = batch_size / target_eps
    
    events_produced = 0
    start_time = time.time()
    last_report_time = start_time
    
    try:
        while True:
            batch_start = time.time()
            events = generator.generate_batch(batch_size)
            
            for event in events:
                producer.produce(
                    topic,
                    value=json.dumps(event).encode('utf-8'),
                    on_delivery=delivery_report
                )
            
            # Non-blocking poll for delivery callbacks
            producer.poll(0)
            events_produced += len(events)
            
            now = time.time()
            if now - last_report_time >= 5.0:
                elapsed = now - start_time
                actual_eps = events_produced / elapsed
                print(f"Produced {events_produced} messages. Current rate: {actual_eps:.2f} EPS")
                last_report_time = now
            
            # Sleep if we are generating too quickly
            processing_time = time.time() - batch_start
            if processing_time < sleep_time:
                time.sleep(sleep_time - processing_time)

    except KeyboardInterrupt:
        print("Stopping producer...")
    finally:
        print("Flushing outstanding messages...")
        producer.flush(10)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="SentinX High-Throughput HTTP Traffic Generator")
    parser.add_argument('--broker', default='localhost:9092', help='Kafka bootstrap server')
    parser.add_argument('--topic', default='network-raw-logs', help='Kafka topic destination')
    parser.add_argument('--eps', type=int, default=5000, help='Target Events Per Second')
    args = parser.parse_args()
    
    run_producer(args.broker, args.topic, args.eps)
