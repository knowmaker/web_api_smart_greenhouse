from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.schemas.user import UserCreate
from app.models.user import User
from app.dependencies import get_db
from app.utils.authentication import hash_password

router = APIRouter()

@router.post("/")
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    hashed_password = hash_password(user.password)
    db_user = User(email=user.email, password=hashed_password, last_name=user.last_name, first_name=user.first_name)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user
