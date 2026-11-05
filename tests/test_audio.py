import base64
import json
import unittest
from unittest.mock import patch
from types import SimpleNamespace

import audio


class AudioTests(unittest.TestCase):
    def run_result(self, value):
        return SimpleNamespace(returncode=0, stdout=json.dumps(value), stderr='')

    @patch('audio.subprocess.run')
    def test_ids_survive_duplicate_names_and_changed_indices(self, run):
        run.return_value = self.run_result([
            {'ID': 'a', 'Name': 'Same', 'Type': 'Playback', 'Index': 9},
            {'ID': 'b', 'Name': 'Same', 'Type': 'Playback', 'Index': 1}])
        devices = audio.listar_dispositivos()
        self.assertEqual(set(devices), {'a', 'b'})
        self.assertEqual(devices['a']['Index'], 9)

    @patch('audio.subprocess.run')
    def test_zero_and_one_json_device(self, run):
        for value, count in [(None, 0), ([], 0),
                              ({'ID': 'a', 'Name': 'Áudio', 'Type': 'Playback'}, 1)]:
            run.return_value = self.run_result(value)
            self.assertEqual(len(audio.listar_dispositivos()), count)

    @patch('audio.subprocess.run')
    def test_switch_uses_literal_id(self, run):
        run.return_value = self.run_result(None)
        device_id = "a'; $(throw 'injected')\u2019; throw 'smart quote' #"
        audio.trocar_dispositivo(device_id)
        script = run.call_args.args[0][-1]
        self.assertIn(base64.b64encode(device_id.encode('utf-8')).decode('ascii'), script)
        self.assertIn('-ID $deviceId', script)
        self.assertNotIn(device_id, script)
        self.assertNotIn('-Index', script)

    @patch('audio.subprocess.run')
    def test_errors_are_runtime_errors(self, run):
        run.return_value = SimpleNamespace(returncode=1, stdout='', stderr='failed')
        with self.assertRaises(RuntimeError):
            audio.listar_dispositivos()
        run.return_value = self.run_result('invalid')
        with self.assertRaises(RuntimeError):
            audio.listar_dispositivos()
        run.return_value = self.run_result(False)
        with self.assertRaises(RuntimeError):
            audio.listar_dispositivos()


if __name__ == '__main__':
    unittest.main()
