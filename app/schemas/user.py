from pydantic import BaseModel, Field

class UserCreate(BaseModel):
    email: str
    password: str
    last_name: str
    first_name: str

class UserLogin(BaseModel):
    email: str
    password: str