# SPEC-003 — Similaridade Multidimensional entre Parlamentares

## 1. Objetivo e Escopo

### Objetivo
Identificar parlamentares com padrões de atuação e agendas legislativas similares a determinado deputado, superando a análise superficial de bancada ou legenda partidária através de representação vetorial composta (distribuição temática ponderada, proposições apresentadas e discursos proferidos).

### Escopo de Implementação
- **Tarefas de Processamento (Batch):** `tasks/calcular_similaridade.py`
- **Serviço de Domínio:** `backend/services/similaridade_service.py`
- **Endpoints FastAPI:** `backend/api/v1/politico_api.py` (ou `backend/api/v1/similaridade_api.py`)
- **Modelos Utilizados:**
  - `shared.models_vetorial.DeputadoPerfilVetorial` (`deputadoPerfilVetorial`)
  - `shared.models_vetorial.DeputadoSemelhante` (`deputadosSemelhantes`)
  - `shared.models_vetorial.DeputadoTemaAtuacao` (`deputadoTemasAtuacao`)
  - `shared.models_vetorial.DocumentEmbedding` (`documentEmbeddings`)
  - `shared.models.Deputado` (`deputados`)
- **Testes Obrigatórios:** `backend/tests/test_similaridade.py`

### Ambiente de Execução (Git Worktree Obrigatório)
- **Branch:** `feat/spec-003-similaridade`
- **Diretório da Worktree:** `.worktrees/spec-003-similaridade`
- **Comando de Criação:**
  ```bash
  git worktree add -b feat/spec-003-similaridade .worktrees/spec-003-similaridade main
  ```
- **Desmonte pós-validação (DoD):**
  ```bash
  git worktree remove .worktrees/spec-003-similaridade
  ```

---

## 2. Estrutura do Vetor Parlamentar Composto

Cada parlamentar em uma legislatura deve possuir uma representação vetorial em `deputadoPerfilVetorial` com dimensão fixa **1024** (modelo `BAAI/bge-m3`), composta por três dimensões normalizadas:

### 1. Vetor Temático ($\vec{v}_{\text{tematico}}$)
Média ponderada dos embeddings dos temas oficiais (`TemaAtuacao.embedding`), utilizando os scores de `deputadoTemasAtuacao`:
$$\vec{u}_{\text{tem}} = \sum_{i=1}^{M} (\text{score}_i \cdot \vec{v}_{T_i})$$
$$\vec{v}_{\text{tematico}} = \frac{\vec{u}_{\text{tem}}}{\|\vec{u}_{\text{tem}}\|_2}$$

### 2. Vetor de Proposições ($\vec{v}_{\text{proposicoes}}$)
Centróide normalizado de todos os embeddings em `documentEmbeddings` correspondentes às proposições em que o deputado é autor ou relator:
$$\vec{v}_{\text{proposicoes}} = \frac{\sum_{p \in P} \vec{v}_p}{\|\sum_{p \in P} \vec{v}_p\|_2}$$

### 3. Vetor de Discursos ($\vec{v}_{\text{discursos}}$)
Centróide normalizado de todos os discursos em `documentEmbeddings` proferidos pelo parlamentar.  
*(Caso o parlamentar não possua discursos registrados, adotar $\vec{v}_{\text{discursos}} = \vec{v}_{\text{tematico}}$).*

### 4. Vetor Composto Final ($\vec{v}_{\text{composto}}$)
Combinação linear com pesos normalizados:
$$\vec{v}_{\text{raw}} = 0.45 \cdot \vec{v}_{\text{tematico}} + 0.35 \cdot \vec{v}_{\text{proposicoes}} + 0.20 \cdot \vec{v}_{\text{discursos}}$$
$$\vec{v}_{\text{composto}} = \frac{\vec{v}_{\text{raw}}}{\|\vec{v}_{\text{raw}}\|_2}$$

---

## 3. Algoritmo de Busca e Geração de Explicações

### Etapa 1: Busca Vetorial no pgvector
Para cada deputado $A$:
1. Consultar a distância por cosseno com todos os demais deputados $B$ da mesma legislatura usando o operador `<=>` e o índice HNSW `ix_deputado_perfil_vetor_composto_hnsw`:
   $$\text{similaridade}(A, B) = 1.0 - (\vec{v}_{\text{composto}, A} \Leftrightarrow \vec{v}_{\text{composto}, B})$$
2. Restrição mandatória: `idDeputado <> idDeputadoSimilar`.
3. Ordenar por `similaridade DESC` e selecionar os **Top 5**.

### Etapa 2: Explicação Factual Determinística
Para garantir neutralidade e zero alucinação, a explicação armazenada em `deputadosSemelhantes.explicacao` deve ser construída exclusivamente a partir dos temas comuns de maior pontuação:
- Identificar os temas que estão simultaneamente entre os Top 3 de ambos os parlamentares em `deputadoTemasAtuacao`.
- **Regra de Formatação:**
  - Se houver 2 ou mais temas comuns:
    *"Possuem atuação prioritária compartilhada em {tema_1} e {tema_2}."*
  - Se houver 1 tema comum:
    *"Apresentam convergência de pautas prioritárias em {tema_1}."*
  - Caso não haja intersecção nos Top 3:
    *"Apresentam alinhamento na distribuição geral de temas e perfil de iniciativas legislativas."*

### Etapa 3: Persistência
Inserir ou atualizar em `deputadosSemelhantes` com `on_conflict_do_update` sobre a constraint `uq_dep_semelhante_modelo` (`idDeputado`, `idDeputadoSimilar`, `modelo`).

---

## 4. Contratos de API (FastAPI / Pydantic V2)

### Endpoint
`GET /api/v1/politicos/{id}/semelhantes`

### Parâmetros de Query:
- `idLegislatura` (opcional, `int`, default `57`).
- `limit` (opcional, `int`, default `5`, max `10`).

### Schemas Pydantic:
```python
from typing import Optional
from pydantic import BaseModel, Field

class DeputadoSimilarItemResponse(BaseModel):
    idDeputado: int
    nome: str
    siglaPartido: str
    siglaUF: Optional[str]
    urlFoto: Optional[str]
    similaridade: float = Field(..., description="Índice de similaridade de cosseno (0.0000 a 1.0000)")
    percentualSimilaridade: float = Field(..., description="Ex: 89.5 para 89.5%")
    explicacao: str
    rank: int = Field(..., ge=1, le=10)

class PoliticoSemelhantesResponse(BaseModel):
    idDeputadoReferencia: int
    idLegislatura: int
    semelhantes: list[DeputadoSimilarItemResponse]
```

---

## 5. Critérios de Aceite e Verificação Automatizada (DoD)

1. **Geração dos Perfis e Matriz de Similaridade:**
   ```bash
   python -m tasks.calcular_similaridade --limit-deputados 20 --dry-run
   ```
2. **Testes Unitários:**
   ```bash
   pytest backend/tests/test_similaridade.py -v
   ```
   *Os testes devem cobrir: não inclusão do próprio parlamentar como semelhante, normalização $L_2$ do vetor composto, cálculo correto de similaridade e formatação neutra da explicação.*
3. **Linter:**
   ```bash
   ruff check backend/services/similaridade_service.py tasks/calcular_similaridade.py
   ```
