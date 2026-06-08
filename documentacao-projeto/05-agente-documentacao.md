# Agente de documentacao e analise tecnica

## Objetivo

Este documento registra a infraestrutura local criada para orientar agentes de
IA que precisem analisar o projeto e manter sua documentacao.

O agente deve trabalhar por evidencias, ler o codigo e a documentacao antes de
propor mudancas e alterar apenas arquivos documentais quando houver necessidade
comprovada.

## Evidencias usadas

- `AGENTS.md`: define regras gerais, fluxo recomendado e restricoes.
- `.agents/skills/`: contem uma pasta por skill local.
- `main.py`: concentra o codigo-fonte do bot Selenium.
- `documentacao-projeto/README.md`: indice da documentacao principal.
- `documentacao-projeto/01-visao-geral.md`: descreve objetivo, configuracao e
  efeitos colaterais.
- `documentacao-projeto/02-arquitetura-e-fluxo.md`: descreve funcoes e fluxo.
- `documentacao-projeto/03-debug-e-riscos.md`: descreve riscos e comandos de
  diagnostico.
- `documentacao-projeto/04-skills-usados.md`: registra historico de skills.

## Diretorio documental principal

O diretorio documental encontrado na raiz e:

```text
documentacao-projeto
```

O caminho incorreto `documenatcao-projeteto` apareceu em instrucoes anteriores
como erro de digitacao historico.

## Ordem operacional das skills

Use as skills locais nesta ordem quando o objetivo for analisar o projeto e
manter documentacao:

1. `project-discovery`
2. `documentation-reader`
3. `codebase-analyzer`
4. `documentation-auditor`
5. `documentation-writer`, somente se houver lacunas documentais comprovadas.
6. `documentation-updater`, somente se houver documento desatualizado,
   incompleto ou contraditorio.
7. `ai-agent-readiness`
8. `documentation-validator`

## Limites operacionais

O agente pode:

- ler arquivos do projeto;
- buscar no codigo;
- criar ou atualizar arquivos dentro de `documentacao-projeto`;
- atualizar `AGENTS.md` quando isso melhorar orientacao para agentes futuros.

O agente nao pode:

- alterar codigo-fonte;
- instalar dependencias;
- apagar arquivos;
- fazer commits;
- ler ou expor valores de `credenciais.env`;
- modificar ambientes virtuais, logs ou artefatos gerados.

## Como justificar alteracoes documentais

Toda alteracao documental deve indicar evidencia verificavel. Exemplos:

- uma funcao, variavel ou fluxo observado em `main.py`;
- uma dependencia observada em `requirements.txt`;
- uma regra de ignorados observada em `.gitignore`;
- uma variavel esperada observada em `credenciais.env.example`;
- um documento existente em `documentacao-projeto`;
- uma regra operacional registrada em `AGENTS.md` ou em `.agents/skills/`.

Quando o codigo ou a documentacao nao sustentarem uma conclusao, o agente deve
registrar a incerteza em vez de completar a informacao por suposicao.

## Estado tecnico observado em 2026-06-08

O projeto continua organizado como um script Python procedural em `main.py`,
com dependencias declaradas em `requirements.txt`:

- `selenium`
- `python-dotenv`

O script carrega `credenciais.env`, usa variaveis `URL`, `USUARIO`, `SENHA`,
`MODO_TESTE` e tambem aceita fallback por `TEST_MODE`. A automacao usa Selenium
para navegar no Senior X / HCM, acessar pre-admissoes, filtrar a aba
`Em assinatura`, abrir detalhes, localizar documentos enviados com status
`Em assinatura` e reenviar documentos em modo normal.

Essas conclusoes sao sustentadas por `main.py` e pelos documentos existentes em
`documentacao-projeto`.

## Riscos para agentes futuros

- A documentacao de codigo depende de um unico arquivo grande, `main.py`, o que
  exige leitura cuidadosa antes de qualquer conclusao.
- O fluxo Selenium depende de textos, IDs e classes do front-end Senior X.
- `credenciais.env` existe localmente, mas nao deve ser lido por agentes.
- `logs/`, `venv/`, `__pycache__/` e arquivos de runtime nao devem ser usados
  como fonte principal de documentacao.
- `documentacao-projeto` deve ser usado como fonte documental oficial por
  agentes futuros.
