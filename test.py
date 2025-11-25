import json
import time
import os
from awscrt import io, mqtt, http
from awsiot import mqtt_connection_builder, auth
from dotenv import load_dotenv
from livescores import process_and_save_scores
from odds import get_daily_odds, odds_cache

# -------- Load environment variables --------
load_dotenv()

ENDPOINT = os.getenv("MLBENDPOINT")
REGION = os.getenv("MLBREGION")
CLIENT_ID = os.getenv("MLBCLIENT_ID")
TOPIC_SCORES = os.getenv("MLBTOPIC_SCORES")
TOPIC_ODDS = os.getenv("MLBTOPIC_ODDS")
POLL_INTERVAL = int(os.getenv("POLL_INTERVAL", "180"))
POLL_INTERVAL = 180  # 3 minutes

# -------- MQTT Setup --------
event_loop_group = io.EventLoopGroup()
host_resolver = io.DefaultHostResolver(event_loop_group)
client_bootstrap = io.ClientBootstrap(event_loop_group, host_resolver)

mqtt_connection = mqtt_connection_builder.websockets_with_default_aws_signing(
    endpoint=ENDPOINT,
    client_bootstrap=client_bootstrap,
    region=REGION,
    credentials_provider=auth.AwsCredentialsProvider.new_default_chain(),
    http_proxy_options=None,
    ca_filepath=None,  # AWS manages root CA internally
    client_id=CLIENT_ID,
    clean_session=False,
    keep_alive_secs=30,
)

print(f"Connecting to {ENDPOINT} as {CLIENT_ID}...")
connect_future = mqtt_connection.connect()
connect_future.result()
print("Connected to AWS IoT Core!")

# -------- Publishing Functions --------
def publish_scores():
    games = process_and_save_scores(return_data=True)  # Ensure process_and_save_scores returns dict
    payload = json.dumps(games)
    mqtt_connection.publish(
        topic=TOPIC_SCORES,
        payload=payload,
        qos=mqtt.QoS.AT_LEAST_ONCE,
    )
    print(f"Published scores to {TOPIC_SCORES}")

def publish_odds():
    get_daily_odds()
    payload = json.dumps(odds_cache)
    mqtt_connection.publish(
        topic=TOPIC_ODDS,
        payload=payload,
        qos=mqtt.QoS.AT_LEAST_ONCE,
    )
    print(f"Published odds to {TOPIC_ODDS}")

# -------- Main Loop --------
if __name__ == "__main__":
    while True:
        try:
            publish_scores()
            publish_odds()
        except Exception as e:
            print(f"Error: {e}")

        time.sleep(POLL_INTERVAL)
