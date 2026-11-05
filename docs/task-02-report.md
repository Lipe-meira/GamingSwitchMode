# TASK 02 — Relatório arquitetural

## Objetivo e situação

A TASK 02 separou a interface Tkinter, áudio, bandeja e controle de instância do
ponto de entrada, preservando o formato de configuração e os fluxos da TASK 01.
Antes, `audio_switcher.py` concentrava widgets, estado global, callbacks,
restauração de atalhos, filas, workers e ciclo de vida. `audio.py`,
`configuration.py` e `hotkeys.py` já isolavam as respectivas operações, mas a
coordenação e a apresentação permaneciam acopladas.

As correções da TASK 02.4.2 foram publicadas na branch de arquitetura. A TASK 02
ainda requer avaliação da revisão externa e das validações pendentes antes de ser
definitivamente encerrada.

## Estrutura e dependências

| Módulo | Responsabilidade atual |
| --- | --- |
| `audio_switcher.py` | Ponto de entrada: instancia `ApplicationController` e chama `run`. |
| `application.py` | Compõe dependências e coordena estado, ações, filas, inicialização e encerramento. |
| `main_window.py` | Constrói widgets Tk, apresenta listas/status/diálogos e recebe callbacks de ações. |
| `audio_service.py` | Consulta e ativa endpoints pelo backend injetado, publicando resultados na fila. |
| `audio.py` | Invoca PowerShell/AudioDeviceCmdlets, interpreta JSON e troca por ID. |
| `hotkeys.py` | Conflitos, registro e remoção transacionais, tokens e restauração de atalhos. |
| `configuration.py` | Schema, validação, migração, caminhos, backup, recuperação e escrita atômica. |
| `system_tray.py` | Ícone pystray, callbacks que publicam eventos e consulta de visibilidade. |
| `windows_instance.py` | Aquisição e fechamento do handle do mutex Windows. |

Os módulos extraídos nesta task incluem `application.py`, `main_window.py`,
`audio_service.py`, `system_tray.py` e `windows_instance.py`. O controlador importa
os serviços e a janela; `hotkeys.py` depende da validação de `configuration.py`.
O backend de áudio e a fila são passados ao serviço; os callbacks são fornecidos à
janela. A inspeção AST dos imports internos não encontrou ciclos. Os imports dos
nove módulos foram executados sem iniciar a aplicação.

`shortcuts.py` é um exemplo independente que captura Q, não é importado pelo
aplicativo. `ApplicationController.show_window`, `exit_app` e `create_image` são
encaminhamentos legados: os dois primeiros também são exercitados por testes e o
smoke test; o último não aparece no fluxo principal. Não foram removidos nesta
etapa documental. O controlador ainda contém lógica de apresentação de rótulos e
orquestração de ações, uma separação pragmática que pode ser revista quando houver
necessidade concreta.

## Inicialização, eventos e encerramento

1. `python audio_switcher.py` cria o controlador; imports não criam janela nem workers.
2. O controlador adquire o mutex, cria o Tk, enumera saídas, carrega configuração,
   cria `HotkeyManager` e `MainWindow`, restaura atalhos e apresenta avisos.
3. Inicia o worker serial de áudio, agenda o processamento da fila no Tk e inicia a
   bandeja. O fechamento da janela a oculta quando o ícone está visível.
4. Callbacks de atalhos e bandeja e o worker de áudio enfileiram eventos. O Tk
   consome até 100 eventos por ciclo e chama métodos de apresentação na thread da
   janela. A captura de teclado também é executada em thread separada e envia o
   resultado pela fila. A janela chama ações do controlador por callbacks explícitos.
5. Ao selecionar Sair, o controlador invalida o processamento posterior, fecha os
   handlers, coloca um sentinela na fila de áudio, solicita parada da bandeja,
   destrói a janela e fecha o handle do mutex. A rotina é protegida contra repetição
   e cobre inicialização parcial; fechamento da janela normalmente apenas a oculta.

O gerenciamento de atalhos e configurações foi preservado: IDs persistentes,
associações de endpoints indisponíveis, migração legada com confirmação, schema 1,
backup, escrita atômica, tratamento de conflitos e rollback. A task não introduziu
mudança de schema. `AudioSwitcher.spec` mantém `audio_switcher.py` como entrada e
inclui `modules/AudioDeviceCmdlets`; o build demonstrou que os imports são coletados.

## Correções direcionadas 02.4.2

- `tests/windows_smoke.py --send-input` usa `keyboard.send` diretamente, sem
  depender de um atributo inexistente do controlador; um teste com mock cobre a
  chamada. Não se executou o modo sintético nesta validação final.
- Se o ícone ainda não estiver visível ou a bandeja falhar, fechar a janela não a
  oculta. Uma exceção ou término inesperado do loop da bandeja é enviado à fila e
  o Tk volta a mostrar a janela. Ao fechar sem bandeja operacional, uma confirmação
  permite encerrar ou aguardar. Testes simulam falha e confirmam que a thread da
  bandeja não chama métodos da janela diretamente.
- A cobertura adicional inclui falha na construção da janela e liberação do mutex,
  encerramento repetido, eventos pendentes e trabalhos de áudio enfileirados.

## Evidências desta validação

- `python -m unittest discover -s tests -v`: **49 testes passaram**. Testes usam
  fakes/mocks para integração de áudio/teclado; testes da janela criam widgets Tk
  reais na sessão gráfica. Os cenários de falhas e de trabalhos pendentes são
  simulados, não dependem de dispositivos físicos.
- `python -m py_compile` e importação dos nove módulos principais: concluídos sem
  erros. Inspeção estática dos imports internos não identificou ciclos.
- `python tests/windows_smoke.py`: passou em Windows com Tk e bandeja reais,
  instância única, registro/edição/remoção/restauração de hooks, confirmação de
  legado e troca real por ID. A ativação foi **simulada pela fila**. O teste usa
  configuração temporária e restaura os padrões de áudio anteriores.
- `python -m PyInstaller --noconfirm --workpath <temporário>/work --distpath
  <temporário>/dist AudioSwitcher.spec`: build concluído. Os diretórios `build/` e
  `dist/` do projeto não foram usados pelo build. A execução interativa do `.exe`
  gerado nesta validação não foi realizada.

## Limites, problemas e TASK 03

- Teclas físicas, funcionamento efetivo de hotkeys em outros aplicativos, execução
  interativa do `.exe`, desconexão/reconexão física e endpoints homônimos reais
  continuam pendentes. O teste da referência a `keyboard.send` usa mock e não prova
  entrega de teclas sintetizadas ou físicas.
- O worker não é aguardado ao encerrar: tarefas de áudio já enfileiradas executam
  antes do sentinela e uma operação em andamento pode prosseguir após a janela ser
  destruída e o mutex liberado. Isso pode coincidir com uma nova instância. Avaliar
  política de cancelamento, sincronização e encerramento limitado na TASK 03.
- A criação de `Tk` e a primeira enumeração de áudio ocorrem sequencialmente na
  thread principal antes de iniciar o loop; o PowerShell tem timeout de 20 segundos.
  A interface pode demorar para aparecer quando essa consulta falha ou demora.
- A proteção da bandeja usa visibilidade observada e eventos de fim do loop; condições
  de corrida de criação/parada, falhas em threads internas do pystray e recuperação
  posterior merecem revisão de concorrência na TASK 03. A implementação não valida
  continuamente a presença visual do ícone na área de notificação do Windows.
- Falhas de leitura e gravação foram injetadas em testes; não foram exercitados corte
  de energia, ACLs restritivas ou disco cheio real. IDs podem mudar após reinstalação
  de drivers/Windows. O roteiro detalhado consta em `docs/task-01-report.md`.
- A aplicação ainda guarda referências a threads e estado mutável no controlador;
  revisão aprofundada de ownership, cancelamento, shutdown, erros e logging pertence
  à TASK 03. Não se deve alterar o comportamento atual sem testes direcionados.
