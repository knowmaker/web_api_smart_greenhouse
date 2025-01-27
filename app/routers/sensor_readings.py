from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.orm import Session
from app.models.sensor_reading import SensorReading
from app.models.sensor import Sensor
from app.models.greenhouse import Greenhouse
from app.dependencies import get_db
from sqlalchemy.sql import func
from fastapi.responses import JSONResponse
from app.utils.authentication import get_current_user, auth_scheme
from fastapi.security import HTTPAuthorizationCredentials
from app.external_services.fcm import send_push_notification
from app.models.fcm_token import FCMToken

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



@router.post("/send_notification/")
async def send_notification(id_test: int, title: str, body: str, db: Session = Depends(get_db)):
    try:
        user_tokens = db.query(FCMToken).filter(FCMToken.id_user == id_test).all()

        if not user_tokens:
            return {"message": "У пользователя нет зарегистрированных FCM-токенов."}

        # Отправляем уведомления для всех токенов пользователя
        for token in user_tokens:
            send_push_notification(fcm_token=token.token, title=title, body=body)
            print(token.token)

        return {"message": "Уведомления успешно отправлены."}
    except Exception as e:
        print(f"Ошибка при отправке уведомления: {e}")
        return {"error": "Произошла ошибка при отправке уведомления."}


