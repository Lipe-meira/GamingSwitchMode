"""System tray integration; callbacks communicate through the event queue."""
import pystray
from PIL import Image, ImageDraw


class SystemTray:
    def __init__(self, events):
        self.events = events
        self.icon = None
        self.stop_requested = False

    def show_window(self, icon, item):
        self.events.put(('show',))

    def exit_app(self, icon, item):
        icon.stop()
        self.events.put(('exit',))

    @staticmethod
    def create_image():
        image = Image.new('RGB', (64, 64), '#111827')
        draw = ImageDraw.Draw(image)
        draw.rectangle((16, 22, 30, 42), fill='#60a5fa')
        draw.polygon([(30, 22), (46, 12), (46, 52), (30, 42)], fill='#93c5fd')
        return image

    def run(self):
        menu = (pystray.MenuItem('Mostrar', self.show_window, default=True),
                pystray.MenuItem('Sair', self.exit_app))
        self.icon = pystray.Icon('audio_switcher', self.create_image(), 'Audio Switcher', menu)
        if not self.stop_requested:
            self.icon.run()

    def stop(self):
        self.stop_requested = True
        if self.icon is not None:
            self.icon.stop()

    def is_operational(self):
        return not self.stop_requested and self.icon is not None and self.icon.visible
