"""CardputerZero transport integration: reads real frames without sending remote keys."""
import json
import os
import socket
import subprocess
import sys
import tempfile
import time

BRIDGE = sys.argv[1] if len(sys.argv) > 1 else '/usr/share/APPLaunch/apps/flipper-one-remote/bridge.py'
WIFI_HOST = os.environ['FLIPPER_TEST_WIFI_HOST']  # Set to the real device IP for this hardware test.


def check(no_cable=False):
    with tempfile.TemporaryDirectory(prefix='flipctl-network-check-') as folder:
        path = folder + '/screen'
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
        sock.bind(path)
        sock.settimeout(8)
        env = dict(os.environ, XDG_CONFIG_HOME=folder)
        if no_cable:
            # Simulate missing Ethernet without changing any real interface.
            env['FLIPPER_ONE_WIRED_INTERFACE'] = 'absent-test-interface'
        process = subprocess.Popen(['python3', BRIDGE, path, '192.168.50.2'], env=env,
                                   stderr=subprocess.PIPE)
        states = []

        def await_frame(host):
            deadline = time.monotonic() + 12
            confirmed = False
            while time.monotonic() < deadline:
                data = sock.recv(40000)
                if data[:1] in (b'C', b'S', b'R'):
                    text = data.decode()
                    states.append(text)
                    print(repr(text), flush=True)
                    if data[:1] == b'C' and text.split('\n')[1] == host:
                        confirmed = True
                if confirmed and data[:1] == b'F':
                    assert len(data) == 36865
                    print('PASS real frame from', host, flush=True)
                    return
            raise AssertionError('No frame from ' + host)

        def connect(mode, host):
            sock.sendto(json.dumps({'action': 'connect', 'mode': mode, 'host': host}).encode(), path + '.net')

        try:
            if no_cable:
                while sock.recv(40000) != b'R':
                    pass
                print('PASS absent Ethernet prompts before attempting WiFi', flush=True)
            else:
                await_frame('192.168.50.2')
            connect('wifi', WIFI_HOST)
            await_frame(WIFI_HOST)
            if not no_cable:
                connect('auto', WIFI_HOST)
                await_frame('192.168.50.2')
            assert process.poll() is None
        finally:
            process.terminate()
            process.wait(timeout=5)
            errors = process.stderr.read().decode()
            print(errors, flush=True)
            assert 'Traceback' not in errors, errors
            sock.close()


check()
check(no_cable=True)
