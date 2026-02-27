import os
import json
import time
import random
from datetime import datetime, timezone
from faker import Faker

fake = Faker()

class TrafficGenerator:
    def __init__(self, eps_target=5000):
        self.eps_target = eps_target
        # Weighted selection: 90% normal, 10% malicious
        self.attack_types = ['Normal'] * 90 + ['DDoS'] * 4 + ['SQLi'] * 3 + ['Brute Force'] * 3
        
        self.methods = ['GET', 'POST', 'PUT', 'DELETE', 'HEAD']
        self.normal_statuses = [200, 201, 204, 301, 302, 304, 404]
        self.error_statuses = [400, 401, 403, 500, 502, 503]
        
        self.common_paths = ['/login', '/dashboard', '/api/users', '/api/data', '/images/logo.png', '/about']
        self.sql_payloads = ["' OR 1=1 --", "admin' --", "'; DROP TABLE users; --", "UNION SELECT * FROM passwords"]
        
        # Keep a small pool of attacker IPs for DDoS/Brute force burstiness
        self.attacker_ip_pool = [fake.ipv4() for _ in range(20)]

    def generate_event(self):
        attack_type = random.choice(self.attack_types)
        
        # Base event
        dest_ip = os.environ.get('DESTINATION_IP', '10.0.0.1')
        event = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "source_ip": fake.ipv4() if attack_type not in ['DDoS', 'Brute Force'] else random.choice(self.attacker_ip_pool),
            "destination_ip": dest_ip,
            "http_method": random.choice(self.methods),
            "url_path": random.choice(self.common_paths),
            "user_agent": fake.user_agent(),
            "response_status": random.choice(self.normal_statuses),
            "response_size": random.randint(100, 10000),
            "latency_ms": random.randint(10, 100),
            "attack_type": attack_type
        }
        
        # Morph event based on attack type
        if attack_type == 'SQLi':
            event['http_method'] = 'POST'
            event['url_path'] = '/login'
            event['user_agent'] = "sqlmap/1.4.11"
            event['response_status'] = random.choice(self.error_statuses + [200])
        elif attack_type == 'Brute Force':
            event['http_method'] = 'POST'
            event['url_path'] = '/login'
            event['response_status'] = 401 # Unauthorized expected
        elif attack_type == 'DDoS':
            # DDoS requests are often simple GETs trying to overwhelm
            event['http_method'] = 'GET'
            event['url_path'] = '/'
        
        return event

    def generate_batch(self, batch_size=1000):
        """Yields a batch of raw dict events"""
        return [self.generate_event() for _ in range(batch_size)]
