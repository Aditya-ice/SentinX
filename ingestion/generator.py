import time
import json
import random
import uuid
from datetime import datetime

# Common web paths
PATHS = ['/login', '/dashboard', '/api/data', '/cart', '/checkout', '/profile', '/search']

# SQLi signatures
SQLI_PAYLOADS = [
    "' OR '1'='1",
    "admin' --",
    "1; DROP TABLE users",
    "UNION SELECT username, password FROM users"
]

def generate_ip():
    return f"{random.randint(1, 255)}.{random.randint(1, 255)}.{random.randint(1, 255)}.{random.randint(1, 255)}"

def generate_log_event():
    """Generates a single synthetic network log event."""
    
    # Simulate attack types: 0=Normal, 1=DDoS, 2=Brute Force, 3=SQLi
    event_type = random.choices([0, 1, 2, 3], weights=[0.85, 0.05, 0.05, 0.05])[0]
    
    source_ip = generate_ip()
    method = 'GET'
    path = random.choice(PATHS)
    status_code = 200
    user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
    response_size = random.randint(500, 5000)
    
    if event_type == 1:
        # DDoS simulation: same IP repeatedly, simple path
        source_ip = f"10.0.0.{random.randint(1, 5)}"
        path = '/'
    elif event_type == 2:
        # Brute Force simulation: login failures
        source_ip = f"192.168.1.{random.randint(10, 50)}"
        path = '/login'
        method = 'POST'
        status_code = 401
    elif event_type == 3:
        # SQL Injection simulation
        path = f"/api/data?q={random.choice(SQLI_PAYLOADS)}"
    
    # Introduce small probability of other methods for normal traffic
    if event_type == 0 and random.random() < 0.2:
        method = random.choice(['POST', 'PUT', 'DELETE'])
        if method == 'POST':
            status_code = random.choice([201, 400, 500])

    event = {
        "event_id": str(uuid.uuid4()),
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "source_ip": source_ip,
        "method": method,
        "path": path,
        "status_code": status_code,
        "response_size_bytes": response_size,
        "user_agent": user_agent,
        "is_attack": int(event_type != 0),  # Labeled for Model Training/Validation later
        "attack_type": event_type
    }
    
    return event

if __name__ == "__main__":
    # Test generator
    for _ in range(5):
        print(json.dumps(generate_log_event(), indent=2))
