from pydantic import BaseModel

class FCMTokenPayload(BaseModel):
    fcm_token: str