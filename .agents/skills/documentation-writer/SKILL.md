---
name: documentation-writer
description: Cria novos documentos somente quando lacunas documentais forem comprovadas por auditoria e evidencias.
---

# Documentation Writer

## Objetivo

Criar documentacao nova para cobrir lacunas comprovadas que nao sejam melhor resolvidas por atualizacao de documentos existentes.

## Quando usar

Use esta skill somente apos uma auditoria indicar lacuna documental clara e evidenciada.

## Entradas

- Lacuna documental aprovada para escrita.
- Evidencias do codigo ou da documentacao existente.
- Local recomendado dentro de `documentacao-projeto`.
- Publico-alvo do documento, quando definido.

## Processo

1. Confirmar que a lacuna nao e coberta por documento existente.
2. Definir objetivo, escopo e publico do novo documento.
3. Escrever conteudo baseado somente em evidencias verificaveis.
4. Incluir referencias a arquivos, modulos ou documentos usados como fonte.
5. Declarar incertezas quando houver informacao incompleta.
6. Manter o documento coeso, direto e util para manutencao futura.

## Saida esperada

- Novo arquivo documental em `documentacao-projeto`, quando autorizado pelo fluxo.
- Resumo do conteudo criado.
- Lista de evidencias usadas.
- Lista de incertezas ou pontos que exigem validacao humana.

## Restricoes

- Nao criar documentos sem lacuna comprovada.
- Nao duplicar conteudo que deveria ser atualizado em documento existente.
- Nao alterar codigo-fonte.
- Nao instalar dependencias.
- Nao apagar arquivos.
- Nao fazer commits.
- Nao inventar arquitetura, regras de negocio ou comportamento nao evidenciado.
