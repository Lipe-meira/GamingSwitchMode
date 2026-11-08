"""Opt-in Windows integration: python tests/windows_smoke.py

Uses a temporary configuration, F23/F24 chords and the current playback
endpoint. By default injects callback events into the queue; --send-input tries
real synthetic keystrokes (some remote/isolated desktops cannot deliver them).
Restores the previous communication endpoint in finally. Requires a
Windows desktop session; not part of the hardware-independent unit suite.
"""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import traceback
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import audio
import application as module
import pystray
import keyboard
from tkinter import messagebox
ui = module.ApplicationController()
from configuration import ConfigStore


def send_input(chord):
    keyboard.send(chord)


def main():
    playback = json.loads(audio._run('Get-AudioDevice -Playback | Select-Object ID | ConvertTo-Json'))['ID']
    communication = json.loads(audio._run('Get-AudioDevice -PlaybackCommunication | Select-Object ID | ConvertTo-Json'))['ID']
    original_switch = audio.trocar_dispositivo
    original_loop = module.tk.Tk.mainloop
    original_icon = pystray.Icon
    icons, switched, failures = [], [], []
    phase = 0
    deadline = time.monotonic() + 25

    def icon_factory(*args, **kwargs):
        icon = original_icon(*args, **kwargs)
        icons.append(icon)
        return icon

    def switch(device_id):
        original_switch(device_id)
        switched.append(device_id)

    def fail_dialog(*args, **kwargs):
        raise AssertionError(str(args))

    def activate(chord):
        if '--send-input' in sys.argv:
            send_input(chord)
        else:
            ui.manager.enqueue(playback, ui.manager.tokens[playback])

    def finish():
        if icons:
            icons[0].stop()
        ui.events.put(('exit',))

    def check():
        nonlocal phase
        try:
            if time.monotonic() > deadline:
                raise AssertionError(f'Timed out at phase {phase}: {ui.window.status_var.get()}')
            if phase == 0 and icons and icons[0].visible:
                result = subprocess.run([sys.executable, '-c',
                    "import windows_instance as u; assert u.garantir_instancia_unica('GamingSwitchMode_AudioSwitcher_UniqueMutex') is None"],
                    capture_output=True, text=True, timeout=5)
                assert result.returncode == 0, result.stderr
                label = next(k for k, v in ui.device_labels().items() if v == playback)
                ui.window.dispositivo_var.set(label)
                ui.window.tecla_var.set('ctrl+alt+shift+f24')
                ui.registrar_atalho()
                assert ui.manager.config['bindings'][0]['device_id'] == playback
                ui.hide_window()
                assert ui.window.root.state() == 'withdrawn'
                ui.window.root.after(500, lambda: activate('ctrl+alt+shift+f24'))
                phase = 1
            elif phase == 1 and len(switched) == 1:
                ui.window.lista_atalhos.selection_set('id:' + playback)
                ui.editar_atalho()
                ui.window.tecla_var.set('ctrl+alt+shift+f23')
                ui.registrar_atalho()
                assert ConfigStore(ui.store.path).load() == ui.manager.config
                ui.manager.close()
                assert not ui.manager.restore()
                ui.window.root.after(500, lambda: activate('ctrl+alt+shift+f23'))
                phase = 2
            elif phase == 2 and len(switched) == 2:
                assert switched == [playback, playback]
                ui.window.lista_atalhos.selection_set('id:' + playback)
                ui.remover_atalho()
                assert not ui.manager.config['bindings']
                assert not ui.manager.handles
                ui.manager.config['unresolved'] = [{'legacy_index': '99', 'hotkey': 'ctrl+alt+shift+f24'}]
                ui.store.save(ui.manager.config)
                ui.refresh_views()
                ui.window.lista_atalhos.selection_set('legacy:99')
                ui.editar_atalho()
                assert ui.window.tecla_var.get() == 'ctrl+alt+shift+f24'
                ui.window.dispositivo_var.set(next(k for k, v in ui.device_labels().items() if v == playback))
                ui.registrar_atalho()
                assert not ui.manager.config['unresolved']
                ui.show_window(None, None)
                phase = 3
            elif phase == 3 and ui.window.root.state() == 'normal':
                for parameter in ('Playback', 'PlaybackCommunication'):
                    current = json.loads(audio._run(f'Get-AudioDevice -{parameter} | Select-Object ID | ConvertTo-Json'))
                    assert current['ID'] == playback, current
                mode = 'synthetic global keystrokes' if '--send-input' in sys.argv else 'queued callback simulation'
                print(f'PASS: real Tk, tray, single instance, hook registration/edit/remove/restore, legacy confirmation, ID switch; activation: {mode}')
                finish()
                return
        except BaseException:
            failures.append(traceback.format_exc())
            finish()
            return
        ui.window.root.after(100, check)

    def loop(root):
        root.withdraw()
        root.after(100, check)
        original_loop(root)

    try:
        with tempfile.TemporaryDirectory(prefix='gsm-smoke-') as directory:
            store = ConfigStore(Path(directory) / 'config.json')
            with patch.object(module, 'ConfigStore', return_value=store), \
                    patch.object(module.tk.Tk, 'mainloop', loop), \
                    patch.object(pystray, 'Icon', side_effect=icon_factory), \
                    patch.object(audio, 'trocar_dispositivo', side_effect=switch), \
                    patch.object(messagebox, 'showerror', side_effect=fail_dialog), \
                    patch.object(messagebox, 'showwarning', side_effect=fail_dialog), \
                    patch.object(messagebox, 'askyesno', return_value=True):
                ui.run()
            if failures:
                raise AssertionError('\n'.join(failures))
    finally:
        if ui.manager is not None:
            ui.manager.close()
        if icons:
            icons[0].stop()
        # Preserve both original defaults even when the integration assertion fails.
        original_switch(playback)
        if communication != playback:
            literal = communication.replace("'", "''")
            audio._run(f"Set-AudioDevice -ID '{literal}' -CommunicationOnly | Out-Null")


if __name__ == '__main__':
    main()
