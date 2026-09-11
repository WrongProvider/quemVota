# SPEC-007 — Discursos & Atuação Legislativa (Casamento Factual de Pronunciamentos, Propostas e Votações)

## 1. Objetivo e Escopo

### Objetivo
Apresentar de forma transparente, rastreável e factual as manifestações em plenário e comissões dos deputados federais (discursos de tribuna), cruzando cada pronunciamento com as iniciativas legislativas concretas (proposições apresentadas, coautorias e relatorias) e com as votações nominais ocorridas em plenário (votos registrados e desfecho das matérias).

### Princípio da Neutralidade Factual Absoluta (AGENTS.md)
- **Apenas fatos observáveis:** Exibir exclusivamente os pronunciamentos oficiais da taquigrafia, proposições protocoladas e votos nominais registrados na Câmara dos Deputados.
- **Zero julgamento de valor:** É estritamente proibido emitir elogios, críticas, rotulações normativas ("incoerente", "fiel", "traidor") ou notas/scores de 0 a 100.
- **Rastreabilidade total:** Toda informação apresentada deve possuir identificadores verificáveis (`id` da proposição com link para a ficha de tramitação na Câmara, `id` da votação e link para o texto taquigráfico no Diário da Câmara).

### Escopo de Implementação
- **Pipeline de Ingestão (ETL):** `injest_banco/collectors/discursos_collector.py` e `injest_banco/injest_discursos.py`
- **Orquestração Airflow:** `airflow/dags/dag_injest_discursos.py`
- **Vetorização e Embeddings:** `tasks/correlacionar_discursos_atuacao.py`
- **Repositório e Serviço:** `backend/repositories/politico_repository.py` e `backend/services/politico_service.py`
- **Contratos e Schemas:** `backend/schemas.py`
- **Endpoint FastAPI:** `GET /politicos/{politico_id}/discursos-atuacao`
- **Interface e Componentes:** `frontend/src/components/PainelDiscursosAtuacao.tsx`, `frontend/src/pages/PoliticosDetalhe.tsx`
- **Testes Automatizados:** `backend/tests/test_discursos_atuacao.py` e `frontend/tests/discursos_atuacao.spec.ts`

---

## 2. Fonte de Dados e Modelagem

### Endpoint da API da Câmara
```http
GET https://dadosabertos.camara.leg.br/api/v2/deputados/{id}/discursos?idLegislatura=57&ordenarPor=dataHoraInicio&ordem=DESC
```

### Entidade Relacional (`discursos`)
Mapeada em `shared.models.Discurso`:
- `id` (Integer, PK)
- `idDeputado` (Integer, FK `deputados.id`)
- `idEvento` (Integer, FK `eventos.id`, nullable)
- `dataHoraInicio` (DateTime, not null)
- `dataHoraFim` (DateTime, nullable)
- `tipoDiscurso` (String(100)) — Ex.: "COMO LÍDER", "PELA ORDEM", "GRANDE EXPEDIENTE", "BREVES COMUNICAÇÕES", "ENCAMINHAMENTO DE VOTAÇÃO"
- `faseEventoTitulo` (String(255)) — Ex.: "Ordem do Dia", "Breves Comunicações"
- `sumario` (Text) — Resumo oficial produzido pela taquigrafia da Câmara
- `transcricao` (Text) — Transcrição integral da fala
- `keywords` (Text) — Termos-chave catalogados
- `urlTexto` (Text) — Link para a publicação no Diário da Câmara
- `urlAudio`, `urlVideo` (Text)
- **Unicidade e Idempotência:** Constraint `uq_discursos_dep_inicio_tipo` sobre `(idDeputado, dataHoraInicio, tipoDiscurso)`

---

## 3. Algoritmo de Correlação (Discurso × Proposição × Votação)

### 3.1 Citação Explícita de Matéria Legislativa
Nos sumários e transcrições dos discursos, matérias legislativas são identificadas pela expressão canônica:
```regex
\b(PEC|PLP|PL|MPV|REQ|PDL|PDC|PRC|RIC)\s*(?:n[º°o]?\.\s*)?(\d+)[/\-](\d{2,4})\b
```

Para cada proposição detectada:
1. Localiza a proposição correspondente em `proposicoes` (`siglaTipo = match[1]`, `numero = match[2]`, `ano = match[3]`).
2. Determina o papel do parlamentar consultando `proposicoesAutores`:
   - `proponente = True` e `ordemAssinatura = 1`: **Autoria**
   - `proponente = True` e `ordemAssinatura > 1`: **Coautoria**
   - Relator designado em tramitação: **Relatoria**
   - Sem autoria registrada: **Matéria Citada**
3. Identifica votações nominais associadas consultando `votacoesObjetos` (`proposicao_id = proposicoes.idCamara`) e cruza com `votacoesVotos` (`idDeputado = deputado.id`):
   - Voto registrado: `Sim`, `Não`, `Abstenção`, `Obstrução`, `Artigo 17`
   - Desfecho oficial da votação: `aprovacao = 1` (Aprovada), `aprovacao = 0` (Rejeitada)

### 3.2 Correlação Semântica e Temática (Vetorização BAAI/bge-m3)
Discursos gerais sem citação numérica direta recebem vetorização semântica (1024 dimensões) a partir de `"{sumario} {keywords}"` em `documentEmbeddings` (`tipoEntidade = 'discurso'`), viabilizando a busca por temas prioritários da atuação do parlamentar (SPEC-001).

---

## 4. Contratos de API (OpenAPI / Pydantic V2)

```http
GET /politicos/{politico_id}/discursos-atuacao?limit=20&offset=0&q=educacao&tipo_discurso=COMO%20L%C3%8DDER
```

### Resposta JSON (200 OK)
```json
{
  "id_deputado": 592,
  "nome_deputado": "Tabata Amaral",
  "total_discursos": 54,
  "itens": [
    {
      "id": 2,
      "data_hora_inicio": "2026-07-07T20:40:00",
      "tipo_discurso": "PELA ORDEM",
      "fase_evento_titulo": "Ordem do Dia",
      "sumario": "A Deputada orientou a bancada na votação do substitutivo oferecido ao Projeto de Lei Complementar nº 41, de 2026...",
      "keywords": "Orientação de bancada, Projeto de lei complementar, Voto favorável",
      "url_texto": "https://www.camara.leg.br/...",
      "proposicoes_correlatas": [
        {
          "id": 672890,
          "sigla_tipo": "PLP",
          "numero": 41,
          "ano": 2026,
          "ementa": "Dispõe sobre o Sistema Nacional de Enfrentamento da Violência contra Meninas e Mulheres...",
          "tipo_participacao": "Coautoria",
          "url_camara": "https://www.camara.leg.br/proposicoesWeb/fichadetramitacao?idProposicao=2606313"
        }
      ],
      "votacoes_correlatas": [
        {
          "id": 138651,
          "id_votacao_camara": "2606313-100",
          "data": "2026-07-07",
          "sigla_orgao": "PLEN",
          "descricao": "Aprovado o Substitutivo ao Projeto de Lei Complementar nº 41, de 2026...",
          "proposicao_ementa": "Dispõe sobre o Sistema Nacional de Enfrentamento da Violência...",
          "voto_registrado": "Artigo 17",
          "aprovacao": 1
        }
      ]
    }
  ]
}
```
