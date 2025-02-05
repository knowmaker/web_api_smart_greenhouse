from sqlalchemy import Column, Integer, String, Boolean
from app.dependencies import Base
from sqlalchemy.orm import relationship

class User(Base):
    __tablename__ = "user"
    id_user = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password = Column(String, nullable=False)
    last_name = Column(String, nullable=True)
    first_name = Column(String, nullable=True)
    is_verified = Column(Boolean, default=False)
    greenhouses = relationship("Greenhouse", back_populates="owner")
    fcm_tokens = relationship("FCMToken", back_populates="user", cascade="all, delete")
