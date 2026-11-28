# SPDX-License-Identifier: GPL-2.0-or-later
# Copyright (C) 2026-present Team LibreELEC (https://libreelec.tv)

PKG_NAME="flatpak.vacuumtubemod"
PKG_VERSION="1.1.1"
PKG_REV="2"
PKG_ARCH="x86_64"
PKG_LICENSE="MIT"
PKG_SITE="https://github.com/atrugiel69/vacuumtubemod"
PKG_MAINTAINER="atrugiel"
PKG_DEPENDS_TARGET="toolchain"
PKG_SHORTDESC="VacuumTube Mod (Dynamic HDR + 5.1 E-AC-3)"
PKG_LONGDESC="Standalone modded VacuumTube client with Dynamic HDR switching and 5.1 E-AC-3 audio support."
PKG_TOOLCHAIN="manual"
PKG_IS_ADDON="yes"
PKG_ADDON_NAME="VacuumTube Mod"
PKG_ADDON_TYPE="xbmc.python.script"
PKG_ADDON_PROJECTS="any !Generic-legacy"
PKG_ADDON_PROVIDES="executable"
PKG_ADDON_VERSION="1.2.1"
PKG_ADDON_REQUIRES="tools.flatpak:0.0.0 tools.hyprland:1.1.1"

addon() {
  :
}
