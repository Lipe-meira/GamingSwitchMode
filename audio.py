import subprocess


def listar_dispositivos(tipo="Playback"):
    comando = [
        "powershell",
        "-NoProfile",
        "-Command",
        (
            "Get-AudioDevice -List | "
            f"Where-Object {{ $_.Type -eq '{tipo}' }} | "
            "ForEach-Object { $_.Index.ToString() + ' - ' + $_.Name + ' (' + $_.Type + ')' }"
        ),
    ]

    resultado = subprocess.run(comando, capture_output=True, text=True)
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
    comando = ["powershell", "-NoProfile", "-Command", f"Set-AudioDevice -Index {index}"]
    resultado = subprocess.run(comando, capture_output=True, text=True)
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
