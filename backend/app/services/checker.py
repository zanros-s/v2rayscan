import socket
import ssl
import time
from datetime import datetime
from typing import Tuple

from sqlalchemy.orm import Session

from .. import models
from ..config import settings
from .notifier import notify_status_change, get_settings
from .xray_helper import do_request_via_xray
from ..models import Server, Check
from ..database import SessionLocal

def check_server_tcp(server: models.Server, timeout: float = 3.0) -> Tuple[bool, float | None, str | None]:

    start = time.time()
    try:
        with socket.create_connection((server.host, server.port), timeout=timeout) as sock:
            if server.security in ("tls", "reality"):
                context = ssl.create_default_context()
                sni = server.sni or server.host
                with context.wrap_socket(sock, server_hostname=sni):
                    pass
        latency_ms = (time.time() - start) * 1000.0
        return True, latency_ms, None
    except Exception as e:
        return False, None, str(e)


def run_single_check(db: Session, server: Server):


    ok, latency, error = do_request_via_xray(
        server,
        method="GET",
        url=settings.XRAY_TEST_URL,
    )

    status = "UP" if ok else "DOWN"
    latency_ms = latency if latency is not None else None

    check = Check(
        server_id=server.id,
        status=status,
        latency_ms=latency_ms,
        error=error,
    )
    db.add(check)
    db.commit()
    db.refresh(check)


    last_check = (
        db.query(Check)
        .filter(Check.server_id == server.id)
        .order_by(Check.checked_at.desc())
        .offset(1)
        .first()
    )
    prev_status = last_check.status if last_check else None


    settings_obj = get_settings(db)
    threshold = settings_obj.down_fail_threshold or 1
    if threshold < 1:
        threshold = 1


    if status == "DOWN":

        recent_checks = (
            db.query(Check)
            .filter(Check.server_id == server.id)
            .order_by(Check.checked_at.desc())
            .limit(threshold)
            .all()
        )

        consecutive_down = 0
        for c in recent_checks:
            if c.status == "DOWN":
                consecutive_down += 1
            else:
                break


        if consecutive_down == threshold:
            notify_status_change(
                db,
                server,
                prev_status,
                "DOWN",
                error=error,
                latency=latency_ms,
            )

    elif status == "UP":

        recent_checks = (
            db.query(Check)
            .filter(Check.server_id == server.id)
            .order_by(Check.checked_at.desc())
            .offset(1)  
            .limit(threshold)
            .all()
        )

        consecutive_down = 0
        for c in recent_checks:
            if c.status == "DOWN":
                consecutive_down += 1
            else:
                break

        if consecutive_down == threshold:
            notify_status_change(
                db,
                server,
                "DOWN",  
                "UP",
                error=None,
                latency=latency_ms,
            )

