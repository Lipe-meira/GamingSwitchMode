import tkinter as tk
from tkinter import messagebox
import subprocess
import audio  


# Criar a janela principal
root = tk.Tk()
root.title("Switcher de Áudio")
root.geometry("400x300")

dispositivos = audio.listar_dispositivos()



# Criar botões para cada dispositivo
for idx, nome in dispositivos.items():
    btn = tk.Button(root, text=nome, width=40, command=lambda i=idx: audio.trocar_dispositivo(i))
    btn.pack(pady=5)

root.mainloop()
