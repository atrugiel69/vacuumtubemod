# VacuumTube Mod for LibreELEC (Dynamic HDR10 + Refresh Rate Matching + 5.1 E-AC-3)

Standalone Kodi add-ons and runtime patches for running [Vacuum Tube](https://github.com/shy1132/VacuumTube) on **LibreELEC 13 (`Generic.x86_64`)** with:

- **Per-video Dynamic SDR <-> HDR10 switching** via a self-contained **Hyprland 0.57.2** Wayland compositor add-on (`tools.hyprland`) and real-time stream detection (`hdr_state` + `hdr-watcher.py`), keeping menus and SDR videos in SDR while switching the display to HDR10 only during PQ/HLG HDR playback, and honoring Kodi's `videoscreen.maxbpc` setting.
- **Automatic Display Refresh Rate Matching** (`23.976`–`120 Hz` with NTSC fractional pairing, configurable pre-playback hold delay, and YouTube Shorts skip option) parsed directly from stream container headers and player metadata. 1.2.0 release brings added logic to minimize refresh rate switching, leveraging clean multiples (i.e., 120Hz working fine for 60fps, 30fps, and 24fps content).
- **5.1 Surround Sound (Dolby Digital Plus / E-AC-3 & AC-3)** via a custom **Electron 44.5.1** (`libffmpeg.so`) runtime and a 6-channel PulseAudio ALSA sink.
- **Zero-conflict isolation**: Does not modify LibreELEC's `tools.externalhelper` add-on or Flathub's official `rocks.shy.VacuumTube` installation.

## Quick Installation (Pre-built Releases)

> Provided "as is", with no guarantee of support.

1. **Install official prerequisites in Kodi**:
   - Install **Flatpak** (`tools.flatpak`) and **External programs helper** (`tools.externalhelper`) from the official LibreELEC Add-on repository.
2. **Download the two add-on `.zip` files** from the [latest Release](https://github.com/atrugiel69/vacuumtubemod/releases/latest):
   - `tools.hyprland-1.1.1.zip`
   - `flatpak.vacuumtubemod-1.2.0.zip`
3. **Install both `.zip` files in Kodi**:
   - Go to **Add-ons -> Install from zip file** and install `tools.hyprland-1.1.1.zip` first, then `flatpak.vacuumtubemod-1.2.0.zip`.
4. **First Launch**:
   - Open **VacuumTube Mod** from Kodi Program Add-ons.
   - On first run, it prompts to install `org.freedesktop.Platform` (if not already present) and automatically downloads `vacuumtube-mod-runtime-x86_64.tar.gz` from the latest GitHub Release into `/storage/.kodi/userdata/addon_data/flatpak.vacuumtubemod/runtime/` (or extracts `/storage/vacuumtube-mod-runtime-x86_64.tar.gz` if placed there manually).
5. **Configure Display Options**:
   - Inside VacuumTube's settings overlay, turn **Wayland HDR** ON and adjust **Match display refresh rate**, **Refresh rate switch delay**, and **Skip refresh rate switch for Shorts** as desired.

## Building from Source

### 1. LibreELEC Add-ons (`tools.hyprland` & `flatpak.vacuumtubemod`)

    git clone --depth 1 https://github.com/LibreELEC/LibreELEC.tv.git
    ./libreelec/build-addons.sh ./LibreELEC.tv

Generated `.zip` packages appear under `LibreELEC.tv/target/addons/*/Generic/x86_64/`.

### 2. Custom Electron 44.5.1 + E-AC-3 Runtime & Modded `app.asar`

1. **Electron + FFmpeg (E-AC-3/AC-3)**:
   - Set up an Electron `v44.5.1` Linux `x64` build tree.
   - Apply `vacuumtube/patches/chromium-eac3.patch` in `src/` and `vacuumtube/patches/ffmpeg-eac3.patch` in `src/third_party/ffmpeg/`.
   - Copy `vacuumtube/build/args.gn` to `src/out/Release/args.gn` and build `ninja -C out/Release electron`.
2. **VacuumTube JS (`app.asar` with Dynamic HDR & Refresh Rate Matching)**:
   - Clone `https://github.com/shy1132/VacuumTube.git` (`v2.1.0`), apply `vacuumtube/patches/vacuumtube-dynamic-hdr.patch` and `vacuumtube/patches/vacuumtube-refresh-rate.patch` via `git am`, and run `npm install && npx electron-builder --linux --dir -c.electronVersion=44.5.1`.
   - Replace `dist/linux-unpacked/vacuumtube` and `dist/linux-unpacked/libffmpeg.so` with your custom Electron `v44.5.1` binaries and archive `dist/linux-unpacked/` into `vacuumtube-mod-runtime-x86_64.tar.gz`.

## Credits & License

- **Vacuum Tube**: [shy1132/VacuumTube](https://github.com/shy1132/VacuumTube) (MIT)
- **Hyprland**: [hyprwm/Hyprland](https://github.com/hyprwm/Hyprland) (BSD-3-Clause)
- **LibreELEC**: [Team LibreELEC](https://libreelec.tv) (GPL-2.0-or-later)
- **E-AC-3 Patches**: Adapted from [Alex313031/thorium](https://github.com/Alex313031/thorium)

Packaging scripts and integration code in this repository are licensed under **GPL-2.0-or-later** (see [LICENSE](LICENSE)).
