import os
import queue
import sys
import threading
import tkinter as tk

import keyboard

import audio
from configuration import ConfigStore, empty_config
from hotkeys import HotkeyManager
from system_tray import SystemTray
from audio_service import AudioService
from main_window import MainWindow

from windows_instance import garantir_instancia_unica, liberar_mutex


CONFIG_FILE = "audio_switcher_config.json"


def app_dir():
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


class ApplicationController:
    def __init__(self):
        self.app_mutex = None
        self.dispositivos = {}
        self.events = queue.Queue()
        self.audio_jobs = queue.Queue()
        self.editing_legacy = None
        self.store = None
        self.manager = None
        self.window = None
        self.tray = None
        self.worker_thread = None
        self.tray_thread = None
        self.stopping = False

    def shutdown(self):
        if self.stopping:
            return
        self.stopping = True
        try:
            if self.manager is not None:
                self.manager.close()
        finally:
            self.audio_jobs.put(None)
            try:
                if self.tray is not None:
                    self.tray.stop()
            finally:
                try:
                    if self.window is not None:
                        self.window.destroy()
                    elif getattr(self, "root", None) is not None:
                        self.root.destroy()
                finally:
                    if self.app_mutex:
                        handle, self.app_mutex = self.app_mutex, None
                        liberar_mutex(handle)

    def bindings(self):
        return {x['device_id']: x for x in self.manager.config['bindings']}


    def device_name(self, device_id):
        device = self.dispositivos.get(device_id) or self.bindings().get(device_id, {})
        return device.get('Name', device.get('name', 'Dispositivo desconhecido'))


    def device_labels(self):
        # A unique ID suffix comes first so even long duplicate names are readable.
        devices = dict(self.dispositivos)
        for key, entry in self.bindings().items():
            devices.setdefault(key, {'Name': entry['name'] + ' (indisponivel)'})
        return {f"[{self.device_tag(key)}] {entry['Name']}": key for key, entry in devices.items()}


    def device_tag(self, device_id):
        ids = set(self.dispositivos) | set(self.bindings())
        for length in range(min(8, len(device_id)), len(device_id) + 1):
            suffix = device_id[-length:]
            if sum(key.endswith(suffix) for key in ids) == 1:
                return suffix
        return device_id


    def carregar_dispositivos(self):
        try:
            return audio.listar_dispositivos("Playback")
        except RuntimeError as error:
            MainWindow.show_error("Erro", str(error))
            return {}


    def trocar_dispositivo(self, device_id):
        self.window.set_status('Alterando dispositivo de áudio…')
        device_name_snapshot = self.device_name(device_id)
        service = AudioService(audio, self.events)
        self.audio_jobs.put(lambda: service.activate(device_id, device_name_snapshot))


    def atualizar_lista_atalhos(self):
        rows = []
        for device_id, entry in self.bindings().items():
            estado = 'Disponivel' if device_id in self.dispositivos else 'Indisponivel'
            if device_id in self.manager.errors:
                estado += ' / erro no atalho: ' + self.manager.errors[device_id]
            rows.append(('id:' + device_id, f'{estado} — [{self.device_tag(device_id)}] {self.device_name(device_id)}', entry['hotkey']))
        for entry in self.manager.config['unresolved']:
            rows.append(('legacy:' + entry['legacy_index'], f'Legado: indice {entry["legacy_index"]} — confirmar dispositivo', entry['hotkey']))
        self.window.set_hotkeys(rows)


    def gravar_tecla(self):
        self.window.set_recording_state(True, "Gravando...")
        self.window.set_status("Pressione a combinacao desejada.")

        def worker():
            try:
                hotkey = keyboard.read_hotkey(suppress=False)
            except Exception as error:
                self.events.put(('capture_error', str(error)))
                return

            self.events.put(('captured', hotkey))

        threading.Thread(target=worker, daemon=True).start()


    def registrar_atalho(self):
        selected_name = self.window.selected_device()
        hotkey = self.window.hotkey_value().strip()

        if selected_name == "Selecione..." or not hotkey or hotkey == "Gravando...":
            MainWindow.show_error("Erro", "Selecione um dispositivo e grave um atalho.")
            return

        device_id = self.device_labels().get(selected_name)
        if device_id is None:
            MainWindow.show_error("Erro", "Dispositivo nao encontrado.")
            return

        try:
            device = self.dispositivos.get(device_id)
            if device is None:
                entry = self.bindings()[device_id]
                device = {'ID': device_id, 'Name': entry['name'], 'Type': entry['type']}
            if self.editing_legacy is not None:
                if not MainWindow.confirm('Confirmar associacao',
                        f'Associar o atalho legado {hotkey} ao dispositivo {selected_name}?\n'
                        'O indice antigo nao comprova a identidade do dispositivo.'):
                    return
            self.manager.set_binding(device, hotkey, legacy_index=self.editing_legacy)
        except Exception as error:
            MainWindow.show_error("Erro", f"Nao foi possivel registrar o atalho: {error}")
            return
        self.editing_legacy = None
        self.refresh_views()
        self.window.set_status(f"Atalho {hotkey} registrado para: {selected_name}")


    def indice_atalho_selecionado(self):
        selected = self.window.selected_shortcut()
        if not selected:
            MainWindow.show_error("Erro", "Selecione um atalho na lista.")
        return selected


    def editar_atalho(self):
        device_id = self.indice_atalho_selecionado()
        if device_id is None:
            return

        if device_id.startswith('legacy:'):
            self.editing_legacy = device_id.removeprefix('legacy:')
            entry = next(x for x in self.manager.config['unresolved'] if x['legacy_index'] == self.editing_legacy)
            self.window.set_selection('Selecione...', entry['hotkey'])
            self.window.set_status('Selecione o dispositivo correto e registre para confirmar o atalho legado.')
            return
        self.editing_legacy = None
        device_id = device_id.removeprefix('id:')
        label = next(label for label, key in self.device_labels().items() if key == device_id)
        self.window.set_selection(label, self.bindings()[device_id]['hotkey'])
        self.window.set_status("Atalho carregado para edicao.")


    def remover_atalho(self):
        device_id = self.indice_atalho_selecionado()
        if device_id is None:
            return

        legacy_index = device_id.removeprefix('legacy:') if device_id.startswith('legacy:') else None
        device_id = device_id.removeprefix('id:')
        nome = f'legado {legacy_index}' if legacy_index else self.device_name(device_id)
        confirmar = MainWindow.confirm("Remover atalho", f"Remover o atalho de {nome}?")
        if not confirmar:
            return

        try:
            self.manager.remove(device_id if legacy_index is None else None, legacy_index=legacy_index)
        except Exception as error:
            MainWindow.show_error('Erro', f'Nao foi possivel remover o atalho: {error}')
            return
        self.editing_legacy = None
        self.refresh_views()
        self.window.set_status(f"Atalho removido de: {nome}")


    def atualizar_lista(self):
        self.audio_jobs.put(AudioService(audio, self.events).refresh)
        errors = self.manager.restore()
        self.window.set_status('Atualizando dispositivos.' + (' ' + '; '.join(errors) if errors else ''))


    def refresh_views(self):
        rows = []
        for device_id in self.dispositivos:
            text = f'[{self.device_tag(device_id)}] {self.device_name(device_id)}'
            if device_id in self.bindings():
                text += f"    [{self.bindings()[device_id]['hotkey']}]"
            rows.append((device_id, text))
        self.window.set_devices(rows, self.device_labels())
        self.atualizar_lista_atalhos()


    def process_events(self):
        if self.stopping:
            return
        for _ in range(100):
            try:
                event, *args = self.events.get_nowait()
            except queue.Empty:
                break
            if event == 'activate':
                device_id = self.manager.resolve_event(*args)
                if device_id:
                    self.trocar_dispositivo(device_id)
            elif event == 'status':
                self.window.set_status(args[0])
            elif event == 'devices':
                self.dispositivos.clear()
                self.dispositivos.update(args[0])
                self.refresh_views()
            elif event in ('captured', 'capture_error'):
                self.window.set_recording_state(False, args[0] if event == 'captured' else '')
                self.window.set_status(('Atalho capturado: ' if event == 'captured' else 'Erro ao gravar atalho: ') + args[0])
            elif event == 'show':
                self.window.show()
            elif event == 'tray_failed':
                self.window.show()
                self.window.set_status(f'Bandeja indisponivel: {args[0]}')
            elif event == 'exit':
                self.shutdown()
                return
        self.window.schedule(50, self.process_events)


    def audio_worker(self):
        while True:
            job = self.audio_jobs.get()
            if job is None:
                return
            job()


    def hide_window(self):
        if self.stopping:
            return
        if self.tray is not None and self.tray.is_operational():
            self.window.hide()
        else:
            self.window.set_status('Bandeja indisponivel; janela mantida aberta.')
            if MainWindow.confirm('Bandeja indisponivel',
                    'A bandeja ainda nao esta disponivel ou falhou.\n'
                    'Deseja encerrar o aplicativo?\n'
                    'Selecione Nao para manter a janela aberta e aguardar.'):
                self.shutdown()


    def show_window(self, icon, item):
        SystemTray(self.events).show_window(icon, item)


    def exit_app(self, icon, item):
        SystemTray(self.events).exit_app(icon, item)


    def create_image(self):
        return SystemTray.create_image()


    def setup_tray(self):
        try:
            self.tray.run()
        except Exception as error:
            if not self.stopping:
                self.events.put(('tray_failed', str(error)))
        else:
            if not self.stopping and not self.tray.stop_requested:
                self.events.put(('tray_failed', 'icone encerrado inesperadamente'))


    def run(self):
        try:
            self._run()
        finally:
            self.shutdown()

    def _run(self):
        # Cria ou obtém o Mutex nomeado único
        self.app_mutex = garantir_instancia_unica("GamingSwitchMode_AudioSwitcher_UniqueMutex")
        if not self.app_mutex:
            return

        root = tk.Tk()
        self.root = root
        root.title("Switcher de Audio")
        root.geometry("640x560")

        self.dispositivos = self.carregar_dispositivos()
        self.events = queue.Queue()
        self.audio_jobs = queue.Queue()
        self.editing_legacy = None
        self.store = ConfigStore(legacy_paths=[os.path.join(app_dir(), CONFIG_FILE), os.path.join(os.getcwd(), CONFIG_FILE)])
        try:
            config = self.store.load()
        except (OSError, ValueError, UnicodeError) as error:
            config = empty_config()
            MainWindow.show_error('Erro de configuracao', f'{error}\nO arquivo foi preservado; corrija-o e reinicie.')
        self.manager = HotkeyManager(config, self.store, keyboard, lambda *args: self.events.put(('activate', *args)))

        # The window receives explicit actions; the existing controller retains lifecycle.
        from types import SimpleNamespace
        actions = SimpleNamespace(
            device_labels=self.device_labels, trocar_dispositivo=self.trocar_dispositivo,
            atualizar_lista=self.atualizar_lista, gravar_tecla=self.gravar_tecla,
            registrar_atalho=self.registrar_atalho, editar_atalho=self.editar_atalho,
            remover_atalho=self.remover_atalho)
        self.window = MainWindow(root, actions)
        self.refresh_views()

        errors = self.manager.restore()
        self.atualizar_lista_atalhos()
        if config['unresolved']:
            self.window.set_status('Atalhos legados pendentes: selecione e edite para confirmar o dispositivo.')
        if self.store.warnings or errors:
            MainWindow.show_warning('Configuracoes e atalhos', '\n'.join(self.store.warnings + errors))
        self.worker_thread = threading.Thread(target=self.audio_worker, daemon=True)
        self.worker_thread.start()
        self.window.schedule(50, self.process_events)

        self.window.on_close(self.hide_window)

        self.tray = SystemTray(self.events)
        self.tray_thread = threading.Thread(target=self.setup_tray, daemon=True)
        self.tray_thread.start()

        try:
            self.window.run()
        finally:
            self.shutdown()
