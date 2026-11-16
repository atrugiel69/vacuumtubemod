PKG_NAME="hyprwire"
PKG_VERSION="0.3.1"
PKG_LICENSE="BSD-3-Clause"
PKG_SITE="https://github.com/hyprwm/hyprwire"
PKG_URL="https://github.com/hyprwm/hyprwire/archive/v${PKG_VERSION}.tar.gz"
PKG_DEPENDS_HOST="toolchain:host pugixml:host libfmt:host"
PKG_DEPENDS_TARGET="toolchain hyprutils pugixml libffi libfmt"
PKG_LONGDESC="A fast and consistent wire protocol for IPC."
PKG_BUILD_FLAGS="+pic"

post_unpack() {
  sed -i 's|\${CMAKE_SOURCE_DIR}/include|\${CMAKE_CURRENT_SOURCE_DIR}/../include|g' "${PKG_BUILD}/scanner/CMakeLists.txt"
  sed -i '1i #include <fmt/format.h>' "${PKG_BUILD}/scanner/main.cpp"
  sed -i 's|std::format(|fmt::format(|g' "${PKG_BUILD}/scanner/main.cpp"
  echo "target_compile_definitions(hyprwire-scanner PRIVATE FMT_HEADER_ONLY)" >> "${PKG_BUILD}/scanner/CMakeLists.txt"
}

configure_host() {
  cmake ${CMAKE_GENERATOR_NINJA} ${HOST_CMAKE_OPTS} -DHYPRWIRE_VERSION=${PKG_VERSION} "${PKG_BUILD}/scanner"
}

pre_configure_target() {
  for pkg in hyprutils pugixml libffi; do
    local pdir="$(get_install_dir ${pkg})"
    [ -d "${pdir}/usr" ] && cp -af "${pdir}/usr/"* "${SYSROOT_PREFIX}/usr/" 2>/dev/null || true
  done
}
