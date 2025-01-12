from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.schemas.sensor_reading import SensorReadingCreate
from app.models.sensor_reading import SensorReading
from app.models.sensor import Sensor
from app.models.greenhouse import Greenhouse
from app.dependencies import get_db
from sqlalchemy.sql import func
from fastapi.responses import JSONResponse
from app.utils.authentication import get_current_user, auth_scheme
from fastapi.security import HTTPAuthorizationCredentials

router = APIRouter()

@router.get("/{guid}")
def get_latest_sensor_readings(guid: str, db: Session = Depends(get_db), token: HTTPAuthorizationCredentials = Depends(auth_scheme)):
    user_id = get_current_user(token, db)

    greenhouse = db.query(Greenhouse).filter(Greenhouse.guid == guid).first()
    if not greenhouse:
        raise HTTPException(status_code=404, detail="Greenhouse not found")

    if greenhouse.id_user != user_id:
        raise HTTPException(status_code=403, detail="Access denied to this greenhouse")

    subquery = (
        db.query(
            SensorReading.id_sensor,
            func.max(SensorReading.timestamp).label("latest_timestamp"),
        )
        .filter(SensorReading.id_greenhouse == greenhouse.id_greenhouse)
        .group_by(SensorReading.id_sensor)
        .subquery()
    )

    latest_readings = (
        db.query(SensorReading, Sensor.label)
        .join(
            subquery,
            (SensorReading.id_sensor == subquery.c.id_sensor) &
            (SensorReading.timestamp == subquery.c.latest_timestamp),
        )
        .join(Sensor, Sensor.id_sensor == SensorReading.id_sensor)
        .all()
    )

    if not latest_readings:
        raise HTTPException(status_code=404, detail="No sensor readings found")

    response_data = {
        "latest_readings": [
            {
                "sensor_label": reading[1],
                "value": reading[0].value,
            }
            for reading in latest_readings
        ],
    }

    return JSONResponse(content=response_data)
