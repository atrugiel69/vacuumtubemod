#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
# Copyright (C) 2026-present Team LibreELEC (https://libreelec.tv)

import glob
import json
import os
import re
import socket
import time

STATE = os.environ.get(
    'VTMOD_HDR_STATE_FILE',
    '/storage/.kodi/userdata/addon_data/flatpak.vacuumtubemod/userData/hdr_state',
)
KODI_GUISETTINGS = os.environ.get(
    'VTMOD_KODI_GUISETTINGS',
    '/storage/.kodi/userdata/guisettings.xml',
)
LOG = '/tmp/vtmod-hdr-watcher.log'

NTSC_PAIRS = {
    23.976: 24.0,
    24.0: 23.976,
    29.97: 30.0,
    30.0: 29.97,
    59.94: 60.0,
    60.0: 59.94,
    119.88: 120.0,
    120.0: 119.88,
}


def get_max_bitdepth() -> int:
    """Honor Kodi's videoscreen.maxbpc setting (0=Auto, 1=8-bit, 2=10-bit, 3=12-bit)."""
    try:
        with open(KODI_GUISETTINGS, encoding='utf-8', errors='replace') as f:
            xml = f.read()
        m = re.search(r'<setting id="videoscreen\.maxbpc"[^>]*>(\d+)</setting>', xml)
        if m and m.group(1) == '1':
            return 8
    except OSError:
        pass
    return 10


def find_sock() -> str | None:
    rt = f'/run/user/{os.getuid()}/hypr'
    socks = glob.glob(f'{rt}/*/.socket.sock') + glob.glob('/tmp/hypr/*/.socket.sock')
    return max(socks, key=os.path.getmtime) if socks else None


def hypr_cmd(sock_path: str, cmd: str) -> str:
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as s:
        s.settimeout(1.0)
        s.connect(sock_path)
        s.sendall(cmd.encode())
        chunks = []
        while True:
            chunk = s.recv(4096)
            if not chunk:
                break
            chunks.append(chunk)
        return b''.join(chunks).decode(errors='replace').strip()


def format_rr(val: float) -> str:
    return f'{val:.2f}'.rstrip('0').rstrip('.')


def parse_state() -> tuple[str, str | None]:
    """Return (cm, fps_token) where fps_token is None (fixed), 'auto', or a numeric string."""
    try:
        with open(STATE) as f:
            raw = f.read().strip()
        if not raw:
            return 'srgb', None
        parts = raw.split()
        cm = 'hdr' if parts[0] == 'hdr' else 'srgb'
        fps_token = parts[1] if len(parts) > 1 else None
        return cm, fps_token
    except OSError:
        return 'srgb', None


def is_compatible_current_rr(cur_rr_val: float, target_fps: float) -> bool:
    """Return True if cur_rr_val is an exact or clean multiple of target_fps."""
    candidates = [target_fps]
    alt = NTSC_PAIRS.get(round(target_fps, 3))
    if alt is not None:
        candidates.append(alt)

    # 120Hz (or 119.88Hz): keep for 120, 60, 30, 24fps (and NTSC equivalents)
    if abs(cur_rr_val - 120.0) <= 0.2:
        return any(
            abs(c - r) <= 0.1 for c in candidates for r in (120.0, 60.0, 30.0, 24.0)
        )
    # 100Hz: keep for 100, 50, 25fps
    if abs(cur_rr_val - 100.0) <= 0.2:
        return any(abs(c - r) <= 0.1 for c in candidates for r in (100.0, 50.0, 25.0))
    # 60Hz (or 59.94Hz): keep for 60, 30fps (and NTSC equivalents)
    if abs(cur_rr_val - 60.0) <= 0.2:
        return any(abs(c - r) <= 0.1 for c in candidates for r in (60.0, 30.0))
    # 50Hz: keep for 50, 25fps
    if abs(cur_rr_val - 50.0) <= 0.2:
        return any(abs(c - r) <= 0.1 for c in candidates for r in (50.0, 25.0))

    return False


def pick_best_mode_rr(
    available_modes: list[str],
    w: int,
    h: int,
    target_fps: float | None,
    fallback_rr: str,
) -> str:
    if target_fps is None:
        return fallback_rr

    prefix = f'{w}x{h}@'
    rates: list[tuple[float, str]] = []
    for entry in available_modes:
        if entry.startswith(prefix):
            m = re.match(r'^(\d+)x(\d+)@([0-9.]+)', entry)
            if m:
                r_str = m.group(3)
                rates.append((float(r_str), r_str))

    if not rates:
        return fallback_rr

    # 1. Exact / near-exact match (e.g. 23.976 -> 23.98, 24 -> 24.00, 59.94 -> 59.94)
    exact = [r for r in rates if abs(r[0] - target_fps) <= 0.05]
    if exact:
        return min(exact, key=lambda r: abs(r[0] - target_fps))[1]

    # 2. NTSC <-> integer pair fallback (e.g. 23.976 <-> 24, 59.94 <-> 60)
    alt = NTSC_PAIRS.get(round(target_fps, 3))
    if alt is not None:
        pair_match = [r for r in rates if abs(r[0] - alt) <= 0.05]
        if pair_match:
            return min(pair_match, key=lambda r: abs(r[0] - alt))[1]

    # 3. Integer multiple fallback (e.g. 25fps -> 50.00Hz, 24fps -> 48/120Hz)
    for mult in (2, 3, 4, 5):
        cand = target_fps * mult
        mult_match = [r for r in rates if abs(r[0] - cand) <= 0.1]
        if mult_match:
            return min(mult_match, key=lambda r: abs(r[0] - cand))[1]

    return fallback_rr


def apply_display_state(
    sock_path: str,
    cm: str,
    fps_token: str | None,
    bitdepth: int,
    default_rr_by_out: dict[str, str],
    last_applied: tuple[str, str, str, int] | None,
    session_state: dict[str, bool],
) -> tuple[str, str, str, int] | None:
    monitors = json.loads(hypr_cmd(sock_path, 'j/monitors'))
    if not monitors:
        return last_applied

    m = next((x for x in monitors if x.get('focused')), monitors[0])
    out = m.get('name', 'HDMI-A-1')
    w, h = int(m.get('width', 3840)), int(m.get('height', 2160))
    cur_rr_val = float(m.get('refreshRate', 60))
    cur_rr = format_rr(cur_rr_val)
    x, y = int(m.get('x', 0)), int(m.get('y', 0))
    scale = f"{float(m.get('scale', 1)):g}"
    available = m.get('availableModes') or []

    if out not in default_rr_by_out:
        default_rr_by_out[out] = cur_rr
    default_rr = default_rr_by_out[out]

    if fps_token is None:
        target_rr = cur_rr
    elif fps_token == 'auto':
        if session_state.get('played_video'):
            # Video stopped: switch back to 120Hz (if available) to minimize future switches
            target_rr = pick_best_mode_rr(available, w, h, 120.0, default_rr)
        else:
            # Opening flatpak: do not switch if already at 120, 100, 60, or 50Hz
            if any(abs(cur_rr_val - r) <= 0.2 for r in (120.0, 100.0, 60.0, 50.0)):
                target_rr = cur_rr
            else:
                target_rr = default_rr
    else:
        try:
            target_fps = float(fps_token)
        except ValueError:
            target_fps = None
        if target_fps is not None:
            session_state['played_video'] = True
            if is_compatible_current_rr(cur_rr_val, target_fps):
                target_rr = cur_rr
            else:
                target_rr = pick_best_mode_rr(available, w, h, target_fps, default_rr)
        else:
            target_rr = default_rr

    desired = (out, cm, target_rr, bitdepth)
    if desired == last_applied:
        return last_applied

    mode = f'{w}x{h}@{target_rr}'
    lua = (
        f'hl.monitor({{output="{out}",mode="{mode}",position="{x}x{y}",'
        f'scale={scale},bitdepth={bitdepth},cm="{cm}",supports_wide_color=1,supports_hdr=1}})'
    )
    res = hypr_cmd(sock_path, f'eval {lua}')
    with open(LOG, 'a') as f:
        f.write(
            f"{time.strftime('%H:%M:%S')} cm={cm} bpc={bitdepth} mode={mode} (req={fps_token}) -> {res}\n"
        )
    return desired if res == 'ok' else last_applied


def main() -> None:
    last_applied: tuple[str, str, str, int] | None = None
    default_rr_by_out: dict[str, str] = {}
    session_state: dict[str, bool] = {'played_video': False}
    bitdepth = get_max_bitdepth()

    while True:
        sock = find_sock()
        if sock:
            cm, fps_token = parse_state()
            try:
                last_applied = apply_display_state(
                    sock, cm, fps_token, bitdepth, default_rr_by_out, last_applied, session_state
                )
            except Exception as e:
                with open(LOG, 'a') as f:
                    f.write(f"{time.strftime('%H:%M:%S')} err={e}\n")
        else:
            last_applied = None
            default_rr_by_out.clear()
            session_state['played_video'] = False
        time.sleep(0.25)


if __name__ == '__main__':
    main()
