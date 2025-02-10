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
    if day is not None and start_hour is not None and end_hour is not None:
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

    # Если указан только день, считаем среднее по каждому часу
    elif day is not None and start_hour is None and end_hour is None:
        start_hour = datetime(year, month, day, 0, 0)
        end_hour = datetime(year, month, day, 23, 59)

        hourly_data = (
            db.query(
                func.date_trunc('hour', SensorReading.timestamp).label("hour"),
                func.avg(SensorReading.value).label("avg_value"),
                func.count(SensorReading.value).label("count")
            )
            .filter(
                SensorReading.id_sensor == id_sensor,
                SensorReading.id_greenhouse == greenhouse.id_greenhouse,
                SensorReading.timestamp >= start_hour,
                SensorReading.timestamp <= end_hour
            )
            .group_by("hour")
            .order_by("hour")
            .all()
        )

        result = {f"{year}-{month:02d}-{day:02d} {hour:02d}:00-{hour + 1:02d}:00": 0 for hour in range(24)}

        # Заполняем данные, если измерений больше 50
        for hour, avg_value, count in hourly_data:
            hour_str = f"{hour.strftime('%Y-%m-%d %H:00')}-{(hour + timedelta(hours=1)).strftime('%H:00')}"
            result[hour_str] = round(float(avg_value), 1) if count > 5 else 0

        return JSONResponse(
            content={"data": result},
            headers={"Content-Type": "application/json; charset=utf-8"},
        )

    # Если день не указан, считаем среднее значение за каждый день месяца
    elif day is None and start_hour is None and end_hour is None:
        start_day = datetime(year, month, 1, 0, 0)
        end_day = (datetime(year, month + 1, 1) - timedelta(days=1)).day  # Последний день месяца

        daily_data = (
            db.query(
                func.date_trunc('day', SensorReading.timestamp).label("day"),
                func.avg(SensorReading.value).label("avg_value"),
                func.count(SensorReading.value).label("count")
            )
            .filter(
                SensorReading.id_sensor == id_sensor,
                SensorReading.id_greenhouse == greenhouse.id_greenhouse,
                SensorReading.timestamp >= start_day,
                SensorReading.timestamp < datetime(year, month, end_day, 23, 59, 59)
            )
            .group_by("day")
            .order_by("day")
            .all()
        )

        result = {f"{year}-{month:02d}-{day:02d}": 0 for day in range(1, end_day + 1)}

        for day, avg_value, count in daily_data:
            day_str = day.strftime("%Y-%m-%d")
            result[day_str] = round(float(avg_value), 1) if count >= 12 else 0

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

