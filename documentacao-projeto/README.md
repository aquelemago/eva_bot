# Documentacao do projeto

Data da auditoria: 2026-05-28.

Este diretorio documenta o estado existente do projeto `evabot`. Nenhum codigo
foi alterado nesta documentacao.

## Escopo observado

- Entrada principal: `main.py`.
- Dependencias declaradas: `selenium` e `python-dotenv`.
- Configuracao esperada: `credenciais.env`, conforme `credenciais.env.example`.
- Arquivos de runtime: `emails_processados.txt` e `logs/bot.log`.
- Diretorios ignorados para leitura de projeto: `.git/`, `venv/`, `__pycache__/` e `logs/`.

## Arquivos neste diretorio

- `01-visao-geral.md`: objetivo, entradas, saidas e modo de uso observado.
- `02-arquitetura-e-fluxo.md`: funcoes, fluxo Selenium e responsabilidades.
- `03-debug-e-riscos.md`: validacoes executadas, achados e riscos de runtime.
- `04-skills-usados.md`: skills solicitados e resultado da busca/listagem.

## Validacao segura executada

```powershell
python -m py_compile main.py
```

Resultado: comando concluiu sem erro de sintaxe.

## Observacoes de seguranca

- O arquivo `credenciais.env` existe, mas nao foi lido por conter credenciais.
- A documentacao usa apenas `credenciais.env.example` para registrar variaveis
  esperadas.
