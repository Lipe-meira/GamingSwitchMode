import unittest
import tkinter as tk
from ui_theme import apply_theme, BACKGROUND


class ThemeTests(unittest.TestCase):
    def test_theme_sets_dark_background_and_minimum_size(self):
        root = tk.Tk()
        root.withdraw()
        self.addCleanup(root.destroy)
        apply_theme(root)
        self.assertEqual(root.cget('background'), BACKGROUND)
        self.assertGreaterEqual(root.minsize()[0], 680)
