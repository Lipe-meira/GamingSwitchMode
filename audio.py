import os
import subprocess
import sys

CREATE_NO_WINDOW = 0x08000000 if sys.platform == "win32" else 0


def get_base_dir():
    if getattr(sys, "frozen", False):
        return getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))
    return os.path.dirname(os.path.abspath(__file__))


def _get_module_import_cmd():
    base_dir = get_base_dir()
    candidatos = [
        os.path.join(base_dir, "modules", "AudioDeviceCmdlets", "AudioDeviceCmdlets.dll"),
        os.path.join(base_dir, "modules", "AudioDeviceCmdlets", "AudioDeviceCmdlets.psd1"),
        os.path.join(base_dir, "AudioDeviceCmdlets.dll"),
    ]
    for caminho in candidatos:
        if os.path.isfile(caminho):
            escaped = caminho.replace("'", "''")
            return (
                "if (-not (Get-Command Get-AudioDevice -ErrorAction SilentlyContinue)) { "
                f"Import-Module '{escaped}' -ErrorAction Stop"
                " }; "
            )
    return ""


def listar_dispositivos(tipo="Playback"):
    import_cmd = _get_module_import_cmd()
    script = (
        f"{import_cmd}"
        "Get-AudioDevice -List | "
        f"Where-Object {{ $_.Type -eq '{tipo}' }} | "
        "ForEach-Object { $_.Index.ToString() + ' - ' + $_.Name + ' (' + $_.Type + ')' }"
    )
    comando = [
        "powershell",
        "-NoProfile",
        "-ExecutionPolicy",
        "Bypass",
        "-Command",
        script,
    ]

    resultado = subprocess.run(
        comando,
        capture_output=True,
        text=True,
        creationflags=CREATE_NO_WINDOW,
    )
    if resultado.returncode != 0:
        raise RuntimeError(resultado.stderr.strip() or "Erro ao listar dispositivos de audio.")

    dispositivos = {}
    for linha in resultado.stdout.strip().splitlines():
        if not linha or " - " not in linha:
            continue

        index, nome = linha.split(" - ", 1)
        dispositivos[index.strip()] = nome.strip()

    return dispositivos


def trocar_dispositivo(index):
    import_cmd = _get_module_import_cmd()
    script = f"{import_cmd}Set-AudioDevice -Index {index}"
    comando = [
        "powershell",
        "-NoProfile",
        "-ExecutionPolicy",
        "Bypass",
        "-Command",
        script,
    ]
    resultado = subprocess.run(
        comando,
        capture_output=True,
        text=True,
        creationflags=CREATE_NO_WINDOW,
    )
    if resultado.returncode != 0:
        raise RuntimeError(resultado.stderr.strip() or "Erro ao trocar dispositivo de audio.")


if __name__ == "__main__":
    dispositivos = listar_dispositivos()
    print("Dispositivos de audio disponiveis:\n")
    for index, nome in dispositivos.items():
        print(f"{index} - {nome}")

    escolha = input("\nDigite o indice do dispositivo que deseja usar: ").strip()

    if escolha in dispositivos:
        trocar_dispositivo(escolha)
        print(f"\nDispositivo de audio alterado para: {dispositivos[escolha]}")
    else:
        print("\nIndice invalido.")
