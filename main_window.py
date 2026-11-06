"""Tk window construction; actions are supplied by the application."""
import tkinter as tk
from tkinter import ttk
from ui_theme import apply_theme, BACKGROUND, SURFACE, ELEVATED, ACCENT, TEXT, MUTED


class MainWindow:
    def __init__(self, root, actions):
        self.root = root
        self.actions = actions
        apply_theme(root)
        root.geometry('900x700')
        header = ttk.Frame(root, padding=(24, 20, 24, 8))
        header.pack(fill='x')
        ttk.Label(header, text='GamingSwitchMode', style='Title.TLabel').pack(anchor='w')
        ttk.Label(header, text='Seu áudio, no dispositivo certo.', style='Subtitle.TLabel').pack(anchor='w', pady=(3, 0))
        self.status_var = tk.StringVar(value="Pronto.")
        self.tecla_var = tk.StringVar()
        self.dispositivo_var = tk.StringVar(value="Selecione...")

        ttk.Label(self.root, textvariable=self.status_var, anchor="w").pack(side="bottom", fill="x", padx=24, pady=6)

        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(expand=True, fill="both", padx=24, pady=(8, 0))

        self.aba_audio = ttk.Frame(self.notebook)
        self.aba_atalhos = ttk.Frame(self.notebook)
        self.notebook.add(self.aba_audio, text="Dispositivos")
        self.notebook.add(self.aba_atalhos, text="Atalhos")

        device_header = ttk.Frame(self.aba_audio, padding=(0, 18, 0, 10))
        device_header.pack(fill='x')
        ttk.Label(device_header, text='Saídas de áudio', font=('Segoe UI', 15, 'bold')).pack(side='left')
        ttk.Button(device_header, text='Atualizar lista', command=self.actions.atualizar_lista).pack(side='right')
        self.device_canvas = tk.Canvas(self.aba_audio, bg=BACKGROUND, highlightthickness=0, borderwidth=0)
        self.device_scroll = ttk.Scrollbar(self.aba_audio, orient='vertical', command=self.device_canvas.yview)
        self.device_canvas.configure(yscrollcommand=self.device_scroll.set)
        self.device_scroll.pack(side='right', fill='y')
        self.device_canvas.pack(side='left', fill='both', expand=True)
        self.device_frame = tk.Frame(self.device_canvas, bg=BACKGROUND)
        self.device_frame_id = self.device_canvas.create_window((0, 0), window=self.device_frame, anchor='nw')
        self.device_frame.bind('<Configure>', lambda event: self.device_canvas.configure(scrollregion=self.device_canvas.bbox('all')))
        self.device_canvas.bind('<Configure>', self._resize_devices)
        self.device_canvas.bind('<MouseWheel>', lambda event: self.device_canvas.yview_scroll(-int(event.delta / 120), 'units'))
        self.buttons = {}

        ttk.Label(self.aba_atalhos, text="Seus atalhos", font=("Segoe UI", 15, "bold")).pack(anchor="w", pady=(18, 4))
        ttk.Label(self.aba_atalhos, text="Selecione uma saída e grave uma combinação.", style="Subtitle.TLabel").pack(anchor="w", pady=(0, 8))
        ttk.Label(self.aba_atalhos, text="Dispositivo").pack(anchor="w", pady=(4, 5))
        self.dropdown = ttk.Combobox(
            self.aba_atalhos,
            textvariable=self.dispositivo_var,
            values=["Selecione..."] + list(self.actions.device_labels()),
            state="readonly",
            width=58,
        )
        self.dropdown.pack(pady=5, fill="x")

        ttk.Label(self.aba_atalhos, text="Atalho").pack(anchor="w", pady=(10, 5))
        entrada_tecla = ttk.Entry(self.aba_atalhos, textvariable=self.tecla_var, width=34, state="readonly")
        entrada_tecla.pack(pady=5, fill="x")

        self.capture_hint = ttk.Label(self.aba_atalhos, text="Grave uma combinação para associar ao dispositivo.", style="Subtitle.TLabel")
        self.capture_hint.pack(anchor="w", pady=(0, 2))

        capture_actions = ttk.Frame(self.aba_atalhos)
        capture_actions.pack(anchor="w", pady=(4, 2))
        self.btn_gravar = ttk.Button(capture_actions, text="Gravar atalho", command=self.actions.gravar_tecla)
        self.btn_gravar.pack(side="left", padx=(0, 8))
        ttk.Button(capture_actions, text="Registrar atalho", command=self.actions.registrar_atalho).pack(side="left")

        ttk.Label(self.aba_atalhos, text="Atalhos registrados").pack(anchor="w", pady=(10, 5))
        acoes_frame = ttk.Frame(self.aba_atalhos)
        acoes_frame.pack(side="bottom", anchor="w", pady=(4, 8))
        ttk.Button(acoes_frame, text="Editar selecionado", command=self.actions.editar_atalho).pack(side="left", padx=(0, 8))
        ttk.Button(acoes_frame, text="Remover selecionado", command=self.actions.remover_atalho).pack(side="left")
        lista_frame = ttk.Frame(self.aba_atalhos)
        lista_frame.pack(pady=5, fill="both", expand=True)

        self.lista_atalhos = ttk.Treeview(
            lista_frame,
            columns=("dispositivo", "atalho"),
            show="headings",
            height=3,
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


    def _resize_devices(self, event):
        self.device_canvas.itemconfigure(self.device_frame_id, width=event.width)
        for button in self.buttons.values():
            button.configure(wraplength=max(200, event.width - 60))

    def set_devices(self, rows, labels):
        for child in self.device_frame.winfo_children():
            child.destroy()
        self.buttons.clear()
        if not rows:
            tk.Label(self.device_frame, text="Nenhum dispositivo de saída encontrado.\nConecte um dispositivo e atualize a lista.", bg=BACKGROUND, fg=MUTED, font=("Segoe UI", 11)).pack(pady=40)
        for device_id, text in rows:
            card = tk.Frame(self.device_frame, bg=SURFACE, highlightbackground=ELEVATED, highlightthickness=1)
            card.pack(pady=5, fill='x')
            tk.Label(card, text='SAÍDA DISPONÍVEL', bg=SURFACE, fg=ACCENT, font=('Segoe UI', 8, 'bold'), anchor='w').pack(fill='x', padx=16, pady=(11, 0))
            button = tk.Button(card, text=text + '\nSelecionar saída  →', anchor='w', justify='left', wraplength=560, bg=SURFACE, fg=TEXT,
                               activebackground=ELEVATED, activeforeground=TEXT, relief='flat',
                               bd=0, padx=14, pady=10, font=('Segoe UI', 10), cursor='hand2',
                               highlightthickness=1, highlightbackground=SURFACE, highlightcolor=ACCENT,
                               command=lambda value=device_id: self.actions.trocar_dispositivo(value))
            button.pack(fill='x')
            self.buttons[device_id] = button
        self.dropdown.config(values=['Selecione...'] + list(labels))
        if self.dispositivo_var.get() not in labels:
            self.dispositivo_var.set('Selecione...')

    def set_hotkeys(self, rows):
        for item in self.lista_atalhos.get_children():
            self.lista_atalhos.delete(item)
        for item_id, name, hotkey in rows:
            self.lista_atalhos.insert('', 'end', iid=item_id, values=(name, hotkey))

    def set_status(self, value):
        self.status_var.set(value)

    def set_recording_state(self, recording, value=None):
        if value is not None:
            self.tecla_var.set(value)
        self.btn_gravar.config(state='disabled' if recording else 'normal')
        self.capture_hint.config(text='Aguardando combinação de teclas…' if recording else 'Grave uma combinação para associar ao dispositivo.')

    def selected_shortcut(self):
        items = self.lista_atalhos.selection()
        return items[0] if items else None

    def selected_device(self):
        return self.dispositivo_var.get()

    def hotkey_value(self):
        return self.tecla_var.get()

    def set_selection(self, device, hotkey):
        self.dispositivo_var.set(device)
        self.tecla_var.set(hotkey)

    @staticmethod
    def show_error(title, message):
        from tkinter import messagebox
        messagebox.showerror(title, message)

    @staticmethod
    def show_warning(title, message):
        from tkinter import messagebox
        messagebox.showwarning(title, message)

    @staticmethod
    def confirm(title, message):
        from tkinter import messagebox
        return messagebox.askyesno(title, message)

    def hide(self):
        self.root.withdraw()

    def show(self):
        self.root.deiconify()
        self.root.lift()

    def schedule(self, delay, callback):
        self.root.after(delay, callback)

    def on_close(self, callback):
        self.root.protocol('WM_DELETE_WINDOW', callback)

    def destroy(self):
        self.root.destroy()

    def run(self):
        self.root.mainloop()
