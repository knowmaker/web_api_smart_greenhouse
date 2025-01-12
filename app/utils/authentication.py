import bcrypt
import jwt
from fastapi import HTTPException, Depends
from sqlalchemy.orm import Session
from app.models.user import User
from app.dependencies import get_db
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
import os

# load_dotenv()

# SECRET_KEY = os.getenv("SECRET_KEY")
SECRET_KEY = "my_secret_key"
ALGORITHM = "HS256"
auth_scheme = HTTPBearer()

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode(), hashed_password.encode())

def create_access_token(data: dict):
    to_encode = data.copy()
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_current_user(token: HTTPAuthorizationCredentials, db: Session = Depends(get_db)) -> int:
    payload = jwt.decode(token.credentials, SECRET_KEY, algorithms=[ALGORITHM])

    email: str = payload.get("sub")
    if email is None:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")
    user = db.query(User).filter(User.email == email).first()

    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    return user.id_user
