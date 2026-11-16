PKG_NAME="hyprcursor"
PKG_VERSION="0.1.14"
PKG_LICENSE="BSD-3-Clause"
PKG_SITE="https://github.com/hyprwm/hyprcursor"
PKG_URL="https://github.com/hyprwm/hyprcursor/archive/v${PKG_VERSION}.tar.gz"
PKG_DEPENDS_TARGET="toolchain hyprlang cairo librsvg libzip tomlplusplus bzip2 xz zlib"
PKG_DEPENDS_CONFIG="pango"
PKG_LONGDESC="The hyprland cursor format, library and utilities."
PKG_BUILD_FLAGS="+pic"

pre_configure_target() {
  export LDFLAGS="${LDFLAGS} -lbz2 -llzma -lz"
}
