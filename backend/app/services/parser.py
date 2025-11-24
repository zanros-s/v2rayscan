from urllib.parse import urlparse, parse_qs, unquote
import json
import base64


class ParsedLink:
    def __init__(
        self,
        *,
        type_,
        name,
        host,
        port,
        uuid=None,
        security=None,
        sni=None,
        network=None,
        params=None,
        raw_link=None,
    ):
        self.type = type_
        self.name = name
        self.host = host
        self.port = port
        self.uuid = uuid
        self.security = security
        self.sni = sni
        self.network = network
        self.params = params or {}
        self.raw_link = raw_link

    def to_server_kwargs(self):
        return {
            "name": self.name,
            "raw_link": self.raw_link,
            "type": self.type,
            "host": self.host,
            "port": self.port,
            "uuid": self.uuid,
            "security": self.security,
            "sni": self.sni,
            "network": self.network,
            "params_json": json.dumps(self.params, ensure_ascii=False),
        }


# ---------------- VLESS ----------------
def parse_vless(url: str) -> ParsedLink:
    u = urlparse(url)
    if u.scheme.lower() != "vless":
        raise ValueError("Not a vless URL")

    if "@" not in u.netloc:
        raise ValueError("Invalid vless URL: missing userinfo")
    userinfo, _ = u.netloc.split("@", 1)
    uuid = userinfo

    host = u.hostname
    port = u.port
    if not host or not port:
        raise ValueError("Invalid vless URL: missing host or port")

    fragment = unquote(u.fragment) if u.fragment else None
    q = parse_qs(u.query)

    security = q.get("security", [None])[0]
    sni = q.get("sni", [None])[0]
    network = q.get("type", [None])[0]


    params = {k: v[0] for k, v in q.items()}

    name = fragment or host or "unnamed"

    return ParsedLink(
        type_="vless",
        name=name,
        host=host,
        port=port,
        uuid=uuid,
        security=security,
        sni=sni,
        network=network,
        params=params,
        raw_link=url,
    )


# ---------------- VMESS ----------------
def _decode_vmess_payload(payload: str) -> dict:
    s = payload.strip()
    if s.endswith("/"):
        s = s[:-1]

    # padding
    rem = len(s) % 4
    if rem:
        s += "=" * (4 - rem)

    try:
        decoded = base64.urlsafe_b64decode(s.encode("utf-8")).decode(
            "utf-8", errors="ignore"
        )
    except Exception as e:
        raise ValueError(f"Invalid vmess URL: base64 decode failed ({e})")

    try:
        data = json.loads(decoded)
    except Exception as e:
        raise ValueError(f"Invalid vmess URL: JSON decode failed ({e})")

    if not isinstance(data, dict):
        raise ValueError("Invalid vmess URL: JSON must be an object")

    return data


def parse_vmess(url: str) -> ParsedLink:

    u = urlparse(url)
    if u.scheme.lower() != "vmess":
        raise ValueError("Not a vmess URL")


    if "@" not in u.netloc:
        if not u.netloc:
            raise ValueError("Invalid vmess URL: empty payload")

        data = _decode_vmess_payload(u.netloc)

        host = data.get("add")
        port_raw = data.get("port")
        try:
            port = int(port_raw)
        except Exception:
            raise ValueError("Invalid vmess URL: bad port")

        uuid = data.get("id") or data.get("uuid")
        if not uuid:
            raise ValueError("Invalid vmess URL: missing id/uuid")

        fragment = unquote(u.fragment) if u.fragment else None
        name = data.get("ps") or fragment or host or "unnamed"

        network = (data.get("net") or data.get("type") or "tcp") or "tcp"

        tls_flag = (data.get("tls") or data.get("security") or "").lower()
        if tls_flag in ("tls", "reality"):
            security = tls_flag
        else:
            security = None

        sni = data.get("sni") or data.get("host")

        params = data.copy()

        return ParsedLink(
            type_="vmess",
            name=name,
            host=host,
            port=port,
            uuid=uuid,
            security=security,
            sni=sni,
            network=network,
            params=params,
            raw_link=url,
        )


    userinfo, _ = u.netloc.split("@", 1)
    uuid = userinfo

    host = u.hostname
    port = u.port
    if not host or not port:
        raise ValueError("Invalid vmess URL: missing host or port")

    fragment = unquote(u.fragment) if u.fragment else None
    q = parse_qs(u.query)

    security = q.get("security", [None])[0]
    if not security:
        tls_flag = q.get("tls", [None])[0]
        if tls_flag and str(tls_flag).lower() not in ("none", "0", "false", ""):
            security = "tls"

    sni = q.get("sni", [None])[0] or q.get("host", [None])[0]
    network = q.get("type", [None])[0] or q.get("net", [None])[0] or "tcp"

    params = {k: v[0] for k, v in q.items()}
    name = fragment or host or "unnamed"

    return ParsedLink(
        type_="vmess",
        name=name,
        host=host,
        port=port,
        uuid=uuid,
        security=security,
        sni=sni,
        network=network,
        params=params,
        raw_link=url,
    )

# ---------------- TROJAN ----------------
def parse_trojan(url: str) -> ParsedLink:
    u = urlparse(url)
    if u.scheme.lower() != "trojan":
        raise ValueError("Not a trojan URL")

    
    if "@" not in u.netloc:
        raise ValueError("Invalid trojan URL: missing password")

    password, _ = u.netloc.split("@", 1)

    host = u.hostname
    port = u.port
    if not host or not port:
        raise ValueError("Invalid trojan URL: missing host or port")

    fragment = unquote(u.fragment) if u.fragment else None
    q = parse_qs(u.query)

    security = q.get("security", [None])[0]
    sni = q.get("sni", [None])[0]
    network = (
        q.get("type", [None])[0]
        or q.get("net", [None])[0]
        or "tcp"
    )

   
    params = {k: v[0] for k, v in q.items()}
    params["password"] = password

    name = fragment or host or "unnamed"

    return ParsedLink(
        type_="trojan",
        name=name,
        host=host,
        port=port,
        uuid=None,           
        security=security,
        sni=sni,
        network=network,
        params=params,
        raw_link=url,
    )

# ---------------- Router ----------------
def parse_link(url: str) -> ParsedLink:
    url = url.strip()
    u = urlparse(url)
    scheme = (u.scheme or "").lower()

    if scheme == "vless":
        return parse_vless(url)
    if scheme == "vmess":
        return parse_vmess(url)
    if scheme == "trojan":
        return parse_trojan(url)

    raise ValueError(f"Unsupported scheme: {scheme or 'unknown'}")
