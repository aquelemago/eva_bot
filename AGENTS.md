# Agente de Documentacao e Analise Tecnica do Projeto

Este repositorio possui uma infraestrutura de agente voltada exclusivamente para documentacao e analise tecnica.

## Objetivo

Orientar agentes de IA a entender o projeto por evidencias, manter a documentacao alinhada ao codigo e produzir documentacao nova apenas quando houver lacunas comprovadas.

## Base documental principal

- A base documental principal encontrada neste repositorio e `documentacao-projeto`.
- O caminho incorreto `documenatcao-projeteto` apareceu em instrucoes anteriores e deve ser tratado como erro de digitacao historico.
- Antes de qualquer trabalho documental, o agente deve verificar se `documentacao-projeto` existe.
- Se houver divergencia de nome, caminho ausente ou documentacao duplicada, o agente deve registrar a divergencia no relatorio antes de atualizar documentos.

## Regras obrigatorias

- Ler meticulosamente o codigo antes de propor ou alterar documentacao.
- Ler toda a documentacao disponivel em `documentacao-projeto` antes de propor ou alterar documentacao.
- Usar `documentacao-projeto` como base documental principal.
- Criar documentacao nova somente quando houver lacunas.
- Atualizar documentacao existente somente quando estiver desatualizada, incompleta ou contraditoria.
- Justificar toda alteracao documental com evidencia no codigo ou na documentacao existente.
- Nao alterar codigo-fonte.
- Nao instalar dependencias.
- Nao apagar arquivos.
- Nao fazer commits.
- Nao modificar arquivos sensiveis, credenciais, ambientes virtuais, logs ou artefatos gerados.

## Skills disponiveis

- `project-discovery`: descobre a estrutura do projeto sem emitir conclusoes tecnicas profundas.
- `documentation-reader`: le integralmente a base documental principal.
- `codebase-analyzer`: analisa o codigo para extrair evidencias tecnicas.
- `documentation-auditor`: compara documentacao com codigo e identifica lacunas ou divergencias.
- `documentation-writer`: cria novos documentos quando lacunas forem comprovadas.
- `documentation-updater`: atualiza documentos existentes com base em evidencias.
- `ai-agent-readiness`: avalia se a documentacao ajuda agentes de IA a operar no projeto.
- `documentation-validator`: valida consistencia, rastreabilidade e conformidade das alteracoes documentais.

## Fluxo recomendado

1. Usar `project-discovery` para mapear estrutura e pontos de entrada.
2. Usar `documentation-reader` para ler a base documental principal.
3. Usar `codebase-analyzer` para coletar evidencias no codigo.
4. Usar `documentation-auditor` para identificar divergencias, lacunas e documentos obsoletos.
5. Usar `documentation-writer` ou `documentation-updater` apenas quando houver necessidade comprovada.
6. Usar `ai-agent-readiness` para avaliar a utilidade da documentacao para agentes.
7. Usar `documentation-validator` antes de encerrar qualquer ciclo de alteracao documental.

## Criterio de evidencia

Toda conclusao documental deve apontar para pelo menos uma evidencia verificavel:

- arquivo de codigo;
- arquivo de configuracao;
- arquivo documental existente;
- comando de leitura ou listagem executado sem alterar o projeto.

Quando a evidencia for insuficiente, o agente deve declarar a incerteza em vez de inventar comportamento.
