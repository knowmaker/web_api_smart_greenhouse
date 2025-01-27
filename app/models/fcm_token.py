from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.dependencies import Base

class FCMToken(Base):
    __tablename__ = "fcm_token"
    id_token = Column(Integer, primary_key=True, index=True)
    id_user = Column(Integer, ForeignKey("user.id_user"), nullable=False)
    token = Column(String, unique=True, nullable=False)
    user = relationship("User", back_populates="fcm_tokens")