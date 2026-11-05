"""Hotkey transactions, called only by the Tk main thread.

Hook callbacks only enqueue opaque tokens; they never access Tk or mutable state.
"""
from copy import deepcopy

from configuration import validate_config


class HotkeyManager:
    def __init__(self, config, store, keyboard, enqueue):
        self.config = validate_config(config)
        self.store = store
        self.keyboard = keyboard
        self.enqueue = enqueue
        self.handles = {}
        self.tokens = {}
        self.errors = {}
        self.retired = []

    def _combinations(self, hotkey):
        # The library resolves aliases and modifier order into scan-code chords.
        return tuple(frozenset(tuple(sorted(combo)) for combo in step)
                     for step in self.keyboard.parse_hotkey_combinations(hotkey))

    def _conflict(self, hotkey, device_id=None, legacy_index=None):
        candidate = self._combinations(hotkey)
        entries = [x for x in self.config['bindings'] if x['device_id'] != device_id]
        entries += [x for x in self.config['unresolved'] if x['legacy_index'] != legacy_index]
        for entry in entries:
            try:
                other = self._combinations(entry['hotkey'])
            except (ValueError, KeyError):
                continue  # Invalid saved hotkeys stay visible and editable.
            if len(candidate) == len(other) and all(a & b for a, b in zip(candidate, other)):
                raise ValueError('Combinacao ja associada a outro dispositivo ou atalho pendente.')

    def _register(self, device_id, hotkey):
        token = object()
        handle = self.keyboard.add_hotkey(hotkey, lambda: self.enqueue(device_id, token))
        return handle, token

    def _discard(self, handle):
        try:
            self.keyboard.remove_hotkey(handle)
        except Exception as error:
            # Tokens already invalidate this callback even if the OS hook cannot be removed.
            self.retired.append(handle)
            self.errors['cleanup'] = f'Falha ao liberar registro inativo: {error}'

    def restore(self):
        for entry in self.config['bindings']:
            device_id = entry['device_id']
            if device_id in self.handles:
                continue
            try:
                self._conflict(entry['hotkey'], device_id)
                handle, token = self._register(device_id, entry['hotkey'])
                self.handles[device_id], self.tokens[device_id] = handle, token
                self.errors.pop(device_id, None)
            except Exception as error:
                self.errors[device_id] = str(error)
        return list(self.errors.values())

    def set_binding(self, device, hotkey, legacy_index=None):
        device_id = device['ID']
        self._conflict(hotkey, device_id, legacy_index)
        updated = deepcopy(self.config)
        entry = next((x for x in updated['bindings'] if x['device_id'] == device_id), None)
        previous = deepcopy(entry)
        if entry is None:
            entry = {}
            updated['bindings'].append(entry)
        entry.update(device_id=device_id, name=device['Name'], type=device['Type'], hotkey=hotkey)
        if legacy_index is not None:
            source = next(x for x in updated['unresolved'] if x['legacy_index'] == legacy_index)
            entry['legacy'] = deepcopy(source)
            updated['unresolved'].remove(source)
        # Reuse an identical hook: never accumulate handlers on repeated saves.
        reuse = previous and previous['hotkey'] == hotkey and device_id in self.handles
        new_handle, token = (None, None) if reuse else self._register(device_id, hotkey)
        try:
            self.store.save(updated)
        except Exception:
            if not reuse:
                self._discard(new_handle)
            raise
        old = self.handles.get(device_id)
        self.config = updated
        if not reuse:
            self.handles[device_id], self.tokens[device_id] = new_handle, token
            if old is not None:
                self._discard(old)
        self.errors.pop(device_id, None)

    def remove(self, device_id=None, legacy_index=None):
        updated = deepcopy(self.config)
        if legacy_index is not None:
            updated['unresolved'] = [x for x in updated['unresolved'] if x['legacy_index'] != legacy_index]
        else:
            updated['bindings'] = [x for x in updated['bindings'] if x['device_id'] != device_id]
        self.store.save(updated)
        self.config = updated
        self.tokens.pop(device_id, None)
        self.errors.pop(device_id, None)
        handle = self.handles.pop(device_id, None)
        if handle is not None:
            self._discard(handle)

    def resolve_event(self, device_id, token):
        return device_id if self.tokens.get(device_id) is token else None

    def close(self):
        self.tokens.clear()
        handles = list(self.handles.values()) + self.retired
        self.handles.clear()
        self.retired = []
        for handle in handles:
            self._discard(handle)
