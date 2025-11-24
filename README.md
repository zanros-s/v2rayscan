# v2rayscan

A lightweight web panel to monitor VLESS/VMESS/Trojan proxy nodes using Xray core.

- Backend: **FastAPI + SQLAlchemy + SQLite**
- Frontend: **HTML/CSS/JavaScript + Chart.js**
- Core: **Xray** (used to test proxy links end-to-end)

v2rayscan is designed for VPS monitoring, uptime measuring, real-time diagnostics, and Telegram notifications.

---

# 🚀 Quick Install (One Line)

On a fresh **Debian/Ubuntu** server, run:

```bash
curl -Ls https://github.com/zanros-s/v2rayscan/raw/main/remote-install.sh | sudo bash
```

This performs:

- Install `git`
- Clone repo to `/opt/v2rayscan`
- Install:
  - Python, pip, venv
  - SQLite
  - Xray core
- Setup backend virtualenv
- Create/update `.env`
- Generate:
  - `ADMIN_USERNAME`
  - `ADMIN_PASSWORD`
  - `SECRET_KEY`
- Enable systemd service  
  `v2rayscan.service`

At the end, it prints:

✔ Admin login  
✔ Auto-generated username/password  
✔ Panel URL  
✔ Service status  

---

# 🌐 Web Panel URL

After installation:

- Local:
  ```
  http://127.0.0.1:8000/
  ```

- From outside:
  ```
  http://<SERVER_IP>:8000/
  ```

Examples:

```
http://203.0.113.5:8000/
http://192.168.1.10:8000/
```

---

# ✨ Features

### 🔐 Login System
- Session-based authentication
- Credentials loaded from `.env`
  - `ADMIN_USERNAME`
  - `ADMIN_PASSWORD`

### 📡 Server Parsing & Listing

- Add servers by pasting:
  - `vless://...`
  - `vmess://...`
  - `trojan://...`

- Auto-parsing:
  - Host & port
  - UUID (for VLESS / VMESS)
  - Password (for Trojan)
  - Network / transport:
    - `tcp`
    - `ws` (WebSocket)
    - `grpc`
  - Security:
    - `none`
    - `tls`
    - `reality` (for VLESS / Trojan)
  - Extra options from URI:
    - `sni=...`
    - `alpn=http/1.1,h2,h3`
    - `fp=...` (fingerprint)
    - `host=...`, `path=...`, `headertype=...` (HTTP obfs / WS / XHTTP)
    - `serviceName=...` (gRPC)
    - REALITY params: `pbk`, `sid`, `spx`, `flow` (when present)
  - All extra params are stored as JSON in `params_json`
  - Original link is stored as `raw_link`

- Shows:
  - Latest latency
  - UP/DOWN status

### 🔎 Health Monitoring System
- Background checker loop
- Configurable `check_interval_seconds`
- Real proxy testing using **Xray core**
- For each test:
  - Builds a temporary Xray **client** config
  - Starts Xray with local SOCKS + HTTP inbounds
  - Sends HTTP request to `XRAY_TEST_URL` through Xray
  - Measures latency & success
- Stores history in SQLite (`checks` table)

### 📈 Charts & History
- Per-server history endpoint:  
  `GET /api/checks/{server_id}?minutes=N`
- Real-time chart updates with Chart.js
- Latency + status graph over time
- Useful for seeing trends (packet loss, unstable routes, etc.)

### 🔥 Real-Time Monitor (WebSocket)
- WebSocket:
  `/api/monitor/ws`
- Live testing of a single link
- Instant latency & error stream
- Spins up a temporary Xray instance only for that monitor session

### 📬 Telegram Notifications
- When server goes **DOWN**
- Optional recovery notification (UP)
- Configurable:
  - Bot token
  - Chat ID
  - Proxy mode
  - SOCKS or via Xray
  - `down_fail_threshold` (how many fails before "DOWN" alert)
- Once a server is marked DOWN, a "UP" notification is sent when it becomes reachable again.

### 🌍 Multi-language UI
- EN / FA switch
- All translations in `frontend/js/i18n.js`

---

# 📦 Supported Proxy Protocols & Transports

> v2rayscan does **not** expose a public proxy.  
> It only starts short-lived **Xray client** processes to test your remote nodes.

## ✅ Supported URI Schemes

You can paste links of these types:

- `vless://...`
- `vmess://BASE64(JSON)...`
- `trojan://...`

Anything else (Shadowsocks, HTTP, SOCKS URI, WireGuard, etc.) is currently **not supported**.

---

## VLESS Support

**Scheme:** `vless://UUID@host:port?...`

### Transports

- **TCP**
  - Plain TCP
  - TCP + HTTP header obfuscation (using URI params):
    - `host=...`
    - `headertype=...`
    - `path=...`
  - Also integrates with panel’s XHTTP/HTTP header settings

- **WebSocket** (`type=ws` or `net=ws`)
  - `path=...` → WS path
  - `host=...` → Host header (WS Host)

- **gRPC** (`type=grpc` or `net=grpc`)
  - `serviceName=...` is mapped to `grpcSettings.serviceName`

- **REALITY** (`security=reality`)
  - Can be combined with:
    - TCP
    - gRPC

### Options parsed from URI

- `security=`:
  - `none`
  - `tls`
  - `reality`
- `sni=` — SNI / `serverName`
- `alpn=` — e.g. `http/1.1,h2,h3`
- `fp=` — TLS / REALITY fingerprint (if supported by Xray version)
- REALITY extras:
  - `pbk=` — publicKey
  - `sid=` — shortId
  - `spx=` — spiderX
- HTTP obfs on TCP:
  - `host=`
  - `headertype=`
  - `path=`

Backend stores these values in `params_json` and uses them while building the Xray outbound for VLESS.

---

## VMESS Support

**Scheme:** `vmess://` (base64-encoded JSON)

Decoded JSON fields:

- `add` — host
- `port` — port
- `id` — UUID
- `net` — `tcp`, `ws`, `grpc`
- `tls` — `"none"` / `"tls"`
- `sni` — SNI / serverName
- `alpn` — ALPN list
- `host` — HTTP Host header / WS host
- `path` — WS path or gRPC `serviceName`
- `fp` — TLS fingerprint (optional)

### Transports

- **TCP**
  - Plain TCP
  - TCP + HTTP header obfuscation when:
    - `host` / `type` / `path` are set

- **WebSocket** (`net=ws`)
  - `path` → WS path
  - `host` → Host header

- **gRPC** (`net=grpc`)
  - `path` is used as `grpcSettings.serviceName`

### TLS & Extras

- TLS enabled when `tls` is not `"none"` / `""`
- Uses:
  - `sni`
  - `alpn`
  - optional `fp`

---

## Trojan Support

**Scheme:** `trojan://password@host:port?...`

Trojan support is implemented through the same URI-converter logic that builds a full Xray client config.

### Transports

- **TCP**
  - Plain TCP
  - TCP + HTTP header obfuscation:
    - `host=`
    - `headertype=`
    - `path=`

- **WebSocket** (`type=ws`)
  - `path=`
  - `host=` (WS Host header)

- **gRPC** (`type=grpc` or `net=grpc`)
  - `serviceName=...`

- **REALITY** (`security=reality`)
  - REALITY + TCP
  - REALITY + gRPC

### Options

- Password from `trojan://password@host:port`
- `security=`:
  - `none`
  - `tls`
  - `reality`
- TLS / REALITY extras:
  - `sni=`
  - `alpn=`
  - `fp=`
  - `pbk=`
  - `sid=`
  - `spx=`
- HTTP obfs (on TCP):
  - Same params as VLESS: `host=`, `headertype=`, `path=`

---

## Xray Client Inbounds Used by v2rayscan

Each time v2rayscan tests a server or runs live monitor / Telegram via server, it launches Xray with local-only inbounds:

```jsonc
{
  "inbounds": [
    {
      "tag": "socks",
      "listen": "127.0.0.1",
      "port": <SOCKS_PORT>,
      "protocol": "socks",
      "sniffing": {
        "enabled": true,
        "destOverride": ["http", "tls"],
        "routeOnly": false
      },
      "settings": {
        "auth": "noauth",
        "udp": true,
        "allowTransparent": false
      }
    },
    {
      "tag": "http",
      "listen": "127.0.0.1",
      "port": <HTTP_PORT>,
      "protocol": "http",
      "sniffing": {
        "enabled": true,
        "destOverride": ["http", "tls"],
        "routeOnly": false
      },
      "settings": {
        "auth": "noauth",
        "udp": true,
        "allowTransparent": false
      }
    }
  ]
}
```

- `<SOCKS_PORT>` is a random free port on `127.0.0.1`
- `<HTTP_PORT>` is usually `<SOCKS_PORT> + 1`

v2rayscan uses:

- **SOCKS inbound** for:
  - Health checks
  - Telegram bot when configured to use the server as a proxy
- **HTTP inbound** as an optional local HTTP proxy (used by some helpers)

No public-facing inbound is opened by v2rayscan itself.

---

# 📁 Project Structure

```text
.
├─ backend/
│  ├─ app/
│  │  ├─ api/               # FastAPI routers
│  │  ├─ services/          # checker, xray_helper, parser, telegram_bot, uri converters
│  │  ├─ models.py          # SQLAlchemy models
│  │  ├─ schemas.py         # Pydantic schemas
│  │  ├─ config.py          # Settings loader (.env)
│  │  ├─ database.py        # Engine + SessionLocal
│  │  └─ main.py            # FastAPI main App + background tasks
│  ├─ requirements.txt
│  ├─ .env
│  └─ .env.example
│
├─ frontend/
│  ├─ index.html
│  ├─ css/style.css
│  └─ js/
│      ├─ main.js
│      ├─ charts.js
│      └─ i18n.js
│
├─ deploy/v2rayscan.service
├─ install.sh
├─ remote-install.sh
├─ LICENSE
├─ SECURITY.md
├─ CONTRIBUTING.md
├─ CODE_OF_CONDUCT.md
└─ README.md
```

---

# 🧱 Architecture Overview

### Backend (FastAPI)
- Provides:
  - REST API (`/api/*`)
  - WebSocket monitor
  - Static file hosting for frontend
- Runs background workers:
  - Checker loop
  - Telegram loop

### Frontend
- Plain HTML/JS
- AJAX using native `fetch`
- Chart.js graphs
- No frameworks → lightweight & fast

### Database (SQLite)
Tables:
- `servers`
- `checks`
- `settings`
- `server_groups`

### Xray Integration
- Build temporary config for each test
- Bind **SOCKS + HTTP** inbounds on random local ports
- Perform real HTTP request to `XRAY_TEST_URL` through Xray
- Measure latency
- Cleanup process after each test / monitor session

---

# 🛠 Manual Installation

```bash
git clone https://github.com/zanros-s/v2rayscan.git
cd v2rayscan/backend

python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
```

Run server:

```bash
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Open:

```
http://localhost:8000/
```

---

# ⚙️ Environment Variables

| Key                            | Description                      |
|--------------------------------|----------------------------------|
| `DB_URL`                       | SQLite database path             |
| `XRAY_PATH`                    | Path to xray binary              |
| `XRAY_TEST_URL`                | URL used for testing             |
| `XRAY_STARTUP_DELAY`           | Delay after starting xray        |
| `XRAY_REQUEST_TIMEOUT`         | Timeout for checks               |
| `XRAY_MONITOR_REQUEST_TIMEOUT` | Timeout for live checks          |
| `ADMIN_USERNAME`               | Panel user                       |
| `ADMIN_PASSWORD`               | Panel pass                       |
| `SECRET_KEY`                   | Session signing secret           |

Installer auto-generates:

- `ADMIN_USERNAME`
- `ADMIN_PASSWORD`
- `SECRET_KEY`

---

# 🔍 Troubleshooting

Check service:

```bash
sudo systemctl status v2rayscan.service
```

Logs:

```bash
sudo journalctl -u v2rayscan.service -f
```

If something fails:

- Check Python tracebacks in logs
- Verify `XRAY_PATH` and executable bit
- Ensure `DB_URL` is writable

---

# 🔐 Security

- Never commit `.env`
- Use strong credentials
- Prefer HTTPS with Nginx/Caddy
- Consider firewall restrictions
- Change the auto-generated admin password after first login

---

# 🇮🇷 راهنمای فارسی

**نصب سریع:**

```bash
curl -Ls https://github.com/zanros-s/v2rayscan/raw/main/remote-install.sh | sudo bash
```

بعد از نصب:

- آدرس پنل:  
  `http://IP:8000/`
- یوزرنیم و پسورد داخل `.env` و در خروجی اسکریپت نصب نمایش داده می‌شود.

**پروتکل‌ها و حالت‌های پشتیبانی‌شده:**

- `VLESS`  
  - TCP / WS / gRPC  
  - TLS / REALITY  
  - HTTP Obfs (host, path, headertype)
- `VMESS`  
  - TCP / WS / gRPC  
  - TLS + HTTP Obfs (host, path, type)
- `Trojan`  
  - TCP / WS / gRPC / REALITY  
  - TLS + HTTP Obfs

پنل برای تست هر سرور، یک Xray به‌صورت **کلاینت** اجرا می‌کند:

- روی `127.0.0.1` یک SOCKS و یک HTTP inbound باز می‌کند  
- از طریق آن‌ها درخواست به `XRAY_TEST_URL` می‌فرستد  
- پینگ را اندازه می‌گیرد و وضعیت را ذخیره می‌کند  
- بعد از تست، پروسه Xray را می‌بندد

**قابلیت‌ها:**

- مانیتورینگ VLESS / VMESS / Trojan  
- نمایش وضعیت UP/DOWN  
- نمودار پینگ و تاریخچه  
- مانیتور لحظه‌ای (Real-Time) با WebSocket  
- نوتیفیکیشن تلگرام (قطع و وصل شدن)  
- گروه‌بندی سرورها  
- رابط کاربری دو زبانه (فارسی / انگلیسی)

Pull Requests are welcome!
