# Arquitetura e fluxo

## Estrutura geral

O projeto e composto por dois modulos principais:

- `main.py`: script procedural com toda a logica de automacao.
- `windows_service.py`: classe do Servico do Windows que controla o ciclo de
  vida da aplicacao (inicializacao, execucao e encerramento).

Nao ha pacotes internos, testes automatizados ou configuracao de build alem de
`requirements.txt`.

Dependencias importadas em `main.py`:

- `os`, `sys`, `time`, `threading`, `pathlib.Path`.
- `python-dotenv` para carregar `credenciais.env`.
- `selenium` para abrir Chrome, localizar elementos, esperar condicoes e
  disparar acoes.

Dependencias adicionais em `windows_service.py`:

- `pywin32` (`win32serviceutil`, `win32service`, `win32event`) para
  integracao com o Service Control Manager (SCM) do Windows.
- `threading` para executar `main()` em thread separada.

## Funcoes e classes principais

- `configurar_log()`: cria `logs/`, abre `logs/bot.log`, escreve cabecalho com
  timestamp da execucao e duplica saida para console e arquivo com timestamps
  em cada linha via `TeeOutput`.
- `reiniciar_emails_processados()`: apaga e recria `emails_processados.txt`.
- `carregar_emails_processados()`: le emails do arquivo de controle.
- `registrar_email_processado(email)`: adiciona email normalizado ao arquivo de
  controle.
- `switch_to_internal_frame(driver)`: procura o iframe onde aparece
  `Em assinatura`.
- `fechar_popup_se_existir(...)`: tenta fechar popups por seletor CSS.
- `clicar_elemento(...)`: tenta clicar usando coordenada, click direto,
  JavaScript, eventos de mouse e ENTER.
- `clicar_aba_em_assinatura(driver)`: seleciona a aba `Em assinatura`.
- `aguardar_lista_em_assinatura(driver)`: espera a lista carregar.
- `clicar_item_menu(driver, texto)`: clica em item de menu pelo texto.
- `clicar_ver_detalhes(driver)`: clica em `Ver detalhes`.
- `clicar_documentos_enviados(driver)`: abre a aba `Documentos enviados`.
- `selecionar_100_registros(driver)`: tenta selecionar 100 registros por pagina.
- `clicar_acoes_documentos(driver)`: localiza documento com status
  `Em assinatura` e clica em `Acoes`.
- `confirmar_reenviar(driver)`: confirma a acao `Reenviar`.
- `obter_usuarios_acoes_lista(driver)`: executa JavaScript para extrair usuarios
  e botoes `Acoes` da lista.
- `clicar_acoes_usuario(driver, usuario)`: clica no botao `Acoes` de
  um usuario especifico.
- `menu_visivel(driver, texto)`: verifica se um item de menu com o texto
  fornecido esta visivel na tela.
- `processar_usuario_em_assinatura(driver, usuario, modo_teste=False)`: executa
  o fluxo de detalhes, documentos enviados e reenvio para um usuario.
- `navegar_ate_em_assinatura(driver, wait, primeira_vez=False)`: navega ate a
  tela e prepara a aba `Em assinatura`.
- `sinalizar_parada()`: ativa o evento de parada para interromper o bot
  graciosamente.
- `parada_sinalizada()`: consulta se o evento de parada foi ativado.
- `main()`: orquestra login, navegacao, loop de usuarios e finalizacao.
- `EvabotService` (classe em `windows_service.py`): implementa o servico
  Windows com metodos `SvcStop()` para sinalizar parada e `SvcDoRun()` para
  iniciar `main()` em thread separada e monitorar seu ciclo de vida.

## Constantes e variaveis de controle

- `_SCRIPT_DIR`: caminho absoluto do diretorio onde `main.py` esta localizado,
  usado para resolver caminhos de arquivos independentemente do diretorio de
  trabalho.
- `_stop_event`: `threading.Event` que sinaliza a parada do bot quando o
  servico e interrompido.
- `ARQUIVO_PROCESSADOS`, `ARQUIVO_LOG`: agora resolvidos com `_SCRIPT_DIR`
  para garantir funcionamento correto em contexto de servico Windows.
- `MODO_TESTE`: mantido inalterado.

## Fluxo de execucao

1. Carrega `credenciais.env`.
2. Configura log com `TeeOutput`.
3. Recria `emails_processados.txt`.
4. Inicia Chrome com `--headless=new`, `--window-size=1920,1080` e `--incognito`.
5. Le `URL`, `USUARIO` e `SENHA`.
6. Acessa a URL e realiza login por IDs:
   - `username-input-field`
   - `nextBtn`
   - `password-input-field`
   - `loginbtn`
7. Fecha popups iniciais se existirem.
8. Navega pelos menus:
   - `Gestao de Pessoas | HCM`
   - `Admissao Digital`
   - `Pre-admissoes`
9. Entra no iframe interno.
10. Abre a aba `Em assinatura`.
11. Tenta selecionar 100 registros por pagina.
12. Obtem usuarios e botoes `Acoes`.
13. Para cada usuario pendente da tela:
    - abre `Acoes`;
    - clica em `Detalhar`;
    - clica em `Ver detalhes`;
    - abre `Documentos enviados`;
    - localiza documento com status `Em assinatura`;
    - abre `Acoes` do documento;
    - em modo teste, reenvia mas nao registra o email em `emails_processados.txt`;
    - em modo normal, clica `Reenviar` e confirma.
14. Atualiza a pagina e volta para `Em assinatura`.
15. A cada iteracao do loop, verifica `parada_sinalizada()`: se o servico
    solicitou parada, encerra o loop.
16. Finaliza quando nao ha usuarios, nao ha pendentes, ha 3 ciclos sem avanco
    ou a parada foi solicitada.
17. Fecha o navegador no `finally`.

## Execucao como Servico do Windows

Quando executado via `windows_service.py`, o fluxo e:

1. `EvabotService.SvcDoRun()` e chamado pelo Service Control Manager.
2. Uma thread separada executa `main()` com toda a logica de automacao.
3. A thread principal fica em loop monitorando:
   - o evento de parada do SCM (`hWaitStop`);
   - se a thread do bot ainda esta viva.
4. Quando o administrador para o servico, `SvcStop()` e chamado:
   - reporta `SERVICE_STOP_PENDING` ao SCM;
   - aciona `sinalizar_parada()` para interromper `main()`;
   - aciona `hWaitStop` para liberar a thread principal.
5. A thread principal aguarda a finalizacao da thread do bot (join com 30s de
   timeout).
6. O servico e encerrado de forma limpa.

## Seletores importantes

O script depende fortemente de IDs, classes e textos do front-end Senior X,
incluindo:

- `apps-menu-item-9`
- `apps-menu-item-3`
- `pre-admission-list.component`
- `pre-admission-list-actions-button-`
- `s-employee-data`
- `.person-secondary-info`
- `p-treetable tbody.ui-treetable-tbody > tr`
- `btn-actions-pre-admission-documents`
- textos `Em assinatura`, `Acoes`, `Detalhar`, `Ver detalhes`,
  `Documentos enviados`, `Reenviar`.

Qualquer mudanca no DOM ou nos textos pode quebrar o fluxo.
