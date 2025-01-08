from fastapi import APIRouter
from app.external_services.mqtt import publish_to_mqtt

router = APIRouter()

@router.post("/publish/")
def publish_message(topic: str, payload: str):
    publish_to_mqtt(topic, payload)
    return {"message": "Published to MQTT"}
