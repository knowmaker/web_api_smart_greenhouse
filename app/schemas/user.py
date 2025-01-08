from pydantic import BaseModel

class UserCreate(BaseModel):
    email: str
    password: str
    last_name: str
    first_name: str
