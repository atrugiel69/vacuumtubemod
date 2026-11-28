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


def get_available_rates(available_modes: list[str], w: int, h: int) -> list[tuple[float, str]]:
    prefix = f'{w}x{h}@'
    rates: list[tuple[float, str]] = []
    for entry in available_modes:
        if entry.startswith(prefix):
            m = re.match(r'^(\d+)x(\d+)@([0-9.]+)', entry)
            if m:
                r_str = m.group(3)
                rates.append((float(r_str), r_str))
    return rates


def find_mode_rate(rates: list[tuple[float, str]], target: float, tol: float = 0.05) -> str | None:
    matches = [r for r in rates if abs(r[0] - target) <= tol]
    if matches:
        return min(matches, key=lambda r: abs(r[0] - target))[1]
    return None


def get_compatible_mode_rr(
    available_modes: list[str],
    w: int,
    h: int,
    cur_rr_val: float,
    cur_rr: str,
    target_fps: float,
) -> str | None:
    """Return exact available mode rate string if cur_rr_val is an exact integer multiple of target_fps."""
    rates = get_available_rates(available_modes, w, h)

    # Exact-family compatibility (no 1000/1001 cross-family mixing)
    families: tuple[tuple[float, tuple[float, ...]], ...] = (
        (120.0, (120.0, 60.0, 30.0, 24.0)),
        (119.88, (119.88, 59.94, 29.97, 23.976)),
        (100.0, (100.0, 50.0, 25.0)),
        (60.0, (60.0, 30.0)),
        (59.94, (59.94, 29.97)),
        (50.0, (50.0, 25.0)),
        (24.0, (24.0,)),
        (23.98, (23.976,)),
    )
    for mode_hz, supported_fps in families:
        if abs(cur_rr_val - mode_hz) <= 0.05:
            if any(abs(target_fps - f) <= 0.02 for f in supported_fps):
                return find_mode_rate(rates, mode_hz, tol=0.05) or cur_rr
            return None

    return None


def pick_best_mode_rr(
    available_modes: list[str],
    w: int,
    h: int,
    target_fps: float | None,
    fallback_rr: str,
) -> str:
    if target_fps is None:
        return fallback_rr

    rates = get_available_rates(available_modes, w, h)
    if not rates:
        return fallback_rr

    # Minimal covering sets (exact integer multiples first; avoid 25/29.97/30Hz)
    preferences: tuple[tuple[float, float, tuple[float, ...]], ...] = (
        (23.976, 0.02, (119.88, 23.98, 120.0, 24.0)),
        (24.0, 0.02, (120.0, 24.0, 119.88, 23.98)),
        (25.0, 0.02, (100.0, 50.0, 25.0)),
        (29.97, 0.02, (119.88, 59.94, 120.0, 60.0, 29.97)),
        (30.0, 0.02, (120.0, 60.0, 119.88, 59.94, 30.0)),
        (50.0, 0.02, (100.0, 50.0)),
        (59.94, 0.02, (119.88, 59.94, 120.0, 60.0)),
        (60.0, 0.02, (120.0, 60.0, 119.88, 59.94)),
        (100.0, 0.05, (100.0, 50.0)),
        (119.88, 0.05, (119.88, 59.94, 120.0, 60.0)),
        (120.0, 0.05, (120.0, 60.0, 119.88, 59.94)),
    )
    for fps_ref, tol, cand_order in preferences:
        if abs(target_fps - fps_ref) <= tol:
            for cand in cand_order:
                matched = find_mode_rate(rates, cand, tol=0.05)
                if matched is not None:
                    return matched
            return fallback_rr

    # Fallback for uncommon framerates: exact match, then integer multiple
    exact = find_mode_rate(rates, target_fps, tol=0.05)
    if exact is not None:
        return exact

    for mult in (2, 3, 4, 5):
        mult_match = find_mode_rate(rates, target_fps * mult, tol=0.1)
        if mult_match is not None:
            return mult_match

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
    x, y = int(m.get('x', 0)), int(m.get('y', 0))
    scale = f"{float(m.get('scale', 1)):g}"
    available = m.get('availableModes') or []
    rates = get_available_rates(available, w, h)
    cur_rr = find_mode_rate(rates, cur_rr_val, tol=0.05) or format_rr(cur_rr_val)

    if out not in default_rr_by_out:
        default_rr_by_out[out] = cur_rr
    default_rr = default_rr_by_out[out]

    if fps_token is None:
        target_rr = cur_rr
    elif fps_token == 'auto':
        # Lazy return: stay in any fluid UI mode (>=50Hz); only exit 23.98/24Hz
        if cur_rr_val >= 49.0:
            target_rr = cur_rr
        elif abs(cur_rr_val - 23.98) <= 0.05:
            target_rr = pick_best_mode_rr(available, w, h, 59.94, default_rr)
        else:
            target_rr = pick_best_mode_rr(available, w, h, 60.0, default_rr)
    else:
        try:
            target_fps = float(fps_token)
        except ValueError:
            target_fps = None
        if target_fps is not None:
            session_state['played_video'] = True
            compat_rr = get_compatible_mode_rr(available, w, h, cur_rr_val, cur_rr, target_fps)
            if compat_rr is not None:
                target_rr = compat_rr
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
