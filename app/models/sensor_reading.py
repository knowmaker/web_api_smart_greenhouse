from sqlalchemy import Column, Integer, DateTime, ForeignKey
from app.dependencies import Base
from datetime import datetime

class SensorReading(Base):
    __tablename__ = "sensor_reading"
    id_sreading = Column(Integer, primary_key=True, index=True)
    id_sensor = Column(Integer, ForeignKey("sensor.id_sensor"), nullable=False)
    id_greenhouse = Column(Integer, ForeignKey("greenhouse.id_greenhouse"), nullable=False)
    value = Column(Integer, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)