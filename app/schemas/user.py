from pydantic import BaseModel, Field
from typing import Optional

class UserCreate(BaseModel):
    email: str
    password: str
    last_name: str
    first_name: str

class UserLogin(BaseModel):
    email: str
    password: str


class UserUpdate(BaseModel):
    first_name: Optional[str] = Field(None, title="Имя")
    last_name: Optional[str] = Field(None, title="Фамилия")

class FCMTokenPayload(BaseModel):
    fcm_token: str