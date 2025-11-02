import ssl
from dotenv import load_dotenv
load_dotenv()
import paho.mqtt.client as paho
from paho import mqtt
from mqtt_config import *


def on_message(c,u,m):
    print(f"{m.topic}: {m.payload.decode()}")

def on_subscribe(c, u, mid, qos, props=None):
    print(f"✓ Subscribed successfully with QoS: {qos}")

def on_connect(client, userdata, flags, rc, properties=None):
    if rc == 0:
        print("✓ Connected successfully to MQTT broker")
    else:
        print(f"✗ Failed to connect, return code {rc}")

def on_disconnect(client, userdata, rc, properties=None):
    if rc != 0:
        print(f"✗ Unexpected disconnection with return code {rc}")

def on_log(client, userdata, level, buf):
    print(f"LOG: {buf}")

client = paho.Client(client_id="mac-tester", userdata=None, protocol=paho.MQTTv5)
client.tls_set(tls_version=mqtt.client.ssl.PROTOCOL_TLS)
client.username_pw_set(MQTT_USER, MQTT_PASSWORD)
client.on_connect = on_connect
client.on_disconnect = on_disconnect
client.on_subscribe = on_subscribe
client.on_message = on_message
client.on_log = on_log


print(f"Connecting to {MQTT_BROKER}:{MQTT_PORT}")
client.connect(MQTT_BROKER, MQTT_PORT)
client.subscribe('#', qos=1)
print("Listening for messages...")
client.loop_forever()