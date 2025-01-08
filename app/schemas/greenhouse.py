from pydantic import BaseModel

class GreenhouseCreate(BaseModel):
    label: str