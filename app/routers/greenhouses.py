from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.schemas.greenhouse import GreenhouseCreate
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