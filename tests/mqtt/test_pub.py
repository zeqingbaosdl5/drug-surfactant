import json, time
import paho.mqtt.client as paho
from paho import mqtt
from dotenv import load_dotenv

load_dotenv()
from mqtt_config import *

def on_publish(client, userdata, mid, properties=None, reasonCode=None):
    print(f"✓ Message {mid} acknowledged by broker")

client = paho.Client(client_id="flex-tester", protocol=paho.MQTTv5)
client.username_pw_set(MQTT_USER, MQTT_PASSWORD)
client.tls_set(tls_version=mqtt.client.ssl.PROTOCOL_TLS)
client.on_publish = on_publish

print(f"Connecting to {MQTT_BROKER}:{MQTT_PORT}")
client.connect(MQTT_BROKER, int(MQTT_PORT))
client.loop_start()

topic = "lab/experiments/new"
payload = json.dumps({"msg": "hello from Python"})
info = client.publish(topic, payload, qos=1, retain=True)
info.wait_for_publish(timeout=5)
print("publish rc =", info.rc, "mid =", info.mid, "is_published =", info.is_published())

time.sleep(2)  # wait for PUBACK
client.loop_stop()
client.disconnect()
