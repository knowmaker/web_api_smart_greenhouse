from pydantic import BaseModel

class DeviceStateUpdate (BaseModel):
    id_device: int
    id_greenhouse: int
    state: bool
