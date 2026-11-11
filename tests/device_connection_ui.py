"""Isolated real framebuffer/evdev UI check; stop APPLaunch before running.

Uses an isolated config and private FIFO keyboard; never injects remote keys.
Restarts no services: the caller must restore APPLaunch after this check.
"""
import os
from pathlib import Path
import socket
import struct
import subprocess
import tempfile
import time
import zlib

BASE = '/usr/share/APPLaunch/apps/flipper-one-remote'
WIFI_HOST = os.environ['FLIPPER_TEST_WIFI_HOST']  # Real target IP required for this hardware test.
UNREACHABLE_HOST = os.environ.get('FLIPPER_TEST_UNREACHABLE_HOST', '192.0.2.254')
OUT = Path('/tmp/flipctl-connection-ui-results')
OUT.mkdir(exist_ok=True)


def capture(name):
    raw = Path('/dev/fb0').read_bytes()[:320*170*2]
    assert len(raw) == 320*170*2
    pixels = bytearray()
    for value, in struct.iter_unpack('<H', raw):
        pixels.extend((((value >> 11) & 31)*255//31,
                       ((value >> 5) & 63)*255//63, (value & 31)*255//31))
    def chunk(tag, data):
        return struct.pack('!I', len(data)) + tag + data + struct.pack('!I', zlib.crc32(tag+data))
    data = b''.join(b'\0'+pixels[y*960:(y+1)*960] for y in range(170))
    png = (b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('!IIBBBBB', 320, 170, 8, 2, 0, 0, 0)) +
           chunk(b'IDAT', zlib.compress(data)) + chunk(b'IEND', b''))
    (OUT / (name+'.png')).write_bytes(png)
    print('CAPTURE', name, flush=True)


def run(no_cable=False):
    with tempfile.TemporaryDirectory(prefix='flipctl-ui-input-') as folder:
        fifo = folder+'/keyboard'
        os.mkfifo(fifo)
        keep = os.open(fifo, os.O_RDWR | os.O_NONBLOCK)
        env = dict(os.environ, LV_LINUX_KEYBOARD_DEVICE=fifo, LV_LINUX_FBDEV_DEVICE='/dev/fb0',
                   XDG_CONFIG_HOME=str(Path(folder) / 'config'))
        if no_cable:
            env['FLIPPER_ONE_WIRED_INTERFACE'] = 'absent-test-interface'
        log = open(OUT / ('missing-cable.log' if no_cable else 'wired.log'), 'w')
        process = subprocess.Popen([BASE+'/flipper-one-remote', BASE+'/bridge.py', '192.168.50.2'],
                                   env=env, stdout=log, stderr=log)
        def key(code):
            for value in (1, 0):
                os.write(keep, struct.pack('llHHi', 0, 0, 1, code, value))
                time.sleep(.035)
        def type_ip(text):
            for _ in range(16):
                key(14)  # Backspace is local while settings is open.
            for char in text:
                key(52 if char == '.' else (11 if char == '0' else int(char)+1))
        def sockets(host):
            listing = subprocess.check_output(['ss', '-tnp'], text=True)
            relevant = '\n'.join(line for line in listing.splitlines()
                                 if f'{host}:8899' in line and 'python3' in line)
            assert relevant, (host, listing)
            print('SOCKET', relevant, flush=True)
        try:
            time.sleep(2)
            assert process.poll() is None
            if no_cable:
                capture('01-no-cable-ip-prompt')
                # Initial panel is Auto; Right chooses WiFi explicitly.
                key(106)
            else:
                sockets('192.168.50.2')
                capture('05-auto-ethernet-live')
                key(17)  # W opens LOCAL settings while live.
                key(15)
            type_ip(WIFI_HOST)
            capture('02-wifi-ip-entry' if no_cable else '06-switch-while-live')
            key(28)
            time.sleep(2)
            sockets(WIFI_HOST)
            capture('03-wifi-live' if no_cable else '07-wifi-switched-live')
            assert (Path(env['XDG_CONFIG_HOME'])/'flipctl/wifi-ip').read_text().strip() == WIFI_HOST
            if no_cable:
                key(17)
                type_ip(UNREACHABLE_HOST)
                key(28)
                # Wait for first failed WiFi connection (3-second read/connect timeout).
                time.sleep(3.3)
                capture('04-centered-no-signal')
                assert process.poll() is None
                key(17)
                type_ip(WIFI_HOST)
                key(28)
                time.sleep(2)
                sockets(WIFI_HOST)
            else:
                key(17)
                key(15)  # WiFi -> Auto, preserving entered WiFi fallback.
                key(28)
                time.sleep(2)
                sockets('192.168.50.2')
                capture('08-auto-return-ethernet')
            assert process.poll() is None
        finally:
            process.terminate()
            process.wait(timeout=5)
            os.close(keep)
            log.close()
        errors = (OUT / ('missing-cable.log' if no_cable else 'wired.log')).read_text()
        assert 'Traceback' not in errors, errors
        assert 'INPUT ' not in errors, 'Local connection-editor keys leaked to the remote target: '+errors
        print('PASS UI input stayed local; transport and GUI alive', flush=True)


run(no_cable=True)
run()
