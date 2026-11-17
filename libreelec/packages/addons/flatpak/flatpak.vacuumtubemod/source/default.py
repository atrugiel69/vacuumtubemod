# SPDX-License-Identifier: GPL-2.0-or-later
# Copyright (C) 2026-present Team LibreELEC (https://libreelec.tv)

import os
import shutil
import subprocess
import tarfile
import tempfile
import urllib.request

import externalhelper.utils as eh
import xbmc
import xbmcaddon
import xbmcgui
import xbmcvfs

ADDON = xbmcaddon.Addon()
ADDON_ID = ADDON.getAddonInfo('id')
ADDON_NAME = ADDON.getAddonInfo('name')
ADDON_PATH = ADDON.getAddonInfo('path')

FLATPAK_ADDON = xbmcaddon.Addon('tools.flatpak')
FLATPAK_PATH = FLATPAK_ADDON.getAddonInfo('path')
FLATPAK_EXE = os.path.join(FLATPAK_PATH, 'bin', 'flatpak')

DATA_DIR = xbmcvfs.translatePath(ADDON.getAddonInfo('profile'))
RUNTIME_DIR = os.path.join(DATA_DIR, 'runtime')
USER_DATA_DIR = os.path.join(DATA_DIR, 'userData')
BINARY_PATH = os.path.join(RUNTIME_DIR, 'vacuumtube')
SESSION_SCRIPT = os.path.join(ADDON_PATH, 'bin', 'start-vtmod-session')

APP_ID = 'rocks.shy.VacuumTubeMod'
FLATHUB_URL = 'https://dl.flathub.org/repo/flathub.flatpakrepo'


def log(msg: str, level: int = xbmc.LOGINFO) -> None:
    xbmc.log(f'[{ADDON_ID}] {msg}', level)


def notify_error(msg: str) -> None:
    xbmcgui.Dialog().notification(ADDON_NAME, msg, xbmcgui.NOTIFICATION_ERROR, 6000)


def run_flatpak(args: list[str], dbus: bool = False) -> subprocess.CompletedProcess:
    cmd = (['dbus-run-session', '--'] if dbus else []) + [FLATPAK_EXE, *args]
    return subprocess.run(cmd, capture_output=True, text=True)


def install_runtime() -> bool:
    os.makedirs(DATA_DIR, exist_ok=True)
    settings = ADDON.getSettings()
    local_path = settings.getString('local_archive').strip()
    release_url = settings.getString('release_url').strip()

    candidates = [
        p
        for p in (
            local_path,
            '/storage/vacuumtube-mod-runtime-x86_64.tar.gz',
            '/tmp/vacuumtube-mod-runtime-x86_64.tar.gz',
        )
        if p and os.path.isfile(p)
    ]
    archive_path = candidates[0] if candidates else None
    temp_archive = None

    progress = xbmcgui.DialogProgress()
    progress.create(ADDON_NAME, 'Preparing VacuumTube Mod runtime...')
    try:
        if archive_path is None:
            if not release_url:
                notify_error('Runtime release URL is empty and no local archive found.')
                return False
            fd, temp_archive = tempfile.mkstemp(prefix='vtmod-', suffix='.tar.gz', dir=DATA_DIR)
            os.close(fd)
            archive_path = temp_archive

            progress.update(5, f'Downloading runtime from GitHub...\n{release_url}')
            req = urllib.request.Request(
                release_url,
                headers={'User-Agent': 'LibreELEC-VacuumTubeMod/1.0'},
            )
            with urllib.request.urlopen(req, timeout=60) as resp, open(archive_path, 'wb') as out:
                total = int(resp.headers.get('Content-Length') or 0)
                downloaded = 0
                while True:
                    if progress.iscanceled():
                        return False
                    chunk = resp.read(262144)
                    if not chunk:
                        break
                    out.write(chunk)
                    downloaded += len(chunk)
                    if total > 0:
                        pct = min(75, int((downloaded / total) * 75))
                        mb_done = downloaded / (1024 * 1024)
                        mb_tot = total / (1024 * 1024)
                        progress.update(
                            pct,
                            f'Downloading runtime ({mb_done:.1f} / {mb_tot:.1f} MB)...',
                        )

        progress.update(80, 'Extracting runtime archive...')
        staging_dir = tempfile.mkdtemp(prefix='runtime-stage-', dir=DATA_DIR)
        try:
            with tarfile.open(archive_path, 'r:gz') as tf:
                if hasattr(tarfile, 'data_filter'):
                    tf.extractall(staging_dir, filter='data')
                else:
                    tf.extractall(staging_dir)

            if not os.path.isfile(os.path.join(staging_dir, 'vacuumtube')):
                notify_error('Invalid runtime archive: missing vacuumtube executable.')
                return False

            os.chmod(os.path.join(staging_dir, 'vacuumtube'), 0o755)
            staged_ffmpeg = os.path.join(staging_dir, 'libffmpeg.so')
            if os.path.isfile(staged_ffmpeg):
                os.chmod(staged_ffmpeg, 0o755)

            if os.path.isdir(RUNTIME_DIR):
                shutil.rmtree(RUNTIME_DIR)
            os.replace(staging_dir, RUNTIME_DIR)
        finally:
            if os.path.isdir(staging_dir):
                shutil.rmtree(staging_dir, ignore_errors=True)

        settings.setBool('force_reinstall', False)
        progress.update(100, 'Runtime installed.')
        return True
    except Exception as exc:
        log(f'Runtime setup failed: {exc}', xbmc.LOGERROR)
        notify_error(f'Runtime setup failed: {exc}')
        return False
    finally:
        progress.close()
        if temp_archive and os.path.isfile(temp_archive):
            os.remove(temp_archive)


def detect_freedesktop_branch() -> str | None:
    res = run_flatpak(['list', '--system', '--runtime', '--columns=application,branch'])
    if res.returncode != 0:
        return None
    branches = []
    for line in res.stdout.strip().splitlines():
        parts = line.split('\t')
        if len(parts) >= 2 and parts[0].strip() == 'org.freedesktop.Platform':
            branches.append(parts[1].strip())
    return sorted(branches)[-1] if branches else None


def ensure_flatpak_app() -> bool:
    branch = detect_freedesktop_branch()
    if branch is None:
        ok = xbmcgui.Dialog().yesno(
            ADDON_NAME,
            'Flatpak runtime org.freedesktop.Platform is required.\nDownload and install it now?',
        )
        if not ok:
            return False
        progress = xbmcgui.DialogProgress()
        progress.create(ADDON_NAME, 'Installing org.freedesktop.Platform runtime...')
        try:
            run_flatpak(['remote-add', '--system', '--if-not-exists', 'flathub', FLATHUB_URL])
            res = run_flatpak(
                [
                    'install',
                    '--system',
                    '--noninteractive',
                    '-y',
                    'flathub',
                    'org.freedesktop.Platform//24.08',
                ],
                dbus=True,
            )
            if res.returncode != 0:
                log(f'Failed to install org.freedesktop.Platform: {res.stderr}', xbmc.LOGERROR)
                notify_error('Failed to install org.freedesktop.Platform.')
                return False
        finally:
            progress.close()
        branch = detect_freedesktop_branch()
        if branch is None:
            return False

    info = run_flatpak(['info', '--system', APP_ID])
    if info.returncode == 0:
        return True

    tmpdir = tempfile.mkdtemp(prefix='vtmod-fp-')
    try:
        app_dir = os.path.join(tmpdir, 'app')
        repo_dir = os.path.join(tmpdir, 'repo')
        os.makedirs(os.path.join(app_dir, 'files'), exist_ok=True)
        os.makedirs(os.path.join(app_dir, 'export'), exist_ok=True)
        with open(os.path.join(app_dir, 'metadata'), 'w') as mf:
            mf.write(
                f'[Application]\n'
                f'name={APP_ID}\n'
                f'runtime=org.freedesktop.Platform/x86_64/{branch}\n'
                f'command={BINARY_PATH}\n\n'
                f'[Context]\n'
                f'shared=network;ipc;\n'
                f'sockets=wayland;pulseaudio;\n'
                f'devices=dri;\n'
                f'filesystems={DATA_DIR};\n'
            )
        exp = run_flatpak(['build-export', repo_dir, app_dir])
        if exp.returncode != 0:
            log(f'build-export failed: {exp.stderr}', xbmc.LOGERROR)
            notify_error('Failed to register Flatpak app wrapper.')
            return False
        rem = run_flatpak(
            ['remote-add', '--system', '--if-not-exists', '--no-gpg-verify', 'vtmod-local', repo_dir]
        )
        if rem.returncode != 0:
            log(f'local flatpak remote-add failed: {rem.stderr}', xbmc.LOGERROR)
            notify_error('Failed to register Flatpak app repository.')
            return False
        try:
            inst = run_flatpak(
                ['install', '--system', '--noninteractive', '-y', 'vtmod-local', APP_ID],
                dbus=True,
            )
            if inst.returncode != 0:
                log(f'local flatpak install failed: {inst.stderr}', xbmc.LOGERROR)
                notify_error('Failed to install Flatpak app wrapper.')
                return False
        finally:
            run_flatpak(['remote-delete', '--system', '--force', 'vtmod-local'])
        return True
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


def main() -> None:
    os.makedirs(USER_DATA_DIR, exist_ok=True)
    force = ADDON.getSettings().getBool('force_reinstall')
    if force or not os.path.isfile(BINARY_PATH):
        if not install_runtime():
            return
    if not ensure_flatpak_app():
        return

    run_env = {
        'VTMOD_DATA_DIR': DATA_DIR,
        'VTMOD_USER_DATA_DIR': USER_DATA_DIR,
        'VTMOD_APP_ID': APP_ID,
    }
    eh.run_external_program(
        executable=SESSION_SCRIPT,
        env=run_env,
        name=ADDON_NAME,
        wayland=False,
    )


if __name__ == '__main__':
    main()
