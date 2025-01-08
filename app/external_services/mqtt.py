import paho.mqtt.publish as publish

MQTT_BROKER_URL = "mqtt_broker_url"

def publish_to_mqtt(topic: str, payload: str):
    publish.single(topic, payload, hostname=MQTT_BROKER_URL)
