#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
# Copyright (C) 2026-present Team LibreELEC (https://libreelec.tv)

import glob
import json
import os
import socket
import time

STATE = os.environ.get(
    'VTMOD_HDR_STATE_FILE',
    '/storage/.kodi/userdata/addon_data/flatpak.vacuumtubemod/userData/hdr_state',
)
LOG = '/tmp/vtmod-hdr-watcher.log'


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


def get_monitor_spec(sock_path: str) -> tuple[str, str, str, str]:
    try:
        monitors = json.loads(hypr_cmd(sock_path, 'j/monitors'))
        if monitors:
            m = next((x for x in monitors if x.get('focused')), monitors[0])
            name = m.get('name', 'HDMI-A-1')
            w, h = m.get('width', 3840), m.get('height', 2160)
            rr = f"{float(m.get('refreshRate', 60)):.2f}".rstrip('0').rstrip('.')
            x, y = m.get('x', 0), m.get('y', 0)
            scale = f"{float(m.get('scale', 1)):g}"
            return name, f'{w}x{h}@{rr}', f'{x}x{y}', scale
    except Exception:
        pass
    return 'HDMI-A-1', '3840x2160@60', '0x0', '1'


def set_cm(sock_path: str, cm: str) -> str:
    out, mode, pos, scale = get_monitor_spec(sock_path)
    lua = (
        f'hl.monitor({{output="{out}",mode="{mode}",position="{pos}",'
        f'scale={scale},bitdepth=10,cm="{cm}",supports_wide_color=1,supports_hdr=1}})'
    )
    return hypr_cmd(sock_path, f'eval {lua}')


def main() -> None:
    last_cm = None
    while True:
        sock = find_sock()
        if sock:
            cm = 'srgb'
            try:
                with open(STATE) as f:
                    if f.read().strip() == 'hdr':
                        cm = 'hdr'
            except OSError:
                pass
            if cm != last_cm:
                try:
                    res = set_cm(sock, cm)
                    with open(LOG, 'a') as f:
                        f.write(f"{time.strftime('%H:%M:%S')} cm={cm} -> {res}\n")
                    if res == 'ok':
                        last_cm = cm
                except OSError as e:
                    with open(LOG, 'a') as f:
                        f.write(f"{time.strftime('%H:%M:%S')} err={e}\n")
        else:
            last_cm = None
        time.sleep(0.25)


if __name__ == '__main__':
    main()
