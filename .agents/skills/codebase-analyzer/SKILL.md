---
name: codebase-analyzer
description: Analisa o codigo-fonte para coletar evidencias tecnicas que sustentem conclusoes documentais.
---

# Codebase Analyzer

## Objetivo

Ler meticulosamente o codigo-fonte e extrair evidencias verificaveis sobre arquitetura, fluxos, dependencias, entradas, saidas e comportamento real do sistema.

## Quando usar

Use esta skill depois da descoberta inicial e antes de auditar ou alterar documentacao.

## Entradas

- Caminhos de codigo identificados por `project-discovery`.
- Afirmacoes documentais levantadas por `documentation-reader`.
- Escopo tecnico solicitado pelo usuario, quando houver.

## Processo

1. Identificar arquivos de entrada e modulos principais.
2. Ler o codigo relacionado ao escopo.
3. Mapear funcoes, classes, fluxos, dependencias e arquivos de configuracao relevantes.
4. Coletar evidencias com caminho de arquivo e, quando possivel, linha ou trecho especifico.
5. Comparar comportamento real do codigo com afirmacoes documentais previamente levantadas.
6. Registrar incertezas quando o codigo nao permitir conclusao segura.

## Saida esperada

- Lista de evidencias tecnicas com referencias a arquivos.
- Resumo do comportamento observado no codigo.
- Pontos confirmados, contraditorios ou ausentes em relacao a documentacao.
- Riscos de documentar algo sem evidencia suficiente.

## Restricoes

- Nao alterar codigo-fonte.
- Nao executar instaladores.
- Nao instalar dependencias.
- Nao apagar arquivos.
- Nao fazer commits.
- Nao modificar documentacao nesta etapa.
- Nao inferir intencao de negocio sem evidencia no codigo ou na documentacao existente.
