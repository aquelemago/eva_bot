---
name: documentation-reader
description: Le integralmente a base documental principal e organiza seus conteudos antes de qualquer auditoria ou escrita.
---

# Documentation Reader

## Objetivo

Ler toda a documentacao em `documentacao-projeto` e organizar o entendimento documental existente.

## Quando usar

Use esta skill antes de auditar, criar ou atualizar documentacao.

## Entradas

- Caminho da base documental principal: `documentacao-projeto`.
- Lista de arquivos documentais existentes.
- Escopo informado pelo usuario, quando houver.

## Processo

1. Confirmar que `documentacao-projeto` existe.
2. Listar todos os arquivos documentais no diretorio.
3. Ler integralmente os documentos relevantes ao escopo.
4. Registrar titulos, objetivos, assuntos cobertos e lacunas aparentes.
5. Separar fatos documentados de interpretacoes.
6. Marcar documentos que dependem de validacao contra o codigo.

## Saida esperada

- Inventario da documentacao lida.
- Resumo objetivo de cada documento.
- Lista de afirmacoes que precisam ser validadas no codigo.
- Lista preliminar de lacunas documentais, sem ainda propor alteracoes.

## Restricoes

- Nao atualizar documentos durante a leitura.
- Nao criar novos documentos.
- Nao alterar codigo-fonte.
- Nao apagar arquivos.
- Nao instalar dependencias.
- Nao fazer commits.
- Nao tratar afirmacoes documentais como verdade sem validacao quando elas dependerem do codigo.
