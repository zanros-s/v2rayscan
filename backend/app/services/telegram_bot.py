import time
import threading
from typing import Optional, Dict, Any

import requests
from sqlalchemy.orm import Session

from ..database import SessionLocal
from ..models import Server, Check, SettingsModel
from ..config import settings
from .notifier import get_settings, send_telegram_message
from .checker import run_single_check
from .xray_helper import build_xray_config_for_server, find_free_port


def _build_socks_proxies(settings_obj: SettingsModel) -> Optional[Dict[str, str]]:
    if not settings_obj.telegram_use_proxy:
        return None

    mode = (settings_obj.telegram_proxy_mode or "none").lower()
    if mode != "socks":
        return None

    host = settings_obj.telegram_socks_host
    port = settings_obj.telegram_socks_port
    if not host or not port:
        return None

    user = settings_obj.telegram_socks_username or ""
    password = settings_obj.telegram_socks_password or ""

    auth = ""
    if user and password:
        auth = f"{user}:{password}@"

    proxy_url = f"socks5h://{auth}{host}:{port}"
    return {
        "http": proxy_url,
        "https": proxy_url,
    }


def _choose_telegram_server(db: Session, settings_obj: SettingsModel) -> Optional[Server]:

    if settings_obj.telegram_server_id:
        server = (
            db.query(Server)
            .filter(
                Server.id == settings_obj.telegram_server_id,
                Server.enabled == True,
            )
            .first()
        )
        if server:
            return server



    servers = db.query(Server).filter(Server.enabled == True).all()
    best_server: Optional[Server] = None
    best_latency: Optional[float] = None
    best_checked_at = None

    for s in servers:
        last: Optional[Check] = (
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
            if latency < (best_latency or 1e9):
                best_server = s
                best_latency = latency
                best_checked_at = last.checked_at
            elif latency == best_latency and last.checked_at > best_checked_at:
                best_server = s
                best_checked_at = last.checked_at

    return best_server


def _telegram_get_updates_direct(
    settings_obj: SettingsModel,
    url: str,
    params: Dict[str, Any],
) -> Optional[Dict[str, Any]]:

    try:
        resp = requests.get(url, params=params, timeout=25)
        return resp.json()
    except Exception as e:
        print("[v2rayscan] Telegram bot direct getUpdates error:", e)
        return None


def _telegram_get_updates_via_socks(
    settings_obj: SettingsModel,
    url: str,
    params: Dict[str, Any],
) -> Optional[Dict[str, Any]]:
    proxies = _build_socks_proxies(settings_obj)
    if not proxies:
        return _telegram_get_updates_direct(settings_obj, url, params)

    try:
        resp = requests.get(url, params=params, timeout=25, proxies=proxies)
        return resp.json()
    except Exception as e:
        print("[v2rayscan] Telegram bot SOCKS getUpdates error:", e)
        return None


def _telegram_get_updates_via_server(
    db: Session,
    settings_obj: SettingsModel,
    url: str,
    params: Dict[str, Any],
) -> Optional[Dict[str, Any]]:


    server = _choose_telegram_server(db, settings_obj)
    if not server:
        print("[v2rayscan] Telegram bot: no suitable proxy server (no UP servers); falling back to direct")
        return _telegram_get_updates_direct(settings_obj, url, params)

    xray_path = settings.XRAY_PATH
    startup_delay = settings.XRAY_STARTUP_DELAY
    request_timeout = settings.XRAY_REQUEST_TIMEOUT

    socks_port = find_free_port()

    try:
        config_dict = build_xray_config_for_server(server, socks_port)
    except ValueError as e:
        print("[v2rayscan] Telegram bot XRAY config error:", e)
        return _telegram_get_updates_direct(settings_obj, url, params)

    import json
    import subprocess
    import tempfile
    import os

    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = os.path.join(tmpdir, f"xray_telegram_updates_{server.id}.json")
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(config_dict, f, ensure_ascii=False, indent=2)

        try:
            proc = subprocess.Popen(
                [xray_path, "run", "-c", config_path],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except FileNotFoundError:
            print(f"[v2rayscan] Telegram bot XRAY binary not found at {xray_path}")
            return _telegram_get_updates_direct(settings_obj, url, params)
        except Exception as e:
            print("[v2rayscan] Telegram bot failed to start XRAY:", e)
            return _telegram_get_updates_direct(settings_obj, url, params)

        try:

            time.sleep(startup_delay)

            proxies = {
                "http": f"socks5h://127.0.0.1:{socks_port}",
                "https": f"socks5h://127.0.0.1:{socks_port}",
            }

            resp = requests.get(url, params=params, timeout=request_timeout, proxies=proxies)
            return resp.json()
        except Exception as e:
            print("[v2rayscan] Telegram bot XRAY getUpdates error:", e)

            return _telegram_get_updates_direct(settings_obj, url, params)
        finally:
            try:
                proc.terminate()
                proc.wait(timeout=2)
            except Exception:
                try:
                    proc.kill()
                except Exception:
                    pass


def _telegram_get_updates(
    db: Session,
    settings_obj: SettingsModel,
    offset: int,
) -> Optional[Dict[str, Any]]:

    token = settings_obj.telegram_bot_token
    if not token:
        return None

    url = f"https://api.telegram.org/bot{token}/getUpdates"
    params = {
        "timeout": 20,
        "offset": offset + 1,
    }

    mode = (settings_obj.telegram_proxy_mode or "none").lower()

    if not settings_obj.telegram_use_proxy or mode == "none":
        return _telegram_get_updates_direct(settings_obj, url, params)
    elif mode == "socks":
        return _telegram_get_updates_via_socks(settings_obj, url, params)
    elif mode == "server":
        return _telegram_get_updates_via_server(db, settings_obj, url, params)
    else:
        return _telegram_get_updates_direct(settings_obj, url, params)


def telegram_bot_loop():

    print("[v2rayscan] Telegram bot loop started")
    offset = 0

    while True:
        db: Session = SessionLocal()
        try:
            settings_obj = get_settings(db)

            if not settings_obj.telegram_bot_token:

                time.sleep(5)
                continue

            data = _telegram_get_updates(db, settings_obj, offset)
            if data is None:
                time.sleep(5)
                continue

            if not data.get("ok"):
                print("[v2rayscan] Telegram bot getUpdates not ok:", data)
                time.sleep(5)
                continue

            for update in data.get("result", []):
                offset = update.get("update_id", offset)
                _handle_update(db, settings_obj, update)

        finally:
            db.close()


def _handle_update(db: Session, settings_obj: SettingsModel, update: Dict[str, Any]):
    message = update.get("message") or update.get("edited_message")
    if not message:
        return

    chat = message.get("chat") or {}
    chat_id = chat.get("id")
    text = (message.get("text") or "").strip()

    if not chat_id or not text:
        return

  
    if not settings_obj.telegram_chat_id:
        settings_obj.telegram_chat_id = str(chat_id)
        db.commit()
        db.refresh(settings_obj)
        send_telegram_message(db, settings_obj, "این چت به عنوان ادمین v2rayscan ثبت شد ✅")


    if str(chat_id) != str(settings_obj.telegram_chat_id):
        return


    if text in ("/start", "/help"):
        _send_menu(db, settings_obj)
    elif text == "/status":
        _send_status(db, settings_obj)
    elif text == "/servers":
        _send_servers_list(db, settings_obj)
    elif text.startswith("/test_all"):
        _send_test_all(db, settings_obj)
    elif text.startswith("/test"):
        parts = text.split()
        if len(parts) == 2 and parts[1].isdigit():
            server_id = int(parts[1])
            _send_test_one(db, settings_obj, server_id)
        else:
            send_telegram_message(
                db,
                settings_obj,
                "فرمت دستور تست اشتباه است.\nمثال:\n/test 1",
            )
    else:
        _send_menu(db, settings_obj)


def _send_menu(db: Session, settings_obj: SettingsModel):
    text = (
        "👋 خوش آمدی به پنل ادمین v2rayscan\n\n"
        "دستورات:\n"
        "/status - وضعیت کلی سرورها\n"
        "/servers - لیست سرورها\n"
        "/test_all - تست همه سرورها\n"
        "/test <ID> - تست یک سرور خاص (مثال: /test 1)\n"
    )
    send_telegram_message(db, settings_obj, text)


def _send_status(db: Session, settings_obj: SettingsModel):
    servers = db.query(Server).all()
    if not servers:
        send_telegram_message(db, settings_obj, "هیچ سروری در سیستم ثبت نشده است.")
        return

    up = down = unknown = 0
    for s in servers:
        last = (
            db.query(Check)
            .filter(Check.server_id == s.id)
            .order_by(Check.checked_at.desc())
            .first()
        )
        if not last:
            unknown += 1
        elif last.status == "UP":
            up += 1
        elif last.status == "DOWN":
            down += 1
        else:
            unknown += 1

    total = len(servers)
    text = (
        "📊 وضعیت کلی سرورها:\n\n"
        f"کل سرورها: {total}\n"
        f"UP: {up}\n"
        f"DOWN: {down}\n"
        f"نامشخص (بدون چک): {unknown}"
    )
    send_telegram_message(db, settings_obj, text)


def _send_servers_list(db: Session, settings_obj: SettingsModel):
    servers = db.query(Server).order_by(Server.id).all()
    if not servers:
        send_telegram_message(db, settings_obj, "هیچ سروری در سیستم ثبت نشده است.")
        return

    lines = ["📋 لیست سرورها:"]
    for s in servers:
        last = (
            db.query(Check)
            .filter(Check.server_id == s.id)
            .order_by(Check.checked_at.desc())
            .first()
        )
        status = last.status if last else "-"
        latency = f"{last.latency_ms:.0f}ms" if last and last.latency_ms else "-"
        lines.append(
            f"ID {s.id} - {s.name} ({s.type} {s.host}:{s.port}) → {status} / {latency}"
        )

    send_telegram_message(db, settings_obj, "\n".join(lines))


def _send_test_all(db: Session, settings_obj: SettingsModel):
    servers = db.query(Server).order_by(Server.id).all()
    if not servers:
        send_telegram_message(db, settings_obj, "هیچ سروری در سیستم ثبت نشده است.")
        return

    lines = ["⏱ تست همه سرورها:"]
    for s in servers:
        run_single_check(db, s)
        last = (
            db.query(Check)
            .filter(Check.server_id == s.id)
            .order_by(Check.checked_at.desc())
            .first()
        )
        status = last.status if last else "-"
        latency = f"{last.latency_ms:.0f}ms" if last and last.latency_ms else "-"
        lines.append(f"ID {s.id} - {s.name} → {status} / {latency}")

    send_telegram_message(db, settings_obj, "\n".join(lines))


def _send_test_one(db: Session, settings_obj: SettingsModel, server_id: int):
    s = db.query(Server).filter(Server.id == server_id).first()
    if not s:
        send_telegram_message(db, settings_obj, f"سرور با ID {server_id} پیدا نشد.")
        return

    run_single_check(db, s)
    last = (
        db.query(Check)
        .filter(Check.server_id == s.id)
        .order_by(Check.checked_at.desc())
        .first()
    )

    if not last:
        send_telegram_message(db, settings_obj, "مشکلی در ثبت نتیجه تست به وجود آمد.")
        return

    latency = f"{last.latency_ms:.0f}ms" if last.latency_ms is not None else "-"
    text = (
        f"نتیجه تست سرور:\n\n"
        f"ID: {s.id}\n"
        f"نام: {s.name}\n"
        f"آدرس: {s.host}:{s.port}\n"
        f"وضعیت: {last.status}\n"
        f"Latency: {latency}\n"
        f"Error: {last.error or '-'}"
    )
    send_telegram_message(db, settings_obj, text)


def start_telegram_bot_loop():

    t = threading.Thread(target=telegram_bot_loop, daemon=True)
    t.start()
