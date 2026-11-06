"""Shared desktop palette and ttk styles."""
from tkinter import ttk

BACKGROUND = '#101722'
SURFACE = '#192434'
ELEVATED = '#223149'
ACCENT = '#76B5FF'
TEXT = '#F1F5FA'
MUTED = '#9AAEC5'
PRIMARY = '#76B5FF'
PRIMARY_HOVER = '#A3CEFF'
PRIMARY_TEXT = '#101722'
DESTRUCTIVE = '#56323D'
DESTRUCTIVE_HOVER = '#754451'


def apply_theme(root):
    root.configure(background=BACKGROUND)
    root.minsize(680, 540)
    style = ttk.Style(root)
    style.theme_use('clam')
    style.configure('.', background=BACKGROUND, foreground=TEXT, font=('Segoe UI', 10))
    style.configure('TFrame', background=BACKGROUND)
    style.configure('TLabel', background=BACKGROUND, foreground=TEXT)
    style.configure('Title.TLabel', font=('Segoe UI', 20, 'bold'))
    style.configure('Subtitle.TLabel', foreground=MUTED, font=('Segoe UI', 10))
    style.configure('TButton', background=ELEVATED, foreground=TEXT, padding=(14, 9), borderwidth=0)
    style.map('TButton', background=[('disabled', SURFACE), ('pressed', '#304963'), ('active', '#2a405b')], foreground=[('disabled', MUTED)])
    style.configure('TNotebook', background=BACKGROUND, borderwidth=0)
    style.configure('TNotebook.Tab', background=BACKGROUND, foreground=MUTED, padding=(18, 10), font=('Segoe UI', 10, 'bold'))
    style.map('TNotebook.Tab', background=[('selected', SURFACE), ('active', ELEVATED)], foreground=[('selected', ACCENT), ('active', TEXT)])
    style.configure('Treeview', background=SURFACE, fieldbackground=SURFACE, foreground=TEXT, rowheight=38, borderwidth=0)
    style.map('Treeview', background=[('selected', ELEVATED)], foreground=[('selected', TEXT)])
    style.configure('Treeview.Heading', background=ELEVATED, foreground=MUTED, padding=8, relief='flat')
    style.configure('TCombobox', fieldbackground=ELEVATED, background=ELEVATED, foreground=TEXT, arrowcolor=TEXT, padding=6)
    style.map('TCombobox', fieldbackground=[('readonly', ELEVATED)], foreground=[('readonly', TEXT)])
    style.configure('TEntry', fieldbackground=ELEVATED, foreground=TEXT, padding=7)
    style.map('TEntry', fieldbackground=[('readonly', ELEVATED)], foreground=[('readonly', TEXT)])
    return style
