# 🎧 GamingSwitchMode

GamingSwitchMode é um utilitário para Windows criado em Python para trocar rapidamente entre dispositivos de saída de áudio.

A ideia é facilitar a vida de quem alterna com frequência entre, por exemplo:

* 🎧 Headset
* 🔊 Caixas de som
* 📺 Monitor / TV via HDMI
* 🎮 Outros dispositivos de áudio

Você pode trocar o dispositivo diretamente pela interface ou configurar atalhos globais no teclado.

## ✨ Funcionalidades

* Lista automaticamente os dispositivos de áudio disponíveis no Windows
* Troca o dispositivo de saída com um clique
* Permite criar atalhos de teclado para cada dispositivo
* Atalhos funcionam globalmente, mesmo com o programa minimizado
* Salva automaticamente os atalhos configurados
* Permite editar ou remover atalhos
* Atualiza a lista de dispositivos sem reiniciar o programa
* Continua rodando na bandeja do sistema
* Pode ser compilado como `.exe`

## 🖥️ Requisitos

* Windows 10 ou Windows 11
* Python 3
* PowerShell

Também é necessário instalar o módulo `AudioDeviceCmdlets` do PowerShell.

```powershell
Install-Module AudioDeviceCmdlets -Scope CurrentUser
```

Caso seja solicitada confirmação durante a instalação, aceite para continuar.

## 📦 Instalação

Clone o repositório:

```bash
git clone https://github.com/Lipe-meira/GamingSwitchMode.git
cd GamingSwitchMode
```

Instale as dependências Python:

```bash
pip install keyboard pystray pillow
```

Instale também o módulo responsável pelo controle dos dispositivos de áudio:

```powershell
Install-Module AudioDeviceCmdlets -Scope CurrentUser
```

## ▶️ Executando

Execute:

```bash
python audio_switcher.py
```

A aplicação abrirá exibindo os dispositivos de saída de áudio disponíveis.

## ⌨️ Configurando atalhos

1. Abra a aba **Atalhos**
2. Selecione um dispositivo
3. Clique em **Gravar atalho**
4. Pressione a combinação desejada
5. Clique em **Registrar atalho**

Exemplo:

```text
Ctrl + Alt + 1 → Headset
Ctrl + Alt + 2 → Caixa de som
Ctrl + Alt + 3 → Monitor
```

Os atalhos ficam salvos no arquivo:

```text
audio_switcher_config.json
```

Assim, eles são restaurados automaticamente na próxima execução.

## 🔽 Bandeja do sistema

Ao fechar a janela, o GamingSwitchMode não encerra imediatamente.

Ele continua executando na bandeja do sistema para que os atalhos permaneçam funcionando.

Pelo ícone da bandeja é possível:

* Abrir novamente a interface
* Encerrar completamente o programa

## 🛠️ Tecnologias utilizadas

* Python
* Tkinter
* PowerShell
* AudioDeviceCmdlets
* keyboard
* pystray
* Pillow
* PyInstaller

## 📂 Estrutura principal

```text
GamingSwitchMode/
│
├── audio_switcher.py    # Interface, atalhos e tray icon
├── audio.py             # Controle dos dispositivos de áudio
├── shortcuts.py         # Utilitários relacionados a atalhos
├── AudioSwitcher.spec   # Configuração do PyInstaller
├── build/
└── dist/
```

## 🏗️ Gerando o executável

Instale o PyInstaller:

```bash
pip install pyinstaller
```

Depois utilize o arquivo `.spec` do projeto:

```bash
pyinstaller AudioSwitcher.spec
```

O executável gerado ficará na pasta:

```text
dist/
```

## 🎯 Objetivo

O projeto nasceu para tornar mais rápido o processo de alternar o áudio durante o uso do PC, principalmente em setups onde é comum mudar entre headset, caixas de som e monitor.

Em vez de abrir as configurações de som do Windows toda vez, basta usar um atalho.

## 📄 Licença

Projeto desenvolvido para uso pessoal e aprendizado.

---

Desenvolvido por [Lipe-meira](https://github.com/Lipe-meira)
