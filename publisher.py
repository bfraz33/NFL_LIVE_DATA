import os
import json
import time
from datetime import datetime
from zoneinfo import ZoneInfo
from dotenv import load_dotenv
from awscrt import io, mqtt, auth
from awsiot import mqtt_connection_builder

# Import your existing logic
from main import run_once  # run_once() should return dict with 'scores' and 'odds'

# Load environment variables
load_dotenv()
ENDPOINT = os.getenv("ENDPOINT")
CLIENT_ID = os.getenv("CLIENT_ID", "nfl-publisher-ec2")
TOPIC = os.getenv("TOPIC", "nfl/live/scores")
REGION = os.getenv("REGION", "us-east-2")
POLL_INTERVAL = 180  # 3 minutes

# Set up AWS CRT event loop
event_loop_group = io.EventLoopGroup(1)
host_resolver = io.DefaultHostResolver(event_loop_group)
client_bootstrap = io.ClientBootstrap(event_loop_group, host_resolver)

# MQTT connection using WebSockets + EC2 IAM role credentials
mqtt_connection = mqtt_connection_builder.websockets_with_default_aws_signing(
    endpoint=ENDPOINT,
    client_id=CLIENT_ID,
    region=REGION,
    credentials_provider=auth.AwsCredentialsProvider.new_default_chain(client_bootstrap),
    clean_session=False,
    keep_alive_secs=30,
)

print(f"Connecting to {ENDPOINT} with client ID {CLIENT_ID}...")
mqtt_connection.connect().result()
print("✅ Connected to AWS IoT!")

# Track last published data
last_data = None

try:
    while True:
        # Get latest scores and odds from your main script
        new_data = run_once()  # Must return dict: {'scores': [...], 'odds': [...]}

        # Publish only if data changed
        if new_data != last_data:
            mqtt_connection.publish(
                topic=TOPIC,
                payload=json.dumps(new_data, default=str, indent=2),
                qos=mqtt.QoS.AT_LEAST_ONCE
            )
            print(f"📡 Published updated data to {TOPIC} at {datetime.now(ZoneInfo('America/Chicago'))}")
            last_data = new_data
        else:
            print(f"⏸ No change in data at {datetime.now(ZoneInfo('America/Chicago'))}")

        time.sleep(POLL_INTERVAL)

except KeyboardInterrupt:
    print("Stopping publisher...")

finally:
    mqtt_connection.disconnect().result()
    print("🔌 Disconnected from AWS IoT")