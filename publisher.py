import os, json
from dotenv import load_dotenv
from awscrt import io, mqtt
from awsiot import mqtt_connection_builder
from main import run_once   # <-- import the new function

# Load .env variables
load_dotenv()

ENDPOINT = os.getenv("ENDPOINT")
CLIENT_ID = os.getenv("CLIENT_ID", "nfl-publisher-ec2")
TOPIC = os.getenv("TOPIC", "nfl/live/test")
REGION = os.getenv("REGION", "us-east-2")

# Event loop for AWS CRT
event_loop_group = io.EventLoopGroup(1)
host_resolver = io.DefaultHostResolver(event_loop_group)
client_bootstrap = io.ClientBootstrap(event_loop_group, host_resolver)

# Build MQTT connection using WebSockets + IAM role from EC2
mqtt_connection = mqtt_connection_builder.websockets_with_default_aws_signing(
    endpoint=ENDPOINT,
    client_id=CLIENT_ID,
    region=REGION,
    credentials_provider=io.AwsCredentialsProvider.new_default_chain(client_bootstrap),
    clean_session=False,
    keep_alive_secs=30,
)

print(f"Connecting to {ENDPOINT} with client ID {CLIENT_ID}...")
mqtt_connection.connect().result()
print("✅ Connected!")

# Run your NFL data once
data = run_once()

# Publish the JSON payload
mqtt_connection.publish(
    topic=TOPIC,
    payload=json.dumps(data, indent=2, default=str),
    qos=mqtt.QoS.AT_LEAST_ONCE
)
print(f"📡 Published game data to {TOPIC}")

mqtt_connection.disconnect().result()
print("🔌 Disconnected")
