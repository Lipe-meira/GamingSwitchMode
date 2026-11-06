"""Tk window construction; actions are supplied by the application."""
import tkinter as tk
from tkinter import ttk
import customtkinter as ctk
from ui_theme import apply_theme, BACKGROUND, SURFACE, ELEVATED, ACCENT, TEXT, MUTED


class MainWindow:
    def __init__(self, root, actions):
        self.root = root
        self.actions = actions
        apply_theme(root)
        root.geometry('900x700')
        header = ctk.CTkFrame(root, fg_color='transparent')
        header.pack(fill='x', padx=24, pady=(20, 8))
        ctk.CTkLabel(header, text='GamingSwitchMode', text_color=TEXT, font=ctk.CTkFont(family='Segoe UI', size=22, weight='bold')).pack(anchor='w')
        ctk.CTkLabel(header, text='Seu áudio, no dispositivo certo.', text_color=MUTED, font=ctk.CTkFont(family='Segoe UI', size=12)).pack(anchor='w')
        self.status_var = tk.StringVar(value="Pronto.")
        self.tecla_var = tk.StringVar()
        self.dispositivo_var = tk.StringVar(value="Selecione...")

        ttk.Label(self.root, textvariable=self.status_var, anchor="w").pack(side="bottom", fill="x", padx=24, pady=6)

        self.navigation = ctk.CTkSegmentedButton(root, values=['Dispositivos', 'Atalhos'],
            command=self._select_page, selected_color=ELEVATED, selected_hover_color=ELEVATED,
            unselected_color=SURFACE, unselected_hover_color=ELEVATED, text_color=TEXT,
            corner_radius=10, font=ctk.CTkFont(family='Segoe UI', size=13, weight='bold'))
        self.navigation.pack(fill='x', padx=24, pady=(4, 8))
        self.navigation.set('Dispositivos')
        self.page_container = tk.Frame(root, bg=BACKGROUND)
        self.page_container.pack(expand=True, fill='both', padx=24, pady=(0, 4))
        self.aba_audio = ctk.CTkFrame(self.page_container, fg_color='transparent')
        self.aba_atalhos = ttk.Frame(self.page_container)
        self.aba_audio.pack(fill='both', expand=True)
        device_header = ctk.CTkFrame(self.aba_audio, fg_color='transparent')
        device_header.pack(fill='x', pady=(8, 10))
        ctk.CTkLabel(device_header, text='Saídas de áudio', text_color=TEXT,
                     font=ctk.CTkFont(family='Segoe UI', size=18, weight='bold')).pack(side='left')
        self.refresh_button = ctk.CTkButton(device_header, text='Atualizar lista', width=120,
            fg_color=ELEVATED, hover_color='#304963', text_color=TEXT, corner_radius=9,
            command=self.actions.atualizar_lista)
        self.refresh_button.pack(side='right')
        self.device_frame = ctk.CTkScrollableFrame(self.aba_audio, fg_color='transparent',
            scrollbar_button_color=ELEVATED, scrollbar_button_hover_color=ACCENT)
        self.device_frame.pack(fill='both', expand=True)
        self.buttons = {}
        self.device_labels = {}

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


    def _select_page(self, page):
        self.aba_audio.pack_forget()
        self.aba_atalhos.pack_forget()
        target = self.aba_audio if page == 'Dispositivos' else self.aba_atalhos
        target.pack(fill='both', expand=True)
        self.navigation.set(page)

    def set_devices(self, rows, labels):
        for child in self.device_frame.winfo_children():
            child.destroy()
        self.buttons.clear()
        self.device_labels.clear()
        if not rows:
            ctk.CTkLabel(self.device_frame, text='Nenhum dispositivo de saída encontrado.\nConecte um dispositivo e atualize a lista.',
                         text_color=MUTED, justify='left').pack(anchor='w', padx=16, pady=28)
        for device_id, text in rows:
            card = ctk.CTkFrame(self.device_frame, fg_color=SURFACE, corner_radius=12,
                                border_color=ELEVATED, border_width=1)
            card.pack(pady=5, fill='x')
            content = ctk.CTkFrame(card, fg_color='transparent')
            content.pack(fill='x', padx=16, pady=12)
            button = ctk.CTkButton(content, text='Selecionar saída', width=126, height=36,
                fg_color=ELEVATED, hover_color='#304963', text_color=TEXT, corner_radius=9,
                command=lambda value=device_id: self.actions.trocar_dispositivo(value))
            button.pack(side='right', padx=(12, 0))
            label = ctk.CTkLabel(content, text=text, text_color=TEXT, anchor='w', justify='left',
                                 font=ctk.CTkFont(family='Segoe UI', size=13, weight='bold'), wraplength=430)
            label.pack(fill='x', anchor='w')
            ctk.CTkLabel(content, text='Disponível', text_color=ACCENT, anchor='w',
                         font=ctk.CTkFont(family='Segoe UI', size=11)).pack(fill='x', anchor='w')
            self.buttons[device_id] = button
            self.device_labels[device_id] = label
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
