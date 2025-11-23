#!/usr/bin/env bash
set -e

#############################################
#  v2rayscan auto installer                 #
#  - Installs system dependencies           #
#  - Installs Xray core                     #
#  - Sets up Python venv and requirements   #
#  - Generates random admin credentials     #
#  - Creates and starts systemd service     #
#############################################

APP_NAME="v2rayscan"
APP_PORT=8000
SERVICE_NAME="v2rayscan.service"
INSTALL_DIR="/opt/v2rayscan"

# Detect repository directory (where this script lives)
REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

BACKEND_SUBDIR="backend"
BACKEND_DIR="${INSTALL_DIR}/${BACKEND_SUBDIR}"
ENV_FILE="${BACKEND_DIR}/.env"
VENV_DIR="${BACKEND_DIR}/venv"

if [ "$EUID" -ne 0 ]; then
    echo "Please run this script as root, for example:"
    echo "  sudo ./install.sh"
    exit 1
fi

if ! command -v apt >/dev/null 2>&1; then
    echo "This installer currently supports Debian/Ubuntu (apt-based) systems only."
    exit 1
fi

if [ -n "$SUDO_USER" ] && [ "$SUDO_USER" != "root" ]; then
    RUN_USER="$SUDO_USER"
else
    RUN_USER="root"
fi
RUN_GROUP="$(id -gn "$RUN_USER")"

echo "============================================="
echo " Installing ${APP_NAME}"
echo " Repository dir : ${REPO_DIR}"
echo " Install dir    : ${INSTALL_DIR}"
echo " Backend dir    : ${BACKEND_DIR}"
echo " Service user   : ${RUN_USER}:${RUN_GROUP}"
echo "============================================="
echo

#############################################
# 1) Install system dependencies
#############################################
echo "[1/6] Updating apt and installing packages..."
apt update -y
apt install -y python3 python3-venv python3-pip sqlite3 curl

#############################################
# 2) Install Xray core
#############################################
echo "[2/6] Installing Xray core..."
bash -c "$(curl -L https://github.com/XTLS/Xray-install/raw/main/install-release.sh)" @ install
echo "[2/6] Xray installation finished."
echo

#############################################
# 3) Copy project to /opt/v2rayscan
#############################################
echo "[3/6] Copying project to ${INSTALL_DIR} ..."
mkdir -p "${INSTALL_DIR}"

# If we are already in INSTALL_DIR, no copy is needed
if [ "${REPO_DIR}" != "${INSTALL_DIR}" ]; then
    rsync -a --delete \
        --exclude 'venv' \
        --exclude '__pycache__' \
        --exclude '.git' \
        "${REPO_DIR}/" "${INSTALL_DIR}/"
fi

if [ ! -d "${BACKEND_DIR}" ]; then
    echo "ERROR: backend directory not found at ${BACKEND_DIR}"
    echo "Make sure the repository structure is:"
    echo "  backend/"
    echo "  frontend/"
    echo "and that install.sh is in the project root."
    exit 1
fi

#############################################
# 4) Setup Python virtual environment
#############################################
echo "[4/6] Setting up Python virtual environment..."

cd "${BACKEND_DIR}"

if [ ! -d "${VENV_DIR}" ]; then
    python3 -m venv "${VENV_DIR}"
fi

# shellcheck disable=SC1090
source "${VENV_DIR}/bin/activate"

REQ_FILE="${BACKEND_DIR}/requirements.txt"
if [ -f "${REQ_FILE}" ]; then
    echo "[4/6] Installing Python requirements from ${REQ_FILE} ..."
    pip install --upgrade pip
    pip install -r "${REQ_FILE}"
else
    echo "WARNING: requirements.txt not found at ${REQ_FILE}, skipping Python dependencies installation."
fi

deactivate
cd "${REPO_DIR}"
echo

#############################################
# 5) Generate random admin credentials
#############################################
echo "[5/6] Generating random admin credentials..."

# Random username: admin_xxxxxx
ADMIN_USERNAME="admin_$(tr -dc 'a-z0-9' </dev/urandom | head -c 6)"

# Random password: 24 chars
ADMIN_PASSWORD="$(tr -dc 'A-Za-z0-9' </dev/urandom | head -c 24)"

# Random secret key: 48 chars
SECRET_KEY="$(tr -dc 'A-Za-z0-9' </dev/urandom | head -c 48)"

export ADMIN_USERNAME ADMIN_PASSWORD SECRET_KEY

mkdir -p "$(dirname "${ENV_FILE}")"

if [ ! -f "${ENV_FILE}" ]; then
    echo "Creating new .env file at ${ENV_FILE} ..."
    cat > "${ENV_FILE}" <<EOF
DB_URL=sqlite:///data.db
XRAY_PATH=/usr/local/bin/xray
XRAY_TEST_URL=https://speed.cloudflare.com
XRAY_STARTUP_DELAY=0.8
XRAY_REQUEST_TIMEOUT=8.0
XRAY_MONITOR_REQUEST_TIMEOUT=0.5
EOF
fi

# Use Python to update or append admin credentials and secret key, preserving other lines
python3 <<PY
import os
from pathlib import Path

env_path = Path("${ENV_FILE}")

admin_username = os.environ.get("ADMIN_USERNAME")
admin_password = os.environ.get("ADMIN_PASSWORD")
secret_key = os.environ.get("SECRET_KEY")

if not env_path.exists():
    raise SystemExit(f".env file not found at {env_path}")

lines = env_path.read_text().splitlines()
keys = {
    "ADMIN_USERNAME": admin_username,
    "ADMIN_PASSWORD": admin_password,
    "SECRET_KEY": secret_key,
}

output = []
seen = set()

for line in lines:
    stripped = line.lstrip()
    if not stripped or stripped.startswith("#") or "=" not in stripped:
        output.append(line)
        continue

    key, _, _ = stripped.partition("=")
    key = key.strip()
    if key in keys:
        output.append(f"{key}={keys[key]}")
        seen.add(key)
    else:
        output.append(line)

for key, value in keys.items():
    if key not in seen:
        output.append(f"{key}={value}")

env_path.write_text("\n".join(output) + "\n")
PY

echo "[5/6] Admin credentials written to ${ENV_FILE}"
echo

#############################################
# 6) Create and start systemd service
#############################################
echo "[6/6] Creating systemd service ${SERVICE_NAME} ..."

SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}"

cat > "${SERVICE_FILE}" <<EOF
[Unit]
Description=v2rayscan FastAPI service
After=network.target

[Service]
User=${RUN_USER}
Group=${RUN_GROUP}
WorkingDirectory=${BACKEND_DIR}
ExecStart=${VENV_DIR}/bin/python3 -m uvicorn app.main:app --host 0.0.0.0 --port ${APP_PORT}
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable "${SERVICE_NAME}"
systemctl restart "${SERVICE_NAME}"

sleep 2
SERVICE_STATUS="$(systemctl is-active "${SERVICE_NAME}" || true)"

SERVER_IP="$(hostname -I 2>/dev/null | awk '{print $1}')"
if [ -z "${SERVER_IP}" ]; then
    SERVER_IP="SERVER_IP"
fi

PANEL_URL="http://${SERVER_IP}:${APP_PORT}/"

echo
echo "============================================="
echo " Installation finished."
echo " Service name : ${SERVICE_NAME}"
echo " Service status: ${SERVICE_STATUS}"
echo
echo " Panel URL:"
echo "   ${PANEL_URL}"
echo
echo " Admin credentials:"
echo "   Username: ${ADMIN_USERNAME}"
echo "   Password: ${ADMIN_PASSWORD}"
echo
echo " .env file:"
echo "   ${ENV_FILE}"
echo "============================================="
echo "You can check logs with:"
echo "  sudo journalctl -u ${SERVICE_NAME} -f"
echo
