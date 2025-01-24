from fastapi import APIRouter, Depends, status, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from app.schemas.user import UserCreate, UserLogin, UserUpdate, FCMTokenPayload
from app.models.user import User
from app.dependencies import get_db
from app.utils.authentication import hash_password, verify_password, create_access_token
from app.utils.authentication import get_current_user, auth_scheme
from fastapi.security import HTTPAuthorizationCredentials

router = APIRouter()

@router.post("/")
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    hashed_password = hash_password(user.password)
    db_user = User(
        email=user.email,
        password=hashed_password,
        last_name=user.last_name,
        first_name=user.first_name,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return JSONResponse(
        content={"message": "Пользователь успешно создан"},
        status_code=status.HTTP_201_CREATED,
        headers={"Content-Type": "application/json; charset=utf-8"},
    )


@router.post("/login")
def login(user: UserLogin, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == user.email).first()

    if not db_user or not verify_password(user.password, db_user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверные учетные данные",
            headers={"Content-Type": "application/json; charset=utf-8"},
        )

    # Генерация токена
    access_token = create_access_token(data={"sub": db_user.email})

    return JSONResponse(
        content={"access_token": access_token, "token_type": "bearer"},
        headers={"Content-Type": "application/json; charset=utf-8"},
    )


@router.get("/me")
def get_me(
    db: Session = Depends(get_db),
    token: HTTPAuthorizationCredentials = Depends(auth_scheme),
):
    user_id = get_current_user(token, db)
    current_user = db.query(User).filter(User.id_user == user_id).first()

    return JSONResponse(
        content={
            "email": current_user.email,
            "first_name": current_user.first_name,
            "last_name": current_user.last_name,
        },
        headers={"Content-Type": "application/json; charset=utf-8"},
    )

@router.patch("/update")
def update_user(
    user_update: UserUpdate,
    db: Session = Depends(get_db),
    token: HTTPAuthorizationCredentials = Depends(auth_scheme),
):
    user_id = get_current_user(token, db)

    current_user = db.query(User).filter(User.id_user == user_id).first()

    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден",
            headers={"Content-Type": "application/json; charset=utf-8"},
        )

    # Обновление имени или фамилии
    if user_update.first_name:
        current_user.first_name = user_update.first_name
    if user_update.last_name:
        current_user.last_name = user_update.last_name

    db.commit()

    return JSONResponse(
        content={"message": "Данные пользователя успешно обновлены"},
        headers={"Content-Type": "application/json; charset=utf-8"},
    )

@router.put("/fcm")
def update_fcm_token(
    payload: FCMTokenPayload,
    db: Session = Depends(get_db),
    token: HTTPAuthorizationCredentials = Depends(auth_scheme),
):
    user_id = get_current_user(token, db)

    user = db.query(User).filter(User.id_user == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден",
            headers={"Content-Type": "application/json; charset=utf-8"},
        )

    if user.fcm_token != payload.fcm_token:
        user.fcm_token = payload.fcm_token
        db.commit()
        db.refresh(user)

    return JSONResponse(
        content={"message": "FCM-токен успешно обновлен"},
        headers={"Content-Type": "application/json; charset=utf-8"},
    )