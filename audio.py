from pycaw.pycaw import AudioUtilities, IMMDeviceEnumerator
from comtypes import CLSCTX_ALL
from pycaw.utils import AudioUtilities, EDataFlow, ERole

import warnings
warnings.filterwarnings("ignore")


def listar_dispositivos():
    # Retorna apenas dispositivos de saída (Render) e remove duplicados pelo nome
    devices = AudioUtilities.GetAllDevices()
    seen = set()
    unique_devices = []
    for d in devices:
        if d.FriendlyName not in seen:
            seen.add(d.FriendlyName)
            unique_devices.append(d)
    return [f"{i+1}. {d.FriendlyName}" for i, d in enumerate(unique_devices)]

if __name__ == "__main__":
    for d in listar_dispositivos():
        print(d)
