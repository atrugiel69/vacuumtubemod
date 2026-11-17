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
    default_rr_by_out: dict[str, str],
    last_applied: tuple[str, str, str] | None,
) -> tuple[str, str, str] | None:
    monitors = json.loads(hypr_cmd(sock_path, 'j/monitors'))
    if not monitors:
        return last_applied

    m = next((x for x in monitors if x.get('focused')), monitors[0])
    out = m.get('name', 'HDMI-A-1')
    w, h = int(m.get('width', 3840)), int(m.get('height', 2160))
    cur_rr = format_rr(float(m.get('refreshRate', 60)))
    x, y = int(m.get('x', 0)), int(m.get('y', 0))
    scale = f"{float(m.get('scale', 1)):g}"
    available = m.get('availableModes') or []

    if out not in default_rr_by_out:
        default_rr_by_out[out] = cur_rr
    default_rr = default_rr_by_out[out]

    if fps_token is None:
        target_rr = cur_rr
    elif fps_token == 'auto':
        target_rr = default_rr
    else:
        try:
            target_fps = float(fps_token)
        except ValueError:
            target_fps = None
        target_rr = pick_best_mode_rr(available, w, h, target_fps, default_rr)

    desired = (out, cm, target_rr)
    if desired == last_applied:
        return last_applied

    mode = f'{w}x{h}@{target_rr}'
    lua = (
        f'hl.monitor({{output="{out}",mode="{mode}",position="{x}x{y}",'
        f'scale={scale},bitdepth=10,cm="{cm}",supports_wide_color=1,supports_hdr=1}})'
    )
    res = hypr_cmd(sock_path, f'eval {lua}')
    with open(LOG, 'a') as f:
        f.write(f"{time.strftime('%H:%M:%S')} cm={cm} mode={mode} (req={fps_token}) -> {res}\n")
    return desired if res == 'ok' else last_applied


def main() -> None:
    last_applied: tuple[str, str, str] | None = None
    default_rr_by_out: dict[str, str] = {}

    while True:
        sock = find_sock()
        if sock:
            cm, fps_token = parse_state()
            try:
                last_applied = apply_display_state(
                    sock, cm, fps_token, default_rr_by_out, last_applied
                )
            except Exception as e:
                with open(LOG, 'a') as f:
                    f.write(f"{time.strftime('%H:%M:%S')} err={e}\n")
        else:
            last_applied = None
            default_rr_by_out.clear()
        time.sleep(0.25)


if __name__ == '__main__':
    main()
