# SPEC-001 — Classificação de Temas Parlamentares

## Objetivo

Identificar automaticamente os principais temas de atuação de um parlamentar utilizando proposições, discursos, relatorias e eventos.

## Problema

O eleitor não consegue compreender rapidamente quais pautas um parlamentar realmente prioriza.

Os dados brutos da Câmara são extensos e fragmentados.

## Fontes de Dados

### Proposições

* título
* ementa
* palavras-chave
* justificativa (quando disponível)

### Discursos

* resumo
* transcrição

### Eventos

* descrição
* tema

### Relatorias

* pareceres
* proposições relacionadas

## Categorias Iniciais

* Economia
* Educação
* Saúde
* Segurança Pública
* Trabalho
* Direitos Humanos
* Meio Ambiente
* Infraestrutura
* Tecnologia
* Agricultura
* Administração Pública
* Previdência
* Política Externa
* Direitos das Mulheres
* Direitos LGBTQIA+
* Povos Indígenas
* Cultura
* Habitação
* Transporte
* Combate à Corrupção

## Processamento

### Etapa 1

Gerar embedding para cada item.

### Etapa 2

Classificar item em até 3 temas.

### Etapa 3

Calcular frequência ponderada.

Pesos iniciais:

* proposição autoria: 10
* proposição coautoria: 5
* relatoria: 8
* discurso: 2
* evento: 1

## Saída

{
"tema": "Trabalho",
"score": 0.87
}

## Resultado Esperado

Exibir ao usuário:

Principais áreas de atuação:

1. Trabalho
2. Direitos Humanos
3. Direitos LGBTQIA+
