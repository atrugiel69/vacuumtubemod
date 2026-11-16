PKG_NAME="librsvg"
PKG_VERSION="2.63.4"
PKG_LICENSE="LGPL-2.1-or-later"
PKG_SITE="https://wiki.gnome.org/Projects/LibRsvg"
PKG_URL="https://download.gnome.org/sources/librsvg/2.63/librsvg-${PKG_VERSION}.tar.xz"
PKG_DEPENDS_TARGET="toolchain cargo:host cargo-c:host cairo pango gdk-pixbuf libxml2"
PKG_DEPENDS_CONFIG="pango"
PKG_LONGDESC="SVG rendering library."
PKG_BUILD_FLAGS="+pic"
PKG_MESON_OPTS_TARGET="-Dtriplet=${TARGET_NAME} \
                       -Dintrospection=disabled \
                       -Dpixbuf=enabled \
                       -Dpixbuf-loader=disabled \
                       -Drsvg-convert=disabled \
                       -Ddocs=disabled \
                       -Dvala=disabled \
                       -Davif=disabled \
                       -Dtests=false"

pre_configure_target() {
  if [ -f "${TOOLCHAIN}/share/pkgconfig/shared-mime-info.pc" ]; then
    mkdir -p "${SYSROOT_PREFIX}/usr/lib/pkgconfig"
    cp -f "${TOOLCHAIN}/share/pkgconfig/shared-mime-info.pc" "${SYSROOT_PREFIX}/usr/lib/pkgconfig/"
  fi
}
