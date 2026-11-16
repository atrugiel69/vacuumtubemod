PKG_NAME="lua55"
PKG_VERSION="5.5.1"
PKG_LICENSE="MIT"
PKG_SITE="https://www.lua.org"
PKG_URL="https://www.lua.org/ftp/lua-${PKG_VERSION}.tar.gz"
PKG_DEPENDS_TARGET="toolchain"
PKG_LONGDESC="Lua 5.5 embeddable scripting language."
PKG_BUILD_FLAGS="+pic"

make_target() {
  make CC=${CC} AR="${AR} rcu" MYCFLAGS="-fPIC" posix
}

makeinstall_target() {
  mkdir -p ${SYSROOT_PREFIX}/usr/include/lua$(get_pkg_version_maj_min)
  cp src/lua.h src/lua.hpp src/luaconf.h src/lualib.h src/lauxlib.h ${SYSROOT_PREFIX}/usr/include/lua$(get_pkg_version_maj_min)

  mkdir -p ${SYSROOT_PREFIX}/usr/lib
  cp src/liblua.a ${SYSROOT_PREFIX}/usr/lib/liblua$(get_pkg_version_maj_min).a

  mkdir -p ${SYSROOT_PREFIX}/usr/lib/pkgconfig
  cp ${PKG_DIR}/config/lua55.pc ${SYSROOT_PREFIX}/usr/lib/pkgconfig
  sed -e "s/@@VERSION@@/${PKG_VERSION}/g" \
      -e "s/@@VERSION_MM@@/$(get_pkg_version_maj_min)/g" \
      -i ${SYSROOT_PREFIX}/usr/lib/pkgconfig/lua55.pc
}
