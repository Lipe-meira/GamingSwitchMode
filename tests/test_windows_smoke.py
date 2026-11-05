import unittest
from unittest.mock import patch
from tests import windows_smoke


class SmokeInputTests(unittest.TestCase):
    def test_synthetic_input_uses_keyboard_library(self):
        with patch.object(windows_smoke.keyboard, 'send') as send:
            windows_smoke.send_input('ctrl+alt+shift+f24')
        send.assert_called_once_with('ctrl+alt+shift+f24')
