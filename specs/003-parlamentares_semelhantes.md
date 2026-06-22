# SPEC-003 — Similaridade entre Parlamentares

## Objetivo

Identificar parlamentares com atuação semelhante.

## Problema

Partido político não representa necessariamente atuação.

## Fontes

* temas
* proposições
* votações
* discursos
* comissões

## Modelo

Cada parlamentar recebe um vetor composto por:

* distribuição temática
* embeddings de proposições
* embeddings de discursos

## Similaridade

Utilizar:

* cosine similarity

## Saída

[
{
"politico": "...",
"similaridade": 0.91
}
]

## Resultado Esperado

Parlamentares com atuação semelhante:

* Erika Hilton
* Talíria Petrone
* Sâmia Bomfim

Exibir explicação:

"Possuem forte atuação em direitos humanos e relações de trabalho."
