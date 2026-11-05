import importlib
import unittest
from unittest.mock import Mock, patch

import application


class ApplicationTests(unittest.TestCase):
    def test_import_does_not_start_resources(self):
        with patch('tkinter.Tk') as root, patch('threading.Thread') as thread:
            importlib.reload(application)
            root.assert_not_called()
            thread.assert_not_called()

    def test_shutdown_is_idempotent_and_drops_pending_events(self):
        controller = application.ApplicationController()
        controller.manager = Mock()
        controller.tray = Mock()
        controller.window = Mock()
        controller.app_mutex = 123
        controller.events.put(('status', 'late'))
        with patch.object(application, 'liberar_mutex') as release:
            controller.shutdown()
            controller.shutdown()
            controller.process_events()
        controller.manager.close.assert_called_once_with()
        controller.tray.stop.assert_called_once_with()
        controller.window.destroy.assert_called_once_with()
        controller.window.set_status.assert_not_called()
        release.assert_called_once_with(123)
        self.assertIsNone(controller.audio_jobs.get_nowait())

    def test_failed_initialization_releases_mutex(self):
        controller = application.ApplicationController()
        with patch.object(application, 'garantir_instancia_unica', return_value=42), \
                patch.object(application, 'liberar_mutex') as release, \
                patch.object(application.tk, 'Tk', side_effect=RuntimeError('failed')):
            with self.assertRaisesRegex(RuntimeError, 'failed'):
                controller.run()
        release.assert_called_once_with(42)

    def test_event_is_sent_to_window(self):
        controller = application.ApplicationController()
        controller.window = Mock()
        controller.events.put(('status', 'ready'))
        controller.process_events()
        controller.window.set_status.assert_called_once_with('ready')
        controller.window.schedule.assert_called_once()
