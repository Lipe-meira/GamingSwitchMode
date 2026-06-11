import json
import os
import sys
import threading
import tkinter as tk
from tkinter import messagebox, ttk

import keyboard
import pystray
from PIL import Image, ImageDraw

import audio


CONFIG_FILE = "audio_switcher_config.json"


def app_dir():
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


CONFIG_PATH = os.path.join(app_dir(), CONFIG_FILE)


def load_hotkeys():
    if not os.path.exists(CONFIG_PATH):
        return {}

    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as config:
            data = json.load(config)
    except (json.JSONDecodeError, OSError):
        return {}

    if not isinstance(data, dict):
        return {}

    return {str(index): str(hotkey) for index, hotkey in data.items() if hotkey}


def save_hotkeys():
    try:
        with open(CONFIG_PATH, "w", encoding="utf-8") as config:
            json.dump(atalhos, config, indent=4, ensure_ascii=False)
    except OSError as error:
        status_var.set(f"Erro ao salvar configuracoes: {error}")


def carregar_dispositivos():
    try:
        return audio.listar_dispositivos("Playback")
    except RuntimeError as error:
        messagebox.showerror("Erro", str(error))
        return {}


def trocar_dispositivo(index):
    nome = dispositivos.get(index, "dispositivo")
    try:
        audio.trocar_dispositivo(index)
    except RuntimeError as error:
        root.after(0, status_var.set, f"Erro ao trocar audio: {error}")
        return

    root.after(0, status_var.set, f"Audio alterado para: {nome}")


def atualizar_botao(index):
    if index not in botoes:
        return

    nome = dispositivos.get(index, "Dispositivo desconhecido")
    if index in atalhos:
        nome = f"{nome}    [{atalhos[index]}]"

    botoes[index].config(text=nome)


def atualizar_lista_atalhos():
    for item in lista_atalhos.get_children():
        lista_atalhos.delete(item)

    def ordenar_por_indice(item):
        index = item[0]
        return int(index) if index.isdigit() else 9999

    for index, hotkey in sorted(atalhos.items(), key=ordenar_por_indice):
        nome = dispositivos.get(index, "Dispositivo nao encontrado")
        lista_atalhos.insert("", "end", iid=index, values=(nome, hotkey))


def registrar_hotkey(index, hotkey):
    if index in hotkey_handles:
        keyboard.remove_hotkey(hotkey_handles.pop(index))

    for outro_index, outro_hotkey in list(atalhos.items()):
        if outro_index != index and outro_hotkey == hotkey:
            if outro_index in hotkey_handles:
                keyboard.remove_hotkey(hotkey_handles.pop(outro_index))
            atalhos.pop(outro_index)
            atualizar_botao(outro_index)

    hotkey_handles[index] = keyboard.add_hotkey(hotkey, lambda i=index: trocar_dispositivo(i))
    atalhos[index] = hotkey
    atualizar_botao(index)
    atualizar_lista_atalhos()
    save_hotkeys()


def gravar_tecla():
    tecla_var.set("Gravando...")
    btn_gravar.config(state="disabled")
    status_var.set("Pressione a combinacao desejada.")

    def worker():
        try:
            hotkey = keyboard.read_hotkey(suppress=False)
        except Exception as error:
            root.after(0, status_var.set, f"Erro ao gravar atalho: {error}")
            root.after(0, btn_gravar.config, {"state": "normal"})
            return

        root.after(0, tecla_var.set, hotkey)
        root.after(0, status_var.set, f"Atalho capturado: {hotkey}")
        root.after(0, btn_gravar.config, {"state": "normal"})

    threading.Thread(target=worker, daemon=True).start()


def registrar_atalho():
    device_name = dispositivo_var.get()
    hotkey = tecla_var.get().strip()

    if device_name == "Selecione..." or not hotkey or hotkey == "Gravando...":
        messagebox.showerror("Erro", "Selecione um dispositivo e grave um atalho.")
        return

    index = next((idx for idx, nome in dispositivos.items() if nome == device_name), None)
    if index is None:
        messagebox.showerror("Erro", "Dispositivo nao encontrado.")
        return

    try:
        registrar_hotkey(index, hotkey)
    except Exception as error:
        messagebox.showerror("Erro", f"Nao foi possivel registrar o atalho: {error}")
        return

    status_var.set(f"Atalho {hotkey} registrado para: {device_name}")


def indice_atalho_selecionado():
    selecionados = lista_atalhos.selection()
    if not selecionados:
        messagebox.showerror("Erro", "Selecione um atalho na lista.")
        return None

    return selecionados[0]


def editar_atalho():
    index = indice_atalho_selecionado()
    if index is None:
        return

    nome = dispositivos.get(index)
    if not nome:
        messagebox.showerror("Erro", "Esse dispositivo nao esta disponivel agora.")
        return

    dispositivo_var.set(nome)
    tecla_var.set(atalhos.get(index, ""))
    status_var.set("Atalho carregado para edicao.")


def remover_atalho():
    index = indice_atalho_selecionado()
    if index is None:
        return

    nome = dispositivos.get(index, "dispositivo")
    confirmar = messagebox.askyesno("Remover atalho", f"Remover o atalho de {nome}?")
    if not confirmar:
        return

    if index in hotkey_handles:
        keyboard.remove_hotkey(hotkey_handles.pop(index))

    atalhos.pop(index, None)
    atualizar_botao(index)
    atualizar_lista_atalhos()
    save_hotkeys()
    status_var.set(f"Atalho removido de: {nome}")


def atualizar_lista():
    dispositivos.clear()
    dispositivos.update(carregar_dispositivos())

    for button in botoes.values():
        button.destroy()
    botoes.clear()

    criar_botoes_dispositivos()
    dropdown.config(values=["Selecione..."] + list(dispositivos.values()))
    dispositivo_var.set("Selecione...")
    atualizar_lista_atalhos()
    status_var.set("Lista de dispositivos atualizada.")


def hide_window():
    root.withdraw()


def show_window(icon, item):
    root.after(0, root.deiconify)
    root.after(0, root.lift)


def exit_app(icon, item):
    save_hotkeys()
    icon.stop()
    root.after(0, root.destroy)


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
        tk.Label(aba_audio, text="Nenhum dispositivo de saida encontrado.").pack(pady=20)
        return

    for idx, nome in dispositivos.items():
        btn = tk.Button(
            aba_audio,
            text=nome,
            width=56,
            anchor="w",
            command=lambda i=idx: trocar_dispositivo(i),
        )
        btn.pack(padx=12, pady=5, fill="x")
        botoes[idx] = btn
        atualizar_botao(idx)


root = tk.Tk()
root.title("Switcher de Audio")
root.geometry("640x560")

dispositivos = carregar_dispositivos()
botoes = {}
atalhos = load_hotkeys()
hotkey_handles = {}

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
    values=["Selecione..."] + list(dispositivos.values()),
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

for index, hotkey in list(atalhos.items()):
    if index in dispositivos:
        try:
            registrar_hotkey(index, hotkey)
        except Exception:
            atalhos.pop(index, None)
    else:
        atalhos.pop(index, None)

save_hotkeys()
atualizar_lista_atalhos()

root.protocol("WM_DELETE_WINDOW", hide_window)

tray_thread = threading.Thread(target=setup_tray, daemon=True)
tray_thread.start()

root.mainloop()
