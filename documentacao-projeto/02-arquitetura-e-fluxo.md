# Arquitetura e fluxo

## Estrutura geral

O projeto e um unico script procedural em `main.py`. Nao ha pacotes internos,
testes automatizados ou configuracao de build alem de `requirements.txt`.

Dependencias importadas:

- `os`, `sys`, `time`, `pathlib.Path`.
- `python-dotenv` para carregar `credenciais.env`.
- `selenium` para abrir Chrome, localizar elementos, esperar condicoes e
  disparar acoes.

## Funcoes principais

- `configurar_log()`: cria `logs/`, abre `logs/bot.log` e duplica saida para
  console e arquivo.
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
- `clicar_acoes_usuario_por_indice(driver, indice)`: clica no botao `Acoes` de
  um usuario especifico.
- `processar_usuario_em_assinatura(driver, usuario, modo_teste=False)`: executa
  o fluxo de detalhes, documentos enviados e reenvio para um usuario.
- `navegar_ate_em_assinatura(driver, wait, primeira_vez=False)`: navega ate a
  tela e prepara a aba `Em assinatura`.
- `main()`: orquestra login, navegacao, loop de usuarios e finalizacao.

## Fluxo de execucao

1. Carrega `credenciais.env`.
2. Configura log com `TeeOutput`.
3. Recria `emails_processados.txt`.
4. Inicia Chrome com `--start-maximized` e `--incognito`.
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
    - em modo teste, para antes do reenvio;
    - em modo normal, clica `Reenviar` e confirma.
14. Atualiza a pagina e volta para `Em assinatura`.
15. Finaliza quando nao ha usuarios, nao ha pendentes ou ha 3 ciclos sem avanco.
16. Fecha o navegador no `finally`.

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
