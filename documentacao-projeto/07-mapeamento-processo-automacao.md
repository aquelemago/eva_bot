# Mapeamento do Processo da Automacao

## 1. Resumo do fluxo

A automacao e um script Python procedural em `main.py`. Ela carrega variaveis
de ambiente de `credenciais.env`, configura log em `logs/bot.log`, recria o
arquivo de controle `emails_processados.txt`, abre o Chrome via Selenium, acessa
o Senior X / HCM, navega ate `Admissao Digital > Pre-admissoes`, entra na aba
`Em assinatura`, identifica usuarios com botao `Acoes`, abre os detalhes de
cada usuario, acessa `Documentos enviados`, localiza documentos com status
`Em assinatura` e, em modo normal, executa `Reenviar` e confirma a acao.

Em modo de teste, controlado por `MODO_TESTE` ou `TEST_MODE`, o script executa o
reenvio normalmente, mas nao registra o email processado em `emails_processados.txt`.

## 2. Fluxo principal

| Ordem | Etapa | Funcao/arquivo | Entrada | Saida esperada | Dependencias | Possiveis falhas |
| ----- | ----- | -------------- | ------- | -------------- | ------------ | ---------------- |
| 1 | Carregar configuracao de ambiente | `main.py`, `load_dotenv("credenciais.env")` | Arquivo `credenciais.env` | Variaveis disponiveis via `os.getenv` | `python-dotenv`, arquivo local | Arquivo ausente, variaveis vazias, valores incorretos |
| 2 | Definir arquivos de runtime e modo de teste | `main.py`, constantes `ARQUIVO_PROCESSADOS`, `ARQUIVO_LOG`, `MODO_TESTE` | Variaveis `MODO_TESTE` ou `TEST_MODE` | Caminhos e modo booleano definidos | Sistema de arquivos, variaveis de ambiente | Valor inesperado de modo de teste |
| 3 | Configurar log | `configurar_log()` | `logs/bot.log` | `stdout` e `stderr` duplicados para console e log com timestamps `[YYYY-MM-DD HH:MM:SS]` por linha e cabecalho de execucao | Permissao de escrita em `logs/` | Falha ao criar diretorio ou abrir arquivo de log |
| 4 | Reiniciar controle de processados | `reiniciar_emails_processados()` | `emails_processados.txt` existente ou ausente | Arquivo recriado vazio | Sistema de arquivos | Falha de permissao; perda do historico de execucoes anteriores |
| 5 | Preparar Chrome | `main()` | Opcoes `--headless=new`, `--no-sandbox`, `--disable-dev-shm-usage`, `--window-size=1920,1080` e `--incognito` | Instancia `webdriver.Chrome` e `WebDriverWait` | Selenium, Chrome, Selenium Manager/WebDriver | Chrome ausente, driver incompativel, bloqueio do sistema operacional |
| 6 | Validar credenciais minimas | `main()` | `URL`, `USUARIO`, `SENHA` | Execucao continua somente se todas existirem | `credenciais.env` | Navegador pode abrir antes da validacao; variavel ausente encerra o fluxo |
| 7 | Acessar URL e autenticar | `main()` | URL, usuario, senha | Login submetido na pagina | Internet/rede, site Senior X, campos por ID | Timeout, credencial invalida, mudanca nos IDs `username-input-field`, `nextBtn`, `password-input-field`, `loginbtn` |
| 8 | Fechar popups iniciais | `fechar_popup_se_existir()` | Seletores `a.ui-dialog-titlebar-close`, `em.fas.fa-times` | Popups fechados se existirem | DOM da pagina, Selenium | Popup novo ou seletor alterado pode bloquear fluxo |
| 9 | Navegar ate Pre-admissoes | `navegar_ate_em_assinatura(..., primeira_vez=True)` | Menu HCM, `apps-menu-item-9`, `apps-menu-item-3` | Tela de pre-admissoes carregada | Permissoes da conta, DOM do menu | Falha de permissao, menu ausente, ID alterado, carregamento lento |
| 10 | Entrar no iframe interno | `switch_to_internal_frame()` | Iframes da pagina | Contexto do iframe com texto `Em assinatura` | Estrutura da pagina | Iframe nao encontrado apos retentativas |
| 11 | Abrir aba `Em assinatura` | `clicar_aba_em_assinatura()` | Elementos por XPath/texto | Aba selecionada | Texto visivel e roles da UI | Mudanca de texto, aba invisivel, clique interceptado |
| 12 | Selecionar 100 registros | `selecionar_100_registros()` | Dropdown do paginator | Lista configurada para 100 itens, se possivel | Componente `p-paginator`, Selenium | Dropdown ausente, opcao 100 indisponivel; a funcao retorna `False` sem interromper |
| 13 | Aguardar lista | `aguardar_lista_em_assinatura()` | DOM da lista | Lista detectada ou timeout | `obter_usuarios_acoes_lista()`, seletores da lista | Lista vazia, seletor alterado, carregamento lento |
| 14 | Coletar usuarios e botoes | `obter_usuarios_acoes_lista()` | DOM da lista | Lista de usuarios com nome, email e botao `Acoes` | JavaScript no navegador, estrutura `s-employee-data` | Mudanca na estrutura da tabela, e-mail nao encontrado, botao desalinhado |
| 15 | Filtrar pendentes | `main()` | Usuarios coletados e set `emails_processados` | Primeiro usuario pendente da tela | Arquivo de controle, campo email, botao `Acoes` | Usuarios sem email, todos ja processados, botao ausente |
| 16 | Abrir acoes do usuario | `clicar_acoes_usuario()` | Usuario pendente | Menu com `Detalhar` visivel | JavaScript, botao `Acoes`, menu da UI | Botao nao encontrado, clique falha, menu nao abre |
| 17 | Abrir detalhe do usuario | `clicar_item_menu("Detalhar")`, `clicar_ver_detalhes()` | Menu `Detalhar`, botao `Ver detalhes` | Tela de detalhes aberta | Textos da UI, Selenium waits | Item ou botao ausente, estado desabilitado, timeout |
| 18 | Abrir documentos enviados | `clicar_documentos_enviados()` | Aba `Documentos enviados` | Aba selecionada | Texto e role da aba | Aba nao encontrada ou nao clicavel |
| 19 | Localizar documento em assinatura | `clicar_acoes_documentos()` | Tabela `p-treetable`, status dos documentos | Retorna `processar`, `skip_expirado` ou `skip_sem_documento_acionavel` | DOM da tabela, `s-badge`, botao `btn-actions-pre-admission-documents` | Status inesperado, botao ausente, estrutura alterada |
| 20 | Reenviar, validar modo teste ou pular usuario | `processar_usuario_em_assinatura()` | Resultado de `clicar_acoes_documentos()`, `MODO_TESTE` | Documento `Em assinatura` segue fluxo; documento `Expirado` gera skip informativo | Estado do modo, menu `Reenviar`, status dos documentos | Modo configurado errado, item `Reenviar` nao aparece, usuario sem documento acionavel |
| 21 | Confirmar reenvio | `clicar_item_menu("Reenviar")`, `confirmar_reenviar()` | Item e dialogo de confirmacao | Reenvio confirmado | Dialogo Prime/UI, botao com texto `Reenviar` | Confirmacao nao aparece, seletor alterado, clique falha |
| 22 | Registrar processado ou tratado na execucao | `registrar_email_processado()` e set `emails_processados` | Email normalizado e resultado do processamento | Reenvio real grava no arquivo; skip marca o usuario em memoria nesta execucao | Sistema de arquivos, set em memoria | Falha de escrita; skip nao persiste entre execucoes |
| 23 | Atualizar e repetir | `driver.refresh()`, `navegar_ate_em_assinatura(..., primeira_vez=False)` | Pagina atual | Tela recarregada e lista atualizada | Navegador, rede, iframe, aba | Perda de contexto, recarregamento lento, lista nao atualiza |
| 24 | Finalizar | `finally` em `main()` | Driver e streams abertos | Rodape com `Execucao finalizada em ...` no log, navegador fechado, stdout/stderr restaurados, log fechado | Selenium, sistema de arquivos | Excecao antes de inicializar recursos; erro no fechamento |

## 3. Fluxograma textual

```text
[Inicio]
  ↓
[Carregar credenciais.env]
  ↓
[Configurar logs em logs/bot.log]
  ↓
[Recriar emails_processados.txt]
  ↓
[Configurar Chrome]
  ↓
[Abrir navegador com Selenium]
  ↓
[Ler URL, USUARIO e SENHA]
  ↓
{Variaveis obrigatorias existem?}
  ├─ Nao → [Registrar erro de credenciais e finalizar]
  └─ Sim
       ↓
     [Acessar URL]
       ↓
     [Preencher usuario e senha]
       ↓
     [Fechar popups iniciais se existirem]
       ↓
     [Abrir HCM > Admissao Digital > Pre-admissoes]
       ↓
     [Encontrar iframe interno]
       ↓
     [Abrir aba Em assinatura]
       ↓
     [Tentar selecionar 100 registros]
       ↓
     [Aguardar lista carregar]
       ↓
     [Coletar usuarios e botoes Acoes]
       ↓
     {Ha usuarios?}
       ├─ Nao → [Finalizar]
       └─ Sim
            ↓
          {Ha usuario pendente com email e botao Acoes?}
            ├─ Nao → [Finalizar]
            └─ Sim
                 ↓
               [Abrir Acoes do usuario]
                 ↓
               {Menu Detalhar abriu?}
                 ├─ Nao → [Contar tentativa sem avanco]
                 └─ Sim
                      ↓
                    [Detalhar > Ver detalhes > Documentos enviados]
                      ↓
                    [Localizar documento com status Em assinatura]
                      ↓
                    [Abrir Acoes do documento]
                      ↓
                     [Clicar Reenviar e confirmar]
                       ↓
                     {MODO_TESTE ativo?}
                       ├─ Sim → [Registrar email apenas em memoria]
                       └─ Nao → [Registrar email em memoria e no arquivo]
                      ↓
                    [Atualizar pagina e voltar para Em assinatura]
                      ↓
                    [Repetir loop]
```

## 4. Pontos de decisao

| Ponto de decisao | Condicao | Caminho A | Caminho B | Risco |
| ---------------- | -------- | --------- | --------- | ----- |
| Modo de teste | `MODO_TESTE` ou `TEST_MODE` em `{"1", "true", "sim", "yes"}` | Reenvia mas nao registra email no arquivo | Reenvia e registra email em `emails_processados.txt` | Valor errado pode nao filtrar reenvio real ou impedir teste |
| Log inicial | `configurar_log()` executado | Sempre escreve cabecalho com `Execucao iniciada em ...` e separador | — | Log cresce com cabecalhos, mas ganha rastreabilidade entre execucoes |
| Controle de processados | `emails_processados.txt` existe | Arquivo e removido e recriado | Arquivo e criado | Historico entre execucoes e perdido |
| Credenciais minimas | `URL`, `USUARIO`, `SENHA` existem | Continua login | Registra erro e finaliza | Chrome ja foi aberto antes dessa validacao |
| Popup existente | Selenium encontra seletor do popup dentro do timeout | Fecha popup | Continua sem fechar | Popup nao mapeado pode bloquear cliques posteriores |
| Iframe interno | Texto `Em assinatura` aparece no contexto atual ou iframe | Continua no frame correto | Tenta outros iframes por ate 5 ciclos | Mudanca de iframe impede toda a navegacao interna |
| Clique generico | `clicar_elemento()` tenta coordenada, click direto, JS, eventos e ENTER | Retorna `True` se verificacao passar | Tenta proximo metodo ou retorna `False` | Clique pode parecer executado sem abrir o estado esperado |
| Aba `Em assinatura` | Seletores encontram aba clicavel | Seleciona aba | Usa fallback por teclado com TAB/ENTER | Fallback por teclado depende do foco atual |
| Lista carregada | Usuarios ou sinais de lista aparecem ate timeout | Continua | Retorna `False` e apenas registra mensagem | Fluxo pode seguir com lista vazia ou incompleta |
| Selecionar 100 | Dropdown e opcao 100 aparecem | Seleciona 100 | Retorna `False` sem interromper | Pode processar apenas quantidade padrao da pagina |
| Usuarios encontrados | `obter_usuarios_acoes_lista()` retorna itens | Filtra pendentes | Finaliza com "Nenhum usuario encontrado" | Seletor quebrado pode parecer lista vazia |
| Usuarios pendentes | Usuario tem email, nao esta processado e tem botao | Processa primeiro pendente | Finaliza com "Nenhum usuario pendente" | Estado do arquivo ou email ausente pode pular usuarios |
| Acoes do usuario | Botao correlacionado por email, nome ou indice e encontrado | Clica e espera menu `Detalhar` | Retorna `False` | Mapeamento por posicao pode falhar se tabela e botoes desalinharem |
| Documento elegivel | Status normalizado igual a `em assinatura` e tem botao | Clica `Acoes` do documento e segue para `Reenviar` | Se todos os documentos estiverem `Expirado`, registra `[SKIP]` e retorna sem erro critico | Mudanca no texto/status pode impedir reenvio ou classificar usuario como sem documento acionavel |
| Documento sem acao de reenvio | Nao ha documento `Em assinatura` | Retorna `skip_expirado` quando todos estao `Expirado` | Retorna `skip_sem_documento_acionavel` para outros casos sem documento acionavel | Skip e marcado apenas em memoria na execucao atual |
| Confirmacao | Botao de confirmacao contem texto `Reenviar` | Confirma | Aguarda ate timeout e levanta excecao | Dialogo alterado quebra etapa final |
| Tentativas sem avanco | `processar_usuario_em_assinatura()` retorna `False` | Incrementa contador | Reseta contador quando processa | Apos 3 falhas encerra para evitar loop |
| Parada solicitada pelo servico | `parada_sinalizada()` retorna `True` | Encerra loop e executa cleanup | Continua processamento normal | Encerramento lento se `main()` estiver em operacao de longa duracao (ex: `time.sleep` ou `WebDriverWait`) |
| Excecao geral | Qualquer excecao no `try` principal | Registra `Erro Critico` | Executa `finally` | Erro amplo reduz diagnostico sem traceback completo |

## 5. Dependencias externas

| Dependencia | Onde e usada | Obrigatoria? | Como validar | Risco |
| ----------- | ------------ | ------------ | ------------ | ----- |
| Python | Execucao de `main.py` | Sim | Verificar versao e executar validacao de sintaxe | Ambiente Python incorreto |
| `selenium` | Imports e automacao do navegador | Sim | `requirements.txt` declara `selenium`; importar em ambiente local | Versao incompativel ou ausente |
| `python-dotenv` | `load_dotenv()` | Sim | `requirements.txt` declara `python-dotenv`; importar em ambiente local | Variaveis nao carregadas |
| `pywin32` | `windows_service.py` | Sim para execucao como servico | `requirements.txt` declara `pywin32`; importar em ambiente Windows | Servico nao pode ser instalado sem pywin32 |
| Chrome | `webdriver.Chrome(options=chrome_options)` | Sim | Abrir Chrome localmente; validar Selenium Manager/WebDriver | Navegador ausente ou bloqueado |
| WebDriver/Selenium Manager | Inicializacao do Chrome | Sim | Executar ambiente controlado com Selenium | Driver incompativel |
| `credenciais.env` | Variaveis `URL`, `USUARIO`, `SENHA`, `MODO_TESTE` | Sim para execucao real | Confirmar existencia e chaves sem expor valores | Credencial ausente ou incorreta |
| `credenciais.env.example` | Documentacao de chaves esperadas | Nao para runtime | Conferir chaves `URL`, `USUARIO`, `SENHA`, `MODO_TESTE` | Exemplo ficar desatualizado |
| Rede/internet | Acesso ao Senior X / HCM | Sim | Testar acesso manual ao URL no ambiente de execucao | Instabilidade, bloqueio corporativo, VPN |
| Site Senior X / HCM | Login, menus, pre-admissoes e documentos | Sim | Validar manualmente com a conta usada | Mudanca de layout, indisponibilidade |
| Permissoes da conta | Menus HCM, Admissao Digital, Pre-admissoes | Sim | Confirmar acesso manual aos menus | Menu ausente ou dados incompletos |
| Estrutura DOM do login | IDs `username-input-field`, `nextBtn`, `password-input-field`, `loginbtn` | Sim | Inspecionar pagina ou validar Selenium no ponto de login | Timeout por ID alterado |
| Estrutura DOM interna | Iframes, abas, tabelas, botoes e textos | Sim | Inspecionar DOM atual ou logs de seletores | Falhas de localizacao de elemento |
| `logs/` | `configurar_log()` e diagnostico | Sim para log | Conferir permissao de escrita | Sem log para diagnostico |
| `emails_processados.txt` | Controle de usuarios processados na execucao | Sim para controle local | Conferir criacao e escrita | Reprocessamento se execucao reinicia |
| Sistema operacional | Permissoes de arquivo e execucao do Chrome | Sim | Validar escrita em pasta e abertura de navegador | Bloqueio por permissao, antivirus, politicas |
| Agendamento interno | `windows_service.py`, `_proximo_horario()` | Sim para servico | Calcular horario com `datetime` | Fuso horario incorreto pode deslocar a execucao |

## 6. Pontos criticos

- O Chrome e iniciado antes da validacao de `URL`, `USUARIO` e `SENHA`.
- `emails_processados.txt` e recriado no inicio da execucao; ele nao preserva
  historico entre execucoes.
- O fluxo depende de textos e seletores especificos do Senior X, como
  `Em assinatura`, `Acoes`, `Detalhar`, `Ver detalhes`, `Documentos enviados`
  e `Reenviar`.
- A entrada no iframe depende de encontrar o texto `Em assinatura`.
- O mapeamento entre usuario e botao `Acoes` usa estrutura de tabela, email,
  nome ou indice; mudancas de layout podem associar botoes incorretamente.
- `selecionar_100_registros()` falha de forma nao fatal; a automacao continua
  mesmo se nao conseguir selecionar 100 registros.
- Usuarios com documentos apenas `Expirado` agora sao tratados como skip
  informativo, nao como erro critico; o bot nao deve clicar em `Acoes` do
  documento expirado.
- O skip de usuario e marcado em memoria na execucao atual para permitir avancar
  ao proximo usuario, mas nao e persistido em `emails_processados.txt`.
- Ha uso combinado de `WebDriverWait` e `time.sleep`, o que pode ser sensivel a
  lentidao do site.
- O `except Exception` principal registra apenas `Erro Critico: ...`, sem
  traceback completo.
- Logs podem conter dados pessoais exibidos pela aplicacao; ao compartilhar
  logs para diagnostico, remova nomes, e-mails e identificadores pessoais.

## 7. Etapa de falha

A etapa de falha identificada esta em `clicar_acoes_documentos()`, depois que o
usuario ja foi aberto e a aba `Documentos enviados` ja esta acessivel.

O padrao observado e:

- documento encontrado na tabela;
- status do documento igual a `Expirado`;
- zero documentos com status `Em assinatura`;
- a automacao continua aguardando documento `Em assinatura`;
- o fluxo nao avanca para o proximo usuario ate interrupcao manual.

A regra atualizada e: documento `Expirado` nao gera erro critico. Quando todos
os documentos encontrados estiverem `Expirado`, a funcao retorna
`skip_expirado`, registra log informativo e o loop principal marca o usuario
como tratado em memoria nesta execucao.

## 8. Evidencias encontradas

- `main.py` carrega `credenciais.env` com `load_dotenv()` usando caminho
  absoluto baseado em `_SCRIPT_DIR`.
- `main.py` define `ARQUIVO_PROCESSADOS = _SCRIPT_DIR / "emails_processados.txt"`
  e `ARQUIVO_LOG = _SCRIPT_DIR / "logs" / "bot.log"`.
- `main.py` interpreta `MODO_TESTE` e `TEST_MODE` como booleano por conjunto de
  valores textuais.
- `main.py` inicia Chrome com `--headless=new`, `--no-sandbox`, `--disable-dev-shm-usage`, `--window-size=1920,1080` e `--incognito`.
- `main.py` le `URL`, `USUARIO` e `SENHA` antes de acessar o site, mas depois
  de inicializar o Chrome.
- `main.py` usa os IDs `username-input-field`, `nextBtn`,
  `password-input-field` e `loginbtn` para login.
- `main.py` navega por `Gestao de Pessoas | HCM`, `Admissao Digital` e
  `Pre-admissoes`.
- `main.py` procura iframe interno pelo texto `Em assinatura`.
- `main.py` usa JavaScript para extrair usuarios, e-mails e botoes `Acoes`.
- `main.py` procura documentos em `p-treetable tbody.ui-treetable-tbody > tr`
  e filtra status normalizado igual a `em assinatura`.
- `main.py` agora retorna `skip_expirado` quando encontra documentos, mas todos
  os status normalizados sao `expirado`.
- `main.py` agora retorna `skip_sem_documento_acionavel` quando nao ha documento
  `Em assinatura` acionavel.
- O loop principal adiciona o email do usuario ao set `emails_processados` tambem
  quando o resultado e skip, evitando repetir o mesmo usuario na execucao atual.
- `requirements.txt` declara `selenium`, `python-dotenv` e `pywin32`.
- `credenciais.env` declara `URL`, `USUARIO`, `SENHA` e `MODO_TESTE`.
- `logs/bot.log` existe e contem registros de execucoes com finalizacao bem
  sucedida; os dados pessoais observados no log nao foram reproduzidos neste
  documento.
- `main.py` define `_stop_event = threading.Event()` e as funcoes
  `sinalizar_parada()` e `parada_sinalizada()` para controle de parada.
- `main.py` verifica `parada_sinalizada()` a cada iteracao do `while True`
  principal, interrompendo o fluxo quando o servico solicita parada.
- `windows_service.py` implementa `EvabotService` com metodos `SvcStop()` e
  `SvcDoRun()`, controlando o ciclo de vida da automacao como servico Windows.
- `windows_service.py` agenda a execucao diaria as 07:00 via
  `_proximo_horario()` e `_aguardar_proximo_horario()`, eliminando a
  necessidade do Agendador de Tarefas.

## 9. Hipoteses de causa

| Hipotese | Evidencia | Como validar |
| -------- | --------- | ------------ |
| Mudanca no DOM do login | O codigo depende de IDs fixos de campos e botoes de login | Informar mensagem de timeout e confirmar se os IDs ainda existem na pagina |
| Credenciais ou URL ausentes/incorretas | O codigo encerra se `URL`, `USUARIO` ou `SENHA` estiverem vazios | Confirmar apenas quais chaves existem no arquivo, sem compartilhar valores |
| Chrome ou WebDriver falhando | O codigo inicializa `webdriver.Chrome` antes da validacao das credenciais | Informar se a falha ocorre antes de abrir o navegador e enviar erro tecnico sem dados sensiveis |
| Menu HCM ou Pre-admissoes indisponivel para a conta | O codigo depende de textos/IDs de menu e permissao da conta | Validar acesso manual com a mesma conta ate `Pre-admissoes` |
| Iframe interno nao encontrado | `switch_to_internal_frame()` depende do texto `Em assinatura` dentro de algum iframe | Informar se o log mostra "Nao foi possivel encontrar o iframe interno" |
| Aba `Em assinatura` nao abre | A funcao usa XPaths por texto e fallback por teclado | Informar se a tela para antes ou depois de exibir a lista |
| Lista de usuarios nao e detectada | A coleta depende de `pre-admission-list.component`, `s-employee-data` e `.person-secondary-info` | Informar se existem usuarios visiveis manualmente quando o bot diz lista vazia |
| Botao `Acoes` do usuario nao abre `Detalhar` | O mapeamento correlaciona linhas e botoes por estrutura visual | Enviar trecho de log em torno de "Procurando botao 'Acoes' do usuario" sem PII |
| Aba `Documentos enviados` nao aparece | O codigo depende do texto da aba | Informar se `Ver detalhes` abre corretamente e se a aba existe manualmente |
| Documento com status `Expirado` causava repeticao | A etapa de documentos podia encontrar apenas `Expirado` e continuar aguardando `Em assinatura` | Validar em execucao com usuario que tenha apenas documentos expirados; o log deve mostrar `[SKIP]` e seguir para o proximo usuario |
| Documento com status `Em assinatura` nao e encontrado por mudanca de texto | O filtro exige status normalizado igual a `em assinatura` e botao de acoes | Informar quais status aparecem manualmente para o documento |
| Confirmacao de `Reenviar` mudou | `confirmar_reenviar()` procura botoes com texto `Reenviar` | Informar se o modal aparece e qual texto do botao de confirmacao |
| Lentidao do site causa timeout | Ha combinacao de waits e sleeps fixos | Informar se a falha e intermitente e em quais horarios ocorre |
| Servico Windows nao inicia | `pywin32` ausente ou Chrome sem perfil de usuario no contexto do servico | Verificar se `pywin32` esta instalado; configurar servico para rodar com conta de usuario com perfil Chrome |
| Servico nao para dentro do timeout do SCM | `main()` pode estar em `WebDriverWait` ou `time.sleep` longo | Aguardar o join de 30s; se persistir, o SCM forca a parada do processo |

## 10. Informacoes necessarias para correcao

Para corrigir com seguranca, forneca:

- mensagem de erro exata exibida no console ou em `logs/bot.log`;
- trecho do log em torno da falha, removendo nomes, e-mails e credenciais;
- funcao ou etapa onde a falha ocorre, se conhecida;
- se a falha ocorre antes ou depois de abrir o navegador;
- se a falha ocorre antes ou depois do login;
- se o login manual funciona com a mesma conta;
- se o menu `Gestao de Pessoas | HCM > Admissao Digital > Pre-admissoes`
  aparece manualmente;
- se a aba `Em assinatura` aparece manualmente;
- se a lista tem usuarios visiveis quando o bot falha;
- se o problema ocorre ao clicar `Acoes`, `Detalhar`, `Ver detalhes`,
  `Documentos enviados`, `Acoes` do documento, `Reenviar` ou confirmar;
- se o erro e sempre reproduzivel ou intermitente;
- se houve mudanca recente no site Senior X / HCM;
- print da tela no momento da falha, com dados pessoais ocultados;
- valor booleano pretendido para `MODO_TESTE`, sem compartilhar credenciais;
- ultimo comando usado para executar o bot.

## 11. Proximos passos recomendados

1. Reproduzir a falha uma vez com `MODO_TESTE=true`, se o objetivo for evitar
   reenvio real durante diagnostico.
2. Coletar o trecho final de `logs/bot.log` imediatamente apos a falha,
   removendo dados pessoais.
3. Identificar a ultima mensagem impressa antes da falha.
4. Informar se a falha ocorre antes do navegador, no login, na navegacao, na
   lista, no detalhe do usuario, no documento ou na confirmacao.
5. Validar manualmente no navegador a mesma etapa onde o bot parou.
6. Com a etapa confirmada, corrigir o menor trecho de `main.py` necessario em
   uma rodada separada.
