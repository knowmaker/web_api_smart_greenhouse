from fastapi import APIRouter, Depends, status, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from app.schemas.user import UserCreate, UserLogin
from app.models.user import User
from app.dependencies import get_db
from app.utils.authentication import hash_password, verify_password, create_access_token

router = APIRouter()

@router.post("/")
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    hashed_password = hash_password(user.password)
    db_user = User(email=user.email, password=hashed_password, last_name=user.last_name, first_name=user.first_name)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return JSONResponse(content={"message": "User created successfully"}, status_code=status.HTTP_201_CREATED)


@router.post("/login")
def login(user: UserLogin, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == user.email).first()

    if not db_user or not verify_password(user.password, db_user.password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    # Генерация токена
    access_token = create_access_token(data={"sub": db_user.email})

    return JSONResponse(content={"access_token": access_token, "token_type": "bearer"})