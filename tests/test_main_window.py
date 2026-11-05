import importlib
import tkinter as tk
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

import main_window


class MainWindowTests(unittest.TestCase):
    def test_import_does_not_create_root(self):
        with patch('tkinter.Tk') as create_root:
            importlib.reload(main_window)
            create_root.assert_not_called()

    def test_buttons_delegate_to_supplied_callbacks(self):
        root = tk.Tk()
        root.withdraw()
        self.addCleanup(root.destroy)
        actions = SimpleNamespace(**{name: Mock() for name in (
            'criar_botoes_dispositivos', 'device_labels', 'atualizar_lista',
            'gravar_tecla', 'registrar_atalho', 'editar_atalho', 'remover_atalho')})
        actions.device_labels.return_value = {'Headset': 'id'}
        window = main_window.MainWindow(root, actions)
        actions.criar_botoes_dispositivos.assert_called_once_with(window.aba_audio)

        def descendants(widget):
            for child in widget.winfo_children():
                yield child
                yield from descendants(child)

        buttons = {child.cget('text'): child for child in descendants(root)
                   if child.winfo_class() in ('TButton', 'Button')}
        for label, method in [('Atualizar lista', 'atualizar_lista'),
                              ('Gravar atalho', 'gravar_tecla'),
                              ('Registrar atalho', 'registrar_atalho'),
                              ('Editar selecionado', 'editar_atalho'),
                              ('Remover selecionado', 'remover_atalho')]:
            buttons[label].invoke()
            getattr(actions, method).assert_called_once_with()
        self.assertEqual(tuple(window.dropdown.cget('values')), ('Selecione...', 'Headset'))
