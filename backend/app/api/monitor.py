import asyncio
from datetime import datetime

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from .. import models
from ..services.parser import parse_link
from ..services.xray_helper import (
    start_xray_session_for_server,
    stop_xray_session,
    http_request_via_session,
)

router = APIRouter(tags=["monitor"])


@router.websocket("/ws")
async def monitor_ws(websocket: WebSocket):

    await websocket.accept()

    session = None

    try:

        init_msg = await websocket.receive_json()
        link = (init_msg.get("link") or "").strip()
        interval = float(init_msg.get("interval") or 1.0)

        if not link:
            await websocket.send_json(
                {"type": "error", "message": "لینک کانفیگ (link) الزامی است"}
            )
            await websocket.close()
            return

        if interval < 0.2:
            interval = 0.2


        try:
            parsed = parse_link(link)
        except Exception as e:
            await websocket.send_json(
                {"type": "error", "message": f"لینک نامعتبر: {e}"}
            )
            await websocket.close()
            return


        server = models.Server(**parsed.to_server_kwargs())


        try:
            session = start_xray_session_for_server(server)
        except Exception as e:
            await websocket.send_json(
                {"type": "error", "message": f"خطا در راه‌اندازی XRAY: {e}"}
            )
            await websocket.close()
            return

        loop = asyncio.get_running_loop()


        while True:

            ok, latency, error = await loop.run_in_executor(
                None,
                lambda: http_request_via_session(session)
            )

            now = datetime.utcnow().isoformat() + "Z"

            await websocket.send_json(
                {
                    "type": "sample",
                    "ts": now,
                    "ok": ok,
                    "latency_ms": latency,
                    "error": error,
                }
            )

            await asyncio.sleep(interval)


        pass
    except Exception as e:

        try:
            await websocket.send_json(
                {"type": "error", "message": f"خطا: {e}"}
            )
        except Exception:
            pass
    finally:

        if session is not None:
            stop_xray_session(session)
            session = None
