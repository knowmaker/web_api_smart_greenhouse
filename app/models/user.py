from sqlalchemy import Column, Integer, String
from app.dependencies import Base
from sqlalchemy.orm import relationship

class User(Base):
    __tablename__ = "user"
    id_user = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password = Column(String, nullable=False)
    last_name = Column(String, nullable=True)
    first_name = Column(String, nullable=True)
    greenhouses = relationship("Greenhouse", back_populates="owner")
    fcm_token = Column(String, nullable=True)
