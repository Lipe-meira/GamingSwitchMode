import queue
import unittest
from unittest.mock import Mock

from audio_service import AudioService


class AudioServiceTests(unittest.TestCase):
    def test_absent_and_reconnected_device(self):
        backend = Mock()
        backend.listar_dispositivos.return_value = {}
        events = queue.Queue()
        service = AudioService(backend, events)
        service.activate('id', 'Headset')
        backend.trocar_dispositivo.assert_not_called()
        self.assertIn('indisponivel', events.get()[1])
        events.get()
        backend.listar_dispositivos.return_value = {'id': {'Name': 'Headset', 'Index': 9}}
        service.activate('id', 'Headset')
        backend.trocar_dispositivo.assert_called_once_with('id')
        self.assertEqual(events.get()[0], 'devices')
        self.assertEqual(events.get()[0], 'status')

    def test_error_is_reported_without_throwing(self):
        backend = Mock()
        backend.listar_dispositivos.side_effect = RuntimeError('offline')
        events = queue.Queue()
        AudioService(backend, events).activate('id', 'Headset')
        self.assertIn('offline', events.get()[1])
