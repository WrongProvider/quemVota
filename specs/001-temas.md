# SPEC-001 — Classificação de Temas de Atuação Parlamentar

## 1. Objetivo e Escopo

### Objetivo
Identificar e quantificar as áreas temáticas de atuação prioritárias de cada parlamentar a partir do processamento semântico de suas proposições, relatorias, discursos e eventos, persistindo os resultados para consulta pública na API e no frontend.

### Escopo de Implementação
- **Tarefas de Processamento (Batch):** `tasks/classificar_temas.py`
- **Serviço de Domínio:** `backend/services/tema_service.py`
- **Endpoints FastAPI:** `backend/api/v1/politico_api.py` (ou `backend/api/v1/tema_api.py`)
- **Modelos Utilizados (SOMENTE LEITURA/CONSUMO):**
  - `shared.models_vetorial.TemaAtuacao` (`temasAtuacao`)
  - `shared.models_vetorial.DocumentEmbedding` (`documentEmbeddings`)
  - `shared.models_vetorial.ItemTemaAtuacao` (`itensTemasAtuacao`)
  - `shared.models_vetorial.DeputadoTemaAtuacao` (`deputadoTemasAtuacao`)
  - `shared.models.Proposicao`, `shared.models.Discurso`, `shared.models.Deputado`
- **Testes Obrigatórios:** `backend/tests/test_temas.py`

### Ambiente de Execução (Git Worktree Obrigatório)
- **Branch:** `feat/spec-001-temas`
- **Diretório da Worktree:** `.worktrees/spec-001-temas`
- **Comando de Criação:**
  ```bash
  git worktree add -b feat/spec-001-temas .worktrees/spec-001-temas main
  ```
- **Desmonte pós-validação (DoD):**
  ```bash
  git worktree remove .worktrees/spec-001-temas
  ```

---

## 2. Taxonomia Canônica (20 Temas de Atuação)

Caso a tabela `temasAtuacao` não contenha os 20 temas padrão, a rotina de inicialização/seed deve inseri-los com seus respectivos slugs e descrições, calculando o embedding do texto no formato `"{nome}: {descricao}"`:

| Slug | Nome | Descrição para Embedding |
|---|---|---|
| `economia` | Economia | Política fiscal, tributária, inflação, comércio, orçamento público e finanças. |
| `educacao` | Educação | Ensino básico, superior, técnico, valorização docente e infraestrutura escolar. |
| `saude` | Saúde | Sistema Único de Saúde (SUS), vigilância sanitária, vacinação e hospitais. |
| `seguranca-publica` | Segurança Pública | Polícias, sistema prisional, combate ao crime organizado e desarmamento. |
| `trabalho` | Trabalho | Relações trabalhistas, CLT, emprego, renda, escala e seguridade laboral. |
| `direitos-humanos` | Direitos Humanos | Cidadania, proteção a minorias, combate à tortura e igualdade racial. |
| `meio-ambiente` | Meio Ambiente | Clima, desmatamento, transição energética, biodiversidade e recursos hídricos. |
| `infraestrutura` | Infraestrutura | Portos, aeroportos, rodovias, ferrovias, telecomunicações e energia. |
| `tecnologia` | Tecnologia | Inteligência artificial, segurança cibernética, proteção de dados e inovação digital. |
| `agricultura` | Agricultura | Agronegócio, agricultura familiar, crédito rural e exportação agropecuária. |
| `administracao-publica` | Administração Pública | Servidores públicos, reforma administrativa, processos e eficiência estatal. |
| `previdencia` | Previdência | Aposentadorias, regimes próprios, pensões e reformas previdenciárias. |
| `politica-externa` | Política Externa | Relações internacionais, diplomacia, tratados e comércio exterior. |
| `direitos-das-mulheres` | Direitos das Mulheres | Combate à violência doméstica, igualdade salarial e saúde da mulher. |
| `direitos-lgbtqia` | Direitos LGBTQIA+ | Combate à homotransfobia, direitos civis e proteção legal da diversidade. |
| `povos-indigenas` | Povos Indígenas | Demarcação de terras, preservação cultural e proteção de comunidades tradicionais. |
| `cultura` | Cultura | Patrimônio histórico, incentivo cultural, audiovisual, literatura e artes. |
| `habitacao` | Habitação | Moradia popular, saneamento básico, regularização fundiária e urbanismo. |
| `transporte` | Transporte | Mobilidade urbana, transporte coletivo, trânsito e logística viária. |
| `combate-a-corrupcao` | Combate à Corrupção | Transparência, órgãos de controle, compliance e combate à improbidade. |

---

## 3. Algoritmo e Regras de Negócio Determinísticas

### Etapa 1: Embeddings e Similaridade por Item
- Para cada registro em `documentEmbeddings` (`tipoEntidade`: `proposicao`, `discurso`, `evento`, `relatoria`):
  - Calcular a similaridade por cosseno com os 20 vetores de `temasAtuacao.embedding`.
  - Como os vetores do `BAAI/bge-m3` já são unitários ($L_2 = 1$), a similaridade equivale ao produto escalar:
    $$\text{sim}(doc, tema) = \vec{v}_{doc} \cdot \vec{v}_{tema}$$
  - **Limiar Mínimo:** Descartar qualquer tema com $\text{sim} < 0.40$.
  - **Top K:** Selecionar no máximo os 3 maiores scores classificados.

### Etapa 2: Ponderação por Papel Parlamentar
Para cada tema atribuído ao item, registrar em `itensTemasAtuacao`:
- `tipoParticipacao` e pesos obrigatórios:
  - `autoria`: **10.0**
  - `relatoria`: **8.0**
  - `coautoria`: **5.0**
  - `discurso`: **2.0**
  - `evento`: **1.0**
- Gravar:
  - `scoreClassificacao`: valor da similaridade ($\text{sim}$, arredondado para 4 casas decimais).
  - `peso`: peso da participação.
  - `rankNoItem`: posição no item (1 para maior similaridade, 2 para segunda, 3 para terceira).

### Etapa 3: Agregação por Deputado e Legislatura
Para cada parlamentar (`idDeputado`) em uma legislatura (`idLegislatura`):
1. Calcular o peso total ponderado por tema:
   $$\text{pesoPonderado}(T_i) = \sum_{k \in \text{itens}(dep, T_i)} (\text{peso}_k \times \text{scoreClassificacao}_k)$$
2. Calcular o score percentual normalizado:
   $$\text{score}(T_i) = \frac{\text{pesoPonderado}(T_i)}{\sum_{j=1}^{M} \text{pesoPonderado}(T_j)}$$
3. Ordenar os temas por `score DESC`, atribuindo `rank` sequencial (1, 2, 3...).
4. Persistir em `deputadoTemasAtuacao` com `on_conflict_do_update` sobre a constraint `uq_dep_tema_legislatura` (`idDeputado`, `idTemaAtuacao`, `idLegislatura`).

---

## 4. Contratos de API (FastAPI / Pydantic V2)

### Endpoint
`GET /api/v1/politicos/{id}/temas`

### Parâmetros de Query:
- `idLegislatura` (opcional, `int`): se omitido, considerar a legislatura atual (57).
- `limit` (opcional, `int`, default `5`, max `20`).

### Schemas Pydantic:
```python
from pydantic import BaseModel, Field

class TemaAtuacaoItemResponse(BaseModel):
    idTema: int
    slug: str
    nome: str
    score: float = Field(..., description="Proporção da atuação no tema (0.0000 a 1.0000)")
    percentual: float = Field(..., description="Percentual arredondado (ex: 32.5 para 32.5%)")
    pesoTotal: float = Field(..., description="Soma ponderada dos pontos de itens no tema")
    rank: int = Field(..., ge=1, description="Posição no ranking temático do parlamentar")

class PoliticoTemasResponse(BaseModel):
    idDeputado: int
    idLegislatura: int
    totalTemasIdentificados: int
    temas: list[TemaAtuacaoItemResponse]
```

---

## 5. Critérios de Aceite e Verificação Automatizada (DoD)

O agente deve obrigatoriamente executar e reportar o sucesso dos seguintes comandos:

1. **Seed & Classificação:**
   ```bash
   python -m tasks.classificar_temas --limit 50 --dry-run
   ```
2. **Testes Unitários:**
   ```bash
   pytest backend/tests/test_temas.py -v
   ```
   *Os testes devem cobrir: cálculo correto de pesos proporcionais, respeito ao limiar mínimo de 0.40, desempate e limites de score entre 0 e 1.*
3. **Linter e Formatação:**
   ```bash
   ruff check backend/services/tema_service.py tasks/classificar_temas.py
   ```