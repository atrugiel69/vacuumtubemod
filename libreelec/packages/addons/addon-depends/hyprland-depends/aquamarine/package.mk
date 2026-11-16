PKG_NAME="aquamarine"
PKG_VERSION="0.16.0"
PKG_LICENSE="BSD-3-Clause"
PKG_SITE="https://github.com/hyprwm/aquamarine"
PKG_URL="https://github.com/hyprwm/aquamarine/archive/v${PKG_VERSION}.tar.gz"
PKG_DEPENDS_TARGET="toolchain hyprutils hyprwayland-scanner:host wayland wayland-protocols seatd libinput pixman libdrm mesa systemd libdisplay-info hwdata:host"
PKG_LONGDESC="Aquamarine is a very light linux rendering backend library."
PKG_BUILD_FLAGS="+pic"
PKG_CMAKE_OPTS_TARGET="-Dhyprwayland-scanner_DIR=${TOOLCHAIN}/lib/cmake/hyprwayland-scanner"

pre_configure_target() {
  mkdir -p "${SYSROOT_PREFIX}/usr/lib/pkgconfig" "${SYSROOT_PREFIX}/usr/share"
  for pkg in seatd wayland wayland-protocols hyprutils; do
    local pdir="$(get_install_dir ${pkg})"
    [ -d "${pdir}/usr" ] && cp -af "${pdir}/usr/"* "${SYSROOT_PREFIX}/usr/" 2>/dev/null || true
  done
  cp -f "${TOOLCHAIN}/lib/pkgconfig/wayland-scanner.pc" "${SYSROOT_PREFIX}/usr/lib/pkgconfig/" 2>/dev/null || true
  sed -i 's|pkgdatadir=.*|pkgdatadir=/usr/share/wayland|' "${SYSROOT_PREFIX}/usr/lib/pkgconfig/wayland-scanner.pc" 2>/dev/null || true
  cp -af "${TOOLCHAIN}/share/wayland" "${SYSROOT_PREFIX}/usr/share/" 2>/dev/null || true
  cp -f "${TOOLCHAIN}/share/pkgconfig/hwdata.pc" "${SYSROOT_PREFIX}/usr/lib/pkgconfig/" 2>/dev/null || true
  sed -i 's|pkgdatadir=.*|pkgdatadir=/usr/share/hwdata|' "${SYSROOT_PREFIX}/usr/lib/pkgconfig/hwdata.pc" 2>/dev/null || true
  cp -af "${TOOLCHAIN}/share/hwdata" "${SYSROOT_PREFIX}/usr/share/" 2>/dev/null || true
  cp -f "${SYSROOT_PREFIX}/usr/share/pkgconfig/"*.pc "${SYSROOT_PREFIX}/usr/lib/pkgconfig/" 2>/dev/null || true
}
