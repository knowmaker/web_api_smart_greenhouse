from sqlalchemy import Column, Integer, String
from app.dependencies import Base

class Device(Base):
    __tablename__ = "device"
    id_device = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    label = Column(String, nullable=False)

# INSERT INTO device (name) VALUES
# ('Устройство проветривания'),
# ('Насос и клапан 1 грядки'),
# ('Насос и клапан 2 грядки'),
# ('Клапан наполнения емкости'),
# ('LED');
