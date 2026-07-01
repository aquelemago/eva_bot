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
- `requirements.txt`: lista `selenium` e `python-dotenv`.
- `credenciais.env.example`: exemplo das variaveis `URL`, `USUARIO`, `SENHA` e
  `MODO_TESTE`.
- `.gitignore`: ignora credenciais, ambiente virtual, logs e arquivos de
  runtime.
- `emails_processados.txt`: arquivo de runtime usado para registrar emails ja
  processados durante execucao.
- `logs/`: diretorio de runtime para `bot.log`.
- `venv/`: ambiente virtual local.

## Configuracao esperada

O script carrega variaveis de `credenciais.env` com `load_dotenv("credenciais.env")`.
O exemplo do projeto indica estas chaves:

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

Executar o bot:

```powershell
python main.py
```

Pre-condicoes:

- `credenciais.env` deve existir com `URL`, `USUARIO` e `SENHA`.
- O Chrome e o Selenium Manager precisam conseguir iniciar um WebDriver
  compativel.
- A conta usada precisa ter acesso ao menu HCM, Admissao Digital e
  Pre-admissoes.

## Saidas e efeitos colaterais

- Escreve logs em `logs/bot.log`.
- Redireciona `stdout` e `stderr` para console e arquivo de log.
- Recria `emails_processados.txt` no inicio da execucao.
- Abre o Chrome em janela maximizada e modo anonimo.
- Em modo normal, clica em `Reenviar` e confirma o reenvio.
- Em modo teste, reenvia mas nao registra o email em `emails_processados.txt`.
