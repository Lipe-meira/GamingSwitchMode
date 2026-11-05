import queue
import unittest
from unittest.mock import Mock

from system_tray import SystemTray


class SystemTrayTests(unittest.TestCase):
    def test_callbacks_enqueue_events_and_stop_icon(self):
        events = queue.Queue()
        tray = SystemTray(events)
        icon = Mock()
        tray.show_window(icon, None)
        tray.exit_app(icon, None)
        self.assertEqual(events.get_nowait(), ('show',))
        self.assertEqual(events.get_nowait(), ('exit',))
        icon.stop.assert_called_once_with()
