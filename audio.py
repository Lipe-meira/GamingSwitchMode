import base64
import json
import os
import subprocess
import sys

CREATE_NO_WINDOW = 0x08000000 if sys.platform == "win32" else 0


def get_base_dir():
    if getattr(sys, "frozen", False):
        return getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))
    return os.path.dirname(os.path.abspath(__file__))


def _powershell_string(value):
    # Only base64's ASCII alphabet enters the script, including for smart quotes,
    # apostrophes and metacharacters. The decoded value is data, never script.
    encoded = base64.b64encode(value.encode('utf-8')).decode('ascii')
    return f"([Text.Encoding]::UTF8.GetString([Convert]::FromBase64String('{encoded}')))"


def _get_module_import_cmd():
    base_dir = get_base_dir()
    candidatos = [
        os.path.join(base_dir, "modules", "AudioDeviceCmdlets", "AudioDeviceCmdlets.dll"),
        os.path.join(base_dir, "modules", "AudioDeviceCmdlets", "AudioDeviceCmdlets.psd1"),
        os.path.join(base_dir, "AudioDeviceCmdlets.dll"),
    ]
    for caminho in candidatos:
        if os.path.isfile(caminho):
            return (
                "if (-not (Get-Command Get-AudioDevice -ErrorAction SilentlyContinue)) { "
                f"Import-Module {_powershell_string(caminho)} -ErrorAction Stop"
                " }; "
            )
    return ""


def listar_dispositivos(tipo="Playback"):
    if tipo not in ("Playback", "Recording"):
        raise ValueError("Tipo de dispositivo invalido.")
    output = _run(
        "Get-AudioDevice -List | "
        f"Where-Object {{ $_.Type -eq '{tipo}' }} | "
        "Select-Object ID,Name,Type,Index | ConvertTo-Json -Compress"
    )
    try:
        rows = json.loads(output) if output.strip() else []
        rows = [rows] if isinstance(rows, dict) else [] if rows is None else rows
        if not isinstance(rows, list):
            raise ValueError("Lista invalida")
        devices = {}
        for row in rows:
            if not isinstance(row, dict) or not all(
                isinstance(row.get(key), str) and row[key] for key in ("ID", "Name", "Type")
            ) or row["ID"] in devices:
                raise ValueError("Identidade de dispositivo invalida ou duplicada")
            devices[row["ID"]] = row
        return devices
    except (ValueError, TypeError) as error:
        raise RuntimeError(f"Resposta de audio invalida: {error}") from error


def _run(command):
    script = (
        "$ErrorActionPreference = 'Stop'; "
        "[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new(); "
        + _get_module_import_cmd() + command
    )
    comando = [
        "powershell",
        "-NoProfile",
        "-ExecutionPolicy",
        "Bypass",
        "-Command",
        script,
    ]
    try:
        resultado = subprocess.run(
            comando, capture_output=True, text=True, encoding="utf-8",
            creationflags=CREATE_NO_WINDOW, timeout=20,
        )
    except (OSError, subprocess.TimeoutExpired, UnicodeError) as error:
        raise RuntimeError(f"Falha ao executar PowerShell: {error}") from error
    if resultado.returncode != 0:
        raise RuntimeError(resultado.stderr.strip() or "Erro ao trocar dispositivo de audio.")
    return resultado.stdout


def trocar_dispositivo(device_id):
    if not isinstance(device_id, str) or not device_id or '\x00' in device_id:
        raise ValueError("ID de dispositivo invalido.")
    _run(f"$deviceId = {_powershell_string(device_id)}; "
         "Set-AudioDevice -ID $deviceId -ErrorAction Stop | Out-Null")


if __name__ == "__main__":
    dispositivos = listar_dispositivos()
    print("Dispositivos de audio disponiveis:\n")
    for device_id, device in dispositivos.items():
        print(f"{device_id} - {device['Name']} (indice atual: {device.get('Index')})")

    escolha = input("\nDigite o ID do dispositivo que deseja usar: ").strip()

    if escolha in dispositivos:
        trocar_dispositivo(escolha)
        print(f"\nDispositivo de audio alterado para: {dispositivos[escolha]}")
    else:
        print("\nID invalido.")
