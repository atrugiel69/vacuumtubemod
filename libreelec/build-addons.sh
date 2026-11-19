#!/bin/sh
# SPDX-License-Identifier: GPL-2.0-or-later
set -e

if [ -z "$1" ]; then
  echo "Usage: $0 /path/to/LibreELEC.tv" >&2
  exit 1
fi

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
LE_DIR=$(CDPATH= cd -- "$1" && pwd)

cleanup() {
  rm -rf "${LE_DIR}/packages/addons/tools/hyprland" \
         "${LE_DIR}/packages/addons/flatpak/flatpak.vacuumtubemod"
}
trap cleanup EXIT

rm -rf "${LE_DIR}"/target/addons/*/Generic/x86_64/tools.hyprland/*.zip \
       "${LE_DIR}"/target/addons/*/Generic/x86_64/flatpak.vacuumtubemod/*.zip \
       "${LE_DIR}"/build.LibreELEC-Generic.x86_64-*/.stamps/hyprland \
       "${LE_DIR}"/build.LibreELEC-Generic.x86_64-*/.stamps/flatpak.vacuumtubemod

cp -rf "${SCRIPT_DIR}/packages/addons/"* "${LE_DIR}/packages/addons/"
cd "${LE_DIR}"
PROJECT=Generic ARCH=x86_64 scripts/create_addon hyprland
PROJECT=Generic ARCH=x86_64 scripts/create_addon flatpak.vacuumtubemod
