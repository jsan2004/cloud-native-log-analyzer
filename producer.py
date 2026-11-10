import os
import json
import time
import random
from datetime import datetime, timezone
import pika

# Load environment variables from .env if present
def load_env():
    env_file = os.path.join(os.path.dirname(__file__), '.env')
    if os.path.exists(env_file):
        with open(env_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, val = line.split('=', 1)
                    os.environ.setdefault(key.strip(), val.strip().strip('"').strip("'"))

load_env()

# CloudAMQP Connection URL from environment
CLOUDAMQP_URL = os.getenv("CLOUDAMQP_URL", "amqps://<username>:<password>@<host>/<vhost>")

params = pika.URLParameters(CLOUDAMQP_URL)
connection = pika.BlockingConnection(params)
channel = connection.channel()
channel.queue_declare(queue='server_logs', durable=True)

SERVICES = ["auth-service", "payment-service", "order-service", "user-service"]
ENDPOINTS = ["/api/login", "/api/checkout", "/api/products", "/api/cart", "/api/profile"]
LOG_LEVELS = ["INFO", "INFO", "INFO", "WARNING", "ERROR"]

def generate_log():
    level = random.choice(LOG_LEVELS)
    status = 500 if level == "ERROR" else random.choice([200, 200, 201, 400, 404])
    endpoint = random.choice(ENDPOINTS)
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "service_name": random.choice(SERVICES),
        "log_level": level,
        "status_code": status,
        "endpoint": endpoint,
        "response_time_ms": random.randint(30, 1200),
        "client_ip": f"192.168.1.{random.randint(2, 254)}",
        "message": f"HTTP {status} response on {endpoint}"
    }

print("🚀 Producer running: Streaming logs to Cloud Message Queue... (Ctrl+C to stop)")
try:
    while True:
        log = generate_log()
        channel.basic_publish(
            exchange='',
            routing_key='server_logs',
            body=json.dumps(log),
            properties=pika.BasicProperties(delivery_mode=2)  # Make message persistent
        )
        print(f"Sent: [{log['log_level']}] {log['service_name']} -> {log['endpoint']} ({log['status_code']})")
        time.sleep(random.uniform(0.5, 1.5))
except KeyboardInterrupt:
    print("\n🛑 Producer stopped.")
    connection.close()
