from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.schemas.greenhouse import GreenhouseBind, GreenhouseUnbind
from app.models.greenhouse import Greenhouse
from app.dependencies import get_db
from app.utils.authentication import get_current_user, auth_scheme
from fastapi.security import HTTPAuthorizationCredentials

router = APIRouter()

@router.get("/")
def get_all_greenhouses(db: Session = Depends(get_db)):
    greenhouses = db.query(Greenhouse).all()
    return greenhouses

@router.get("/my")
def get_user_greenhouses(db: Session = Depends(get_db), token: HTTPAuthorizationCredentials = Depends(auth_scheme)):
    user_id = get_current_user(token, db)
    greenhouses = db.query(Greenhouse).filter(Greenhouse.id_user == user_id).all()
    return greenhouses

@router.patch("/bind")
def bind_greenhouse(
    greenhouse_data: GreenhouseBind,
    db: Session = Depends(get_db),
    token: HTTPAuthorizationCredentials = Depends(auth_scheme)):

    user_id = get_current_user(token, db)

    greenhouse = db.query(Greenhouse).filter(
        Greenhouse.guid == greenhouse_data.guid,
        Greenhouse.pin == greenhouse_data.pin
    ).first()

    if not greenhouse:
        raise HTTPException(status_code=404, detail="Invalid GUID or PIN")

    if greenhouse.id_user and greenhouse.id_user != user_id:
        raise HTTPException(status_code=403, detail="Greenhouse is already bound to another user")

    greenhouse.id_user = user_id
    db.commit()

    return {"message": "Greenhouse successfully bound", "guid": greenhouse.guid}

@router.patch("/unbind")
def unbind_greenhouse(
    greenhouse_data: GreenhouseUnbind,
    db: Session = Depends(get_db),
    token: HTTPAuthorizationCredentials = Depends(auth_scheme)):

    user_id = get_current_user(token, db)

    greenhouse = db.query(Greenhouse).filter(Greenhouse.guid == greenhouse_data.guid).first()

    if not greenhouse:
        raise HTTPException(status_code=404, detail="Greenhouse not found")

    if greenhouse.id_user != user_id:
        raise HTTPException(status_code=403, detail="Access denied to unbind this greenhouse")

    greenhouse.id_user = None
    db.commit()

    return {"message": "Greenhouse successfully unbound", "guid": greenhouse.guid}

