PKG_NAME="hyprgraphics"
PKG_VERSION="0.6.0"
PKG_LICENSE="BSD-3-Clause"
PKG_SITE="https://github.com/hyprwm/hyprgraphics"
PKG_URL="https://github.com/hyprwm/hyprgraphics/archive/v${PKG_VERSION}.tar.gz"
PKG_DEPENDS_TARGET="toolchain hyprutils pixman cairo pango libdrm libjpeg-turbo libpng libwebp librsvg file zstd xz bzip2"
PKG_DEPENDS_CONFIG="pango"
PKG_LONGDESC="Hyprland graphics / resource utilities."
PKG_BUILD_FLAGS="+pic"

pre_configure_target() {
  local file_dir="$(get_install_dir file)"
  if [ -f "${file_dir}/usr/lib/pkgconfig/libmagic.pc" ]; then
    mkdir -p "${SYSROOT_PREFIX}/usr/lib/pkgconfig" "${SYSROOT_PREFIX}/usr/include"
    cp -f "${file_dir}/usr/lib/pkgconfig/libmagic.pc" "${SYSROOT_PREFIX}/usr/lib/pkgconfig/"
    cp -f "${file_dir}/usr/lib/libmagic.a" "${SYSROOT_PREFIX}/usr/lib/"
    cp -f "${file_dir}/usr/include/magic.h" "${SYSROOT_PREFIX}/usr/include/"
  fi
  local pango_dir="$(get_install_dir pango)"
  if [ -d "${pango_dir}/usr/lib" ]; then
    export LDFLAGS="${LDFLAGS} -L${pango_dir}/usr/lib -Wl,-rpath-link,${pango_dir}/usr/lib -lzstd -llzma -lbz2"
  else
    export LDFLAGS="${LDFLAGS} -lzstd -llzma -lbz2"
  fi
}
