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
            'trocar_dispositivo', 'device_labels', 'atualizar_lista',
            'gravar_tecla', 'registrar_atalho', 'editar_atalho', 'remover_atalho')})
        actions.device_labels.return_value = {'Headset': 'id'}
        window = main_window.MainWindow(root, actions)
        window.set_devices([('id', 'Headset')], {'Headset': 'id'})
        window.buttons['id'].invoke()
        actions.trocar_dispositivo.assert_called_once_with('id')
        window.set_hotkeys([('id:id', 'Headset', 'ctrl+1')])
        window.shortcut_rows['id:id'][2].invoke()
        actions.editar_atalho.assert_called_once_with()
        actions.editar_atalho.reset_mock()
        self.assertEqual(window.selected_shortcut(), 'id:id')
        window.set_selection('Headset', 'ctrl+1')
        self.assertEqual(window.selected_device(), 'Headset')
        self.assertEqual(window.hotkey_value(), 'ctrl+1')
        window.set_status('Pronto para teste')
        self.assertEqual(window.status_var.get(), 'Pronto para teste')

        window.refresh_button.invoke()
        actions.atualizar_lista.assert_called_once_with()
        window.btn_gravar.invoke()
        actions.gravar_tecla.assert_called_once_with()
        window.btn_registrar.invoke()
        actions.registrar_atalho.assert_called_once_with()
        window.shortcut_rows['id:id'][2].invoke()
        actions.editar_atalho.assert_called_once_with()
        window.shortcut_rows['id:id'][3].invoke()
        actions.remover_atalho.assert_called_once_with()
        self.assertEqual(tuple(window.dropdown.cget('values')), ('Selecione...', 'Headset'))

    def test_refresh_replaces_devices_shortcuts_and_recording_state(self):
        root = tk.Tk()
        root.withdraw()
        self.addCleanup(root.destroy)
        actions = SimpleNamespace(**{name: Mock() for name in (
            'device_labels', 'trocar_dispositivo', 'atualizar_lista', 'gravar_tecla',
            'registrar_atalho', 'editar_atalho', 'remover_atalho')})
        actions.device_labels.return_value = {}
        window = main_window.MainWindow(root, actions)
        window.set_devices([('a', 'Headset')], {'Headset': 'a'})
        window.set_selection('Headset', 'ctrl+1')
        window.set_devices([('b', 'Caixa')], {'Caixa': 'b'})
        self.assertEqual(set(window.buttons), {'b'})
        self.assertEqual(window.selected_device(), 'Selecione...')
        window.set_hotkeys([('id:a', 'Indisponivel', 'ctrl+1')])
        self.assertEqual(window.shortcut_rows['id:a'][:2], ('Indisponivel', 'ctrl+1'))
        window.set_hotkeys([('legacy:1', 'Pendente', 'ctrl+2')])
        self.assertEqual(tuple(window.shortcut_rows), ('legacy:1',))
        window.set_recording_state(True, 'Gravando...')
        self.assertEqual(str(window.btn_gravar.cget('state')), 'disabled')
        self.assertIn('aguardando', window.capture_hint.cget('text').lower())
        window.set_recording_state(False, 'ctrl+2')
        self.assertEqual(window.hotkey_value(), 'ctrl+2')

    def test_navigation_selects_both_sections(self):
        root = tk.Tk()
        root.withdraw()
        self.addCleanup(root.destroy)
        actions = SimpleNamespace(**{name: Mock() for name in (
            'device_labels', 'trocar_dispositivo', 'atualizar_lista', 'gravar_tecla',
            'registrar_atalho', 'editar_atalho', 'remover_atalho')})
        actions.device_labels.return_value = {}
        window = main_window.MainWindow(root, actions)
        window._select_page('Atalhos')
        self.assertEqual(window.navigation.get(), 'Atalhos')
        self.assertTrue(window.aba_atalhos.winfo_manager())
        window._select_page('Dispositivos')
        self.assertEqual(window.navigation.get(), 'Dispositivos')
        self.assertTrue(window.aba_audio.winfo_manager())

    def test_device_card_has_explicit_action_and_wraps_long_names(self):
        root = tk.Tk()
        root.withdraw()
        self.addCleanup(root.destroy)
        actions = SimpleNamespace(**{name: Mock() for name in (
            'device_labels', 'trocar_dispositivo', 'atualizar_lista', 'gravar_tecla',
            'registrar_atalho', 'editar_atalho', 'remover_atalho')})
        actions.device_labels.return_value = {}
        window = main_window.MainWindow(root, actions)
        window.set_devices([('a', 'Saída longa ' * 15)], {})
        self.assertIn('Selecionar saída', window.buttons['a'].cget('text'))
        self.assertGreater(window.device_labels['a'].cget('wraplength'), 0)
        window.buttons['a'].invoke()
        actions.trocar_dispositivo.assert_called_once_with('a')
