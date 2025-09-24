import tkinter as tk
from tkinter import ttk, messagebox
import audio
import keyboard
import threading

root = tk.Tk()
root.title("Switcher de Áudio")
root.geometry("500x400")

notebook = ttk.Notebook(root)
notebook.pack(expand=True, fill="both")

aba_audio = ttk.Frame(notebook)
aba_outros = ttk.Frame(notebook)
notebook.add(aba_audio, text="Áudio")
notebook.add(aba_outros, text="Outros")

# ---------- Aba Áudio ----------
dispositivos = audio.listar_dispositivos()
atalhos = {}  # índice do dispositivo → tecla registrada
botoes = {}  # índice → botão correspondente


def atualizar_botao(index):
    nome = dispositivos[index]
    if index in atalhos:
        nome += f" ({atalhos[index]})"
    botoes[index].config(text=nome)


def trocar_dispositivo_e_atualizar(index):
    audio.trocar_dispositivo(index)
    atualizar_botao(index)


for idx, nome in dispositivos.items():
    btn = tk.Button(
        aba_audio,
        text=nome,
        width=40,
        command=lambda i=idx: trocar_dispositivo_e_atualizar(i),
    )
    btn.pack(pady=5)
    botoes[idx] = btn

# ---------- Aba Outros ----------
tk.Label(aba_outros, text="Selecione o dispositivo:").pack(pady=5)
dispositivo_var = tk.StringVar()
dropdown = ttk.Combobox(
    aba_outros,
    textvariable=dispositivo_var,
    values=["Selecione..."] + list(dispositivos.values()),
)
dropdown.current(0)
dropdown.pack(pady=5)

# Entry para mostrar o atalho em tempo real
tecla_var = tk.StringVar()
entrada_tecla = tk.Entry(
    aba_outros, textvariable=tecla_var, font=("Arial", 12), width=30
)
entrada_tecla.pack(pady=5)


def gravar_tecla():
    messagebox.showinfo("Atenção", "Pressione as teclas desejadas para o atalho")
    teclas = set()
    tecla_var.set("")

    def registrar(event):
        if event.name == "enter":
            # finaliza a gravação
            combo = "+".join(teclas)
            tecla_var.set(combo)
            messagebox.showinfo("Tecla registrada", f"Atalho selecionado: {combo}")
            keyboard.unhook_all()
        else:
            teclas.add(event.name)
            tecla_var.set("+".join(teclas))  # atualiza a Entry em tempo real

    keyboard.on_press(registrar)


btn_gravar = tk.Button(aba_outros, text="Gravar Tecla", command=gravar_tecla)
btn_gravar.pack(pady=5)


def registrar_atalho():
    device_name = dispositivo_var.get()
    hotkey = tecla_var.get()

    if device_name == "Selecione..." or not hotkey:
        messagebox.showerror("Erro", "Selecione dispositivo e tecla válidos")
        return

    # Procurar o index do dispositivo
    index = None
    for idx, nome in dispositivos.items():
        if nome == device_name:
            index = idx
            break

    atalhos[index] = hotkey
    atualizar_botao(index)  # atualiza o texto do botão com o hotkey

    def trocar():
        audio.trocar_dispositivo(index)

    def ouvir_tecla():
        keyboard.add_hotkey(hotkey, trocar)
        keyboard.wait()

    threading.Thread(target=ouvir_tecla, daemon=True).start()
    messagebox.showinfo("Sucesso", f"Atalho {hotkey} registrado para {device_name}")


tk.Button(aba_outros, text="Registrar Atalho", command=registrar_atalho).pack(pady=10)

root.mainloop()
