PKG_NAME="hyprwayland-scanner"
PKG_VERSION="0.4.6"
PKG_LICENSE="BSD-3-Clause"
PKG_SITE="https://github.com/hyprwm/hyprwayland-scanner"
PKG_URL="https://github.com/hyprwm/hyprwayland-scanner/archive/v${PKG_VERSION}.tar.gz"
PKG_DEPENDS_HOST="toolchain:host pugixml:host libfmt:host"
PKG_DEPENDS_TARGET="toolchain pugixml"
PKG_LONGDESC="A Hyprland implementation of wayland-scanner, in and for C++."

post_unpack() {
  sed -i '1i #include <fmt/format.h>' "${PKG_BUILD}/src/main.cpp"
  sed -i 's|std::format(|fmt::format(|g' "${PKG_BUILD}/src/main.cpp"
  echo "target_compile_definitions(hyprwayland-scanner PRIVATE FMT_HEADER_ONLY)" >> "${PKG_BUILD}/CMakeLists.txt"
}
