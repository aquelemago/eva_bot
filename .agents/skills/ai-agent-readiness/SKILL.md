---
name: ai-agent-readiness
description: Avalia se a documentacao permite que agentes de IA entendam, naveguem e trabalhem no projeto com seguranca.
---

# AI Agent Readiness

## Objetivo

Avaliar a prontidao da documentacao para uso por agentes de IA, com foco em orientacao, contexto tecnico, limites operacionais e rastreabilidade.

## Quando usar

Use esta skill depois de auditorias ou alteracoes documentais, especialmente quando o objetivo for melhorar onboarding de agentes.

## Entradas

- Documentacao em `documentacao-projeto`.
- `AGENTS.md`.
- Achados de auditoria documental.
- Evidencias do codigo relevantes para operacao por agentes.

## Processo

1. Verificar se ha orientacao clara sobre estrutura do projeto.
2. Verificar se pontos de entrada, fluxos principais e restricoes estao documentados.
3. Avaliar se agentes conseguem identificar o que podem e nao podem alterar.
4. Avaliar se a documentacao aponta para evidencias ou caminhos verificaveis.
5. Identificar lacunas que dificultam manutencao, auditoria ou continuidade por IA.
6. Recomendar melhorias documentais sem alterar arquivos automaticamente.

## Saida esperada

- Diagnostico de prontidao para agentes de IA.
- Lista de lacunas que afetam agentes.
- Recomendacoes priorizadas para escrita ou atualizacao documental.
- Evidencias que sustentam cada recomendacao.

## Restricoes

- Nao alterar arquivos durante a avaliacao.
- Nao alterar codigo-fonte.
- Nao instalar dependencias.
- Nao apagar arquivos.
- Nao fazer commits.
- Nao recomendar automacoes perigosas ou sem controle humano.
- Nao assumir permissao para modificar documentacao sem pedido explicito.
