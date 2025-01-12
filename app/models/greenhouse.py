from sqlalchemy import Column, Integer, String, ForeignKey
from app.dependencies import Base
from sqlalchemy.orm import relationship

class Greenhouse(Base):
    __tablename__ = "greenhouse"
    id_greenhouse = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=True)
    id_user = Column(Integer, ForeignKey("user.id_user"), nullable=True)
    guid = Column(String, unique=True, index=True)
    pin = Column(String, nullable=False)
    owner = relationship("User", back_populates="greenhouses")