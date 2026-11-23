#!/usr/bin/env bash
set -Eeuo pipefail

REPO="userrtm/userrtm-anyconnect-panel"
BRANCH="main"

if [[ $EUID -ne 0 ]]; then
  echo "Run as root, then execute: bash <(curl -fsSL https://raw.githubusercontent.com/${REPO}/${BRANCH}/install.sh)"
  exit 1
fi

command -v curl >/dev/null 2>&1 || { echo "curl is required."; exit 1; }
command -v tar >/dev/null 2>&1 || { echo "tar is required."; exit 1; }

TMP_DIR="$(mktemp -d -t ocserv-panel.XXXXXX)"
cleanup() { rm -rf "$TMP_DIR"; }
trap cleanup EXIT

ARCHIVE_URL="https://github.com/${REPO}/archive/refs/heads/${BRANCH}.tar.gz"
echo "Downloading UserrTM AnyConnect panel installer..."
curl -fL --retry 3 --connect-timeout 20 "$ARCHIVE_URL" | tar -xz -C "$TMP_DIR" --strip-components=1

if [[ ! -f "$TMP_DIR/scripts/install-core.sh" ]]; then
  echo "Installer files are missing from the downloaded repository."
  exit 1
fi
bash "$TMP_DIR/scripts/install-core.sh"
