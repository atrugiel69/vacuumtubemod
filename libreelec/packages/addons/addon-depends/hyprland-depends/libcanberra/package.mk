PKG_NAME="libcanberra"
PKG_VERSION="0.30"
PKG_LICENSE="LGPL-2.1-or-later"
PKG_SITE="http://0pointer.de/lennart/projects/libcanberra/"
PKG_URL="http://0pointer.de/lennart/projects/libcanberra/libcanberra-${PKG_VERSION}.tar.xz"
PKG_DEPENDS_TARGET="toolchain alsa-lib libvorbis libtool"
PKG_LONGDESC="Implementation of the XDG Sound Theme and Name Specifications."
PKG_BUILD_FLAGS="+pic -sysroot"
PKG_CONFIGURE_OPTS_TARGET="--enable-static \
                           --disable-shared \
                           --enable-alsa \
                           --enable-null \
                           --disable-pulse \
                           --disable-oss \
                           --disable-gstreamer \
                           --disable-gtk \
                           --disable-gtk3 \
                           --disable-tdb \
                           --disable-udev \
                           --disable-lynx"
