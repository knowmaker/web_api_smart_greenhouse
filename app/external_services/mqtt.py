import json
from paho.mqtt.client import Client
from sqlalchemy.orm import Session
from app.dependencies import SessionLocal
from app.models.sensor_reading import SensorReading
from app.models.greenhouse import Greenhouse
from app.models.device_state import DeviceState

MQTT_BROKER = "broker.emqx.io"
TOPIC_SENSOR_PATTERN = "m/+/d/cur"
TOPIC_DEVICE_PATTERN = "m/+/st/cur"
TOPIC_REGISTER_PATTERN = "m/+/reg"

client = Client()

def on_message(client, userdata, msg):
    try:
        topic_parts = msg.topic.split('/')
        guid = str(topic_parts[1])

        payload = msg.payload.decode()
        data = json.loads(payload)
        print(f"Received message on topic {msg.topic}: {msg.payload.decode()}")

        db: Session = SessionLocal()

        greenhouse = db.query(Greenhouse).filter(Greenhouse.guid == guid).first()
        if not greenhouse:
            print(f"Greenhouse with GUID {guid} not found")
            return

        # Обработка сообщения для топика регистрации
        if msg.topic.endswith("/reg"):
            pin = payload
            if not pin:
                print("Missing 'pin' in registration payload")
                return

            if not greenhouse:
                new_greenhouse = Greenhouse(guid=guid, pin=pin)
                db.add(new_greenhouse)
                db.commit()
                print(f"New greenhouse registered with GUID {guid} and PIN {pin}")
            elif greenhouse.id_user is None:
                greenhouse.pin = pin
                db.commit()
                print(f"Updated PIN for GUID {guid} to {pin}")
            else:
                print(f"Greenhouse with GUID {guid} already assigned to a user")
            return

        # Обработка сообщения для топика sensor_reading
        if msg.topic.endswith("d/cur"):
            for key, value in data.items():
                id_sensor = int(key)
                new_reading = SensorReading(
                    id_sensor=id_sensor,
                    id_greenhouse=greenhouse.id_greenhouse,
                    value=value,
                )
                db.add(new_reading)
            print(f"Sensor readings saved for GUID {guid}")

        # Обработка сообщения для топика device_state
        elif msg.topic.endswith("st/cur"):
            for key, value in data.items():
                id_device = int(key)
                new_state = DeviceState(
                    id_device=id_device,
                    id_greenhouse=greenhouse.id_greenhouse,
                    state=bool(value),
                )
                db.add(new_state)
            print(f"Device states saved for GUID {guid}")

        db.commit()
    except Exception as e:
        print(f"Error processing message: {e}")

def start_mqtt_listener():
    client.on_message = on_message
    client.connect(MQTT_BROKER)
    client.subscribe([
        (TOPIC_SENSOR_PATTERN, 0),
        (TOPIC_DEVICE_PATTERN, 0),
        (TOPIC_REGISTER_PATTERN, 0)
    ])
    client.loop_start()

def publish_to_mqtt(topic: str, message: str):
    client.publish(topic, message)
