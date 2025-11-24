import json
import socket
import subprocess
import tempfile
import time
import os
import shutil
from typing import Tuple

import requests

from ..config import settings
from .. import models
from .xray_link_converter import convert_uri_json

def find_free_port() -> int:

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


def build_xray_config_for_server(server: models.Server, socks_port: int) -> dict:

    params = {}
    if server.params_json:
        try:
            params = json.loads(server.params_json)
        except Exception:
            params = {}

    proto = (server.type or "").lower()

    
    raw_link = (getattr(server, "raw_link", "") or "").strip()

    
    if raw_link.startswith("trojan://"):
        http_port = socks_port + 1
        cfg = convert_uri_json(
            host="127.0.0.1",
            port=http_port,
            socksport=socks_port,
            uri=raw_link,
        )
        if cfg is None:
            raise ValueError("Failed to build XRAY config from trojan URI")
        return cfg

    
    if "type=grpc" in raw_link:
        http_port = socks_port + 1
        cfg = convert_uri_json(
            host="127.0.0.1",
            port=http_port,
            socksport=socks_port,
            uri=raw_link,
        )
        if cfg is None:
            raise ValueError("Failed to build XRAY config from gRPC URI")
        return cfg

    if proto not in ("vless", "vmess"):
        raise ValueError(f"XRAY config only implemented for VLESS/VMESS, got: {proto}")


    if not server.uuid:
        raise ValueError("Server has no UUID/ID (required for VLESS/VMESS)")

    # -------------- streamSettings مشترک --------------
    network = (server.network or params.get("type") or params.get("net") or "tcp").lower()

    security = (server.security or params.get("security") or "none")
    security = (security or "none").lower()

    # در خیلی از vmess ها فقط tls=1 یا tls=tls هست
    tls_flag = str(params.get("tls", "")).lower()
    if security == "none" and tls_flag not in ("", "0", "false", "none"):
        security = "tls"

    sni = server.sni or params.get("sni") or params.get("host") or server.host

    stream_settings: dict = {
        "network": network,
        "security": security if security != "none" else "",
    }

    # REALITY / TLS
    if security == "reality":
        stream_settings["security"] = "reality"
        stream_settings["realitySettings"] = {
            "show": False,
            "fingerprint": params.get("fp") or "firefox",
            "serverName": sni,
            "publicKey": params.get("pbk"),
            "shortId": params.get("sid", ""),
            "spiderX": params.get("spx", ""),
        }
    elif security == "tls":
        stream_settings["security"] = "tls"

        tls_settings: dict = {
            "serverName": sni,
            "allowInsecure": str(params.get("allowInsecure", "")).lower() == "true",
        }

        # alpn=h2,http/1.1
        alpn = params.get("alpn")
        if alpn:
            tls_settings["alpn"] = [x.strip() for x in alpn.split(",") if x.strip()]

        # fp=chrome / safari / ...
        fp = params.get("fp")
        if fp:
            tls_settings["fingerprint"] = fp

        stream_settings["tlsSettings"] = tls_settings

    else:
        stream_settings["security"] = ""

    # ---------- تنظیمات مخصوص XHTTP ----------
    if network == "xhttp":
        xhttp_settings: dict = {}

        # path (مثلاً / یا /Vpnbaran)
        path = params.get("path")
        if path:
            xhttp_settings["path"] = path

        # mode (مثلاً auto)
        mode = params.get("mode")
        if mode:
            xhttp_settings["mode"] = mode

        # host → هدر Host برای درخواست xhttp
        host_header = params.get("host") or params.get("Host") or params.get("authority")
        if host_header:
            xhttp_settings["host"] = host_header

        if xhttp_settings:
            stream_settings["xhttpSettings"] = xhttp_settings


    # -------------- تنظیمات transport (ws / xhttp و ...) --------------
    if network == "ws":
        ws_settings = {
            "path": params.get("path", "/"),
            "headers": {},
        }
        host_header = params.get("host") or params.get("Host") or params.get("authority")
        if host_header:
            ws_settings["headers"]["Host"] = host_header
        stream_settings["wsSettings"] = ws_settings

    # -------------- outbound بر اساس پروتکل --------------
    if proto == "vless":
        encryption = params.get("encryption", "none")
        flow = params.get("flow", "")

        outbound = {
            "tag": f"healthcheck-{server.id}",
            "protocol": "vless",
            "settings": {
                "vnext": [
                    {
                        "address": server.host,
                        "port": server.port,
                        "users": [
                            {
                                "id": server.uuid,
                                "encryption": encryption,
                                "flow": flow,
                            }
                        ],
                    }
                ]
            },
            "streamSettings": stream_settings,
        }

    else:  # vmess
        # alterId در وی‌مس قدیمی؛ اگر نباشه 0
        alter_id = 0
        for key in ("aid", "alterId"):
            if key in params:
                try:
                    alter_id = int(params.get(key) or 0)
                except Exception:
                    alter_id = 0
                break

        vmess_security = params.get("scy") or "auto"

        outbound = {
            "tag": f"healthcheck-{server.id}",
            "protocol": "vmess",
            "settings": {
                "vnext": [
                    {
                        "address": server.host,
                        "port": server.port,
                        "users": [
                            {
                                "id": server.uuid,
                                "alterId": alter_id,
                                "security": vmess_security,
                            }
                        ],
                    }
                ]
            },
            "streamSettings": stream_settings,
        }

    # -------------- کل کانفیگ --------------
    config = {
        "log": {
            "loglevel": "warning"
        },
        "inbounds": [
            {
                "listen": "127.0.0.1",
                "port": socks_port,
                "protocol": "socks",
                "settings": {
                    "udp": False,
                    "ip": "127.0.0.1",
                }
            }
        ],
        "outbounds": [
            outbound
        ]
    }

    return config



def do_request_via_xray(
    server: models.Server,
    method: str,
    url: str,
    **req_kwargs,
) -> Tuple[bool, float | None, str | None]:


    xray_path = settings.XRAY_PATH
    startup_delay = settings.XRAY_STARTUP_DELAY
    timeout = float(req_kwargs.pop("timeout", settings.XRAY_REQUEST_TIMEOUT))

    socks_port = find_free_port()

    try:
        config_dict = build_xray_config_for_server(server, socks_port)
    except ValueError as e:
        return False, None, f"XRAY config error: {e}"

    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = f"{tmpdir}/xray_request_{server.id}.json"
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(config_dict, f, ensure_ascii=False, indent=2)

        try:
            proc = subprocess.Popen(
                [xray_path, "run", "-c", config_path],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except FileNotFoundError:
            return False, None, f"XRAY binary not found at {xray_path}"
        except Exception as e:
            return False, None, f"Failed to start XRAY: {e}"

        try:
            # کمی صبر کنیم تا xray بالا بیاد
            time.sleep(startup_delay)

            proxies = {
                "http": f"socks5h://127.0.0.1:{socks_port}",
                "https": f"socks5h://127.0.0.1:{socks_port}",
            }

            t0 = time.time()
            resp = requests.request(method, url, proxies=proxies, timeout=timeout, **req_kwargs)
            elapsed_ms = (time.time() - t0) * 1000.0

            # برای تست سلامت یا تلگرام: 2xx یعنی اوکی
            if 200 <= resp.status_code < 300:
                return True, elapsed_ms, None

            return False, None, f"HTTP {resp.status_code}"

        except Exception as e:
            return False, None, f"XRAY request error: {e}"
        finally:
            try:
                proc.terminate()
                proc.wait(timeout=2)
            except Exception:
                try:
                    proc.kill()
                except Exception:
                    pass


def start_xray_session_for_server(server: models.Server):

    xray_path = settings.XRAY_PATH
    startup_delay = settings.XRAY_STARTUP_DELAY

    socks_port = find_free_port()

    try:
        config_dict = build_xray_config_for_server(server, socks_port)
    except ValueError as e:
        raise RuntimeError(f"XRAY config error: {e}")

    tmpdir = tempfile.mkdtemp(prefix=f"xray_live_{server.id or 'tmp'}_")
    config_path = os.path.join(tmpdir, "xray_live.json")
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config_dict, f, ensure_ascii=False, indent=2)

    try:
        proc = subprocess.Popen(
            [xray_path, "run", "-c", config_path],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except FileNotFoundError:
        shutil.rmtree(tmpdir, ignore_errors=True)
        raise RuntimeError(f"XRAY binary not found at {xray_path}")
    except Exception as e:
        shutil.rmtree(tmpdir, ignore_errors=True)
        raise RuntimeError(f"Failed to start XRAY: {e}")

    # کمی صبر تا بالا بیاد
    time.sleep(startup_delay)

    proxies = {
        "http": f"socks5h://127.0.0.1:{socks_port}",
        "https": f"socks5h://127.0.0.1:{socks_port}",
    }

    return {
        "proc": proc,
        "tmpdir": tmpdir,
        "socks_port": socks_port,
        "proxies": proxies,
    }


def stop_xray_session(session: dict):

    if not session:
        return

    proc = session.get("proc")
    tmpdir = session.get("tmpdir")

    if proc is not None:
        try:
            if proc.poll() is None:
                proc.terminate()
                proc.wait(timeout=2)
        except Exception:
            try:
                proc.kill()
            except Exception:
                pass

    if tmpdir:
        shutil.rmtree(tmpdir, ignore_errors=True)


def http_request_via_session(
    session: dict,
    method: str = "GET",
    url: str = settings.XRAY_TEST_URL,
    timeout: float | None = None,
) -> Tuple[bool, float | None, str | None]:

    proxies = session["proxies"]
    if timeout is None:
        timeout = settings.XRAY_MONITOR_REQUEST_TIMEOUT

    try:
        t0 = time.time()
        resp = requests.request(method, url, proxies=proxies, timeout=timeout)
        elapsed_ms = (time.time() - t0) * 1000.0

        if 200 <= resp.status_code < 300:
            return True, elapsed_ms, None

        return False, None, f"HTTP {resp.status_code}"
    except Exception as e:
        return False, None, f"XRAY request error: {e}"
