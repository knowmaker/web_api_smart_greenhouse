from sqlalchemy import Column, Integer, String
from app.dependencies import Base

class Sensor(Base):
    __tablename__ = "sensor"
    id_sensor = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    label = Column(String, nullable=False)
