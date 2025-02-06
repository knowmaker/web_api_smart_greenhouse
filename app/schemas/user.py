from pydantic import BaseModel, Field, model_validator, EmailStr, constr
from typing import Optional

class UserRegister(BaseModel):
    email: EmailStr
    password: constr(min_length=6)
    last_name: str
    first_name: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserUpdate(BaseModel):
    first_name: Optional[str] = Field(None)
    last_name: Optional[str] = Field(None)

    @model_validator(mode="after")
    def validate_at_least_one_field(self):
        if not self.first_name and not self.last_name:
            raise ValueError("Необходимо указать хотя бы одно поле: first_name или last_name")
        return self

class VerifyEmail(BaseModel):
    email: EmailStr
    entered_code: str
    received_hash: str

class ResendCode(BaseModel):
    email: EmailStr

class ForgotPassword(BaseModel):
    email: EmailStr

class ResetPassword(BaseModel):
    email: EmailStr
    entered_code: str
    received_hash: str
    new_password: constr(min_length=6)

class FCMTokenPayload(BaseModel):
    fcm_token: str