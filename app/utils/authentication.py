import bcrypt
import jwt
from fastapi import HTTPException, Depends, status
from sqlalchemy.orm import Session
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.models.user import User
from app.dependencies import get_db
import random
import hashlib
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

def generate_hashed_code(email: str, action: str):
    code = str(random.randint(100000, 999999))
    salt = f"{email}{SECRET_KEY}{action}"
    hash_code = hashlib.sha256(f"{code}{salt}".encode()).hexdigest()
    return code, hash_code

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

def verify_hashed_code(email: str, entered_code: str, received_hash: str, action: str):
    salt = f"{email}{SECRET_KEY}{action}"
    expected_hash = hashlib.sha256(f"{entered_code}{salt}".encode()).hexdigest()
    return expected_hash == received_hash
