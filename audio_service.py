"""Audio operations and event reporting, independent of Tk."""


class AudioService:
    def __init__(self, backend, events):
        self.backend = backend
        self.events = events

    def activate(self, device_id, name):
        try:
            current = self.backend.listar_dispositivos()
            if device_id not in current:
                self.events.put(('status', f'Dispositivo indisponivel: {name}'))
                self.events.put(('devices', current))
                return
            self.backend.trocar_dispositivo(device_id)
            self.events.put(('devices', current))
            self.events.put(('status', f'Audio alterado para: {current[device_id]["Name"]}'))
        except (RuntimeError, ValueError) as error:
            self.events.put(('status', f'Erro ao trocar audio: {error}'))

    def refresh(self):
        try:
            self.events.put(('devices', self.backend.listar_dispositivos()))
        except RuntimeError as error:
            self.events.put(('status', f'Erro ao atualizar dispositivos: {error}'))
