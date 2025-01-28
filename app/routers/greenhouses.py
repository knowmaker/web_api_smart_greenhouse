from fastapi import APIRouter, Depends, status, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from app.schemas.greenhouse import GreenhouseBind, GreenhouseUnbind, GreenhouseUpdate
from app.models.greenhouse import Greenhouse
from app.dependencies import get_db
from app.utils.authentication import get_current_user, auth_scheme
from fastapi.security import HTTPAuthorizationCredentials

router = APIRouter()

@router.get("/my")
def get_user_greenhouses(
    db: Session = Depends(get_db),
    token: HTTPAuthorizationCredentials = Depends(auth_scheme),
):
    user_id = get_current_user(token, db)
    greenhouses = db.query(Greenhouse).filter(Greenhouse.id_user == user_id).order_by(Greenhouse.id_greenhouse).all()
    result = [{"guid": gh.guid, "title": gh.title} for gh in greenhouses]

    return JSONResponse(
        content=result,
        headers={"Content-Type": "application/json; charset=utf-8"},
    )


@router.patch("/bind")
def bind_greenhouse(
    greenhouse_data: GreenhouseBind,
    db: Session = Depends(get_db),
    token: HTTPAuthorizationCredentials = Depends(auth_scheme),
):
    user_id = get_current_user(token, db)

    greenhouse = db.query(Greenhouse).filter(
        Greenhouse.guid == greenhouse_data.guid,
        Greenhouse.pin == greenhouse_data.pin,
    ).first()

    if not greenhouse:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Некорректный GUID или PIN теплицы",
            headers={"Content-Type": "application/json; charset=utf-8"},
        )

    if greenhouse.id_user and greenhouse.id_user != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Теплица уже привязана к другому пользователю",
            headers={"Content-Type": "application/json; charset=utf-8"},
        )

    greenhouse.id_user = user_id
    db.commit()

    return JSONResponse(
        content={"message": "Теплица успешно привязана"},
        headers={"Content-Type": "application/json; charset=utf-8"},
    )


@router.patch("/unbind")
def unbind_greenhouse(
    greenhouse_data: GreenhouseUnbind,
    db: Session = Depends(get_db),
    token: HTTPAuthorizationCredentials = Depends(auth_scheme),
):
    user_id = get_current_user(token, db)

    greenhouse = db.query(Greenhouse).filter(Greenhouse.guid == greenhouse_data.guid).first()

    if not greenhouse:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Теплица не найдена",
            headers={"Content-Type": "application/json; charset=utf-8"},
        )

    if greenhouse.id_user != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Доступ к отвязке теплицы запрещен",
            headers={"Content-Type": "application/json; charset=utf-8"},
        )

    greenhouse.id_user = None
    db.commit()

    return JSONResponse(
        content={"message": "Теплица успешно отвязана"},
        headers={"Content-Type": "application/json; charset=utf-8"},
    )

@router.patch("/{guid}")
def update_greenhouse_title(
    guid: str,
    greenhouse_update: GreenhouseUpdate,
    db: Session = Depends(get_db),
    token: HTTPAuthorizationCredentials = Depends(auth_scheme),
):
    user_id = get_current_user(token, db)

    greenhouse = db.query(Greenhouse).filter(Greenhouse.guid == guid).first()

    if not greenhouse:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Теплица не найдена",
            headers={"Content-Type": "application/json; charset=utf-8"},
        )

    if greenhouse.id_user != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Доступ запрещён",
            headers={"Content-Type": "application/json; charset=utf-8"},
        )

    greenhouse.title = greenhouse_update.title
    db.commit()

    return JSONResponse(
        content={"message": "Название теплицы успешно обновлено"},
        headers={"Content-Type": "application/json; charset=utf-8"},
    )