from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.orm import Session
from app.models.parameter import Parameter
from app.models.setting import Setting
from app.models.greenhouse import Greenhouse
from app.dependencies import get_db
from sqlalchemy.sql import func
from fastapi.responses import JSONResponse
from app.utils.authentication import get_current_user, auth_scheme
from fastapi.security import HTTPAuthorizationCredentials
from app.external_services.mqtt import publish_to_mqtt

router = APIRouter()

@router.get("/{guid}")
def get_latest_settings(
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
            Setting.id_parameter,
            func.max(Setting.timestamp).label("latest_timestamp"),
        )
        .filter(Setting.id_greenhouse == greenhouse.id_greenhouse)
        .group_by(Setting.id_parameter)
        .subquery()
    )

    latest_settings = (
        db.query(Setting, Parameter.label)
        .join(
            subquery,
            (Setting.id_parameter == subquery.c.id_parameter) &
            (Setting.timestamp == subquery.c.latest_timestamp),
        )
        .join(Parameter, Parameter.id_parameter == Setting.id_parameter)
        .all()
    )

    if not latest_settings:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Данные настроек не найдены",
            headers={"Content-Type": "application/json; charset=utf-8"},
        )

    response_data = {
        "latest_settings": [
            {
                "parameter_label": setting[1],
                "value": setting[0].value,
            }
            for setting in latest_settings
        ],
    }

    return JSONResponse(
        content=response_data,
        headers={"Content-Type": "application/json; charset=utf-8"},
    )

@router.post("/{guid}")
def post_latest_settings(
    guid: str,
    payload: dict,
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

    if "new_settings" not in payload:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Неверный формат данных",
            headers={"Content-Type": "application/json; charset=utf-8"}
        )

    new_settings = payload["new_settings"]

    id_value_mapping = {}
    for setting in new_settings:
        label = setting.get("parameter_label")
        value = setting.get("value")

        if not label or value is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Неверный формат данных",
                headers={"Content-Type": "application/json; charset=utf-8"}
            )

        parameter = db.query(Parameter).filter(Parameter.label == label).first()

        id_value_mapping[str(parameter.id_parameter)] = value

    result = str(id_value_mapping).replace("'", '"').replace(" ", "")

    mqtt_topic = f"m/{guid}/s/update"
    try:
        publish_to_mqtt(mqtt_topic, result)
        return JSONResponse(
            content={"message": f"Настройки обновлены"},
            headers={"Content-Type": "application/json; charset=utf-8"},
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при публикации MQTT сообщения: {e}",
            headers={"Content-Type": "application/json; charset=utf-8"},
        )