# SPEC-004 — Resumo Automatizado do Mandato

## Objetivo

Gerar um resumo neutro da atuação parlamentar.

## Problema

Usuários não possuem tempo para analisar centenas de proposições.

## Entradas

* temas predominantes
* marcos do mandato
* proposições relevantes
* votações relevantes
* cargos exercidos

## Regras

O sistema NÃO pode:

* elogiar
* criticar
* recomendar voto
* atribuir intenção

O sistema DEVE:

* descrever fatos observáveis
* citar evidências
* utilizar linguagem neutra

## Prompt Base

Você é um analista legislativo.

Descreva a atuação parlamentar utilizando apenas os dados fornecidos.

Não faça julgamentos de valor.

Não utilize adjetivos positivos ou negativos.

## Saída

Resumo textual de 2 a 5 parágrafos.

## Resultado Esperado

"Durante o mandato, o parlamentar concentrou sua atuação em temas relacionados a trabalho, direitos humanos e políticas sociais. Entre suas iniciativas de maior relevância estão..."
