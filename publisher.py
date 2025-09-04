import os, json
from dotenv import load_dotenv
from awscrt import mqtt, io, auth
from awsiot import mqtt_connection_builder

# Load .env variables
load_dotenv()

ENDPOINT = os.getenv("ENDPOINT")  # e.g. a1hzk82khkq5ed-ats.iot.us-east-2.amazonaws.com
CLIENT_ID = os.getenv("CLIENT_ID", "nfl-publisher-ec2")
TOPIC = os.getenv("TOPIC", "nfl/test")
REGION = os.getenv("REGION", "us-east-2")

# Event loop and bootstrap
event_loop_group = io.EventLoopGroup(1)
host_resolver = io.DefaultHostResolver(event_loop_group)
client_bootstrap = io.ClientBootstrap(event_loop_group, host_resolver)

# Use the IAM role credentials (auto provided by EC2 metadata service)
credentials_provider = auth.AwsCredentialsProvider.new_default_chain(client_bootstrap)

# Build the MQTT connection over WebSockets
mqtt_connection = mqtt_connection_builder.websockets_with_default_aws_signing(
    endpoint=ENDPOINT,
    client_id=CLIENT_ID,
    region=REGION,
    credentials_provider=credentials_provider,
    clean_session=False,
    keep_alive_secs=30,
)

print(f"Connecting to {ENDPOINT} with client ID {CLIENT_ID}...")
mqtt_connection.connect().result()
print("✅ Connected!")

# Publish a test message
message = {"msg": "Well done! You have connected successfully!✅"}
mqtt_connection.publish(
    topic=TOPIC,
    payload=json.dumps(message),
    qos=mqtt.QoS.AT_LEAST_ONCE
)
print(f"📡 Published test message to {TOPIC}")

mqtt_connection.disconnect().result()
print("🔌 Disconnected")
