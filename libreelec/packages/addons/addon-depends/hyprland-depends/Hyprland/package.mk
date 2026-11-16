PKG_NAME="Hyprland"
PKG_VERSION="0.57.2"
PKG_LICENSE="BSD-3-Clause"
PKG_SITE="https://hypr.land"
PKG_URL="https://github.com/hyprwm/Hyprland/archive/v${PKG_VERSION}.tar.gz"
PKG_DEPENDS_TARGET="toolchain hyprwayland-scanner:host hyprwire:host hyprwire hyprland-protocols aquamarine hyprlang hyprcursor hyprutils hyprgraphics wayland wayland-protocols libxkbcommon util-linux cairo pango pixman libXcursor libdrm libinput libei mesa glib re2 muparser lcms2 libcanberra libtool lua55 glaze glslang spirv-tools"
PKG_LONGDESC="A dynamic tiling Wayland compositor that doesn't sacrifice on its looks."
PKG_CMAKE_OPTS_TARGET="-Dhyprwayland-scanner_DIR=${TOOLCHAIN}/lib/cmake/hyprwayland-scanner \
                       -DNO_XWAYLAND=ON \
                       -DNO_SYSTEMD=ON \
                       -DNO_HYPRPM=ON \
                       -DTRACY_ENABLE=OFF \
                       -DINSTALL_HYPRLAND_HEADERS=OFF \
                       -DBUILD_TESTING=OFF"

post_unpack() {
  rm -rf "${PKG_BUILD}/subprojects/udis86"
  git clone --depth 1 https://github.com/canihavesomecoffee/udis86.git "${PKG_BUILD}/subprojects/udis86"
}

pre_configure_target() {
  mkdir -p "${SYSROOT_PREFIX}/usr/lib/pkgconfig" "${SYSROOT_PREFIX}/usr/share"
  for pkg in libXcursor libtool hyprwire hyprland-protocols aquamarine hyprlang hyprcursor hyprutils hyprgraphics wayland wayland-protocols seatd libei re2 abseil-cpp muparser libcanberra libtool lua55 glaze glslang spirv-tools pango; do
    local pdir="$(get_install_dir ${pkg})"
    [ -d "${pdir}/usr" ] && cp -af "${pdir}/usr/"* "${SYSROOT_PREFIX}/usr/" 2>/dev/null || true
  done
  cp -f "${TOOLCHAIN}/lib/pkgconfig/wayland-scanner.pc" "${SYSROOT_PREFIX}/usr/lib/pkgconfig/" 2>/dev/null || true
  sed -i "s|pkgdatadir=.*|pkgdatadir=${SYSROOT_PREFIX}/usr/share/wayland|" "${SYSROOT_PREFIX}/usr/lib/pkgconfig/wayland-scanner.pc" 2>/dev/null || true
  cp -af "${TOOLCHAIN}/share/wayland" "${SYSROOT_PREFIX}/usr/share/" 2>/dev/null || true
  cp -f "${TOOLCHAIN}/share/pkgconfig/hwdata.pc" "${SYSROOT_PREFIX}/usr/lib/pkgconfig/" 2>/dev/null || true
  sed -i 's|pkgdatadir=.*|pkgdatadir=/usr/share/hwdata|' "${SYSROOT_PREFIX}/usr/lib/pkgconfig/hwdata.pc" 2>/dev/null || true
  cp -af "${TOOLCHAIN}/share/hwdata" "${SYSROOT_PREFIX}/usr/share/" 2>/dev/null || true
  cp -f "${SYSROOT_PREFIX}/usr/share/pkgconfig/"*.pc "${SYSROOT_PREFIX}/usr/lib/pkgconfig/" 2>/dev/null || true
  export LDFLAGS="${LDFLAGS} -lltdl"
}
