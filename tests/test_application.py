import importlib
import threading
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

    def test_hide_requires_operational_tray(self):
        controller = application.ApplicationController()
        controller.window = Mock()
        controller.tray = Mock()
        controller.tray.is_operational.return_value = False
        controller.hide_window()
        controller.window.hide.assert_not_called()
        controller.window.set_status.assert_called()
        controller.tray.is_operational.return_value = True
        controller.hide_window()
        controller.window.hide.assert_called_once()

    def test_tray_failure_is_queued_and_window_restored_on_main_thread(self):
        controller = application.ApplicationController()
        controller.window = Mock()
        controller.tray = Mock()
        controller.tray.run.side_effect = RuntimeError('failed')
        thread = threading.Thread(target=controller.setup_tray)
        thread.start()
        thread.join(2)
        self.assertFalse(thread.is_alive())
        controller.window.show.assert_not_called()
        controller.process_events()
        controller.window.show.assert_called_once()
        self.assertIn('failed', controller.window.set_status.call_args.args[0])

    def test_main_window_failure_releases_root_manager_and_mutex(self):
        controller = application.ApplicationController()
        root = Mock()
        manager = Mock()
        with patch.object(application, 'garantir_instancia_unica', return_value=42), \
                patch.object(application, 'liberar_mutex') as release, \
                patch.object(application.tk, 'Tk', return_value=root), \
                patch.object(application.audio, 'listar_dispositivos', return_value={}), \
                patch.object(application, 'ConfigStore') as store, \
                patch.object(application, 'HotkeyManager', return_value=manager), \
                patch.object(application, 'MainWindow', side_effect=RuntimeError('window failed')):
            store.return_value.load.return_value = {'schema_version': 1, 'bindings': [], 'unresolved': []}
            with self.assertRaisesRegex(RuntimeError, 'window failed'):
                controller.run()
        root.destroy.assert_called_once()
        manager.close.assert_called_once()
        release.assert_called_once_with(42)

    def test_pending_audio_jobs_execute_before_shutdown_sentinel(self):
        controller = application.ApplicationController()
        pending = Mock()
        controller.audio_jobs.put(pending)
        controller.shutdown()
        worker = threading.Thread(target=controller.audio_worker)
        worker.start()
        worker.join(2)
        self.assertFalse(worker.is_alive())
        pending.assert_called_once()
