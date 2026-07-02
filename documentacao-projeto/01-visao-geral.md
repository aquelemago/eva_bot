# Visao geral

## Objetivo aparente

O projeto automatiza, via Selenium, o acesso ao sistema Senior X / HCM para
percorrer a area de admissao digital, localizar pre-admissoes na aba
`Em assinatura` e reenviar documentos com status `Em assinatura`.

O fluxo tambem possui um modo de teste controlado por variavel de ambiente. Em
modo de teste, o script executa o reenvio normalmente, mas nao registra o email
processado em `emails_processados.txt`.

## Arquivos do projeto

- `main.py`: script principal, contem todo o fluxo de automacao.
- `windows_service.py`: implementacao do Servico do Windows (pywin32).
- `requirements.txt`: lista `selenium`, `python-dotenv` e `pywin32`.
- `credenciais.env`: variaveis `URL`, `USUARIO`, `SENHA` e `MODO_TESTE`.
- `.gitignore`: ignora credenciais, ambiente virtual, logs e arquivos de
  runtime.
- `emails_processados.txt`: arquivo de runtime usado para registrar emails ja
  processados durante execucao.
- `logs/`: diretorio de runtime para `bot.log`.
- `venv/`: ambiente virtual local.

## Configuracao esperada

O script carrega variaveis de `credenciais.env` com `load_dotenv()`, resolvendo
o caminho absoluto via `_SCRIPT_DIR` (baseado em `__file__`). O projeto usa
caminhos absolutos para garantir funcionamento mesmo quando executado como
Servico do Windows (onde o diretorio de trabalho pode ser `C:\Windows\System32`).
As chaves esperadas sao:

```env
URL=
USUARIO=
SENHA=
MODO_TESTE=
```

`MODO_TESTE` tambem aceita fallback por `TEST_MODE`. Valores interpretados como
verdadeiro: `1`, `true`, `sim`, `yes`.

## Como executar

Instalar dependencias em um ambiente Python:

```powershell
pip install -r requirements.txt
```

### Execucao direta (console)

```powershell
python main.py
```

### Execucao como Servico do Windows (requer Windows e pywin32)

```powershell
python windows_service.py install --start auto
python windows_service.py start
python windows_service.py stop
python windows_service.py remove
```

Pre-condicoes:

- `credenciais.env` deve existir com `URL`, `USUARIO` e `SENHA`.
- O Chrome e o Selenium Manager precisam conseguir iniciar um WebDriver
  compativel.
- A conta usada precisa ter acesso ao menu HCM, Admissao Digital e
  Pre-admissoes.

## Saidas e efeitos colaterais

- Escreve logs em `logs/bot.log` com timestamps e separador entre execucoes.
- Redireciona `stdout` e `stderr` para console e arquivo de log, com timestamps em cada linha.
- Recria `emails_processados.txt` no inicio da execucao.
- Abre o Chrome em modo headless (sem janela visivel) e modo anonimo.
- Em modo normal, clica em `Reenviar` e confirma o reenvio.
- Em modo teste, reenvia mas nao registra o email em `emails_processados.txt`.
- Quando executado como servico, aguarda ate as 07:00, executa o bot, e repete
  o ciclo diariamente. Atende ao sinal de parada do SCM: interrompe o loop no
  proximo ciclo e executa cleanup (fecha Chrome, restaura streams, fecha log).
