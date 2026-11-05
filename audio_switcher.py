import os
import queue
import sys
import threading
import tkinter as tk
from tkinter import messagebox, ttk

import keyboard
import pystray
from PIL import Image, ImageDraw

import audio
from configuration import ConfigStore, empty_config
from hotkeys import HotkeyManager
from system_tray import SystemTray
from audio_service import AudioService
from main_window import MainWindow

from windows_instance import garantir_instancia_unica


CONFIG_FILE = "audio_switcher_config.json"


def app_dir():
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def bindings():
    return {x['device_id']: x for x in manager.config['bindings']}


def device_name(device_id):
    device = dispositivos.get(device_id) or bindings().get(device_id, {})
    return device.get('Name', device.get('name', 'Dispositivo desconhecido'))


def device_labels():
    # A unique ID suffix comes first so even long duplicate names are readable.
    devices = dict(dispositivos)
    for key, entry in bindings().items():
        devices.setdefault(key, {'Name': entry['name'] + ' (indisponivel)'})
    return {f"[{device_tag(key)}] {entry['Name']}": key for key, entry in devices.items()}


def device_tag(device_id):
    ids = set(dispositivos) | set(bindings())
    for length in range(min(8, len(device_id)), len(device_id) + 1):
        suffix = device_id[-length:]
        if sum(key.endswith(suffix) for key in ids) == 1:
            return suffix
    return device_id


def carregar_dispositivos():
    try:
        return audio.listar_dispositivos("Playback")
    except RuntimeError as error:
        MainWindow.show_error("Erro", str(error))
        return {}


def trocar_dispositivo(device_id):
    device_name_snapshot = device_name(device_id)
    service = AudioService(audio, events)
    audio_jobs.put(lambda: service.activate(device_id, device_name_snapshot))


def atualizar_lista_atalhos():
    rows = []
    for device_id, entry in bindings().items():
        estado = 'Disponivel' if device_id in dispositivos else 'Indisponivel'
        if device_id in manager.errors:
            estado += ' / erro no atalho: ' + manager.errors[device_id]
        rows.append(('id:' + device_id, f'{estado} — [{device_tag(device_id)}] {device_name(device_id)}', entry['hotkey']))
    for entry in manager.config['unresolved']:
        rows.append(('legacy:' + entry['legacy_index'], f'Legado: indice {entry["legacy_index"]} — confirmar dispositivo', entry['hotkey']))
    window.set_hotkeys(rows)


def gravar_tecla():
    window.set_recording_state(True, "Gravando...")
    window.set_status("Pressione a combinacao desejada.")

    def worker():
        try:
            hotkey = keyboard.read_hotkey(suppress=False)
        except Exception as error:
            events.put(('capture_error', str(error)))
            return

        events.put(('captured', hotkey))

    threading.Thread(target=worker, daemon=True).start()


def registrar_atalho():
    global editing_legacy
    device_name = window.selected_device()
    hotkey = window.hotkey_value().strip()

    if device_name == "Selecione..." or not hotkey or hotkey == "Gravando...":
        MainWindow.show_error("Erro", "Selecione um dispositivo e grave um atalho.")
        return

    device_id = device_labels().get(device_name)
    if device_id is None:
        MainWindow.show_error("Erro", "Dispositivo nao encontrado.")
        return

    try:
        device = dispositivos.get(device_id)
        if device is None:
            entry = bindings()[device_id]
            device = {'ID': device_id, 'Name': entry['name'], 'Type': entry['type']}
        if editing_legacy is not None:
            if not MainWindow.confirm('Confirmar associacao',
                    f'Associar o atalho legado {hotkey} ao dispositivo {device_name}?\n'
                    'O indice antigo nao comprova a identidade do dispositivo.'):
                return
        manager.set_binding(device, hotkey, legacy_index=editing_legacy)
    except Exception as error:
        MainWindow.show_error("Erro", f"Nao foi possivel registrar o atalho: {error}")
        return
    editing_legacy = None
    refresh_views()
    window.set_status(f"Atalho {hotkey} registrado para: {device_name}")


def indice_atalho_selecionado():
    selected = window.selected_shortcut()
    if not selected:
        MainWindow.show_error("Erro", "Selecione um atalho na lista.")
    return selected


def editar_atalho():
    global editing_legacy
    device_id = indice_atalho_selecionado()
    if device_id is None:
        return

    if device_id.startswith('legacy:'):
        editing_legacy = device_id.removeprefix('legacy:')
        entry = next(x for x in manager.config['unresolved'] if x['legacy_index'] == editing_legacy)
        window.set_selection('Selecione...', entry['hotkey'])
        window.set_status('Selecione o dispositivo correto e registre para confirmar o atalho legado.')
        return
    editing_legacy = None
    device_id = device_id.removeprefix('id:')
    label = next(label for label, key in device_labels().items() if key == device_id)
    window.set_selection(label, bindings()[device_id]['hotkey'])
    window.set_status("Atalho carregado para edicao.")


def remover_atalho():
    global editing_legacy
    device_id = indice_atalho_selecionado()
    if device_id is None:
        return

    legacy_index = device_id.removeprefix('legacy:') if device_id.startswith('legacy:') else None
    device_id = device_id.removeprefix('id:')
    nome = f'legado {legacy_index}' if legacy_index else device_name(device_id)
    confirmar = MainWindow.confirm("Remover atalho", f"Remover o atalho de {nome}?")
    if not confirmar:
        return

    try:
        manager.remove(device_id if legacy_index is None else None, legacy_index=legacy_index)
    except Exception as error:
        MainWindow.show_error('Erro', f'Nao foi possivel remover o atalho: {error}')
        return
    editing_legacy = None
    refresh_views()
    window.set_status(f"Atalho removido de: {nome}")


def atualizar_lista():
    audio_jobs.put(AudioService(audio, events).refresh)
    errors = manager.restore()
    window.set_status('Atualizando dispositivos.' + (' ' + '; '.join(errors) if errors else ''))


def refresh_views():
    rows = []
    for device_id in dispositivos:
        text = f'[{device_tag(device_id)}] {device_name(device_id)}'
        if device_id in bindings():
            text += f"    [{bindings()[device_id]['hotkey']}]"
        rows.append((device_id, text))
    window.set_devices(rows, device_labels())
    atualizar_lista_atalhos()


def process_events():
    for _ in range(100):
        try:
            event, *args = events.get_nowait()
        except queue.Empty:
            break
        if event == 'activate':
            device_id = manager.resolve_event(*args)
            if device_id:
                trocar_dispositivo(device_id)
        elif event == 'status':
            window.set_status(args[0])
        elif event == 'devices':
            dispositivos.clear()
            dispositivos.update(args[0])
            refresh_views()
        elif event in ('captured', 'capture_error'):
            window.set_recording_state(False, args[0] if event == 'captured' else '')
            window.set_status(('Atalho capturado: ' if event == 'captured' else 'Erro ao gravar atalho: ') + args[0])
        elif event == 'show':
            window.show()
        elif event == 'exit':
            manager.close()
            audio_jobs.put(None)
            window.destroy()
            return
    window.schedule(50, process_events)


def audio_worker():
    while True:
        job = audio_jobs.get()
        if job is None:
            return
        job()


def hide_window():
    window.hide()


def show_window(icon, item):
    SystemTray(events).show_window(icon, item)


def exit_app(icon, item):
    SystemTray(events).exit_app(icon, item)


def create_image():
    return SystemTray.create_image()


def setup_tray():
    SystemTray(events).run()


def main():
    global app_mutex, dispositivos, events, audio_jobs, editing_legacy
    global store, manager, window
    # Cria ou obtém o Mutex nomeado único
    app_mutex = garantir_instancia_unica("GamingSwitchMode_AudioSwitcher_UniqueMutex")
    if not app_mutex:
        sys.exit(0)

    root = tk.Tk()
    root.title("Switcher de Audio")
    root.geometry("640x560")

    dispositivos = carregar_dispositivos()
    events = queue.Queue()
    audio_jobs = queue.Queue()
    editing_legacy = None
    store = ConfigStore(legacy_paths=[os.path.join(app_dir(), CONFIG_FILE), os.path.join(os.getcwd(), CONFIG_FILE)])
    try:
        config = store.load()
    except (OSError, ValueError, UnicodeError) as error:
        config = empty_config()
        MainWindow.show_error('Erro de configuracao', f'{error}\nO arquivo foi preservado; corrija-o e reinicie.')
    manager = HotkeyManager(config, store, keyboard, lambda *args: events.put(('activate', *args)))

    # The window receives explicit actions; the existing controller retains lifecycle.
    from types import SimpleNamespace
    actions = SimpleNamespace(
        device_labels=device_labels, trocar_dispositivo=trocar_dispositivo,
        atualizar_lista=atualizar_lista, gravar_tecla=gravar_tecla,
        registrar_atalho=registrar_atalho, editar_atalho=editar_atalho,
        remover_atalho=remover_atalho)
    window = MainWindow(root, actions)
    refresh_views()

    errors = manager.restore()
    atualizar_lista_atalhos()
    if config['unresolved']:
        window.set_status('Atalhos legados pendentes: selecione e edite para confirmar o dispositivo.')
    if store.warnings or errors:
        MainWindow.show_warning('Configuracoes e atalhos', '\n'.join(store.warnings + errors))
    threading.Thread(target=audio_worker, daemon=True).start()
    window.schedule(50, process_events)

    window.on_close(hide_window)

    tray_thread = threading.Thread(target=setup_tray, daemon=True)
    tray_thread.start()

    window.run()


if __name__ == "__main__":
    main()
