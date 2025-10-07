import subprocess


def listar_dispositivos():
    comando = [
        "powershell",
        "-Command",
        "Get-AudioDevice -List | ForEach-Object { $_.Index.ToString() + ' - ' + $_.Name + ' (' + $_.Type + ')' }",
    ]

    # capture_output faz a captura da saída do comando poder ser usada no script
    # subprocess.run executa o programa externo (no caso, o PowerShell)
    # resultado vira um objeto
    resultado = subprocess.run(comando, capture_output=True, text=True)

    # acessa os dados de resultado e strip retira os espacos em branco do começo e do fim
    # split corta os resultados em linhas, cria uma lista /n eh o separador
    linhas = resultado.stdout.strip().split("\n")

    # cria um dicionário para armazenar os dispositivos
    dispositivos = {}
    print("Dispositivos de áudio disponíveis:\n")

    for linha in linhas:
        if linha:

            # Separa o - e no maximo uma vez
            # exemplo de como ficaria ['2', 'Alto-falantes (Realtek) (Playback)']
            # list unpacking
            index, nome = linha.split(" - ", 1)
            
            # uso do strip por seguranca, pra retirar qualquer espaco em branco
            dispositivos[index.strip()] = nome.strip()
            print(f"{index.strip()} - {nome.strip()}")
    return dispositivos

#------------------------------------------------------------------------------

def trocar_dispositivo(index):
    comando = ["powershell", "-Command", f"Set-AudioDevice -Index {index}"]
    subprocess.run(comando)

#------------------------------------------------------------------------------

if __name__ == "__main__":
    dispositivos = listar_dispositivos()
    escolha = input("\nDigite o índice do dispositivo que deseja usar: ").strip()

    if escolha in dispositivos:
        trocar_dispositivo(escolha)
        print(f"\n✅ Dispositivo de áudio alterado para: {dispositivos[escolha]}")
    else:
        print("\n❌ Índice inválido.")
