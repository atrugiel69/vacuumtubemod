# SPDX-License-Identifier: GPL-2.0-or-later
# Copyright (C) 2026-present Team LibreELEC (https://libreelec.tv)

PKG_NAME="hyprland"
PKG_VERSION="0.57.2"
PKG_REV="3"
PKG_LICENSE="BSD-3-Clause"
PKG_SITE="https://hypr.land"
PKG_URL=""
PKG_MAINTAINER="atrugiel"
PKG_DEPENDS_TARGET="toolchain seatd Hyprland"
PKG_SECTION="tools"
PKG_SHORTDESC="Hyprland Wayland compositor"
PKG_LONGDESC="Hyprland dynamic tiling Wayland compositor addon for running standalone Wayland applications."
PKG_TOOLCHAIN="manual"

PKG_IS_ADDON="yes"
PKG_ADDON_NAME="Hyprland Compositor"
PKG_ADDON_ICON_NAME="HYPRLAND"
PKG_ADDON_ICON_SIZE="250"
PKG_ADDON_PROJECTS="any !Generic-legacy"
PKG_ADDON_VERSION="1.1.0"

addon() {
  mkdir -p "${ADDON_BUILD}/${PKG_ADDON_ID}/bin"
  cp -P $(get_install_dir seatd)/usr/bin/{seatd,seatd-launch} "${ADDON_BUILD}/${PKG_ADDON_ID}/bin/"
  cp -P $(get_install_dir Hyprland)/usr/bin/{Hyprland,hyprctl} "${ADDON_BUILD}/${PKG_ADDON_ID}/bin/"
  [ -e "$(get_install_dir Hyprland)/usr/bin/start-hyprland" ] && cp -P $(get_install_dir Hyprland)/usr/bin/start-hyprland "${ADDON_BUILD}/${PKG_ADDON_ID}/bin/"

  mkdir -p "${ADDON_BUILD}/${PKG_ADDON_ID}/lib.private"
  for pkg in libtool aquamarine hyprwire hyprutils hyprlang hyprgraphics hyprcursor librsvg seatd wayland libXcursor libdisplay-info tomlplusplus; do
    if [ -d "$(get_install_dir ${pkg})/usr/lib" ]; then
      cp -d $(get_install_dir ${pkg})/usr/lib/*.so* "${ADDON_BUILD}/${PKG_ADDON_ID}/lib.private/" 2>/dev/null || true
    fi
  done

  cp -d "${SYSROOT_PREFIX}/usr/lib/"{libpango,libgdk_pixbuf,libglslang}*.so* "${ADDON_BUILD}/${PKG_ADDON_ID}/lib.private/" 2>/dev/null || true

  for f in "${ADDON_BUILD}/${PKG_ADDON_ID}/bin/"*; do
    if [ -f "${f}" ] && [ ! -L "${f}" ]; then
      patchelf --add-rpath '${ORIGIN}/../lib.private' "${f}" || true
    fi
  done

  for f in "${ADDON_BUILD}/${PKG_ADDON_ID}/lib.private/"*.so*; do
    if [ -f "${f}" ] && [ ! -L "${f}" ]; then
      patchelf --add-rpath '${ORIGIN}' "${f}" || true
    fi
  done
}
