import firebase_admin
from firebase_admin import credentials, messaging, exceptions
from app.models.fcm_token import FCMToken
from sqlalchemy.orm import Session
from app.dependencies import SessionLocal

cred = credentials.Certificate("smart-greenhouse-24953-firebase-adminsdk-fbsvc-e37e4bd4bb.json")
firebase_admin.initialize_app(cred)

def send_push_notification(fcm_token: str, title: str, body: str):
    message = messaging.Message(
        notification=messaging.Notification(
            title=title,
            body=body,
        ),
        token=fcm_token,
    )

    try:
        response = messaging.send(message)
        print("Successfully sent message:", response)
    except exceptions.FirebaseError as e:
        print(f"Failed to send message to {fcm_token}: {e}")
        db: Session = SessionLocal()
        db.query(FCMToken).filter(FCMToken.token == fcm_token).delete()
        db.commit()