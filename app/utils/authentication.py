import bcrypt
import jwt
from fastapi import HTTPException, Depends, status
from sqlalchemy.orm import Session
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.models.user import User
from app.dependencies import get_db
from datetime import datetime, timedelta
from dotenv import load_dotenv
import os

load_dotenv()
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"
auth_scheme = HTTPBearer()

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode(), hashed_password.encode())

def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def create_email_token(email: str, expires_delta: timedelta) -> str:
    expire = datetime.utcnow() + expires_delta
    to_encode = {"sub": email, "exp": expire, "token_type": "email_verification"}
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def create_reset_token(email: str, expires_delta: timedelta) -> str:
    expire = datetime.utcnow() + expires_delta
    to_encode = {"sub": email, "exp": expire, "token_type": "password_reset"}
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def get_current_user(
    token: HTTPAuthorizationCredentials,
    db: Session = Depends(get_db)
) -> int:
    try:
        payload = jwt.decode(token.credentials, SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Срок действия токена истёк", headers={"WWW-Authenticate": "Bearer"})
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Некорректный токен")

    email: str = payload.get("sub")
    if email is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Недействительные учетные данные")

    user = db.query(User).filter(User.email == email).first()

    return user.id_user


def decode_email_token(token: str) -> str:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Срок действия токена истёк")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Некорректный токен")

    if payload.get("token_type") != "email_verification":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Некорректный тип токена")
    email = payload.get("sub")
    if not email:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Некорректный токен (нет email)")

    return email


def decode_reset_token(token: str) -> str:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Срок действия токена истёк")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Некорректный токен")

    if payload.get("token_type") != "password_reset":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Некорректный тип токена")
    email = payload.get("sub")
    if not email:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Некорректный токен (нет email)")

    return email

