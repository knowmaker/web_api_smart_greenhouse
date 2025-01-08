from sqlalchemy import Column, Integer, String
from app.dependencies import Base

class Device(Base):
    __tablename__ = "device"
    id_device = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)