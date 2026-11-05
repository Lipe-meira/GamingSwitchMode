"""Exercise UI event boundaries without a display or physical audio devices."""
import importlib
import queue
import unittest
from unittest.mock import Mock, patch


class UITests(unittest.TestCase):
    def setUp(self):
        self.ui = importlib.import_module('application').ApplicationController()
        self.ui.events = queue.Queue()
        self.ui.audio_jobs = queue.Queue()
        self.ui.dispositivos = {}
        self.ui.manager = Mock()
        self.ui.manager.config = {'bindings': [{'device_id': 'a', 'name': 'Headset'}]}

    def test_absent_device_does_not_switch_and_reconnection_uses_same_id(self):
        with patch.object(importlib.import_module('audio'), 'listar_dispositivos', return_value={}) as listing, \
                patch.object(importlib.import_module('audio'), 'trocar_dispositivo') as switch:
            self.ui.trocar_dispositivo('a')
            self.ui.audio_jobs.get_nowait()()
            switch.assert_not_called()
            self.assertIn('indisponivel', self.ui.events.get_nowait()[1])
            listing.return_value = {'a': {'ID': 'a', 'Name': 'Headset', 'Index': 99}}
            self.ui.trocar_dispositivo('a')
            self.ui.audio_jobs.get_nowait()()
            switch.assert_called_once_with('a')

    def test_tray_callbacks_only_enqueue_events(self):
        self.ui.root = Mock()
        icon = Mock()
        self.ui.show_window(icon, None)
        self.ui.exit_app(icon, None)
        self.ui.root.after.assert_not_called()
        self.assertEqual(self.ui.events.get_nowait(), ('show',))
        self.assertEqual(self.ui.events.get_nowait(), ('exit',))

    def test_duplicate_name_labels_map_to_distinct_ids(self):
        self.ui.manager.config = {'bindings': []}
        self.ui.dispositivos = {key: {'Name': 'Same'} for key in ('a', 'b')}
        self.assertEqual(set(self.ui.device_labels().values()), {'a', 'b'})

    def test_long_duplicate_names_show_distinguishing_id_before_name(self):
        self.ui.manager.config = {'bindings': []}
        self.ui.dispositivos = {key: {'Name': 'Same long name ' * 10} for key in ('endpoint-a', 'endpoint-b')}
        labels = self.ui.device_labels()
        self.assertNotEqual(*(label[:24] for label in labels))


if __name__ == '__main__':
    unittest.main()
