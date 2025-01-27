from fastapi import FastAPI
from app.routers import users, greenhouses, sensor_readings, device_states, settings
from app.dependencies import Base, engine
from app.external_services.mqtt import start_mqtt_listener
from app.models.greenhouse import Greenhouse
from app.models.sensor_reading import SensorReading
from app.models.device_state import DeviceState
from app.models.sensor import Sensor
from app.models.device import Device
from app.models.user import User
from app.models.fcm_token import FCMToken
from app.models.parameter import Parameter
from app.models.setting import Setting
from app.models.sensor_alert_state import SensorAlertState

app = FastAPI()
@app.get("/")
async def home():
   return {"data": "Hello World"}

# Создание таблиц
Base.metadata.create_all(bind=engine)

app.include_router(users.router, prefix="/users", tags=["Users"])
app.include_router(greenhouses.router, prefix="/greenhouses", tags=["Greenhouses"])
app.include_router(sensor_readings.router, prefix="/sensor-readings", tags=["Sensor Readings"])
app.include_router(device_states.router, prefix="/device-states", tags=["Device States"])
app.include_router(settings.router, prefix="/settings", tags=["Settings"])

start_mqtt_listener()