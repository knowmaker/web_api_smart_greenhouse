from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.schemas.greenhouse import GreenhouseCreate
from app.models.greenhouse import Greenhouse
from app.dependencies import get_db

router = APIRouter()

@router.post("/")
def create_greenhouse(greenhouse: GreenhouseCreate, user_id: int, db: Session = Depends(get_db)):
    db_greenhouse = Greenhouse(label=greenhouse.label, id_user=user_id)
    db.add(db_greenhouse)
    db.commit()
    db.refresh(db_greenhouse)
    return db_greenhouse
