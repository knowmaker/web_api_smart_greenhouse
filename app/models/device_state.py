from sqlalchemy import Column, Integer, DateTime, ForeignKey, Boolean
from app.dependencies import Base
from datetime import datetime

class DeviceState(Base):
    __tablename__ = "device_state"
    id_dstate = Column(Integer, primary_key=True, index=True)
    id_device = Column(Integer, ForeignKey("device.id_device"), nullable=False)
    id_greenhouse = Column(Integer, ForeignKey("greenhouse.id_greenhouse"), nullable=False)
    state = Column(Boolean, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)