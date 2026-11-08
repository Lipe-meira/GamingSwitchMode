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

import ctypes
from ctypes import wintypes


CONFIG_FILE = "audio_switcher_config.json"


# Código de erro do Windows para recurso já existente
ERROR_ALREADY_EXISTS = 183

def garantir_instancia_unica(nome_mutex: str):
    kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)
    kernel32.CreateMutexW.argtypes = (ctypes.c_void_p, wintypes.BOOL, wintypes.LPCWSTR)
    kernel32.CreateMutexW.restype = wintypes.HANDLE
    kernel32.CloseHandle.argtypes = (wintypes.HANDLE,)
    kernel32.CloseHandle.restype = wintypes.BOOL
    
    # Cria (ou abre) o Mutex nomeado
    # Importante: guarde o handle em uma variável global ou retorne-o
    # para que o garbage collector do Python não o destrua enquanto o app roda.
    mutex = kernel32.CreateMutexW(None, False, nome_mutex)
    ultimo_erro = ctypes.get_last_error()
    if not mutex:
        raise ctypes.WinError(ultimo_erro)
    
    if ultimo_erro == ERROR_ALREADY_EXISTS:
        # Já existe outra instância rodando!
        # Se quiser, pode exibir um messagebox rápido ou apenas sair em silêncio:
        kernel32.CloseHandle(mutex)
        return None
        
    return mutex

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
        messagebox.showerror("Erro", str(error))
        return {}


def trocar_dispositivo(device_id):
    # Re-enumerate on activation so a reconnected endpoint works without restarting.
    def worker():
        try:
            current = audio.listar_dispositivos()
            if device_id not in current:
                events.put(('status', f'Dispositivo indisponivel: {device_name_snapshot}'))
                events.put(('devices', current))
                return
            audio.trocar_dispositivo(device_id)
            events.put(('devices', current))
            events.put(('status', f'Audio alterado para: {current[device_id]["Name"]}'))
        except (RuntimeError, ValueError) as error:
            events.put(('status', f'Erro ao trocar audio: {error}'))
    device_name_snapshot = device_name(device_id)
    # One worker serializes PowerShell operations; no Tk calls from this thread.
    audio_jobs.put(worker)


def atualizar_botao(device_id):
    if device_id not in botoes:
        return

    nome = f'[{device_tag(device_id)}] {device_name(device_id)}'
    if device_id in bindings():
        nome = f"{nome}    [{bindings()[device_id]['hotkey']}]"

    botoes[device_id].config(text=nome)


def atualizar_lista_atalhos():
    for item in lista_atalhos.get_children():
        lista_atalhos.delete(item)

    for device_id, entry in bindings().items():
        estado = 'Disponivel' if device_id in dispositivos else 'Indisponivel'
        if device_id in manager.errors:
            estado += ' / erro no atalho: ' + manager.errors[device_id]
        nome = f'{estado} — [{device_tag(device_id)}] {device_name(device_id)}'
        lista_atalhos.insert('', 'end', iid='id:' + device_id, values=(nome, entry['hotkey']))
    for entry in manager.config['unresolved']:
        nome = f'Legado: indice {entry["legacy_index"]} — confirmar dispositivo'
        lista_atalhos.insert('', 'end', iid='legacy:' + entry['legacy_index'], values=(nome, entry['hotkey']))


def gravar_tecla():
    tecla_var.set("Gravando...")
    btn_gravar.config(state="disabled")
    status_var.set("Pressione a combinacao desejada.")

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
    device_name = dispositivo_var.get()
    hotkey = tecla_var.get().strip()

    if device_name == "Selecione..." or not hotkey or hotkey == "Gravando...":
        messagebox.showerror("Erro", "Selecione um dispositivo e grave um atalho.")
        return

    device_id = device_labels().get(device_name)
    if device_id is None:
        messagebox.showerror("Erro", "Dispositivo nao encontrado.")
        return

    try:
        device = dispositivos.get(device_id)
        if device is None:
            entry = bindings()[device_id]
            device = {'ID': device_id, 'Name': entry['name'], 'Type': entry['type']}
        if editing_legacy is not None:
            if not messagebox.askyesno('Confirmar associacao',
                    f'Associar o atalho legado {hotkey} ao dispositivo {device_name}?\n'
                    'O indice antigo nao comprova a identidade do dispositivo.'):
                return
        manager.set_binding(device, hotkey, legacy_index=editing_legacy)
    except Exception as error:
        messagebox.showerror("Erro", f"Nao foi possivel registrar o atalho: {error}")
        return
    editing_legacy = None
    refresh_views()
    status_var.set(f"Atalho {hotkey} registrado para: {device_name}")


def indice_atalho_selecionado():
    selecionados = lista_atalhos.selection()
    if not selecionados:
        messagebox.showerror("Erro", "Selecione um atalho na lista.")
        return None

    return selecionados[0]


def editar_atalho():
    global editing_legacy
    device_id = indice_atalho_selecionado()
    if device_id is None:
        return

    if device_id.startswith('legacy:'):
        editing_legacy = device_id.removeprefix('legacy:')
        entry = next(x for x in manager.config['unresolved'] if x['legacy_index'] == editing_legacy)
        dispositivo_var.set('Selecione...')
        tecla_var.set(entry['hotkey'])
        status_var.set('Selecione o dispositivo correto e registre para confirmar o atalho legado.')
        return
    editing_legacy = None
    device_id = device_id.removeprefix('id:')
    label = next(label for label, key in device_labels().items() if key == device_id)
    dispositivo_var.set(label)
    tecla_var.set(bindings()[device_id]['hotkey'])
    status_var.set("Atalho carregado para edicao.")


def remover_atalho():
    global editing_legacy
    device_id = indice_atalho_selecionado()
    if device_id is None:
        return

    legacy_index = device_id.removeprefix('legacy:') if device_id.startswith('legacy:') else None
    device_id = device_id.removeprefix('id:')
    nome = f'legado {legacy_index}' if legacy_index else device_name(device_id)
    confirmar = messagebox.askyesno("Remover atalho", f"Remover o atalho de {nome}?")
    if not confirmar:
        return

    try:
        manager.remove(device_id if legacy_index is None else None, legacy_index=legacy_index)
    except Exception as error:
        messagebox.showerror('Erro', f'Nao foi possivel remover o atalho: {error}')
        return
    editing_legacy = None
    refresh_views()
    status_var.set(f"Atalho removido de: {nome}")


def atualizar_lista():
    def worker():
        try:
            events.put(('devices', audio.listar_dispositivos()))
        except RuntimeError as error:
            events.put(('status', f'Erro ao atualizar dispositivos: {error}'))
    audio_jobs.put(worker)
    errors = manager.restore()
    status_var.set('Atualizando dispositivos.' + (' ' + '; '.join(errors) if errors else ''))


def refresh_views():
    for button in botoes.values():
        button.destroy()
    botoes.clear()

    criar_botoes_dispositivos()
    dropdown.config(values=['Selecione...'] + list(device_labels()))
    if dispositivo_var.get() not in device_labels():
        dispositivo_var.set('Selecione...')
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
            status_var.set(args[0])
        elif event == 'devices':
            dispositivos.clear()
            dispositivos.update(args[0])
            refresh_views()
        elif event in ('captured', 'capture_error'):
            tecla_var.set(args[0] if event == 'captured' else '')
            status_var.set(('Atalho capturado: ' if event == 'captured' else 'Erro ao gravar atalho: ') + args[0])
            btn_gravar.config(state='normal')
        elif event == 'show':
            root.deiconify()
            root.lift()
        elif event == 'exit':
            manager.close()
            audio_jobs.put(None)
            root.destroy()
            return
    root.after(50, process_events)


def audio_worker():
    while True:
        job = audio_jobs.get()
        if job is None:
            return
        job()


def hide_window():
    root.withdraw()


def show_window(icon, item):
    events.put(('show',))


def exit_app(icon, item):
    icon.stop()
    events.put(('exit',))


def create_image():
    image = Image.new("RGB", (64, 64), "#111827")
    draw = ImageDraw.Draw(image)
    draw.rectangle((16, 22, 30, 42), fill="#60a5fa")
    draw.polygon([(30, 22), (46, 12), (46, 52), (30, 42)], fill="#93c5fd")
    return image


def setup_tray():
    menu = (
        pystray.MenuItem("Mostrar", show_window, default=True),
        pystray.MenuItem("Sair", exit_app),
    )
    icon = pystray.Icon("audio_switcher", create_image(), "Audio Switcher", menu)
    icon.run()


def criar_botoes_dispositivos():
    if not dispositivos:
        label = tk.Label(aba_audio, text="Nenhum dispositivo de saida encontrado.")
        label.pack(pady=20)
        botoes['empty'] = label
        return

    for device_id in dispositivos:
        btn = tk.Button(
            aba_audio,
            text=device_name(device_id),
            width=56,
            anchor="w",
            command=lambda i=device_id: trocar_dispositivo(i),
        )
        btn.pack(padx=12, pady=5, fill="x")
        botoes[device_id] = btn
        atualizar_botao(device_id)

def main():
    global app_mutex, root, dispositivos, botoes, events, audio_jobs, editing_legacy
    global store, manager, status_var, tecla_var, dispositivo_var, notebook
    global aba_audio, aba_atalhos, dropdown, btn_gravar, lista_atalhos
    # Cria ou obtém o Mutex nomeado único
    app_mutex = garantir_instancia_unica("GamingSwitchMode_AudioSwitcher_UniqueMutex")
    if not app_mutex:
        sys.exit(0)

    root = tk.Tk()
    root.title("Switcher de Audio")
    root.geometry("640x560")

    dispositivos = carregar_dispositivos()
    botoes = {}
    events = queue.Queue()
    audio_jobs = queue.Queue()
    editing_legacy = None
    store = ConfigStore(legacy_paths=[os.path.join(app_dir(), CONFIG_FILE), os.path.join(os.getcwd(), CONFIG_FILE)])
    try:
        config = store.load()
    except (OSError, ValueError, UnicodeError) as error:
        config = empty_config()
        messagebox.showerror('Erro de configuracao', f'{error}\nO arquivo foi preservado; corrija-o e reinicie.')
    manager = HotkeyManager(config, store, keyboard, lambda *args: events.put(('activate', *args)))

    status_var = tk.StringVar(value="Pronto.")
    tecla_var = tk.StringVar()
    dispositivo_var = tk.StringVar(value="Selecione...")

    notebook = ttk.Notebook(root)
    notebook.pack(expand=True, fill="both")

    aba_audio = ttk.Frame(notebook)
    aba_atalhos = ttk.Frame(notebook)
    notebook.add(aba_audio, text="Audio")
    notebook.add(aba_atalhos, text="Atalhos")

    criar_botoes_dispositivos()
    tk.Button(aba_audio, text="Atualizar lista", command=atualizar_lista).pack(pady=12)

    ttk.Label(aba_atalhos, text="Dispositivo").pack(pady=(20, 5))
    dropdown = ttk.Combobox(
        aba_atalhos,
        textvariable=dispositivo_var,
        values=["Selecione..."] + list(device_labels()),
        state="readonly",
        width=58,
    )
    dropdown.pack(pady=5)

    ttk.Label(aba_atalhos, text="Atalho").pack(pady=(16, 5))
    entrada_tecla = ttk.Entry(aba_atalhos, textvariable=tecla_var, width=34, state="readonly")
    entrada_tecla.pack(pady=5)

    btn_gravar = ttk.Button(aba_atalhos, text="Gravar atalho", command=gravar_tecla)
    btn_gravar.pack(pady=8)

    ttk.Button(aba_atalhos, text="Registrar atalho", command=registrar_atalho).pack(pady=8)

    ttk.Label(aba_atalhos, text="Atalhos registrados").pack(pady=(18, 5))
    lista_frame = ttk.Frame(aba_atalhos)
    lista_frame.pack(padx=12, pady=5, fill="both", expand=True)

    lista_atalhos = ttk.Treeview(
        lista_frame,
        columns=("dispositivo", "atalho"),
        show="headings",
        height=6,
        selectmode="browse",
    )
    lista_atalhos.heading("dispositivo", text="Dispositivo")
    lista_atalhos.heading("atalho", text="Atalho")
    lista_atalhos.column("dispositivo", width=360, anchor="w")
    lista_atalhos.column("atalho", width=120, anchor="center")
    lista_atalhos.pack(side="left", fill="both", expand=True)
    lista_atalhos.bind("<Double-1>", lambda event: editar_atalho())

    scroll_atalhos = ttk.Scrollbar(lista_frame, orient="vertical", command=lista_atalhos.yview)
    scroll_atalhos.pack(side="right", fill="y")
    lista_atalhos.configure(yscrollcommand=scroll_atalhos.set)

    acoes_frame = ttk.Frame(aba_atalhos)
    acoes_frame.pack(pady=(4, 12))
    ttk.Button(acoes_frame, text="Editar selecionado", command=editar_atalho).pack(side="left", padx=5)
    ttk.Button(acoes_frame, text="Remover selecionado", command=remover_atalho).pack(side="left", padx=5)

    ttk.Label(root, textvariable=status_var, anchor="w").pack(side="bottom", fill="x", padx=8, pady=6)

    errors = manager.restore()
    atualizar_lista_atalhos()
    if config['unresolved']:
        status_var.set('Atalhos legados pendentes: selecione e edite para confirmar o dispositivo.')
    if store.warnings or errors:
        messagebox.showwarning('Configuracoes e atalhos', '\n'.join(store.warnings + errors))
    threading.Thread(target=audio_worker, daemon=True).start()
    root.after(50, process_events)

    root.protocol("WM_DELETE_WINDOW", hide_window)

    tray_thread = threading.Thread(target=setup_tray, daemon=True)
    tray_thread.start()

    root.mainloop()


if __name__ == "__main__":
    main()
