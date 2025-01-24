import json
from datetime import datetime
from paho.mqtt.client import Client
from sqlalchemy.orm import Session
from app.dependencies import SessionLocal
from app.models.sensor_reading import SensorReading
from app.models.device_state import DeviceState
from app.models.setting import Setting
from app.models.greenhouse import Greenhouse
from app.models.sensor_alert_state import SensorAlertState
from app.routers.sensor_readings import send_push_notification

MQTT_BROKER = "broker.emqx.io"
TOPIC_SENSOR_PATTERN = "m/+/d/cur"
TOPIC_DEVICE_PATTERN = "m/+/st/cur"
TOPIC_SETTING_PATTERN = "m/+/s/cur"
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
            notifications = []
            for key, value in data.items():
                id_sensor = int(key)
                new_reading = SensorReading(
                    id_sensor=id_sensor,
                    id_greenhouse=greenhouse.id_greenhouse,
                    value=value,
                )
                db.add(new_reading)

                # Получаем состояние уведомления для этого датчика
                alert_state = db.query(SensorAlertState).filter(
                    SensorAlertState.id_sensor == id_sensor,
                    SensorAlertState.id_greenhouse == greenhouse.id_greenhouse
                ).first()

                if not alert_state:
                    # Если состояние ещё не создано, создаём его
                    alert_state = SensorAlertState(
                        id_sensor=id_sensor,
                        id_greenhouse=greenhouse.id_greenhouse,
                        last_alert_sent=False
                    )
                    db.add(alert_state)

                # Логика проверки превышения порогов
                if id_sensor == 1 and value > 60:  # Температура воздуха
                    if not alert_state.last_alert_sent:
                        notifications.append(f"Температура воздуха превышает 60°C ({value}°C)")
                        alert_state.last_alert_sent = True
                        alert_state.alert_timestamp = datetime.utcnow()
                elif id_sensor == 2 and value > 80:  # Влажность воздуха
                    if not alert_state.last_alert_sent:
                        notifications.append(f"Влажность воздуха превышает 80% ({value}%)")
                        alert_state.last_alert_sent = True
                        alert_state.alert_timestamp = datetime.utcnow()
                elif id_sensor == 3 and value > 85:  # Влажность почвы 1
                    if not alert_state.last_alert_sent:
                        notifications.append(f"Влажность почвы 1 превышает 85% ({value}%)")
                        alert_state.last_alert_sent = True
                        alert_state.alert_timestamp = datetime.utcnow()
                elif id_sensor == 4 and value > 85:  # Влажность почвы 2
                    if not alert_state.last_alert_sent:
                        notifications.append(f"Влажность почвы 2 превышает 85% ({value}%)")
                        alert_state.last_alert_sent = True
                        alert_state.alert_timestamp = datetime.utcnow()
                else:
                    # Если значение вернулось в норму, сбрасываем флаг уведомления
                    alert_state.last_alert_sent = False

                db.add(alert_state)

            user = greenhouse.owner

            # Если есть уведомления и у пользователя есть FCM-токены, отправляем их
            # if notifications and user and user.fcm_tokens:
            #     for token in user.fcm_tokens:
            #         title = f"Уведомление от теплицы {greenhouse.title or greenhouse.guid}"
            #         body = "\n".join(notifications)
            #         send_push_notification(token, title, body)
            #     print(f"Уведомления отправлены для теплицы {guid}: {notifications}")
            # else:
            #     print(f"Пропущено уведомление для теплицы {guid}: пользователь отсутствует или нет токенов")
            if notifications and user and user.fcm_token:
                title = f"Уведомление от теплицы {greenhouse.title or greenhouse.guid}"
                body = "\n".join(notifications)
                send_push_notification(user.fcm_token, title, body)
                print(f"Уведомления отправлены для теплицы {guid}: {notifications}")

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

        # Обработка сообщения для топика setting
        elif msg.topic.endswith("s/cur"):
            for key, value in data.items():
                id_parameter= int(key)
                new_setting = Setting(
                    id_parameter=id_parameter,
                    id_greenhouse=greenhouse.id_greenhouse,
                    value=value,
                )
                db.add(new_setting)
            print(f"Settings saved for GUID {guid}")

        db.commit()
    except Exception as e:
        print(f"Error processing message: {e}")

def start_mqtt_listener():
    client.on_message = on_message
    client.connect(MQTT_BROKER)
    client.subscribe([
        (TOPIC_SENSOR_PATTERN, 0),
        (TOPIC_DEVICE_PATTERN, 0),
        (TOPIC_SETTING_PATTERN, 0),
        (TOPIC_REGISTER_PATTERN, 0)
    ])
    client.loop_start()

def publish_to_mqtt(topic: str, message: str):
    client.publish(topic, message)
