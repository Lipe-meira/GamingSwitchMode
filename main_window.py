"""Tk window construction; actions are supplied by the application."""
import tkinter as tk
from tkinter import ttk


class MainWindow:
    def __init__(self, root, actions):
        self.root = root
        self.actions = actions
        self.status_var = tk.StringVar(value="Pronto.")
        self.tecla_var = tk.StringVar()
        self.dispositivo_var = tk.StringVar(value="Selecione...")

        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(expand=True, fill="both")

        self.aba_audio = ttk.Frame(self.notebook)
        self.aba_atalhos = ttk.Frame(self.notebook)
        self.notebook.add(self.aba_audio, text="Audio")
        self.notebook.add(self.aba_atalhos, text="Atalhos")

        self.actions.criar_botoes_dispositivos(self.aba_audio)
        tk.Button(self.aba_audio, text="Atualizar lista", command=self.actions.atualizar_lista).pack(pady=12)

        ttk.Label(self.aba_atalhos, text="Dispositivo").pack(pady=(20, 5))
        self.dropdown = ttk.Combobox(
            self.aba_atalhos,
            textvariable=self.dispositivo_var,
            values=["Selecione..."] + list(self.actions.device_labels()),
            state="readonly",
            width=58,
        )
        self.dropdown.pack(pady=5)

        ttk.Label(self.aba_atalhos, text="Atalho").pack(pady=(16, 5))
        entrada_tecla = ttk.Entry(self.aba_atalhos, textvariable=self.tecla_var, width=34, state="readonly")
        entrada_tecla.pack(pady=5)

        self.btn_gravar = ttk.Button(self.aba_atalhos, text="Gravar atalho", command=self.actions.gravar_tecla)
        self.btn_gravar.pack(pady=8)

        ttk.Button(self.aba_atalhos, text="Registrar atalho", command=self.actions.registrar_atalho).pack(pady=8)

        ttk.Label(self.aba_atalhos, text="Atalhos registrados").pack(pady=(18, 5))
        lista_frame = ttk.Frame(self.aba_atalhos)
        lista_frame.pack(padx=12, pady=5, fill="both", expand=True)

        self.lista_atalhos = ttk.Treeview(
            lista_frame,
            columns=("dispositivo", "atalho"),
            show="headings",
            height=6,
            selectmode="browse",
        )
        self.lista_atalhos.heading("dispositivo", text="Dispositivo")
        self.lista_atalhos.heading("atalho", text="Atalho")
        self.lista_atalhos.column("dispositivo", width=360, anchor="w")
        self.lista_atalhos.column("atalho", width=120, anchor="center")
        self.lista_atalhos.pack(side="left", fill="both", expand=True)
        self.lista_atalhos.bind("<Double-1>", lambda event: self.actions.editar_atalho())

        scroll_atalhos = ttk.Scrollbar(lista_frame, orient="vertical", command=self.lista_atalhos.yview)
        scroll_atalhos.pack(side="right", fill="y")
        self.lista_atalhos.configure(yscrollcommand=scroll_atalhos.set)

        acoes_frame = ttk.Frame(self.aba_atalhos)
        acoes_frame.pack(pady=(4, 12))
        ttk.Button(acoes_frame, text="Editar selecionado", command=self.actions.editar_atalho).pack(side="left", padx=5)
        ttk.Button(acoes_frame, text="Remover selecionado", command=self.actions.remover_atalho).pack(side="left", padx=5)

        ttk.Label(self.root, textvariable=self.status_var, anchor="w").pack(side="bottom", fill="x", padx=8, pady=6)
