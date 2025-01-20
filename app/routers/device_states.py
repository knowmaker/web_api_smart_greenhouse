from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.orm import Session
from app.models.device_state import DeviceState
from app.models.device import Device
from app.models.greenhouse import Greenhouse
from app.dependencies import get_db
from sqlalchemy.sql import func
from fastapi.responses import JSONResponse
from app.external_services.mqtt import publish_to_mqtt
from app.utils.authentication import get_current_user, auth_scheme
from fastapi.security import HTTPAuthorizationCredentials

router = APIRouter()

@router.get("/{guid}")
def get_latest_device_states(
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
            DeviceState.id_device,
            func.max(DeviceState.timestamp).label("latest_timestamp"),
        )
        .filter(DeviceState.id_greenhouse == greenhouse.id_greenhouse)
        .group_by(DeviceState.id_device)
        .subquery()
    )

    latest_states = (
        db.query(DeviceState, Device.label)
        .join(
            subquery,
            (DeviceState.id_device == subquery.c.id_device) &
            (DeviceState.timestamp == subquery.c.latest_timestamp),
        )
        .join(Device, Device.id_device == DeviceState.id_device)
        .all()
    )

    if not latest_states:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Состояния устройств не найдены",
            headers={"Content-Type": "application/json; charset=utf-8"},
        )

    response_data = {
        "latest_device_states": [
            {
                "device_label": state[1],
                "state": state[0].state,
            }
            for state in latest_states
        ],
    }

    return JSONResponse(
        content=response_data,
        headers={"Content-Type": "application/json; charset=utf-8"},
    )


@router.post("/{guid}/control/{control_name}/{state}")
def control_device(
    guid: str,
    control_name: str,
    state: int,
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

    mqtt_topic = f"m/{guid}/c/{control_name}"

    try:
        publish_to_mqtt(mqtt_topic, state)
        return JSONResponse(
            content={"message": f"Команда отправлена: {control_name} установлено в {state}"},
            headers={"Content-Type": "application/json; charset=utf-8"},
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при публикации MQTT сообщения: {e}",
            headers={"Content-Type": "application/json; charset=utf-8"},
        )
