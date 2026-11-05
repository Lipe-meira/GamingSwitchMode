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

O repositório inclui o módulo `AudioDeviceCmdlets` 3.1.0.2, carregado pelo aplicativo
e incluído pelo PyInstaller. A instalação abaixo é uma alternativa quando esse
módulo não estiver junto do aplicativo:

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
python -m pip install -r requirements.txt
```

Se o módulo incluído não estiver disponível, instale a alternativa no usuário:

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

Os atalhos ficam salvos por usuário, sem exigir administrador:

```text
%APPDATA%\GamingSwitchMode\config.json
```

Assim, eles são restaurados automaticamente na próxima execução.

O aplicativo associa cada atalho ao **ID do endpoint**, independentemente do índice
atual ou de nomes repetidos. Dispositivos ausentes permanecem na lista de atalhos
como **Indisponivel**, podem ser editados/removidos e voltam a funcionar quando
retornam com o mesmo ID. Use **Atualizar lista** para atualizar a interface; cada
ativação também consulta os dispositivos novamente.

Os rótulos começam com um sufixo único do ID para distinguir nomes iguais, mesmo
quando são longos. O ID completo é preservado na configuração e usado na troca.

Na primeira execução, o aplicativo procura `audio_switcher_config.json` junto do
script/executável e, como alternativa, no diretório de trabalho. O arquivo original
é preservado e copiado para `legacy-original.json.bak` no diretório da configuração
do usuário antes da importação. Uma configuração nova válida tem prioridade.

Como o JSON antigo só contém índices, seus atalhos aparecem como **Legado — confirmar
dispositivo** e ficam inativos. Selecione um, clique em **Editar selecionado**, escolha
o dispositivo correto e clique em **Registrar atalho**. Confirme a associação: a
combinação antiga já estará preenchida. Não é possível deduzir com segurança o ID
original a partir do índice antigo.

Combinações conflitantes (inclusive aliases como `control`/`ctrl` e ordem diferente
dos modificadores) são recusadas, preservando o atalho existente. Falhas ao registrar
ou salvar também preservam a associação anterior. Atalhos que falharem na restauração
permanecem salvos; **Atualizar lista** tenta registrá-los novamente.

### Formato e recuperação

```json
{
  "schema_version": 1,
  "bindings": [
    {
      "device_id": "{0.0.0.00000000}.{exemplo-id}",
      "name": "Headset",
      "type": "Playback",
      "hotkey": "ctrl+alt+1"
    }
  ],
  "unresolved": [
    {"legacy_index": "2", "hotkey": "ctrl+alt+2", "source": "caminho-antigo"}
  ]
}
```

`bindings` contém associações confirmadas; `unresolved`, as pendências legadas.
A migração acrescenta `migration` com origem, backup e versão anterior; ao confirmar
uma pendência, seus dados ficam no campo `legacy` da associação. Campos adicionais
são preservados. `Index` é apenas diagnóstico de enumeração e não é persistido como
identidade. Versões de schema desconhecidas bloqueiam gravações para evitar perda.

As gravações usam arquivo temporário no mesmo diretório, `flush`/`fsync` e substituição
atômica. Antes de substituir uma configuração válida existente, sua versão anterior
é salva atomicamente em `config.json.bak`. Um JSON ilegível pode ser recuperado desse
backup: o arquivo danificado é preservado como `config.json.invalid-<identificador>`.
Sem backup válido, ou diante de erro de permissão/schema não suportado, a aplicação
mostra o erro e protege os dados; corrija/restaure o arquivo e reinicie. O backup pode
representar a edição anterior, não necessariamente a última tentativa de gravação.

Se um driver ou o Windows gerar **outro ID**, a identidade anterior continuará
indisponível. Cadastre o novo endpoint e remova a associação anterior explicitamente.
IDs não garantem continuidade após reinstalação de drivers/Windows.

## 🔽 Bandeja do sistema

Ao fechar a janela, o GamingSwitchMode não encerra imediatamente. Se o ícone da
bandeja ainda não estiver visível ou falhar, a janela permanece aberta e informa o estado.

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
├── audio_switcher.py    # Entrada mínima; chama ApplicationController
├── application.py       # Coordenação, estado, eventos e ciclo de vida
├── main_window.py       # Construção e apresentação Tkinter
├── audio_service.py     # Consulta/ativação e eventos de áudio
├── audio.py             # PowerShell e AudioDeviceCmdlets
├── hotkeys.py           # Registro transacional e restauração de atalhos
├── configuration.py     # Schema, migração, backup e gravação atômica
├── system_tray.py       # Ícone, callbacks e disponibilidade da bandeja
├── windows_instance.py  # Aquisição e liberação do mutex Windows
├── modules/             # AudioDeviceCmdlets incluído
├── tests/               # Testes automatizados e smoke test Windows opcional
├── docs/                # Relatórios das tarefas
├── shortcuts.py         # Exemplo independente de captura da tecla Q
├── AudioSwitcher.spec   # Entrada e recursos do PyInstaller
└── requirements.txt
```

`ApplicationController` compõe os serviços, restaura atalhos, cria a janela e
inicia workers e bandeja. A interface envia ações por callbacks e recebe dados
para apresentação; não constrói comandos PowerShell nem grava configurações.
Os callbacks de teclado e bandeja publicam eventos em uma fila processada no
Tk. Um worker serializa operações de áudio. Ao sair, o controlador fecha os
atalhos, sinaliza o worker, para a bandeja, destrói a janela e libera o mutex.
A operação de áudio em andamento não é aguardada; consulte o relatório da TASK 02.

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

## Testes e validação

```powershell
python -m unittest discover -s tests -v
python -m py_compile audio_switcher.py application.py main_window.py audio_service.py audio.py configuration.py hotkeys.py system_tray.py windows_instance.py
python -c "import audio_switcher, application, main_window, audio_service, audio, configuration, hotkeys, system_tray, windows_instance"
```

Os testes usam fakes/mocks para áudio e teclado, sem dispositivos físicos; os testes
de `MainWindow` criam uma janela Tk e exigem uma sessão gráfica disponível.
O teste integrado opcional exige uma sessão de desktop Windows:

```powershell
python tests/windows_smoke.py
```

Ele usa configuração temporária, Tkinter/bandeja e registro real de hooks; simula
o callback na fila, aplica o ID da saída atual e restaura os padrões anteriores.
`python tests/windows_smoke.py --send-input` tenta acionar os hooks com teclas
sintetizadas. Isso pode falhar em sessões remotas/isoladas; valide teclas físicas
manualmente. Veja o [relatório da TASK 02](docs/task-02-report.md) e o
[roteiro da TASK 01](docs/task-01-report.md).

## 🎯 Objetivo

O projeto nasceu para tornar mais rápido o processo de alternar o áudio durante o uso do PC, principalmente em setups onde é comum mudar entre headset, caixas de som e monitor.

Em vez de abrir as configurações de som do Windows toda vez, basta usar um atalho.

## 📄 Licença

Projeto desenvolvido para uso pessoal e aprendizado.

---

Desenvolvido por [Lipe-meira](https://github.com/Lipe-meira)
