---
name: documentation-updater
description: Atualiza documentos existentes quando estiverem desatualizados, incompletos ou contraditorios em relacao ao codigo.
---

# Documentation Updater

## Objetivo

Atualizar documentacao existente para refletir evidencias atuais do codigo e da propria base documental.

## Quando usar

Use esta skill quando `documentation-auditor` apontar que um documento existente precisa de correcao, complemento ou reorganizacao.

## Entradas

- Documento existente a ser atualizado.
- Achados da auditoria.
- Evidencias do codigo ou de outros documentos.
- Escopo exato da alteracao.

## Processo

1. Ler novamente o documento que sera atualizado.
2. Localizar os trechos afetados.
3. Aplicar apenas alteracoes necessarias ao escopo.
4. Preservar estrutura, estilo e intencao do documento quando adequados.
5. Remover ou corrigir afirmacoes contraditorias somente com evidencia.
6. Registrar a justificativa documental de cada alteracao relevante.

## Saida esperada

- Documento existente atualizado.
- Resumo das alteracoes realizadas.
- Evidencias usadas para justificar cada alteracao relevante.
- Pontos pendentes que nao puderam ser corrigidos por falta de evidencia.

## Restricoes

- Nao alterar codigo-fonte.
- Nao instalar dependencias.
- Nao apagar arquivos.
- Nao fazer commits.
- Nao ampliar o escopo alem dos achados aprovados.
- Nao reescrever documentos inteiros sem necessidade clara.
- Nao alterar conteudo sem evidencia no codigo ou na documentacao existente.
