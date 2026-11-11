#!/usr/bin/env python3
"""Capture public-safe UI screenshots on CardputerZero.

Stop FlipCTL and APPLaunch before running; restore them afterwards. Uses an
isolated config and FIFO keyboard, disables Ethernet probing and never connects
to a real target. The only displayed address is the documentation IP 192.0.2.10.
"""
import argparse
import os
from pathlib import Path
import struct
import subprocess
import tempfile
import time
import zlib


def capture(path, framebuffer):
    with open(framebuffer, 'rb', buffering=0) as stream:
        raw = stream.read(320 * 170 * 2)
    if len(raw) != 320 * 170 * 2:
        raise RuntimeError('Expected a 320x170 RGB565 framebuffer')
    pixels = bytearray()
    for value, in struct.iter_unpack('<H', raw):
        pixels.extend((((value >> 11) & 31) * 255 // 31,
                       ((value >> 5) & 63) * 255 // 63,
                       (value & 31) * 255 // 31))
    def chunk(kind, payload):
        return (struct.pack('!I', len(payload)) + kind + payload +
                struct.pack('!I', zlib.crc32(kind + payload)))
    rows = b''.join(b'\0' + pixels[y * 960:(y + 1) * 960] for y in range(170))
    path.write_bytes(b'\x89PNG\r\n\x1a\n' +
                     chunk(b'IHDR', struct.pack('!IIBBBBB', 320, 170, 8, 2, 0, 0, 0)) +
                     chunk(b'IDAT', zlib.compress(rows)) + chunk(b'IEND', b''))
    print(path.name, flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--app-dir', type=Path,
                        default=Path('/usr/share/APPLaunch/apps/flipper-one-remote'))
    parser.add_argument('--framebuffer', default='/dev/fb0')
    parser.add_argument('--output', type=Path, default=Path('/tmp/flipctl-public-screenshots'))
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='flipctl-public-ui-') as folder:
        fifo = str(Path(folder) / 'keyboard')
        os.mkfifo(fifo)
        keyboard = os.open(fifo, os.O_RDWR | os.O_NONBLOCK)
        env = dict(os.environ, XDG_CONFIG_HOME=str(Path(folder) / 'config'),
                   LV_LINUX_KEYBOARD_DEVICE=fifo,
                   LV_LINUX_FBDEV_DEVICE=args.framebuffer,
                   FLIPPER_ONE_WIRED_INTERFACE='absent-screenshot-interface')
        process = None
        try:
            with (Path(folder) / 'app.log').open('w') as log:
                process = subprocess.Popen([str(args.app_dir / 'flipper-one-remote'),
                                            str(args.app_dir / 'bridge.py'), '192.0.2.2'],
                                           env=env, stdout=log, stderr=log)
                time.sleep(1.2)
                if process.poll() is not None:
                    raise RuntimeError('App exited; stop other framebuffer apps before capturing')
                def tap(code):
                    for value in (1, 0):
                        os.write(keyboard, struct.pack('llHHi', 0, 0, 1, code, value))
                        time.sleep(0.04)
                def snap(name):
                    time.sleep(0.25)
                    capture(args.output / name, args.framebuffer)
                snap('connection-auto.png')
                tap(106)  # Right: Auto -> WiFi
                for char in '192.0.2.10':
                    tap(52 if char == '.' else (11 if char == '0' else int(char) + 1))
                snap('connection-wifi.png')
                tap(35)  # H: guide, also available in settings
                snap('key-guide.png')
                tap(35)
                tap(111)  # Delete: clear local input
                for char in '999.1.2.3':
                    tap(52 if char == '.' else int(char) + 1)
                tap(28)  # Invalid input is rejected locally, with no connection attempt
                snap('invalid-ip.png')
        finally:
            if process is not None and process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()
            os.close(keyboard)


if __name__ == '__main__':
    main()
