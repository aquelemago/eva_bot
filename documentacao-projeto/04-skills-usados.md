# Skills usados

Esta auditoria seguiu os skills solicitados pelo usuario, sem instalar novas
skills e sem alterar codigo do projeto.

## Infraestrutura local em 2026-06-08

Foi criada uma infraestrutura local de agente em `.agents/skills/`, com uma
skill por objetivo:

- `project-discovery`: mapeamento inicial de estrutura e caminhos.
- `documentation-reader`: leitura integral da base documental principal.
- `codebase-analyzer`: coleta de evidencias no codigo.
- `documentation-auditor`: comparacao entre documentacao e codigo.
- `documentation-writer`: criacao de novos documentos quando houver lacuna.
- `documentation-updater`: atualizacao de documentos existentes.
- `ai-agent-readiness`: avaliacao de prontidao para agentes de IA.
- `documentation-validator`: validacao final de consistencia e restricoes.

Essas skills estao documentadas em arquivos `SKILL.md` dentro de
`.agents/skills/`. A orientacao geral para agentes fica em `AGENTS.md`.

Observacao de caminho: o diretorio documental oficial e `documentacao-projeto`.
O caminho incorreto `documenatcao-projeteto` apareceu em instrucoes anteriores
como erro de digitacao historico.

## skill-creator

Uso nesta tarefa:

- Serviu como referencia para manter a documentacao concisa, estruturada e com
  contexto reutilizavel.
- Nao foi criada uma nova skill, porque o pedido final foi documentar apenas o
  projeto existente.

## skill-installer

Uso nesta tarefa:

- Foi consultada a lista oficial de skills instalaveis via script do
  `skill-installer`.
- Nenhuma skill foi instalada.

Resultado resumido da listagem oficial:

- Existem skills como `playwright`, `playwright-interactive`,
  `security-best-practices`, `sentry`, `openai-docs`, entre outras.
- Nenhuma skill oficial listada foi aplicada diretamente ao projeto, pois o
  escopo pedido foi documentacao local do projeto Selenium existente.

## find-skills

Busca executada:

```powershell
npx.cmd skills find python selenium debugging
```

Resultados relevantes observados:

- `brightdata/skills@bright-data-best-practices` - 1.4K installs.
- `mindrally/skills@selenium-automation` - 716 installs.
- `pluginagentmarketplace/custom-plugin-python@debugging` - 127 installs.
- `membranedev/application-skills@selenium` - 65 installs.
- `fugazi/test-automation-skills-agents@webapp-selenium-testing` - 29 installs.

Decisao:

- Nenhuma skill foi instalada.
- A analise local foi suficiente para documentar estrutura, fluxo e riscos do
  projeto existente.

## Skills complementares usados como criterio local

Tambem foram considerados os criterios locais de auditoria de projeto Python:

- nao ler arquivos de credenciais;
- ignorar ambiente virtual e artefatos de runtime;
- usar inventario seguro;
- executar validacao estatica antes de registrar achados.
