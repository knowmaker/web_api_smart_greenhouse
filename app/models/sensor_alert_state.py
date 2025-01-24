from sqlalchemy import Column, Integer, Boolean, DateTime, ForeignKey
from app.dependencies import Base

class SensorAlertState(Base):
    __tablename__ = "sensor_alert_state"
    id_salert = Column(Integer, primary_key=True, index=True)
    id_sensor = Column(Integer, ForeignKey("sensor.id_sensor"), nullable=False)
    id_greenhouse = Column(Integer, ForeignKey("greenhouse.id_greenhouse"), nullable=False)
    last_alert_sent = Column(Boolean, default=False)
    alert_timestamp = Column(DateTime, nullable=True)