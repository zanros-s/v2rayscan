# v2rayscan

A lightweight web panel to monitor VLESS/VMESS proxy nodes using Xray core.

- Backend: **FastAPI + SQLAlchemy + SQLite**
- Frontend: **HTML/CSS/JavaScript + Chart.js**
- Core: **Xray** (used to actually test proxy links end-to-end)

v2rayscan is designed to run on a small VPS and continuously monitor your proxy nodes, visualize latency and uptime, and send Telegram alerts when something goes down.

---

## ✨ Features

### Web UI with login

- Login page with session-based authentication.
- Credentials are loaded from `backend/.env`:
  - `ADMIN_USERNAME`
  - `ADMIN_PASSWORD`

### Server list

- Add servers by pasting full config links:
  - `vless://...`
  - `vmess://...`
- The backend parses:
  - type (VLESS / VMESS)
  - host, port
  - UUID / ID
  - security (TLS)
  - SNI
  - network (tcp, ws, grpc, etc.)
  - extra parameters (stored as JSON)
- Each row shows:
  - last status (`UP` / `DOWN`)
  - last latency
  - group name (optional)

### Grouping and tags

- Create named groups (with optional color) to organize servers.
- Assign servers to groups for easier filtering.
- Sort order per group (e.g. important servers on top).

### Scheduled health checks

- Background checker loop runs every `check_interval_seconds` (configurable in Settings).
- Results are stored in the `checks` table (SQLite).
- Xray is used as a real core:
  - For each server, a temporary Xray config is created.
  - Xray is started, a test HTTP request is made to `XRAY_TEST_URL`.
  - Result (success/failure + latency) is recorded.

### Charts & history

- Per-server history endpoint:  
  `GET /api/checks/{server_id}?minutes=<N>`
- Chart.js line charts:
  - Latency over time
  - Status (UP/DOWN) over time
- Time range (in minutes) selectable from UI.

### Real-time monitoring (WebSocket)

- WebSocket endpoint: `/api/monitor/ws`
- The browser can:
  - Send a single config link and interval.
  - Receive streamed results:
    - `ok` / `error`
    - latency
    - error message if any.
- Ideal for debugging a single node in real time.

### Telegram notifications

- Sends notification when a server goes `DOWN`.
- Optional notification when it comes back `UP` (recovery).
- Configurable via Settings page:
  - Bot token
  - Chat ID
  - Check interval
  - `down_fail_threshold` (number of consecutive failures before DOWN alert)
- Flexible Telegram proxy:
  - Direct
  - Custom SOCKS5
  - Use one of your monitored servers as a proxy via Xray.

### Multi-language UI

- Built-in **English / Persian (FA)** language switch:
  - Language selector in header and login page.
- Translations are stored in `frontend/js/i18n.js`.

---

## 📂 Project structure

```text
.
├─ backend/
│  ├─ app/
│  │  ├─ api/               # FastAPI routers (servers, checks, settings, monitor, groups)
│  │  ├─ services/          # checker, xray_helper, parser, notifier, telegram_bot
│  │  ├─ models.py          # SQLAlchemy models (Server, Check, SettingsModel, ServerGroup)
│  │  ├─ schemas.py         # Pydantic schemas
│  │  ├─ config.py          # Settings + .env loading
│  │  ├─ database.py        # Engine, SessionLocal, Base
│  │  └─ main.py            # FastAPI app, routes, startup tasks
│  ├─ requirements.txt
│  ├─ .env                  # Runtime configuration (NOT committed)
│  └─ .env.example          # Example env for users
│
├─ frontend/
│  ├─ index.html
│  ├─ css/style.css
│  └─ js/
│     ├─ main.js
│     ├─ charts.js
│     └─ i18n.js
│
├─ deploy/
│  └─ v2rayscan.service     # Example systemd unit
│
├─ install.sh               # Local installer (system deps, venv, Xray, systemd)
├─ remote-install.sh        # Remote one-liner installer entrypoint
├─ LICENSE
├─ CONTRIBUTING.md
├─ SECURITY.md
├─ CODE_OF_CONDUCT.md
└─ README.md
