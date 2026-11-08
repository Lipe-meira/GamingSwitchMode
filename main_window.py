"""Tk window construction; actions are supplied by the application."""
import tkinter as tk
import re
from tkinter import ttk
import customtkinter as ctk
from ui_theme import (apply_theme, BACKGROUND, SURFACE, ELEVATED, ACCENT, TEXT, MUTED,
                      PRIMARY, PRIMARY_HOVER, PRIMARY_TEXT, DESTRUCTIVE, DESTRUCTIVE_HOVER)


def keyboard_button(button):
    """Expose CustomTkinter's frame to Tk focus traversal and keyboard activation."""
    button._text_label.configure(takefocus=1)
    button.configure(border_width=2, border_color=button.cget('fg_color'))
    def focus_in(event):
        button.configure(border_color=ACCENT)
    def focus_out(event):
        button.configure(border_color=button.cget('fg_color'))
    def activate(event):
        if button.cget('state') != 'disabled':
            button.invoke()
        return 'break'
    button.bind('<FocusIn>', focus_in)
    button.bind('<FocusOut>', focus_out)
    button.bind('<Return>', activate)
    button.bind('<space>', activate)
    return button


def device_name_parts(name):
    """Separate a final parenthesized device description when one is present."""
    match = re.fullmatch(r'(.+?)\s+\(([^()]*)\)', name.strip())
    if match and match.group(2).strip():
        return match.group(1).strip(), match.group(2).strip()
    return name.strip(), ''


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
        for nav_button in self.navigation._buttons_dict.values():
            keyboard_button(nav_button)
        self.page_container = tk.Frame(root, bg=BACKGROUND)
        self.page_container.pack(expand=True, fill='both', padx=24, pady=(0, 4))
        self.aba_audio = ctk.CTkFrame(self.page_container, fg_color='transparent')
        self.aba_atalhos = ctk.CTkFrame(self.page_container, fg_color='transparent')
        self.aba_audio.pack(fill='both', expand=True)
        device_header = ctk.CTkFrame(self.aba_audio, fg_color='transparent')
        device_header.pack(fill='x', pady=(8, 10))
        ctk.CTkLabel(device_header, text='Saídas de áudio', text_color=TEXT,
                     font=ctk.CTkFont(family='Segoe UI', size=18, weight='bold')).pack(side='left')
        self.refresh_button = ctk.CTkButton(device_header, text='Atualizar lista', width=120,
            fg_color=ELEVATED, hover_color='#304963', text_color=TEXT, corner_radius=9,
            command=self.actions.atualizar_lista)
        self.refresh_button.pack(side='right')
        keyboard_button(self.refresh_button)
        self.device_frame = ctk.CTkScrollableFrame(self.aba_audio, fg_color='transparent',
            scrollbar_button_color=ELEVATED, scrollbar_button_hover_color=ACCENT)
        self.device_frame.pack(fill='both', expand=True)
        self.buttons = {}
        self.device_labels = {}

        form = ctk.CTkFrame(self.aba_atalhos, fg_color=SURFACE, corner_radius=12)
        form.pack(fill='x', pady=(8, 10))
        ctk.CTkLabel(form, text='Configurar atalho', text_color=TEXT,
                     font=ctk.CTkFont(family='Segoe UI', size=17, weight='bold')).pack(anchor='w', padx=16, pady=(12, 4))
        ctk.CTkLabel(form, text='Dispositivo', text_color=MUTED).pack(anchor='w', padx=16)
        self.dropdown = ctk.CTkComboBox(form, variable=self.dispositivo_var,
            values=['Selecione...'] + list(self.actions.device_labels()), state='readonly',
            fg_color=ELEVATED, border_color=ELEVATED, text_color=TEXT, button_color=ELEVATED,
            dropdown_fg_color=SURFACE, dropdown_text_color=TEXT)
        self.dropdown.pack(fill='x', padx=16, pady=(0, 4))
        ctk.CTkLabel(form, text='Combinação', text_color=MUTED).pack(anchor='w', padx=16)
        self.entrada_tecla = ctk.CTkEntry(form, textvariable=self.tecla_var, state='readonly',
            fg_color=ELEVATED, border_color=ELEVATED, text_color=TEXT)
        self.entrada_tecla.pack(fill='x', padx=16)
        self.capture_hint = ctk.CTkLabel(form, text='Grave uma combinação para associar ao dispositivo.', text_color=MUTED, anchor='w')
        self.capture_hint.pack(fill='x', padx=16)
        capture_actions = ctk.CTkFrame(form, fg_color='transparent')
        capture_actions.pack(anchor='w', padx=16, pady=(4, 12))
        self.btn_gravar = ctk.CTkButton(capture_actions, text='Gravar atalho', command=self.actions.gravar_tecla, fg_color=ELEVATED, hover_color='#304963', width=130)
        self.btn_gravar.pack(side='left', padx=(0, 8))
        self.btn_registrar = ctk.CTkButton(capture_actions, text='Registrar atalho', command=self.actions.registrar_atalho, fg_color=PRIMARY, hover_color=PRIMARY_HOVER, text_color=PRIMARY_TEXT, width=140)
        self.btn_registrar.pack(side='left')
        keyboard_button(self.btn_gravar)
        keyboard_button(self.btn_registrar)
        ctk.CTkLabel(self.aba_atalhos, text='Atalhos registrados', text_color=TEXT,
                     font=ctk.CTkFont(family='Segoe UI', size=16, weight='bold')).pack(anchor='w', pady=(2, 4))
        self.shortcut_list = ctk.CTkScrollableFrame(self.aba_atalhos, fg_color='transparent',
            scrollbar_button_color=ELEVATED, scrollbar_button_hover_color=ACCENT)
        self.shortcut_list.pack(fill='both', expand=True)
        self.shortcut_rows = {}
        self.shortcut_selected = None


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
        for device_id, name, tag, hotkey in rows:
            card = ctk.CTkFrame(self.device_frame, fg_color=SURFACE, corner_radius=12,
                                border_color=ELEVATED, border_width=1)
            card.pack(pady=5, fill='x')
            content = ctk.CTkFrame(card, fg_color='transparent')
            content.pack(fill='x', padx=16, pady=12)
            button = ctk.CTkButton(content, text='Selecionar saída', width=126, height=36,
                fg_color=ELEVATED, hover_color='#304963', text_color=TEXT, corner_radius=9,
                command=lambda value=device_id: self.actions.trocar_dispositivo(value))
            button.pack(side='right', padx=(12, 0))
            keyboard_button(button)
            icon = tk.Canvas(content, width=24, height=24, bg=SURFACE, highlightthickness=0)
            icon.pack(side='left', anchor='n', padx=(0, 12), pady=(3, 0))
            icon.create_polygon(3, 9, 7, 9, 12, 5, 12, 19, 7, 15, 3, 15,
                                fill=ACCENT, outline=ACCENT)
            icon.create_arc(8, 4, 21, 20, start=-55, extent=110, style='arc', outline=ACCENT, width=2)
            details = ctk.CTkFrame(content, fg_color='transparent')
            details.pack(fill='x', expand=True)
            title, description = device_name_parts(name)
            label = ctk.CTkLabel(details, text=title, text_color=TEXT, anchor='w', justify='left',
                                 font=ctk.CTkFont(family='Segoe UI', size=13, weight='bold'), wraplength=390)
            label.pack(fill='x', anchor='w')
            if description:
                ctk.CTkLabel(details, text=description, text_color=MUTED, anchor='w', justify='left',
                             font=ctk.CTkFont(family='Segoe UI', size=11), wraplength=390).pack(fill='x', anchor='w')
            info = f'Disponível  ·  ID: {tag}' + (f'  ·  {hotkey}' if hotkey else '')
            ctk.CTkLabel(details, text=info, text_color=ACCENT, anchor='w', justify='left',
                         font=ctk.CTkFont(family='Segoe UI', size=11), wraplength=390).pack(fill='x', anchor='w')
            self.buttons[device_id] = button
            self.device_labels[device_id] = label
        self.dropdown.configure(values=['Selecione...'] + list(labels))
        if self.dispositivo_var.get() not in labels:
            self.dispositivo_var.set('Selecione...')

    def _shortcut_action(self, item_id, callback):
        self.shortcut_selected = item_id
        callback()

    def set_hotkeys(self, rows):
        for child in self.shortcut_list.winfo_children():
            child.destroy()
        self.shortcut_rows = {}
        self.shortcut_selected = None
        if not rows:
            ctk.CTkLabel(self.shortcut_list, text='Nenhum atalho cadastrado.', text_color=MUTED).pack(anchor='w', padx=12, pady=12)
        for item_id, name, hotkey in rows:
            card = ctk.CTkFrame(self.shortcut_list, fg_color=SURFACE, corner_radius=10)
            card.pack(fill='x', pady=4)
            buttons = ctk.CTkFrame(card, fg_color='transparent')
            buttons.pack(side='right', padx=10, pady=8)
            edit = ctk.CTkButton(buttons, text='Editar', width=66, fg_color=ELEVATED,
                command=lambda key=item_id: self._shortcut_action(key, self.actions.editar_atalho))
            edit.pack(side='left', padx=3)
            remove = ctk.CTkButton(buttons, text='Remover', width=72, fg_color=DESTRUCTIVE, hover_color=DESTRUCTIVE_HOVER,
                command=lambda key=item_id: self._shortcut_action(key, self.actions.remover_atalho))
            remove.pack(side='left', padx=3)
            keyboard_button(edit)
            keyboard_button(remove)
            text = ctk.CTkLabel(card, text=f'{name}\n{hotkey}', text_color=TEXT, anchor='w', justify='left', wraplength=400)
            text.pack(fill='x', padx=14, pady=8)
            self.shortcut_rows[item_id] = (name, hotkey, edit, remove)

    def set_status(self, value):
        self.status_var.set(value)

    def set_recording_state(self, recording, value=None):
        if value is not None:
            self.tecla_var.set(value)
        self.btn_gravar.configure(state='disabled' if recording else 'normal')
        self.btn_registrar.configure(state='disabled' if recording else 'normal')
        self.capture_hint.configure(text='Aguardando combinação de teclas…' if recording else 'Grave uma combinação para associar ao dispositivo.')

    def selected_shortcut(self):
        return self.shortcut_selected

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
