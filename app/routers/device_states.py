from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.schemas.device_state import DeviceStateUpdate
from app.models.device_state import DeviceState
from app.dependencies import get_db

router = APIRouter()

@router.post("/")
def update_device_state(state_update: DeviceStateUpdate, db: Session = Depends(get_db)):
    db_state = DeviceState(
        id_device=state_update.id_device,
        id_greenhouse=state_update.id_greenhouse,
        state=state_update.state
    )
    db.add(db_state)
    db.commit()
    db.refresh(db_state)
    return db_state
