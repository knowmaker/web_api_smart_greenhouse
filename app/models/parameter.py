from sqlalchemy import Column, Integer, String
from app.dependencies import Base

class Parameter(Base):
    __tablename__ = "parameter"
    id_parameter = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    label = Column(String, nullable=False)