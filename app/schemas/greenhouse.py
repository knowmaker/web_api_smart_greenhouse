from pydantic import BaseModel

class GreenhouseCreate(BaseModel):
    title: str
    guid: str
    pin: str

class GreenhouseBind(BaseModel):
    guid: str
    pin: str

class GreenhouseUnbind(BaseModel):
    guid: str

class GreenhouseUpdate(BaseModel):
    title: str