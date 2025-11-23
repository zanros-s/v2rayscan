# v2rayscan

A lightweight web panel to monitor VLESS/VMESS proxy nodes using Xray core.

- Backend: **FastAPI + SQLAlchemy + SQLite**
- Frontend: **HTML/CSS/JavaScript + Chart.js**
- Core: **Xray** (used to test proxy links end-to-end)

v2rayscan is designed for VPS monitoring, uptime measuring, real-time diagnostics, and Telegram notifications.

---

# 🚀 Quick Install (One Line)

On a fresh **Debian/Ubuntu** server, run:

```bash
curl -Ls https://raw.githubusercontent.com/zanros-s/v2rayscan/main/remote-install.sh | sudo bash
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
- Auto-parsing:
  - host, port, uuid
  - network (tcp/ws/grpc)
  - TLS, SNI
  - Params → JSON
- Shows:
  - latest latency
  - UP/DOWN status

### 🔎 Health Monitoring System
- Background checker loop
- Configurable `check_interval_seconds`
- Real proxy testing using **Xray core**
- Stores history in SQLite (`checks` table)

### 📈 Charts & History
- Per-server history endpoint:  
  `GET /api/checks/{server_id}?minutes=N`
- Real-time chart updates with Chart.js
- Latency + status graph

### 🔥 Real-Time Monitor (WebSocket)
- WebSocket:
  `/api/monitor/ws`
- Live testing of a single link
- Instant latency & error stream

### 📬 Telegram Notifications
- When server goes **DOWN**
- Optional recovery notification (UP)
- Configurable:
  - bot token
  - chat ID
  - proxy mode
  - SOCKS or via Xray
  - down_fail_threshold

### 🌍 Multi-language UI
- EN / FA switch
- All translations in `frontend/js/i18n.js`

---

# 📁 Project Structure

```text
.
├─ backend/
│  ├─ app/
│  │  ├─ api/               # FastAPI routers
│  │  ├─ services/          # checker, xray_helper, parser, telegram_bot
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
│  └─ js/main.js
│      charts.js
│      i18n.js
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
  - checker loop
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
- Bind socks inbound on random port
- Perform real HTTP request to `XRAY_TEST_URL`
- Measure latency
- Cleanup process

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

| Key | Description |
|------|-------------|
| `DB_URL` | SQLite database path |
| `XRAY_PATH` | Path to xray binary |
| `XRAY_TEST_URL` | URL used for testing |
| `XRAY_STARTUP_DELAY` | Delay after starting xray |
| `XRAY_REQUEST_TIMEOUT` | Timeout for checks |
| `XRAY_MONITOR_REQUEST_TIMEOUT` | Timeout for live checks |
| `ADMIN_USERNAME` | Panel user |
| `ADMIN_PASSWORD` | Panel pass |
| `SECRET_KEY` | Session signing secret |

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

---

# 🔐 Security

- Never commit `.env`
- Use strong credentials
- Prefer HTTPS with Nginx/Caddy
- Consider firewall restrictions

---

# 🇮🇷 راهنمای فارسی

**نصب سریع:**

```bash
curl -Ls https://raw.githubusercontent.com/zanros-s/v2rayscan/main/remote-install.sh | sudo bash
```

بعد از نصب:

- آدرس پنل: `http://IP:8000/`
- یوزرنیم و پسورد داخل `.env` و خروجی نصب نمایش داده می‌شود.

پنل قابلیت:
- مانیتورینگ VMESS/VLESS  
- نمودار پینگ  
- مانیتور لحظه‌ای  
- گروه‌بندی  
- نوتیفیکیشن تلگرام  
- زبان فارسی/انگلیسی  
را دارد.

Pull Requests are welcome!
