PKG_NAME="cargo-c"
PKG_VERSION="0.10.26"
PKG_LICENSE="MIT"
PKG_SITE="https://github.com/lu-zero/cargo-c"
PKG_URL="https://github.com/lu-zero/cargo-c/archive/v${PKG_VERSION}/${PKG_NAME}-${PKG_VERSION}.tar.gz"
PKG_DEPENDS_HOST="cargo:host openssl:host"
PKG_LONGDESC="Cargo C-ABI helpers."
PKG_TOOLCHAIN="manual"

pre_configure_host() {
  curl -fsSL "https://github.com/lu-zero/cargo-c/releases/download/v${PKG_VERSION}/Cargo.lock" -o "${PKG_BUILD}/Cargo.lock"
}

make_host() {
  cd "${PKG_BUILD}"
  export OPENSSL_NO_VENDOR=1
  cargo build --target ${RUST_HOST} --release --locked
}

makeinstall_host() {
  mkdir -p "${TOOLCHAIN}/bin"
  cp -a "${PKG_BUILD}/.${RUST_HOST}/target/${RUST_HOST}/release/"cargo-c{api,build,install,test} "${TOOLCHAIN}/bin/"
}
