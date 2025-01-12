from fastapi import APIRouter, Depends, HTTPException
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
def get_latest_device_states(guid: str, db: Session = Depends(get_db), token: HTTPAuthorizationCredentials = Depends(auth_scheme)):
    user_id = get_current_user(token, db)

    greenhouse = db.query(Greenhouse).filter(Greenhouse.guid == guid).first()
    if not greenhouse:
        raise HTTPException(status_code=404, detail="Greenhouse not found")

    if greenhouse.id_user != user_id:
        raise HTTPException(status_code=403, detail="Access denied to this greenhouse")

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
        raise HTTPException(status_code=404, detail="No device states found")

    response_data = {
        "latest_device_states": [
            {
                "device_label": state[1],
                "state": state[0].state,
            }
            for state in latest_states
        ],
    }

    return JSONResponse(content=response_data)


@router.post("/{guid}/control/{control_name}/{state}")
def control_device(guid: str, control_name: str, state: int, db: Session = Depends(get_db)):

    greenhouse = db.query(Greenhouse).filter(Greenhouse.guid == guid).first()
    if not greenhouse:
        raise HTTPException(status_code=404, detail="Greenhouse not found")

    mqtt_topic = f"m/{guid}/c/{control_name}"

    try:
        publish_to_mqtt(mqtt_topic, state)
        return {"message": f"Command sent: {control_name} set to {state}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to publish MQTT message: {e}")
