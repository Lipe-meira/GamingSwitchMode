# audioSwitcher.py - VERSÃO FINAL

import tkinter as tk
from tkinter import ttk, messagebox
import audio
import keyboard
import threading
import pystray
from PIL import Image
import json
import os

# --- Nome do arquivo para salvar as configurações ---
CONFIG_FILE = 'audio_switcher_config.json'


# --- Início da Configuração da Janela ---
root = tk.Tk()
root.title("Switcher de Áudio")
root.geometry("500x400")

notebook = ttk.Notebook(root)
notebook.pack(expand=True, fill='both')

aba_audio = ttk.Frame(notebook)
aba_outros = ttk.Frame(notebook)
notebook.add(aba_audio, text="Áudio")
notebook.add(aba_outros, text="Outros")


# --- Funções para Salvar e Carregar Atalhos ---

def save_hotkeys():
    """Salva o dicionário 'atalhos' no arquivo de configuração JSON."""
    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump(atalhos, f, indent=4)
    except Exception as e:
        print(f"Erro ao salvar configurações: {e}")

def load_hotkeys():
    """Carrega os atalhos do arquivo JSON se ele existir."""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            # Se o arquivo estiver corrompido ou for removido, retorna um dicionário vazio.
            return {}
    return {}


# --- Variáveis Globais ---
dispositivos = audio.listar_dispositivos()
botoes = {}
# Carrega os atalhos salvos ao iniciar o programa
atalhos = load_hotkeys()


# --- Funções do Programa ---

def atualizar_botao(index):
    if index in botoes:
        nome = dispositivos.get(index, "Dispositivo Desconhecido")
        if index in atalhos:
            nome += f" ({atalhos[index]})"
        botoes[index].config(text=nome)

def gravar_tecla():
    messagebox.showinfo("Atenção", "Pressione as teclas desejadas e depois 'Enter' para finalizar.")
    teclas = set()
    tecla_var.set("")
    
    def registrar(event):
        if event.name == "enter":
            keyboard.unhook_all()
            if not teclas: # Se o usuário não pressionou nada, limpa
                tecla_var.set("")
                return
            combo = "+".join(sorted(list(teclas)))
            tecla_var.set(combo)
            messagebox.showinfo("Tecla registrada", f"Atalho selecionado: {combo}")
        else:
            # Ignora teclas modificadoras sozinhas
            if event.name not in ['shift', 'ctrl', 'alt', 'cmd']:
                teclas.add(event.name)
                tecla_var.set("+".join(sorted(list(teclas))))

    keyboard.on_press(registrar)

def registrar_atalho():
    device_name = dispositivo_var.get()
    hotkey = tecla_var.get()
    
    if device_name == "Selecione..." or not hotkey:
        messagebox.showerror("Erro", "Selecione um dispositivo e grave uma tecla.")
        return

    index = None
    for idx, nome in dispositivos.items():
        if nome == device_name:
            index = idx
            break
    
    if index is None:
        messagebox.showerror("Erro", "Dispositivo não encontrado.")
        return

    # Função de callback que será chamada pelo atalho
    def create_callback(i):
        return lambda: audio.trocar_dispositivo(i)
    
    # Remove o atalho antigo se houver, para evitar conflitos
    if index in atalhos:
        try:
            keyboard.remove_hotkey(atalhos[index])
        except KeyError:
            pass

    # Adiciona o novo atalho
    atalhos[index] = hotkey
    keyboard.add_hotkey(hotkey, create_callback(index))
    
    # Atualiza a interface e salva as mudanças
    atualizar_botao(index)
    save_hotkeys()
    
    messagebox.showinfo("Sucesso", f"Atalho '{hotkey}' registrado para '{device_name}'")


# --- Funções para Gerenciar a Bandeja do Sistema ---

def hide_window():
    root.withdraw()

def show_window(icon, item):
    root.deiconify()
    root.lift()
    root.focus_force()

def exit_app(icon, item):
    save_hotkeys() # Garante que tudo seja salvo ao sair
    icon.stop()
    root.destroy()

def create_image():
    width = 64
    height = 64
    image = Image.new("RGB", (width, height), "black")
    # Você pode desenhar um ícone melhor aqui se quiser
    from PIL import ImageDraw
    dc = ImageDraw.Draw(image)
    dc.rectangle((width // 4, height // 4, width * 3 // 4, height * 3 // 4), fill="blue")
    return image

def setup_tray():
    image = create_image()
    menu = (pystray.MenuItem('Mostrar', show_window, default=True),
            pystray.MenuItem('Sair', exit_app))
    icon = pystray.Icon("audio_switcher", image, "Audio Switcher", menu)
    icon.run()


# --- Construção da Interface ---

# Aba Áudio
for idx, nome in dispositivos.items():
    btn = tk.Button(aba_audio, text=nome, width=40, command=lambda i=idx: audio.trocar_dispositivo(i))
    btn.pack(pady=5)
    botoes[idx] = btn

# Aba Outros
tk.Label(aba_outros, text="1. Selecione o dispositivo:").pack(pady=5)
dispositivo_var = tk.StringVar()
dropdown = ttk.Combobox(
    aba_outros, textvariable=dispositivo_var, values=["Selecione..."] + list(dispositivos.values())
)
dropdown.current(0)
dropdown.pack(pady=5)

tk.Label(aba_outros, text="2. Grave o atalho desejado:").pack(pady=5)
tecla_var = tk.StringVar()
entrada_tecla = tk.Entry(aba_outros, textvariable=tecla_var, font=("Arial", 12), width=30, state="readonly")
entrada_tecla.pack(pady=5)

btn_gravar = tk.Button(aba_outros, text="Gravar Tecla", command=gravar_tecla)
btn_gravar.pack(pady=5)

tk.Label(aba_outros, text="3. Registre o atalho:").pack(pady=5)
tk.Button(aba_outros, text="Registrar Atalho", command=registrar_atalho).pack(pady=10)


# --- Lógica Final de Inicialização ---

# Registra os atalhos que foram carregados do arquivo
for index, hotkey in atalhos.items():
    if index in dispositivos:
        def create_callback(i):
            return lambda: audio.trocar_dispositivo(i)
        keyboard.add_hotkey(hotkey, create_callback(index))
        # Atualiza o texto do botão para mostrar o atalho salvo
        atualizar_botao(index)

# Intercepta o 'X' da janela para apenas escondê-la
root.protocol('WM_DELETE_WINDOW', hide_window)

# Inicia o ícone da bandeja em uma thread separada
tray_thread = threading.Thread(target=setup_tray, daemon=True)
tray_thread.start()

# Inicia a interface gráfica
root.mainloop()