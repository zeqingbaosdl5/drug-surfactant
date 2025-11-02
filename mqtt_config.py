import os

MQTT_BROKER = os.getenv("MQTT_BROKER", "15f830b27242414d948b042037f067a6.s1.eu.hivemq.cloud")
MQTT_PORT = int(os.getenv("MQTT_PORT", "8883"))
MQTT_USER = os.getenv("MQTT_USER", "")
MQTT_PASSWORD = os.getenv("MQTT_PASSWORD", "")
TOPIC_NEW = "lab/experiments/new"