#!/bin/sh
# SPDX-License-Identifier: GPL-2.0-or-later
set -e

if [ -z "$1" ]; then
  echo "Usage: $0 /path/to/LibreELEC.tv" >&2
  exit 1
fi

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
LE_DIR=$(CDPATH= cd -- "$1" && pwd)

cp -rf "${SCRIPT_DIR}/packages/addons/"* "${LE_DIR}/packages/addons/"
cd "${LE_DIR}"
PROJECT=Generic ARCH=x86_64 scripts/create_addon hyprland
PROJECT=Generic ARCH=x86_64 scripts/create_addon flatpak.vacuumtubemod
