import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from configuration import ConfigStore, empty_config, validate_config, user_config_path


def binding(device_id='a', hotkey='ctrl+alt+1'):
    return {'device_id': device_id, 'name': 'Same', 'type': 'Playback', 'hotkey': hotkey}


class ConfigTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / 'user' / 'config.json'
        self.legacy = Path(self.temp.name) / 'audio_switcher_config.json'
        self.store = ConfigStore(self.path, [self.legacy])

    def test_missing_and_roundtrip(self):
        self.assertEqual(self.store.load(), empty_config())
        config = empty_config()
        config['bindings'] = [binding(), binding('b', 'ctrl+alt+2')]
        config['future'] = {'preserve': True}
        self.store.save(config)
        self.assertEqual(ConfigStore(self.path).load(), config)

    def test_legacy_migration_is_pending_backed_up_and_idempotent(self):
        original = '{"1": "ctrl+alt+1", "2": "ctrl+alt+2"}'
        self.legacy.write_text(original)
        config = self.store.load()
        self.assertEqual(config['bindings'], [])
        self.assertEqual([x['legacy_index'] for x in config['unresolved']], ['1', '2'])
        backup = Path(config['migration']['backup'])
        self.assertEqual(backup.parent, self.path.parent)
        self.assertEqual(backup.read_text(), original)
        self.assertEqual(ConfigStore(self.path, [self.legacy]).load(), config)
        self.assertEqual(self.legacy.read_text(), original)

    def test_valid_new_config_wins_over_legacy(self):
        self.store.save(empty_config())
        self.legacy.write_text('{"1":"ctrl+1"}')
        self.assertEqual(self.store.load()['unresolved'], [])

    def test_atomic_failure_preserves_file_and_backup(self):
        old = empty_config()
        self.store.save(old)
        new = empty_config()
        new['bindings'] = [binding()]
        with patch('configuration.os.replace', side_effect=PermissionError('denied')):
            with self.assertRaises(OSError):
                self.store.save(new)
        self.assertEqual(json.loads(self.path.read_text()), old)
        self.assertEqual(list(self.path.parent.glob('*.tmp')), [])

    def test_corrupt_config_recovers_valid_backup_without_losing_corrupt_file(self):
        self.store.save(empty_config())
        self.store.save({'schema_version': 1, 'bindings': [binding()], 'unresolved': []})
        self.path.write_text('{broken')
        recovered = ConfigStore(self.path)
        self.assertEqual(recovered.load(), empty_config())
        self.assertTrue(recovered.warnings)
        self.assertTrue(any(p.read_text() == '{broken' for p in self.path.parent.glob('*.invalid-*')))

    def test_invalid_without_backup_is_not_overwritten(self):
        self.path.parent.mkdir()
        self.path.write_text('{broken')
        with self.assertRaises(ValueError):
            self.store.load()
        with self.assertRaises(ValueError):
            self.store.save(empty_config())
        self.assertEqual(self.path.read_text(), '{broken')

    def test_json_null_is_invalid_and_never_reimports_old_data(self):
        self.path.parent.mkdir()
        self.path.write_text('null')
        self.legacy.write_text('{"1":"ctrl+1"}')
        with self.assertRaises(ValueError):
            self.store.load()
        self.assertEqual(self.path.read_text(), 'null')

    def test_read_error_does_not_fall_back_to_legacy(self):
        self.store.save(empty_config())
        with patch.object(Path, 'read_text', side_effect=PermissionError('denied')):
            with self.assertRaises(OSError):
                self.store.load()

    def test_backup_failure_aborts_migration(self):
        self.legacy.write_text('{"1":"ctrl+1"}')
        with patch.object(self.store, '_atomic_bytes', side_effect=PermissionError('denied')):
            with self.assertRaises(OSError):
                self.store.load()
        self.assertFalse(self.path.exists())

    def test_strict_schema_preserves_unsupported_data(self):
        for bad in [{'schema_version': 99}, {'schema_version': 1, 'bindings': [{}], 'unresolved': []}, []]:
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                validate_config(bad)

    def test_primary_replace_failure_keeps_previous_config_and_valid_backup(self):
        self.store.save(empty_config())
        replace = os.replace
        def fail_primary(source, target):
            if Path(target) == self.path:
                raise OSError('locked target')
            return replace(source, target)
        new = empty_config()
        new['bindings'] = [binding()]
        with patch('configuration.os.replace', side_effect=fail_primary):
            with self.assertRaises(OSError):
                self.store.save(new)
        self.assertEqual(self.store.load(), empty_config())
        self.assertEqual(json.loads(self.store.backup.read_text()), empty_config())

    def test_user_path_ignores_executable_directory(self):
        with patch.dict(os.environ, {'APPDATA': self.temp.name}):
            self.assertEqual(user_config_path(), Path(self.temp.name) / 'GamingSwitchMode' / 'config.json')

    def test_migrate_in_place_and_missing_primary_recovery(self):
        self.path.parent.mkdir()
        self.path.write_text('{"7":"ctrl+7"}')
        config = self.store.load()
        self.assertEqual(config['unresolved'][0]['legacy_index'], '7')
        self.assertEqual(ConfigStore(self.path).load(), config)
        self.store.save(config)
        self.path.unlink()
        self.assertEqual(ConfigStore(self.path).load(), config)


if __name__ == '__main__':
    unittest.main()
