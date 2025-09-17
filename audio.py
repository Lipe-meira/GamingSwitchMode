import subprocess

def listar_dispositivos():
    comando = [
        "powershell",
        "-Command",
        "Get-AudioDevice -List | ForEach-Object { $_.Index.ToString() + ' - ' + $_.Name + ' (' + $_.Type + ')' }"
    ]
    resultado = subprocess.run(comando, capture_output=True, text=True)
    linhas = resultado.stdout.strip().split("\n")
    dispositivos = {}
    print("Dispositivos de áudio disponíveis:\n")
    for linha in linhas:
        if linha:
            index, nome = linha.split(" - ", 1)
            dispositivos[index.strip()] = nome.strip()
            print(f"{index.strip()} - {nome.strip()}")
    return dispositivos

def trocar_dispositivo(index):
    comando = [
        "powershell",
        "-Command",
        f"Set-AudioDevice -Index {index}"
    ]
    subprocess.run(comando)

if __name__ == "__main__":
    dispositivos = listar_dispositivos()
    escolha = input("\nDigite o índice do dispositivo que deseja usar: ").strip()
    
    if escolha in dispositivos:
        trocar_dispositivo(escolha)
        print(f"\n✅ Dispositivo de áudio alterado para: {dispositivos[escolha]}")
    else:
        print("\n❌ Índice inválido.")
