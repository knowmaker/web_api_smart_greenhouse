from sqlalchemy import Column, Integer, DateTime, ForeignKey
from app.dependencies import Base
from datetime import datetime

class Setting(Base):
    __tablename__ = "setting"
    id_setting = Column(Integer, primary_key=True, index=True)
    id_parameter = Column(Integer, ForeignKey("parameter.id_parameter"), nullable=False)
    id_greenhouse = Column(Integer, ForeignKey("greenhouse.id_greenhouse"), nullable=False)
    value = Column(Integer, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)