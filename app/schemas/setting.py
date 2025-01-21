from pydantic import BaseModel

class SettingCreate(BaseModel):
    id_setting: int
    id_greenhouse: int
    value: int
