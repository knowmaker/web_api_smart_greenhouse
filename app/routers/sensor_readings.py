from fastapi import APIRouter, Depends, status, HTTPException, Query
from sqlalchemy.orm import Session
from app.models.sensor_reading import SensorReading
from app.models.sensor import Sensor
from app.models.greenhouse import Greenhouse
from app.dependencies import get_db
from sqlalchemy.sql import func
from fastapi.responses import JSONResponse
from app.utils.authentication import get_current_user, auth_scheme
from fastapi.security import HTTPAuthorizationCredentials
from datetime import datetime, timedelta

router = APIRouter()

@router.get("/{guid}")
def get_latest_sensor_readings(
    guid: str,
    db: Session = Depends(get_db),
    token: HTTPAuthorizationCredentials = Depends(auth_scheme),
):
    user_id = get_current_user(token, db)

    greenhouse = db.query(Greenhouse).filter(Greenhouse.guid == guid).first()
    if not greenhouse:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Теплица не найдена",
            headers={"Content-Type": "application/json; charset=utf-8"},
        )

    if greenhouse.id_user != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Доступ запрещён",
            headers={"Content-Type": "application/json; charset=utf-8"},
        )

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
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Данные с датчиков не найдены",
            headers={"Content-Type": "application/json; charset=utf-8"},
        )

    response_data = {
        "latest_readings": [
            {
                "sensor_label": reading[1],
                "value": reading[0].value,
            }
            for reading in latest_readings
        ],
    }

    return JSONResponse(
        content=response_data,
        headers={"Content-Type": "application/json; charset=utf-8"},
    )

@router.get("/{guid}/{label}")
def get_sensor_data(
    guid: str,
    label: str,
    month: int = Query(..., ge=1, le=12),
    day: int = Query(None, ge=1, le=31),
    start_hour: int = Query(None, ge=0, le=23),
    end_hour: int = Query(None, ge=0, le=23),
    db: Session = Depends(get_db),
    token: HTTPAuthorizationCredentials = Depends(auth_scheme)
):
    user_id = get_current_user(token, db)

    greenhouse = db.query(Greenhouse).filter(Greenhouse.guid == guid).first()
    if not greenhouse:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Теплица не найдена",
            headers={"Content-Type": "application/json; charset=utf-8"},
        )

    if greenhouse.id_user != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Доступ запрещён",
            headers={"Content-Type": "application/json; charset=utf-8"},
        )

    sensor = db.query(Sensor).filter(Sensor.label == label).first()
    id_sensor = sensor.id_sensor
    year = datetime.utcnow().year

    # Если указан диапазон часов, возвращаем данные за этот диапазон
    if start_hour is not None and end_hour is not None:
        start_time = datetime(year, month, day, start_hour, 0)
        end_time = datetime(year, month, day, end_hour, 0)

        readings = db.query(SensorReading).filter(
            SensorReading.id_sensor == id_sensor,
            SensorReading.id_greenhouse == greenhouse.id_greenhouse,
            SensorReading.timestamp >= start_time,
            SensorReading.timestamp < end_time + timedelta(hours=1)
        ).all()

        result = {reading.timestamp.strftime("%Y-%m-%d %H:%M:%S"): reading.value for reading in readings}

        return JSONResponse(
            content={"data": result},
            headers={"Content-Type": "application/json; charset=utf-8"},
        )

    # Если указан только день, считаем среднее по каждой половине часа
    elif day is not None and start_hour is None and end_hour is None:
        start_time = datetime(year, month, day, 0, 0)
        end_time = datetime(year, month, day, 23, 59)

        half_hour_avg = (
            db.query(
                func.date_trunc('hour', SensorReading.timestamp).label("hour"),
                func.extract('minute', SensorReading.timestamp).label("minute"),
                func.avg(SensorReading.value).label("avg_value")
            )
            .filter(
                SensorReading.id_sensor == id_sensor,
                SensorReading.id_greenhouse == greenhouse.id_greenhouse,
                SensorReading.timestamp >= start_time,
                SensorReading.timestamp <= end_time
            )
            .group_by("hour", "minute")
            .order_by("hour", "minute")
            .all()
        )

        result = {}
        for hour, minute, avg_value in half_hour_avg:
            hour_str = hour.strftime("%Y-%m-%d %H:00")
            half = "00-30" if minute < 30 else "30-59"
            if hour_str not in result:
                result[hour_str] = {}
            result[hour_str][half] = float(avg_value)

        return JSONResponse(
            content={"data": result},
            headers={"Content-Type": "application/json; charset=utf-8"},
        )

    # Если день не указан, считаем среднее значение за каждый день месяца
    elif day is None and start_hour is None and end_hour is None:
        start_time = datetime(year, month, 1, 0, 0)
        end_time = datetime(year, month, 31, 23, 59)

        daily_avg = (
            db.query(
                func.date_trunc('day', SensorReading.timestamp).label("day"),
                func.avg(SensorReading.value).label("avg_value")
            )
            .filter(
                SensorReading.id_sensor == id_sensor,
                SensorReading.id_greenhouse == greenhouse.id_greenhouse,
                SensorReading.timestamp >= start_time,
                SensorReading.timestamp <= end_time
            )
            .group_by("day")
            .order_by("day")
            .all()
        )

        result = {day.strftime("%Y-%m-%d"): float(avg_value) for day, avg_value in daily_avg}

        return JSONResponse(
                content={"data": result},
                headers={"Content-Type": "application/json; charset=utf-8"},
            )

    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Некорректные параметры. Укажите либо диапазон часов, либо день, либо оставьте все пустыми для месячного отчета",
            headers={"Content-Type": "application/json; charset=utf-8"},
        )
