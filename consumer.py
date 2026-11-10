import os
import json
import pika
import psycopg2

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

# CloudAMQP Configuration
CLOUDAMQP_URL = os.getenv("CLOUDAMQP_URL", "amqps://<username>:<password>@<host>/<vhost>")

# Supabase Data Warehouse Configuration
DB_HOST = os.getenv("DB_HOST", "aws-0-ap-south-1.pooler.supabase.com")
DB_PORT = int(os.getenv("DB_PORT", "6543"))
DB_NAME = os.getenv("DB_NAME", "postgres")
DB_USER = os.getenv("DB_USER", "postgres.<project_ref>")
DB_PASSWORD = os.getenv("DB_PASSWORD", "your_password_here")

# Connect to Database
print("🔌 Connecting to Supabase Data Warehouse...")
db_conn = psycopg2.connect(
    host=DB_HOST,
    port=DB_PORT,
    dbname=DB_NAME,
    user=DB_USER,
    password=DB_PASSWORD
)
cursor = db_conn.cursor()
print("✅ Connected to Data Warehouse successfully.")

# Connect to Message Queue
print("🔌 Connecting to CloudAMQP Broker...")
params = pika.URLParameters(CLOUDAMQP_URL)
mq_conn = pika.BlockingConnection(params)
channel = mq_conn.channel()
channel.queue_declare(queue='server_logs', durable=True)
print("✅ Connected to CloudAMQP successfully.")

def callback(ch, method, properties, body):
    try:
        log = json.loads(body.decode('utf-8'))
        
        insert_query = """
        INSERT INTO server_logs (timestamp, service_name, log_level, status_code, endpoint, response_time_ms, client_ip, message)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s);
        """
        cursor.execute(insert_query, (
            log["timestamp"],
            log["service_name"],
            log["log_level"],
            log["status_code"],
            log["endpoint"],
            log["response_time_ms"],
            log["client_ip"],
            log["message"]
        ))
        db_conn.commit()
        print(f"📥 Ingested into Data Warehouse: [{log['log_level']}] from {log['service_name']} -> {log['endpoint']} ({log['status_code']})")
        ch.basic_ack(delivery_tag=method.delivery_tag)
    except Exception as e:
        print(f"❌ Error inserting log into database: {e}")
        db_conn.rollback()

channel.basic_consume(queue='server_logs', on_message_callback=callback)
print("⚙️ Ingestion Worker started: Waiting for logs in queue... (Ctrl+C to stop)")

try:
    channel.start_consuming()
except KeyboardInterrupt:
    print("\n🛑 Ingestion worker stopped.")
    cursor.close()
    db_conn.close()
    mq_conn.close()
