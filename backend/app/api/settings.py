from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from .. import models, schemas
from ..deps import get_db
from ..services.notifier import get_settings

router = APIRouter()


@router.get("/", response_model=schemas.SettingsRead)
def read_settings(db: Session = Depends(get_db)):
    settings = get_settings(db)
    return schemas.SettingsRead(
        check_interval_seconds=settings.check_interval_seconds,
        telegram_bot_token=settings.telegram_bot_token,
        telegram_chat_id=settings.telegram_chat_id,
        notify_on_recover=settings.notify_on_recover,
        telegram_use_proxy=settings.telegram_use_proxy,
        telegram_proxy_mode=settings.telegram_proxy_mode or "none",
        telegram_socks_host=settings.telegram_socks_host,
        telegram_socks_port=settings.telegram_socks_port,
        telegram_socks_username=settings.telegram_socks_username,
        telegram_socks_password=settings.telegram_socks_password,
        telegram_server_id=settings.telegram_server_id,
        down_fail_threshold=settings.down_fail_threshold, 
    )


@router.put("/", response_model=schemas.SettingsRead)
def update_settings(payload: schemas.SettingsUpdate, db: Session = Depends(get_db)):
    settings = get_settings(db)

    if payload.check_interval_seconds is not None:
        settings.check_interval_seconds = payload.check_interval_seconds

    if payload.telegram_bot_token is not None:
        settings.telegram_bot_token = payload.telegram_bot_token.strip() or None

    if payload.telegram_chat_id is not None:
        settings.telegram_chat_id = payload.telegram_chat_id.strip() or None

    if payload.notify_on_recover is not None:
        settings.notify_on_recover = payload.notify_on_recover

    if payload.telegram_use_proxy is not None:
        settings.telegram_use_proxy = payload.telegram_use_proxy

    if payload.telegram_proxy_mode is not None:
        settings.telegram_proxy_mode = (payload.telegram_proxy_mode or "none").lower()

    if payload.telegram_socks_host is not None:
        settings.telegram_socks_host = payload.telegram_socks_host.strip() or None

    if payload.telegram_socks_port is not None:
        settings.telegram_socks_port = payload.telegram_socks_port

    if payload.telegram_socks_username is not None:
        settings.telegram_socks_username = payload.telegram_socks_username.strip() or None

    if payload.telegram_socks_password is not None:
        settings.telegram_socks_password = payload.telegram_socks_password.strip() or None

    if payload.telegram_server_id is not None:
        settings.telegram_server_id = payload.telegram_server_id

    if payload.down_fail_threshold is not None:
        settings.down_fail_threshold = payload.down_fail_threshold

    db.commit()
    db.refresh(settings)

    return read_settings(db)
