from app.dependencies import  SessionLocal
from app.models.sensor import Sensor
from app.models.device import Device
from app.models.parameter import Parameter

def initialize_database():
    with SessionLocal() as session:
        if not session.query(Sensor).first():
            sensors = [
                Sensor(name="Датчик температуры воздуха", label="airTemp"),
                Sensor(name="Датчик влажности воздуха", label="airHum"),
                Sensor(name="Датчик влажности почвы 1", label="soilMoist1"),
                Sensor(name="Датчик влажности почвы 2", label="soilMoist2"),
                Sensor(name="Датчик температуры воды", label="waterTemp"),
                Sensor(name="Датчики уровня воды", label="waterLevel"),
                Sensor(name="Датчик освещенности", label="light"),
            ]
            session.add_all(sensors)
            session.commit()
            print("Таблица 'sensor' успешно заполнена начальными данными.")
        else:
            print("Таблица 'sensor' была заполнена ранее.")

        if not session.query(Device).first():
            devices = [
                Device(name="Устройство проветривания", label="ventilation"),
                Device(name="Насос и клапан 1 грядки", label="watering1"),
                Device(name="Насос и клапан 2 грядки", label="watering2"),
                Device(name="Клапан наполнения емкости", label="refilling"),
                Device(name="LED", label="lighting"),
            ]
            session.add_all(devices)
            session.commit()
            print("Таблица 'device' успешно заполнена начальными данными.")
        else:
            print("Таблица 'device' была заполнена ранее.")

        if not session.query(Parameter).first():
            parameters = [
                Parameter(name="Температура воздуха", label="airTempThreshold"),
                Parameter(name="Влажность воздуха", label="airHumThreshold"),
                Parameter(name="Влажность почвы 1", label="soilMoistThreshold1"),
                Parameter(name="Влажность почвы 2", label="soilMoistThreshold2"),
                Parameter(name="Температура воды 1", label="waterTempThreshold1"),
                Parameter(name="Температура воды 2", label="waterTempThreshold2"),
                Parameter(name="Уровень воды", label="waterLevelThreshold"),
                Parameter(name="Освещенность", label="lightThreshold"),
                Parameter(name="Движение", label="motionThreshold"),
            ]
            session.add_all(parameters)
            session.commit()
            print("Таблица 'parameter' успешно заполнена начальными данными.")
        else:
            print("Таблица 'parameter' была заполнена ранее.")

initialize_database()
