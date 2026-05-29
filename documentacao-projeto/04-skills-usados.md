# Skills usados

Esta auditoria seguiu os skills solicitados pelo usuario, sem instalar novas
skills e sem alterar codigo do projeto.

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
