from fastapi import APIRouter, Depends, status, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from app.schemas.user import UserRegister, UserLogin, UserUpdate, ResendCode, VerifyEmail, ForgotPassword, ResetPassword
from app.schemas.fcm_token import  FCMTokenPayload
from app.models.user import User
from app.models.fcm_token import FCMToken
from app.dependencies import get_db
from app.utils.authentication import hash_password, verify_password, create_access_token, generate_hashed_code, verify_hashed_code
from app.utils.authentication import get_current_user, auth_scheme
from fastapi.security import HTTPAuthorizationCredentials
from app.external_services.email import send_email

router = APIRouter()

@router.post("/register")
def create_user(user: UserRegister, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == user.email).first()
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Пользователь уже существует",
            headers={"Content-Type": "application/json; charset=utf-8"},
        )

    hashed_password = hash_password(user.password)
    new_user = User(
        email=user.email,
        password=hashed_password,
        last_name=user.last_name,
        first_name=user.first_name,
        is_verified=False
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    code, hash_code = generate_hashed_code(new_user.email, "verify_email")

    send_email(
        to=str(user.email),
        subject="Подтверждение регистрации",
        message="Ваш код для подтверждения почты:",
        code=code
    )

    return JSONResponse(
        content={"hash_code": hash_code, "message": "Пользователь создан. Проверьте почту для подтверждения."},
        status_code=status.HTTP_201_CREATED,
        headers={"Content-Type": "application/json; charset=utf-8"},
    )

@router.post("/verify-email")
def verify_email(request: VerifyEmail, db: Session = Depends(get_db)):
    if not verify_hashed_code(str(request.email), request.entered_code, request.received_hash, "verify_email"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Неверный код",
            headers={"Content-Type": "application/json; charset=utf-8"},
        )

    user = db.query(User).filter(User.email == str(request.email)).first()
    if user.is_verified:
        return JSONResponse(
            content={"message": "Почта уже подтверждена"},
            headers={"Content-Type": "application/json; charset=utf-8"},
        )

    user.is_verified = True
    db.commit()

    return JSONResponse(
        content={"message": "Почта успешно подтверждена"},
        headers={"Content-Type": "application/json; charset=utf-8"},
    )

@router.post("/resend-verification-code")
def resend_verification_code(request: ResendCode, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == str(request.email)).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден",
            headers={"Content-Type": "application/json; charset=utf-8"},
        )

    if user.is_verified:
        return JSONResponse(
            content={"message": "Почта уже подтверждена"},
            headers={"Content-Type": "application/json; charset=utf-8"},
        )

    # Генерируем новый код и его хеш
    code, hash_code = generate_hashed_code(user.email, "verify_email")

    send_email(
        to=user.email,
        subject="Повторный код подтверждения",
        message="Ваш новый код для подтверждения почты:",
        code=code
    )

    return JSONResponse(
        content={"hash_code": hash_code, "message": "Новый код отправлен на почту"},
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

    if not db_user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Почта не подтверждена",
            headers={"Content-Type": "application/json; charset=utf-8"}
        )

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

    if user_update.first_name:
        current_user.first_name = user_update.first_name
    if user_update.last_name:
        current_user.last_name = user_update.last_name

    db.commit()

    return JSONResponse(
        content={"message": "Данные пользователя успешно обновлены"},
        headers={"Content-Type": "application/json; charset=utf-8"},
    )

@router.post("/forgot-password")
def forgot_password(request: ForgotPassword, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == str(request.email)).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден",
            headers={"Content-Type": "application/json; charset=utf-8"},
        )

    if not user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Почта не подтверждена",
            headers={"Content-Type": "application/json; charset=utf-8"}
        )

    code, hash_code = generate_hashed_code(user.email, "reset_password")

    send_email(
        to=user.email,
        subject="Сброс пароля",
        message="Ваш код для сброса пароля:",
        code=code
    )

    return JSONResponse(
        content={"hash_code": hash_code, "message": "Проверьте почту для сброса пароля."},
        headers={"Content-Type": "application/json; charset=utf-8"},
    )

@router.post("/reset-password")
def reset_password(request: ResetPassword, db: Session = Depends(get_db)):
    if not verify_hashed_code(str(request.email), request.entered_code, request.received_hash, "reset_password"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Неверный код",
            headers={"Content-Type": "application/json; charset=utf-8"},
        )

    user = db.query(User).filter(User.email == str(request.email)).first()
    user.password = hash_password(request.new_password)
    db.commit()

    return JSONResponse(
        content={"message": "Пароль успешно изменен"},
        headers={"Content-Type": "application/json; charset=utf-8"},
    )

@router.put("/fcm")
def update_fcm_token(
    payload: FCMTokenPayload,
    db: Session = Depends(get_db),
    token: HTTPAuthorizationCredentials = Depends(auth_scheme),
):
    user_id = get_current_user(token, db)

    existing_token = db.query(FCMToken).filter(FCMToken.token == payload.fcm_token).first()
    if not existing_token:
        new_token = FCMToken(id_user=user_id, token=payload.fcm_token)
        db.add(new_token)

    db.commit()

    return JSONResponse(
        content={"message": "FCM-токен успешно обновлен"},
        headers={"Content-Type": "application/json; charset=utf-8"},
    )
