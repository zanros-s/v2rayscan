import requests
from sqlalchemy.orm import Session

from ..models import SettingsModel, Server, Check
from .xray_helper import do_request_via_xray


def get_settings(db: Session) -> SettingsModel:

    settings = db.query(SettingsModel).filter(SettingsModel.id == 1).first()
    if not settings:
        settings = SettingsModel(id=1)
        db.add(settings)
        db.commit()
        db.refresh(settings)
    return settings


def _send_telegram_direct(settings: SettingsModel, text: str) -> None:

    if not settings.telegram_bot_token or not settings.telegram_chat_id:
        return

    url = f"https://api.telegram.org/bot{settings.telegram_bot_token}/sendMessage"
    data = {"chat_id": settings.telegram_chat_id, "text": text}

    try:
        requests.post(url, data=data, timeout=10)
    except Exception as e:
        print(f"Telegram direct send error: {e}")


def _send_telegram_via_socks(settings: SettingsModel, text: str) -> None:

    if not settings.telegram_bot_token or not settings.telegram_chat_id:
        return
    if not settings.telegram_socks_host or not settings.telegram_socks_port:
        _send_telegram_direct(settings, text)
        return

    host = settings.telegram_socks_host
    port = settings.telegram_socks_port

    user = settings.telegram_socks_username or ""
    password = settings.telegram_socks_password or ""

    auth_part = ""
    if user and password:
        auth_part = f"{user}:{password}@"

    proxy_url = f"socks5h://{auth_part}{host}:{port}"

    url = f"https://api.telegram.org/bot{settings.telegram_bot_token}/sendMessage"
    data = {"chat_id": settings.telegram_chat_id, "text": text}

    proxies = {
        "http": proxy_url,
        "https": proxy_url,
    }

    try:
        requests.post(url, data=data, timeout=15, proxies=proxies)
    except Exception as e:
        print(f"Telegram SOCKS send error: {e}")


def _choose_telegram_server(db: Session, settings: SettingsModel) -> Server | None:

    if settings.telegram_server_id:
        server = (
            db.query(Server)
            .filter(Server.id == settings.telegram_server_id, Server.enabled == True)
            .first()
        )
        if server:
            return server


  
    servers = db.query(Server).filter(Server.enabled == True).all()
    best_server = None
    best_latency = None
    best_checked_at = None

    for s in servers:
        last = (
            db.query(Check)
            .filter(Check.server_id == s.id)
            .order_by(Check.checked_at.desc())
            .first()
        )
        if not last or last.status != "UP":
            continue

        latency = last.latency_ms if last.latency_ms is not None else 1e9

        if best_server is None:
            best_server = s
            best_latency = latency
            best_checked_at = last.checked_at
        else:
            if latency < best_latency:
                best_server = s
                best_latency = latency
                best_checked_at = last.checked_at
            elif latency == best_latency and last.checked_at > best_checked_at:
                best_server = s
                best_checked_at = last.checked_at

    return best_server


def _send_telegram_via_server(db: Session, settings: SettingsModel, text: str) -> None:

    if not settings.telegram_bot_token or not settings.telegram_chat_id:
        return

    server = _choose_telegram_server(db, settings)
    if not server:
        print("Telegram proxy server not found or no UP servers; falling back to direct.")
        _send_telegram_direct(settings, text)
        return

    url = f"https://api.telegram.org/bot{settings.telegram_bot_token}/sendMessage"
    data = {"chat_id": settings.telegram_chat_id, "text": text}

    ok, latency, error = do_request_via_xray(
        server,
        method="POST",
        url=url,
        data=data,
    )

    if not ok:
        print(f"Telegram via XRAY failed: {error}")
      
        _send_telegram_direct(settings, text)


def send_telegram_message(db: Session, settings: SettingsModel, text: str) -> None:

    if not settings.telegram_bot_token or not settings.telegram_chat_id:
        return

    mode = (settings.telegram_proxy_mode or "none").lower()

    if not settings.telegram_use_proxy or mode == "none":
        _send_telegram_direct(settings, text)
    elif mode == "socks":
        _send_telegram_via_socks(settings, text)
    elif mode == "server":
        _send_telegram_via_server(db, settings, text)
    else:
        _send_telegram_direct(settings, text)


def notify_status_change(
    db: Session,
    server: Server,
    prev_status: str,
    new_status: str,
    error: str = None,
    latency: float = None,
):

    settings = get_settings(db)
    if not settings.telegram_bot_token or not settings.telegram_chat_id:
        return  

    if new_status == "DOWN":
        text = (
            f"❌ سرور '{server.name}' قطع شد.\n"
            f"Host: {server.host}:{server.port}\n"
            f"Error: {error or '-'}"
        )
    elif new_status == "UP":
        if not settings.notify_on_recover:
            return
        if latency is not None:
            text = (
                f"✅ اتصال سرور '{server.name}' دوباره وصل شد.\n"
                f"Latency: {latency:.0f} ms"
            )
        else:
            text = f"✅ اتصال سرور '{server.name}' دوباره وصل شد."
    else:
        return

    send_telegram_message(db, settings, text)
