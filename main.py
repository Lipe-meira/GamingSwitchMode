import audio
import warnings
warnings.filterwarnings("ignore")

def menu():
    print("=== Switcher ===")
    print("1 - Listar dispositivos de áudio")
    print("2 - (Futuro) Trocar dispositivo de áudio")
    print("0 - Sair")

while True:
    menu()
    opcao = input("Escolha: ")
    if opcao == "1":
        print(audio.listar_dispositivos())
    elif opcao == "0":
        break
