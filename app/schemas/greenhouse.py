from pydantic import BaseModel

class GreenhouseCreate(BaseModel):
    title: str
    guid: str
    pin: str