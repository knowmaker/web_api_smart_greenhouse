from pydantic import BaseModel, Field, model_validator
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
    first_name: Optional[str] = Field(None)
    last_name: Optional[str] = Field(None)

    @model_validator(mode="after")
    def validate_at_least_one_field(self):
        if not self.first_name and not self.last_name:
            raise ValueError("Необходимо указать хотя бы одно поле: first_name или last_name")
        return self

class FCMTokenPayload(BaseModel):
    fcm_token: str