# Documentacao do projeto

Data da auditoria: 2026-07-02.

Este diretorio documenta o estado existente do projeto `evabot`. Nenhum codigo
foi alterado nesta documentacao.

## Escopo observado

- Entrada principal: `main.py`.
- Servico Windows: `windows_service.py`.
- Dependencias declaradas: `selenium`, `python-dotenv` e `pywin32`.
- Configuracao esperada: `credenciais.env`.
- Arquivos de runtime: `emails_processados.txt` e `logs/bot.log`.
- Diretorios ignorados para leitura de projeto: `.git/`, `venv/`, `__pycache__/` e `logs/`.

## Arquivos neste diretorio

- `01-visao-geral.md`: objetivo, entradas, saidas, modo de uso e execucao
  como servico Windows.
- `02-arquitetura-e-fluxo.md`: funcoes, fluxo Selenium, classe do servico
  Windows e novas constantes de controle.
- `03-debug-e-riscos.md`: validacoes executadas, achados, riscos de runtime
  e riscos adicionais do servico Windows.
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

## Validacao segura

```powershell
python -m py_compile main.py
python -m py_compile windows_service.py
```

Resultados: ambos os modulos compilam sem erro de sintaxe.
Esta documentacao foi produzida por leitura estatica do codigo, sem executar
o bot e sem instalar dependencias alem das ja declaradas.

## Observacoes de seguranca

- O arquivo `credenciais.env` existe, mas nao foi lido por conter credenciais.
- A documentacao registra as variaveis esperadas (`URL`, `USUARIO`, `SENHA`,
  `MODO_TESTE`) sem expor valores.
