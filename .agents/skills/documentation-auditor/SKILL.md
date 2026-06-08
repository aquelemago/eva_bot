---
name: documentation-auditor
description: Audita a documentacao contra evidencias do codigo e identifica lacunas, obsolescencias e contradicoes.
---

# Documentation Auditor

## Objetivo

Comparar a documentacao existente com o codigo e apontar lacunas, informacoes desatualizadas, contradicoes e oportunidades de melhoria documental.

## Quando usar

Use esta skill depois de `documentation-reader` e `codebase-analyzer`.

## Entradas

- Inventario e resumos da documentacao lida.
- Evidencias coletadas no codigo.
- Base documental principal: `documentacao-projeto`.

## Processo

1. Cruzar cada afirmacao documental relevante com evidencias do codigo.
2. Classificar achados como confirmado, desatualizado, incompleto, contraditorio ou sem evidencia.
3. Identificar documentos existentes que devem ser atualizados.
4. Identificar lacunas que exigem novos documentos.
5. Priorizar achados por impacto para entendimento, manutencao e uso por agentes de IA.
6. Preparar recomendacoes documentais sem executar alteracoes.

## Saida esperada

- Relatorio de auditoria documental.
- Lista de documentos candidatos a atualizacao.
- Lista de novos documentos candidatos.
- Evidencia usada para cada achado.
- Recomendacao de proxima skill: `documentation-writer`, `documentation-updater` ou `documentation-validator`.

## Restricoes

- Nao alterar arquivos durante a auditoria.
- Nao criar documentacao.
- Nao atualizar documentacao.
- Nao alterar codigo-fonte.
- Nao instalar dependencias.
- Nao apagar arquivos.
- Nao fazer commits.
- Nao recomendar mudancas sem evidencia verificavel.
