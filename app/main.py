from fastapi import FastAPI
from app.routers import users, greenhouses, sensor_readings, device_states, mqtt
from app.dependencies import Base, engine

app = FastAPI()

# Создание таблиц
Base.metadata.create_all(bind=engine)

# Подключение маршрутов
app.include_router(users.router, prefix="/users", tags=["Users"])
app.include_router(greenhouses.router, prefix="/greenhouses", tags=["Greenhouses"])
app.include_router(sensor_readings.router, prefix="/sensor-readings", tags=["Sensor Readings"])
app.include_router(device_states.router, prefix="/device-states", tags=["Device States"])
app.include_router(mqtt.router, prefix="/mqtt", tags=["MQTT"])
