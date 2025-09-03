import os, json
from dotenv import load_dotenv
from awscrt import io, mqtt
from awsiot import mqtt_connection_builder

# Load .env variables
load_dotenv()

ENDPOINT = os.getenv("ENDPOINT")
CLIENT_ID = os.getenv("CLIENT_ID")
TOPIC = os.getenv("TOPIC")
REGION = os.getenv("REGION", "us-east-2")

# MQTT connection using WebSockets + IAM auth (for testing without certs)
mqtt_connection = mqtt_connection_builder.websockets_with_default_aws_signing(
    endpoint=ENDPOINT,
    client_id=CLIENT_ID,
    region=REGION,
    clean_session=False,
    keep_alive_secs=30,
)

print(f"Connecting to {ENDPOINT} with client ID {CLIENT_ID}...")
mqtt_connection.connect().result()
print("✅ Connected!")

# Publish a test message
message = {"msg": "Successful try!!"}
mqtt_connection.publish(
    topic=TOPIC,
    payload=json.dumps(message),
    qos=mqtt.QoS.AT_LEAST_ONCE
)
print(f"📡 Published test message to {TOPIC}")

mqtt_connection.disconnect().result()
print("🔌 Disconnected")
