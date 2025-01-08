from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.schemas.sensor_reading import SensorReadingCreate
from app.models.sensor_reading import SensorReading
from app.dependencies import get_db

router = APIRouter()

@router.post("/")
def create_sensor_reading(reading: SensorReadingCreate, db: Session = Depends(get_db)):
    db_reading = SensorReading(
        id_sensor=reading.id_sensor,
        id_greenhouse=reading.id_greenhouse,
        value=reading.value
    )
    db.add(db_reading)
    db.commit()
    db.refresh(db_reading)
    return db_reading
