from copy import deepcopy
import unittest

from configuration import empty_config
from hotkeys import HotkeyManager


DEVICE = {'ID': 'a', 'Name': 'Same', 'Type': 'Playback', 'Index': 1}


class MemoryStore:
    def __init__(self):
        self.data = empty_config()
        self.fail = False

    def save(self, data):
        if self.fail:
            raise OSError('disk full')
        self.data = deepcopy(data)


class FakeKeyboard:
    def __init__(self):
        self.handlers = {}
        self.fail = False

    def parse_hotkey_combinations(self, hotkey):
        aliases = {'control': 'ctrl'}
        chord = tuple(sorted(aliases.get(k.strip().lower(), k.strip().lower())
                             for k in hotkey.split('+')))
        return ((chord,),)

    def add_hotkey(self, hotkey, callback):
        if self.fail:
            raise ValueError('hook failed')
        handle = object()
        self.handlers[handle] = callback
        return handle

    def remove_hotkey(self, handle):
        del self.handlers[handle]


class HotkeyTests(unittest.TestCase):
    def setUp(self):
        self.store = MemoryStore()
        self.keyboard = FakeKeyboard()
        self.events = []
        self.manager = HotkeyManager(self.store.data, self.store, self.keyboard,
                                     lambda *event: self.events.append(event))

    def trigger(self):
        for callback in list(self.keyboard.handlers.values()):
            callback()
        events, self.events = self.events, []
        return [self.manager.resolve_event(*event) for event in events]

    def test_register_edit_remove_restart(self):
        self.manager.set_binding(DEVICE, 'ctrl+1')
        self.assertEqual(self.trigger(), ['a'])
        self.manager.set_binding(DEVICE, 'ctrl+2')
        self.assertEqual(len(self.keyboard.handlers), 1)
        self.assertEqual(self.store.data['bindings'][0]['hotkey'], 'ctrl+2')
        self.manager.close()
        restored = HotkeyManager(self.store.data, self.store, self.keyboard, lambda *x: None)
        self.assertEqual(restored.restore(), [])
        self.assertEqual(len(self.keyboard.handlers), 1)
        restored.remove('a')
        self.assertEqual(self.store.data['bindings'], [])
        self.assertFalse(self.keyboard.handlers)

    def test_registration_failure_preserves_previous(self):
        self.manager.set_binding(DEVICE, 'ctrl+1')
        self.keyboard.fail = True
        with self.assertRaises(ValueError):
            self.manager.set_binding(DEVICE, 'ctrl+2')
        self.assertEqual(self.trigger(), ['a'])
        self.assertEqual(self.store.data['bindings'][0]['hotkey'], 'ctrl+1')

    def test_save_failure_rolls_back_new_handler(self):
        self.manager.set_binding(DEVICE, 'ctrl+1')
        self.store.fail = True
        with self.assertRaises(OSError):
            self.manager.set_binding(DEVICE, 'ctrl+2')
        self.assertEqual(self.trigger(), ['a'])
        self.assertEqual(len(self.keyboard.handlers), 1)
        with self.assertRaises(OSError):
            self.manager.remove('a')
        self.assertEqual(self.trigger(), ['a'])

    def test_duplicate_equivalent_chords_rejected(self):
        self.manager.set_binding(DEVICE, 'ctrl+alt+1')
        with self.assertRaises(ValueError):
            self.manager.set_binding(dict(DEVICE, ID='b'), '1+control+alt')
        self.assertEqual(len(self.keyboard.handlers), 1)

    def test_same_registration_is_idempotent(self):
        self.manager.set_binding(DEVICE, 'ctrl+1')
        self.manager.set_binding(DEVICE, 'ctrl+1')
        self.assertEqual(len(self.keyboard.handlers), 1)

    def test_offline_binding_retained_and_id_independent_of_index(self):
        self.manager.set_binding(DEVICE, 'ctrl+1')
        self.manager.close()
        manager = HotkeyManager(self.store.data, self.store, self.keyboard,
                                lambda *event: self.events.append(event))
        manager.restore()  # No enumeration, even while the device is disconnected.
        self.assertEqual(manager.config['bindings'][0]['device_id'], 'a')
        for callback in self.keyboard.handlers.values():
            callback()
        self.assertEqual(manager.resolve_event(*self.events[-1]), 'a')
        manager.set_binding(dict(DEVICE, Index=99), 'ctrl+1')
        self.assertEqual(manager.config['bindings'][0]['device_id'], 'a')

    def test_legacy_not_registered_and_reassociation_preserves_chord(self):
        self.manager.config['unresolved'] = [{'legacy_index': '1', 'hotkey': 'ctrl+1'}]
        self.assertEqual(self.manager.restore(), [])
        self.assertFalse(self.keyboard.handlers)
        self.manager.set_binding(DEVICE, 'ctrl+1', legacy_index='1')
        self.assertEqual(self.store.data['unresolved'], [])
        self.assertEqual(self.trigger(), ['a'])

    def test_restore_failure_preserves_config_and_reports(self):
        self.manager.set_binding(DEVICE, 'ctrl+1')
        self.manager.close()
        self.keyboard.fail = True
        errors = self.manager.restore()
        self.assertTrue(errors)
        self.assertEqual(len(self.manager.config['bindings']), 1)

    def test_queued_callback_of_replaced_or_removed_binding_is_inert(self):
        self.manager.set_binding(DEVICE, 'ctrl+1')
        old = next(iter(self.keyboard.handlers.values()))
        old()
        self.manager.set_binding(DEVICE, 'ctrl+2')
        self.assertIsNone(self.manager.resolve_event(*self.events.pop()))
        self.manager.remove('a')
        old()
        self.assertIsNone(self.manager.resolve_event(*self.events.pop()))

    def test_remove_failure_leaves_callback_inert_and_reports_cleanup(self):
        self.manager.set_binding(DEVICE, 'ctrl+1')
        self.keyboard.remove_hotkey = lambda handle: (_ for _ in ()).throw(OSError('failed'))
        self.manager.remove('a')
        self.assertEqual(self.trigger(), [None])
        self.assertEqual(self.store.data['bindings'], [])
        self.assertIn('cleanup', self.manager.errors)

    def test_conflicting_restored_bindings_are_not_activated(self):
        self.manager.config['bindings'] = [
            {'device_id': key, 'name': 'Same', 'type': 'Playback', 'hotkey': 'ctrl+1'}
            for key in ('a', 'b')]
        self.assertEqual(len(self.manager.restore()), 2)
        self.assertFalse(self.keyboard.handlers)
        self.assertEqual(len(self.manager.config['bindings']), 2)


if __name__ == '__main__':
    unittest.main()
