# Documentacao do projeto

Data da auditoria: 2026-06-08.

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
- `05-agente-documentacao.md`: infraestrutura local do agente de documentacao,
  ordem de uso das skills e limites operacionais.
- `07-mapeamento-processo-automacao.md`: mapa tecnico do processo executado
  pela automacao, com etapas, decisoes, dependencias e informacoes necessarias
  para diagnostico de falhas.

## Infraestrutura de agente

Em 2026-06-08 foram adicionados:

- `AGENTS.md`, com regras para agentes de documentacao e analise tecnica.
- `.agents/skills/`, com skills locais para descoberta, leitura documental,
  analise de codigo, auditoria, escrita, atualizacao, prontidao para IA e
  validacao.

O diretorio documental oficial e `documentacao-projeto`. O caminho incorreto
`documenatcao-projeteto` apareceu em instrucoes anteriores como erro de
digitacao historico.

## Validacao segura registrada anteriormente

```powershell
python -m py_compile main.py
```

Resultado registrado na auditoria anterior: comando concluiu sem erro de
sintaxe. Esta rodada de 2026-06-08 fez validacao documental e estatica por
leitura, sem executar o bot e sem instalar dependencias.

## Observacoes de seguranca

- O arquivo `credenciais.env` existe, mas nao foi lido por conter credenciais.
- A documentacao usa apenas `credenciais.env.example` para registrar variaveis
  esperadas.
