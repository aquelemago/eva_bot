---
name: project-discovery
description: Mapeia a estrutura do projeto e identifica artefatos relevantes sem analisar profundamente nem alterar arquivos.
---

# Project Discovery

## Objetivo

Descobrir a organizacao basica do repositorio, os diretorios relevantes, os arquivos de entrada e a localizacao da base documental principal.

## Quando usar

Use esta skill no inicio de um ciclo de documentacao, antes de ler documentos em detalhe ou analisar codigo.

## Entradas

- Caminho da raiz do repositorio.
- Nome da base documental principal: `documentacao-projeto`.
- Lista de arquivos e diretorios existentes.

## Processo

1. Listar a raiz do repositorio.
2. Identificar diretorios de codigo, documentacao, configuracao, logs, ambientes virtuais e artefatos gerados.
3. Verificar se `documentacao-projeto` existe.
4. Registrar divergencias de nome ou ausencia da base documental principal.
5. Identificar arquivos que provavelmente sao pontos de entrada, sem interpretar seu comportamento em profundidade.

## Saida esperada

- Mapa resumido da estrutura do repositorio.
- Lista de caminhos relevantes para leitura posterior.
- Registro de divergencias, caso a base documental principal nao esteja disponivel no caminho esperado.
- Proximas skills recomendadas.

## Restricoes

- Nao alterar arquivos.
- Nao criar documentacao.
- Nao atualizar documentacao.
- Nao instalar dependencias.
- Nao apagar arquivos.
- Nao fazer commits.
- Nao inferir comportamento do sistema sem leitura posterior do codigo.
