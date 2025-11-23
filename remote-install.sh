#!/usr/bin/env bash
set -e

#############################################
#  v2rayscan remote installer               #
#  - Fetches project from GitHub            #
#  - Runs local install.sh                  #
#############################################

# TODO: set your real GitHub repo URL before publishing
REPO_URL="https://github.com/zanros-s/v2rayscan.git"
INSTALL_DIR="/opt/v2rayscan"

if [ "$EUID" -ne 0 ]; then
    echo "Please run this script as root, for example:"
    echo "  curl -Ls https://raw.githubusercontent.com/zanros-s/v2rayscan/main/remote-install.sh | sudo bash"
    exit 1
fi

if ! command -v git >/dev/null 2>&1; then
    echo "[remote] Installing git..."
    if command -v apt >/dev/null 2>&1; then
        apt update -y
        apt install -y git
    else
        echo "This installer currently supports apt-based systems (Debian/Ubuntu)."
        exit 1
    fi
fi

echo "[remote] Using install directory: ${INSTALL_DIR}"

if [ -d "${INSTALL_DIR}/.git" ]; then
    echo "[remote] Existing repository detected, pulling latest changes..."
    cd "${INSTALL_DIR}"
    git fetch --all
    git reset --hard origin/$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo main)
else
    echo "[remote] Cloning repository..."
    rm -rf "${INSTALL_DIR}"
    git clone "${REPO_URL}" "${INSTALL_DIR}"
    cd "${INSTALL_DIR}"
fi

if [ ! -f "install.sh" ]; then
    echo "ERROR: install.sh not found in ${INSTALL_DIR}"
    exit 1
fi

chmod +x install.sh

echo "[remote] Running local installer..."
./install.sh
