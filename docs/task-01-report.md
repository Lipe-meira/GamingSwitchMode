# Task 01 — IDs estáveis e persistência de atalhos

Implementação na branch `fix/stable-audio-devices`. Sem push, merge ou publicação.

## Diagnóstico e escopo

Antes da mudança, `audio.py` interpretava texto formatado e usava `Index` como chave
e argumento de `Set-AudioDevice`. Em `audio_switcher.py`, o mesmo índice identificava
botões, callbacks e o JSON; a seleção pelo nome confundia endpoints homônimos. A
inicialização removia associações ausentes ou com erro de registro e regravava o JSON.
A edição removia handlers existentes antes de tentar instalar o novo.

O fluxo anterior foi revisto desde a leitura (`load_hotkeys`) até registro,
edição, remoção, restauração e gravação na saída. `shortcuts.py` é um exemplo
independente de leitura da tecla Q e não participa do aplicativo.

Foram preservados stack, abas, ações, bandeja, instância única e arquivo `.spec`.
As únicas separações são persistência e transações de atalhos, permitindo testes
sem dispositivos físicos. Não foram adicionados perfis, controles de volume,
microfone, inicialização automática, instalador ou atualização.

## Arquivos

| Arquivo | Mudança |
| --- | --- |
| `audio.py` | JSON com ID/Name/Type/Index; troca por ID; dados codificados em UTF-8/base64 antes de entrar no script PowerShell; timeout e erros tratados |
| `audio_switcher.py` | Integração por ID, estados disponível/indisponível/legado, confirmação de migração, filas entre threads e Tk, entrada `main()` sem efeitos ao importar |
| `configuration.py` (novo) | Schema, validação, diretório do usuário, migração, backup, recuperação e gravação atômica |
| `hotkeys.py` (novo) | Detecção de conflitos, registro e edição com rollback, tokens de ativação e restauração sem apagar dados |
| `tests/__init__.py`, `test_audio.py`, `test_config.py`, `test_hotkeys.py`, `test_ui.py` (novos) | Suíte unitária com fakes/mocks |
| `tests/windows_smoke.py` (novo) | Teste integrado opcional em sessão Windows |
| `README.md`, este relatório | Formato, migração, recuperação, uso e validação |

`requirements.txt`, `AudioSwitcher.spec` e o módulo incluído foram analisados e não
precisaram de alterações. Os imports locais são detectados pelo PyInstaller. Arquivos
preexistentes modificados em `build/` e `dist/` foram preservados e excluídos do commit.

## Configuração, migração e recuperação

Local: `%APPDATA%\GamingSwitchMode\config.json`; se APPDATA não estiver definida,
usa `AppData\Roaming` na pasta pessoal. Não depende de `_MEIPASS`, do diretório de
instalação ou de privilégios de administrador para gravar.

O schema 1 contém `bindings` com `device_id`, `name`, `type`, `hotkey` e `unresolved`
com `legacy_index`, `hotkey`, `source`. Metadados de origem ficam em `migration`;
depois da confirmação, a associação preserva o registro legado no campo `legacy`.
Campos adicionais são preservados, possibilitando evolução. Índices atuais não são
identidades persistentes. O README contém um exemplo completo.

Na ausência da configuração nova/backup, procura o JSON antigo junto do script ou
executável, depois no diretório de trabalho. Copia o original atomicamente para
`legacy-original.json.bak` no diretório do usuário antes de gravar o schema novo.
Se já existir um original diferente, cria outro backup com identificador único.
Isso também permite importar de um diretório de instalação sem permissão de escrita.
O original não é modificado. A presença do schema novo impede reimportação: a migração
é idempotente. Também há suporte a um JSON legado encontrado no próprio destino novo.

**Limite fundamental:** índice antigo não comprova a identidade do endpoint atual.
Nenhuma associação legada é executada automaticamente. O usuário seleciona a pendência,
edita, escolhe o endpoint e confirma; a combinação permanece preenchida. Pendências
também reservam combinações para evitar conflitos silenciosos e podem ser removidas
explicitamente. Se já houver um atalho no endpoint escolhido, a confirmação aplica a
combinação escolhida a esse endpoint, como na edição normal.

Ao salvar, valida os dados e preserva a configuração anterior válida em
`config.json.bak`, também por escrita atômica. O temporário fica no mesmo diretório,
é sincronizado e substituído com `os.replace`. Falha de backup ou substituição aborta
a alteração e mantém os handlers anteriores. Temporários são limpos.

JSON ilegível é recuperado de backup validado; antes, o arquivo danificado é copiado
para `config.json.invalid-<identificador>`. Um destino ausente também pode ser
recuperado do backup. Sem backup válido, erros de leitura/permissão ou schema
desconhecido impedem gravação, preservando os dados e exibindo erro. Corrija/restaure
o arquivo e reinicie. Schema estruturalmente inválido também é protegido; não se
tenta converter silenciosamente dados não reconhecidos.

## Disponibilidade e registro

Dispositivos ausentes continuam em `bindings`. Seus hooks permanecem registrados;
ao ativar, o worker consulta novamente a enumeração e só troca se encontrar o mesmo
ID. Ausência gera status sem encerrar nem bloquear o Tk. Ao retornar com o mesmo ID,
o atalho funciona sem cadastro adicional. Atualizar lista ou ativar atualiza a
disponibilidade exibida. Nomes iguais não se fundem: seleção e callbacks usam IDs.

Uma edição instala o novo hook antes de persistir e desativar o anterior. Se o
registro ou a gravação falhar, mantém o anterior; o novo fica inativo e é removido.
Tokens invalidam callbacks antigos ou já enfileirados. Repetir um registro idêntico
reutiliza o hook. Conflitos são comparados pelas combinações de scan codes que a
própria biblioteca resolve, incluindo aliases e ordem de modificadores. Registros
conflitantes restaurados ficam inativos e visíveis, sem exclusão de dados.

Em uma falha excepcional de remoção de hook, seu token fica inválido, o erro é
registrado e há nova tentativa na saída. Não é possível garantir a liberação do
recurso do sistema quando a biblioteca falha; o callback residual não ativa áudio.
Callbacks de teclado, captura e bandeja só enviam eventos. Tk consome a fila na
thread principal; um worker serializa as chamadas PowerShell.

## Verificação executada

- `python -m unittest discover -v`: **32 testes passaram**, sem hardware real.
  Cobrem serialização, extensibilidade, migração repetida, prioridade da configuração
  nova, backup/recuperação, falhas de leitura, backup e substituição, arquivos ausentes
  e inválidos, schema incompatível, desconexão/reconexão simulada, índices alterados,
  nomes duplicados, criação/edição/remoção/restauração, conflitos, falhas de registro
  e persistência, callbacks obsoletos e fronteira entre threads e UI.
- Compilação de sintaxe e importação dos quatro módulos, sem abrir interface ao importar.
- PowerShell real: o manifesto e o módulo carregado informam **3.1.0.2**; inspeção de
  `Get-Command Set-AudioDevice` confirmou `ID`, `DefaultOnly` e `CommunicationOnly`.
  Enumeração real retornou cinco saídas com os quatro campos necessários.
- `python tests/windows_smoke.py`: passou com Tk, bandeja e mutex reais, registro,
  edição, restauração e remoção reais no `keyboard`, persistência temporária,
  confirmação de legado e `Set-AudioDevice -ID`. A ativação foi simulada na fila.
  Consultas reais confirmaram tanto o padrão de reprodução quanto o de comunicação
  no ID solicitado. Os padrões originais foram restaurados no `finally`.
- PyInstaller 6.22.2 com o `.spec` existente: build em diretório temporário, fora de
  `build/` e `dist/` do repositório. Nenhum binário gerado integra o commit.
- Revisão do diff e verificação de whitespace.

A documentação oficial de [AudioDeviceCmdlets](https://github.com/frgnca/AudioDeviceCmdlets#readme)
indica que `-ID`, assim como `-Index` sem flags adicionais, define padrão e comunicação.
Esse comportamento foi mantido e verificado no módulo incluído. A documentação do
[keyboard](https://github.com/boppreh/keyboard#api) confirma callbacks assíncronos e
remoção pelo handle retornado.

## Limites da validação e riscos restantes

- A tentativa de ativação por teclas sintetizadas terminou em timeout; um teste
  isolado de `keyboard` também não recebeu a combinação sintetizada nesta sessão.
  Não se considera validado o acionamento por teclas físicas. O smoke test dispõe de
  `--send-input` para repetir a tentativa em uma sessão que entregue esses eventos.
- Desconectar/reconectar hardware, alteração real de índices entre boots e nomes
  duplicados físicos foram simulados, não realizados no hardware desta máquina.
- A execução interativa do `.exe` final precisa ser verificada manualmente; o build
  bem-sucedido não comprova todos os fluxos do executável.
- Não houve validação de corte de energia, antivírus, ACLs reais restritivas ou
  disco cheio real; as falhas de I/O foram injetadas nos testes.
- Reinstalar driver/Windows pode gerar ID diferente; não há reassociação automática
  por nome ou índice. É necessário cadastrar o novo ID e remover o anterior.
- Conflitos internos são detectados. Atalhos reservados pelo Windows ou interferência
  de outros aplicativos exigem verificação no ambiente do usuário.
- Recuperação pelo backup pode voltar à edição anterior. Os originais migrados e
  arquivos inválidos são mantidos para recuperação manual.

## Roteiro manual no Windows

1. Execute a suíte unitária e depois `python audio_switcher.py`. Para testar sem sua
   configuração pessoal, execute em um novo PowerShell definindo `$env:APPDATA` para
   uma pasta temporária da sua escolha antes de iniciar o Python.
2. Cadastre atalhos diferentes para duas saídas. Pressione as teclas físicas e confira
   os padrões de reprodução/comunicação nas configurações do Windows.
3. Edite um atalho; confira que o anterior para de atuar e o novo funciona. Tente
   cadastrar a mesma combinação em outra saída: deve informar conflito e manter o
   registro anterior. Remova um selecionado e confirme que só ele é excluído.
4. Feche a janela para a bandeja. Pressione o atalho físico, reabra pelo ícone e tente
   abrir uma segunda instância. Deve permanecer somente uma instância.
5. Encerre pela bandeja e reinicie. Confira a configuração em
   `%APPDATA%\GamingSwitchMode\config.json` e a restauração dos atalhos.
6. Com um atalho salvo para um USB/HDMI, desconecte o dispositivo e inicie o app.
   Confira **Indisponivel**. Ative o atalho: deve informar ausência sem apagar dados.
   Reconecte; pressione de novo e use **Atualizar lista**. Repita após reiniciar o
   Windows e compare `Index`/`ID` em `Get-AudioDevice -List`.
7. Em configuração de usuário isolada, coloque um JSON antigo junto do script/exe.
   Inicie: deve criar backup no diretório do usuário e mostrar pendências inativas.
   Edite uma, selecione o dispositivo e confirme sem regravar a combinação. Reinicie
   duas vezes e verifique que a pendência não reaparece nem duplica o registro.
8. Teste saídas homônimas, confirmando IDs distintos. Não use somente o nome para
   conferir a saída selecionada.
9. Após duas gravações válidas, encerre e danifique deliberadamente uma **cópia de
   teste** de `config.json`: reinicie e confira recuperação/arquivo `.invalid-*`.
   Sem backup válido, confira o erro e a preservação do arquivo. Em uma pasta de
   teste com gravação negada, tente editar: o atalho anterior deve continuar ativo.
10. Gere `pyinstaller AudioSwitcher.spec`. Copie apenas o executável para uma pasta
    sem os scripts/módulos externos e repita os passos 2–7. Teste também uma pasta
    de instalação sem permissão de gravação para o usuário comum: a configuração e
    o backup de migração devem continuar no APPDATA.
