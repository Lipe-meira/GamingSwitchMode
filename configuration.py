"""Versioned user configuration. No device enumeration is trusted during migration."""
from copy import deepcopy
import json
import os
from pathlib import Path
import shutil
import tempfile
from uuid import uuid4


def empty_config():
    return {'schema_version': 1, 'bindings': [], 'unresolved': []}


def validate_config(data):
    if not isinstance(data, dict) or type(data.get('schema_version')) is not int or data['schema_version'] != 1:
        raise ValueError('Versao de configuracao invalida ou nao suportada.')
    ids = set()
    for field in ('bindings', 'unresolved'):
        if not isinstance(data.get(field), list):
            raise ValueError(f'Lista {field} invalida.')
        for entry in data[field]:
            required = ('device_id', 'name', 'type', 'hotkey') if field == 'bindings' else ('legacy_index', 'hotkey')
            if not isinstance(entry, dict) or not all(isinstance(entry.get(k), str) and entry[k].strip() for k in required):
                raise ValueError('Associacao de atalho invalida.')
            key = (field, entry[required[0]])
            if key in ids:
                raise ValueError('Associacao duplicada.')
            ids.add(key)
    return deepcopy(data)


def is_legacy(data):
    return isinstance(data, dict) and 'schema_version' not in data and all(
        isinstance(k, str) and k.isdigit() and isinstance(v, str) and v.strip()
        for k, v in data.items()
    )


def user_config_path():
    appdata = os.environ.get('APPDATA')
    return (Path(appdata) if appdata else Path.home() / 'AppData' / 'Roaming') / 'GamingSwitchMode' / 'config.json'


class ConfigStore:
    def __init__(self, path=None, legacy_paths=()):
        self.path = Path(path) if path is not None else user_config_path()
        self.legacy_paths = list(dict.fromkeys(Path(p) for p in legacy_paths))
        self.warnings = []
        self.blocked = False

    @property
    def backup(self):
        return Path(str(self.path) + '.bak')

    @staticmethod
    def _read(path):
        return json.loads(path.read_text(encoding='utf-8-sig'))

    def load(self):
        self.blocked = True
        missing = object()
        try:
            data = self._read(self.path)
        except FileNotFoundError:
            if self.backup.exists():
                data = validate_config(self._read(self.backup))
                self.warnings.append('Configuracao ausente; recuperada do backup.')
                self._write(data)
            else:
                data = missing
        except (ValueError, UnicodeError):
            data = self._recover()
        if data is not missing:
            if is_legacy(data):
                return self._migrate(data, self.path)
            try:
                result = validate_config(data)
            except ValueError:
                # Unknown schemas must never be silently downgraded from a backup.
                raise ValueError(f'Configuracao nao suportada: {self.path}')
            self.blocked = False
            return result
        for source in self.legacy_paths:
            try:
                legacy = self._read(source)
            except FileNotFoundError:
                continue
            if not is_legacy(legacy):
                raise ValueError(f'Configuracao antiga invalida: {source}')
            return self._migrate(legacy, source)
        self.blocked = False
        return empty_config()

    def _recover(self):
        try:
            data = validate_config(self._read(self.backup))
        except (OSError, ValueError, UnicodeError) as error:
            raise ValueError(f'JSON invalido em {self.path}; restaure um backup valido.') from error
        preserved = Path(str(self.path) + '.invalid-' + uuid4().hex)
        shutil.copy2(self.path, preserved)
        self._write(data)
        self.warnings.append(f'Configuracao recuperada do backup. Original preservado: {preserved}')
        return data

    def _migrate(self, legacy, source):
        backup = self.path.parent / 'legacy-original.json.bak'
        original = source.read_bytes()
        # The install directory may be read-only. Back up inside the user directory.
        # Preserve previous originals too if a different source was imported before.
        if backup.exists() and backup.read_bytes() != original:
            backup = self.path.parent / f'legacy-original-{uuid4().hex}.json.bak'
        if not backup.exists():
            self._atomic_bytes(backup, original)
        data = empty_config()
        data['unresolved'] = [dict(legacy_index=k, hotkey=v, source=str(source)) for k, v in legacy.items()]
        data['migration'] = {'source': str(source), 'backup': str(backup), 'from_schema': 0}
        self._write(data)
        self.blocked = False
        return data

    def save(self, data):
        if self.blocked:
            raise ValueError('Configuracao protegida apos falha de leitura. Corrija o arquivo e reinicie.')
        data = validate_config(data)
        if self.path.exists():
            # Validate before touching the backup; never replace a valid backup with corrupt JSON.
            validate_config(self._read(self.path))
            self._atomic_bytes(self.backup, self.path.read_bytes())
        self._write(data)

    def _write(self, data):
        self._atomic_bytes(self.path, (json.dumps(data, indent=2, ensure_ascii=False) + '\n').encode('utf-8'))

    @staticmethod
    def _atomic_bytes(path, content):
        path.parent.mkdir(parents=True, exist_ok=True)
        fd, temporary = tempfile.mkstemp(prefix=path.name + '.', suffix='.tmp', dir=path.parent)
        try:
            with os.fdopen(fd, 'wb') as stream:
                stream.write(content)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, path)
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)
