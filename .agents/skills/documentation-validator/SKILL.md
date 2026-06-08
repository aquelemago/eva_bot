---
name: documentation-validator
description: Valida consistencia, rastreabilidade e conformidade das alteracoes documentais antes de encerrar o trabalho.
---

# Documentation Validator

## Objetivo

Validar se a documentacao criada ou atualizada esta consistente, rastreavel, limitada ao escopo e alinhada as regras do agente.

## Quando usar

Use esta skill apos qualquer criacao ou atualizacao documental e antes de entregar o resultado ao usuario.

## Entradas

- Arquivos documentais alterados.
- Resumo das alteracoes.
- Evidencias usadas.
- Regras de `AGENTS.md`.

## Processo

1. Conferir se nenhum codigo-fonte foi alterado.
2. Conferir se nenhum arquivo foi apagado.
3. Conferir se nenhuma dependencia foi instalada.
4. Conferir se nenhum commit foi feito.
5. Verificar se cada alteracao documental tem evidencia associada.
6. Validar consistencia interna, links, nomes de arquivos e ausencia de contradicoes obvias.
7. Registrar qualquer risco residual ou validacao nao realizada.

## Saida esperada

- Checklist de validacao.
- Lista de arquivos documentais alterados.
- Confirmacao de conformidade com as restricoes.
- Riscos residuais ou pendencias.

## Restricoes

- Nao alterar codigo-fonte.
- Nao instalar dependencias.
- Nao apagar arquivos.
- Nao fazer commits.
- Nao aprovar alteracao documental sem evidencia.
- Nao ocultar validacoes que nao puderam ser executadas.
