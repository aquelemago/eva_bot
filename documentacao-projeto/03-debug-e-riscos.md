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
credenciais.env.example
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

## Riscos operacionais

- Reenvio duplicado se a automacao for interrompida antes de registrar o email ou
  se a mesma pessoa reaparecer em execucao futura, ja que o arquivo e recriado.
- Falha por alteracao de layout, texto ou componente do Senior X.
- Falha por popup novo nao coberto pelos seletores atuais.
- Falha por Chrome/WebDriver incompatavel ou sem permissao no ambiente local.
- Headless pode ser detectado por alguns sites via User-Agent; se o Senior X bloquear, pode ser necessario falsear o User-Agent.
- Log pode crescer indefinidamente, pois `logs/bot.log` e aberto em modo append.

## Comandos uteis para diagnostico futuro

Validar sintaxe:

```powershell
python -m py_compile main.py
```

Ver arquivos relevantes, sem segredos:

```powershell
rg --files -g "!venv/**" -g "!.git/**" -g "!__pycache__/**" -g "!logs/**" -g "!credenciais.env"
```

Buscar pontos sensiveis no codigo:

```powershell
rg -n "load_dotenv|os.getenv|webdriver.Chrome|WebDriverWait|time.sleep|except Exception|driver.quit|while True|execute_script|MODO_TESTE|emails_processados" main.py
```

Consultar erros recentes de log:

```powershell
Select-String -Path logs\bot.log -Pattern "Erro|Critico|Falha|Nao foi possivel|Traceback|Exception" | Select-Object -Last 30
```
