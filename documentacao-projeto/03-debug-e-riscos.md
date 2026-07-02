# Debug e riscos

## Validacoes executadas

Inventario sem ler segredos:

```powershell
rg --files -g "!venv/**" -g "!.git/**" -g "!__pycache__/**" -g "!logs/**" -g "!credenciais.env"
```

Resultado observado:

```text
requirements.txt
main.py
windows_service.py
credenciais.env
```

Validacao de sintaxe:

```powershell
python -m py_compile main.py
```

Resultado: sem erro.

Leitura de logs:

```powershell
Get-ChildItem -Path logs -Force -File -ErrorAction SilentlyContinue
Select-String -Path logs\bot.log -Pattern "Erro|Critico|Falha|Nao foi possivel|Traceback|Exception"
```

Resultado observado durante a auditoria: sem entradas retornadas.
O log agora contem timestamps `[YYYY-MM-DD HH:MM:SS]` e separadores entre execucoes.

## Achados de debug estatico

1. `emails_processados.txt` e recriado no inicio de toda execucao.

   A funcao `reiniciar_emails_processados()` apaga o arquivo se ele existir e
   cria outro vazio. Depois disso, `main()` chama `carregar_emails_processados()`.
   Na pratica, o historico de execucoes anteriores nao e preservado. O arquivo
   funciona como controle durante a execucao atual, mas nao como historico entre
   execucoes.

2. O Chrome e iniciado antes da validacao das credenciais.

   `webdriver.Chrome(options=chrome_options)` roda antes de verificar se `URL`,
   `USUARIO` e `SENHA` existem. Se a configuracao estiver incompleta, o navegador
   pode abrir mesmo sem possibilidade de executar o fluxo.

3. Muitos seletores dependem de detalhes internos do DOM.

   O script usa IDs e classes especificos do front-end Senior X, alem de textos
   visiveis. Isso e esperado em automacao Selenium, mas aumenta risco de quebra
   quando a interface muda.

4. Existem varios `except Exception` amplos.

   Em alguns pontos isso e usado como fallback intencional de Selenium. O custo e
   que erros diferentes podem ser tratados da mesma forma, dificultando diagnostico
   quando uma falha real ocorre.

5. Ha uso misto de `WebDriverWait` e `time.sleep`.

   O script tem varias esperas fixas. Isso pode tornar a execucao lenta em dias
   bons e instavel em dias lentos. As esperas explicitas ajudam em alguns pontos,
   mas nao cobrem todo o fluxo.

6. `MODO_TESTE` nao registra email processado.

   Em modo teste, usuarios sao adicionados ao set em memoria, mas nao sao gravados
   em `emails_processados.txt`. Isso parece intencional para evitar registrar
   processamento real quando nao houve reenvio.

7. Chrome agora executa em modo headless.

   As flags `--start-maximized` foi substituida por `--headless=new`,
   `--no-sandbox`, `--disable-dev-shm-usage` e `--window-size=1920,1080`.
   O Chrome funciona sem janela visivel, permitindo execucao em servidores
   sem interface grafica. O comportamento e identico ao modo com janela,
   exceto pela ausencia de renderizacao visual.

8. Logs agora possuem formato profissional com timestamps e separadores.

   O `configurar_log()` foi simplificado: removeu a checagem de "Log iniciado."
   e agora sempre escreve um cabecalho com separador visual e timestamp da
   execucao. O `TeeOutput.write()` foi alterado para adicionar
   `[YYYY-MM-DD HH:MM:SS]` automaticamente em cada linha. No encerramento,
   o `finally` do `main()` escreve um rodape com "Execucao finalizada em ...".

9. Caminhos de arquivo agora sao absolutos com `_SCRIPT_DIR`.

   `ARQUIVO_PROCESSADOS`, `ARQUIVO_LOG` e `load_dotenv` usam
   `Path(__file__).parent.resolve()` para garantir funcionamento
   independentemente do diretorio de trabalho. Isso e necessario para execucao
   como Servico do Windows, onde o CWD pode ser `C:\Windows\System32`.

10. Adicionado mecanismo de parada graciosa via `threading.Event`.

    As funcoes `sinalizar_parada()` e `parada_sinalizada()` em `main.py`
    permitem que o servico interrompa o bot de forma controlada. O loop
    principal verifica o evento a cada iteracao, e o `finally` executa o
    cleanup completo.

11. Criado `windows_service.py` para execucao como Servico do Windows.

    A classe `EvabotService` gerencia o ciclo de vida usando `pywin32`. Ela
    inicia `main()` em uma thread separada e responde ao sinal de parada do
    SCM.

## Riscos operacionais

- Reenvio duplicado se a automacao for interrompida antes de registrar o email ou
  se a mesma pessoa reaparecer em execucao futura, ja que o arquivo e recriado.
- Falha por alteracao de layout, texto ou componente do Senior X.
- Falha por popup novo nao coberto pelos seletores atuais.
- Falha por Chrome/WebDriver incompatavel ou sem permissao no ambiente local.
- Headless pode ser detectado por alguns sites via User-Agent; se o Senior X bloquear, pode ser necessario falsear o User-Agent.
- Log pode crescer indefinidamente, pois `logs/bot.log` e aberto em modo append.
  Os separadores entre execucoes e timestamps facilitam a identificacao de
  cada sessao e a busca por eventos especificos.
- Chromedriver ou Chrome podem nao funcionar no contexto de servico Windows
  (usuario `SYSTEM` ou `LOCAL_SERVICE` sem perfil de usuario). Recomenda-se
  configurar o servico para executar com uma conta de usuario com perfil.
- `pywin32` e dependencia exclusiva do Windows; `windows_service.py` nao
  pode ser utilizado em Linux/macOS.
- O servico depende do `_SCRIPT_DIR` para localizar `credenciais.env`; o
  arquivo deve estar no mesmo diretorio de `main.py`.

## Comandos uteis para diagnostico futuro

Validar sintaxe:

```powershell
python -m py_compile main.py
python -m py_compile windows_service.py
```

Ver arquivos relevantes, sem segredos:

```powershell
rg --files -g "!venv/**" -g "!.git/**" -g "!__pycache__/**" -g "!logs/**" -g "!credenciais.env"
```

Buscar pontos sensiveis no codigo:

```powershell
rg -n "load_dotenv|os.getenv|webdriver.Chrome|WebDriverWait|time.sleep|except Exception|driver.quit|while True|execute_script|MODO_TESTE|emails_processados|_stop_event|sinalizar_parada|parada_sinalizada" main.py
```

Consultar erros recentes de log:

```powershell
Select-String -Path logs\bot.log -Pattern "Erro|Critico|Falha|Nao foi possivel|Traceback|Exception" | Select-Object -Last 30
```

Gerenciar o servico Windows:

```powershell
# Instalar e configurar inicializacao automatica
python windows_service.py install --start auto

# Iniciar
python windows_service.py start

# Verificar status
sc query Evabot

# Parar
python windows_service.py stop

# Remover
python windows_service.py remove
```
