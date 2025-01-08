from pydantic import BaseModel

class SensorReadingCreate(BaseModel):
    id_sensor: int
    id_greenhouse: int
    value: int
