import importlib.util
from pathlib import Path
import struct
import unittest
import tempfile
import os
from unittest.mock import patch, MagicMock
spec=importlib.util.spec_from_file_location('bridge',Path(__file__).parents[1]/'main/bridge.py')
bridge=importlib.util.module_from_spec(spec)
spec.loader.exec_module(bridge)
class Protocol(unittest.TestCase):
    def test_partial_rectangle_preserves_surroundings(self):
        screen=bytearray([7])*(256*144)
        self.assertTrue(bridge.apply_frame(screen,struct.pack('<4H',2,3,2,2),bytes([1,2,3,4])))
        self.assertEqual(screen[770:774],bytes([1,2,7,7]))
        self.assertEqual(screen[1026:1028],bytes([3,4]))
        self.assertEqual(screen[0],7)
    def test_heartbeat(self):
        self.assertFalse(bridge.apply_frame(bytearray(36864),bytes(8),b''))
    def test_bounds_and_truncation(self):
        for rect,payload in [((255,0,2,1),b'xx'),((0,143,1,2),b'xx'),((0,0,2,2),b'x')]:
            with self.assertRaises(ValueError):
                bridge.apply_frame(bytearray(36864),struct.pack('<4H',*rect),payload)
    def test_fragmented_read(self):
        class Response:
            def read(self,n): return b'x'
        self.assertEqual(bridge.read_exact(Response(),8),b'x'*8)
class Connections(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.env = patch.dict(os.environ, {'XDG_CONFIG_HOME': self.temp.name})
        self.env.start()
        self.messages = []

    def tearDown(self):
        self.env.stop()
        self.temp.cleanup()

    def test_no_cable_opens_editor_without_connecting_saved_wifi(self):
        bridge.save_wifi_host('192.0.2.124')
        state = bridge.TargetState('192.168.50.2', self.messages.append, probe=lambda _: False)
        state.auto_select()
        self.assertIsNone(state.snapshot()[0])
        self.assertIn(b'R', self.messages)
        self.assertIn(b'Cauto\n\n192.0.2.124', self.messages)

    def test_cable_automatically_selects_wired_device(self):
        state = bridge.TargetState('192.168.50.2', self.messages.append, probe=lambda _: True)
        state.auto_select()
        self.assertEqual(state.snapshot()[0], ('192.168.50.2', bridge.WIRED_INTERFACE))
        self.assertNotIn(b'R', self.messages)

    def test_manual_wifi_persists_and_binds_wifi_even_with_cable(self):
        state = bridge.TargetState('192.168.50.2', self.messages.append, probe=lambda _: True)
        state.auto_select()
        conn = MagicMock()
        state.connection = conn
        state.ready.set()
        previous = state.generation
        state.request({'mode': 'wifi', 'host': '192.0.2.124'})
        self.assertEqual(state.snapshot()[0], ('192.0.2.124', bridge.WIFI_INTERFACE))
        self.assertEqual(bridge.load_wifi_host(), '192.0.2.124')
        self.assertGreater(state.generation, previous)
        self.assertFalse(state.ready.is_set())
        conn.close.assert_not_called()  # HTTPResponse is closed only by its owner.
        conn.sock.shutdown.assert_called_once()

    def test_auto_fallback_and_reinsertion(self):
        cable = [False]
        state = bridge.TargetState('192.168.50.2', self.messages.append, probe=lambda _: cable[0])
        state.request({'mode': 'auto', 'host': '192.0.2.124'})
        self.assertEqual(state.snapshot()[0][1], bridge.WIFI_INTERFACE)
        cable[0] = True
        state.auto_select()
        self.assertEqual(state.snapshot()[0][1], bridge.WIRED_INTERFACE)
        cable[0] = False
        state.auto_select()
        self.assertEqual(state.snapshot()[0][1], bridge.WIFI_INTERFACE)

    def test_invalid_ip_never_changes_existing_target_or_saved_settings(self):
        state = bridge.TargetState('192.168.50.2', self.messages.append, probe=lambda _: True)
        state.auto_select()
        original = state.snapshot()
        for host in ['999.1.1.1', 'http://192.0.2.124', '0.0.0.0', '127.0.0.1',
                     '224.1.1.1', '255.255.255.255', '192.0.2.124;rm -rf /', '']:
            with self.subTest(host=host), self.assertRaises(ValueError):
                state.request({'mode': 'wifi', 'host': host})
            self.assertEqual(state.snapshot(), original)
        self.assertEqual(bridge.load_wifi_host(), '')

    def test_resubmitting_same_target_keeps_ready_even_on_still_screen(self):
        state = bridge.TargetState('192.168.50.2', self.messages.append, probe=lambda _: True)
        state.request({'mode': 'wifi', 'host': '192.0.2.124'})
        state.ready.set()
        generation = state.generation
        state.request({'mode': 'wifi', 'host': '192.0.2.124'})
        self.assertTrue(state.ready.is_set())
        self.assertEqual(state.generation, generation)

    def test_transport_binds_selected_interface(self):
        for iface in ['eth0', 'wlan0']:
            with patch.object(bridge.socket, 'socket') as factory, \
                 patch.object(bridge.socket, 'SO_BINDTODEVICE', 25, create=True):
                conn = bridge.InterfaceHTTP('192.0.2.124', interface=iface, timeout=1)
                conn.connect()
                factory.return_value.setsockopt.assert_called_once_with(
                    bridge.socket.SOL_SOCKET, bridge.socket.SO_BINDTODEVICE, iface.encode()+b'\0')
                conn.close()

if __name__=='__main__': unittest.main()
