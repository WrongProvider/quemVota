# SPEC 008 — Métricas Factuais e Transparência (Comparador de Parlamentares)

## 1. Objetivo
Criar um conjunto de endpoints no Backend (FastAPI) e componentes no Frontend para disponibilizar métricas quantitativas reais e neutras dos parlamentares. O objetivo é substituir a ideia genérica de "Ranking" (que infringe a neutralidade descritiva) por estatísticas desagregadas que permitam ao cidadão ordenar, comparar e tirar suas próprias conclusões.

Nenhuma dessas métricas utilizará pesos subjetivos ou gerará um "score" único.

## 2. Princípio da Neutralidade (AGENTS.md)
* **Zero Juízo de Valor**: As descrições não podem usar adjetivos (ex: não usar "gastou muito", usar "Total gasto: R$ X").
* **Sem Score Unificado**: Os dados serão apresentados separadamente (Presenças, Gastos, Produção Legislativa).

## 3. Fontes de Dados e Queries (SQLAlchemy)

Todas as consultas serão feitas nas tabelas existentes do banco relacional (`shared/models.py`).

### 3.1. Uso da Cota Parlamentar (Transparência Financeira)
Agregação baseada na tabela `Despesa` (`despesas`).

* **Total Gasto (Por Ano ou Mandato):**
  ```python
  from sqlalchemy.sql import func
  
  query = (
      session.query(func.sum(Despesa.valorLiquido))
      .filter(Despesa.idDeputado == deputado_id)
  )
  ```
* **Top Categorias de Gastos:**
  ```python
  query = (
      session.query(
          Despesa.tipoDespesa,
          func.sum(Despesa.valorLiquido).label('total')
      )
      .filter(Despesa.idDeputado == deputado_id)
      .group_by(Despesa.tipoDespesa)
      .order_by(func.sum(Despesa.valorLiquido).desc())
      .limit(5)
  )
  ```

### 3.2. Produção Legislativa (Autoria)
Agregação baseada nas tabelas `ProposicaoAutor` e `Proposicao`.

* **Total de Proposições (Como Autor Principal - proponente = True):**
  ```python
  query = (
      session.query(func.count(Proposicao.id))
      .join(ProposicaoAutor, Proposicao.id == ProposicaoAutor.idProposicao)
      .filter(
          ProposicaoAutor.idDeputadoAutor == deputado_id,
          ProposicaoAutor.proponente == True
      )
  )
  ```
* **Distribuição por Tipo (PL, PEC, INC, etc.):**
  ```python
  query = (
      session.query(Proposicao.siglaTipo, func.count(Proposicao.id).label('total'))
      .join(ProposicaoAutor, Proposicao.id == ProposicaoAutor.idProposicao)
      .filter(
          ProposicaoAutor.idDeputadoAutor == deputado_id,
          ProposicaoAutor.proponente == True
      )
      .group_by(Proposicao.siglaTipo)
      .order_by(func.count(Proposicao.id).desc())
  )
  ```

### 3.3. Assiduidade (Presença em Eventos)
Agregação baseada na tabela `PresencaDeputado`.
* **Total de Presenças Registradas:**
  ```python
  query = (
      session.query(func.count(PresencaDeputado.id))
      .filter(PresencaDeputado.idDeputado == deputado_id)
  )
  ```

### 3.4. Engajamento na Tribuna
Agregação baseada na tabela `Discurso`.
* **Total de Discursos Proferidos:**
  ```python
  query = (
      session.query(func.count(Discurso.id))
      .filter(Discurso.idDeputado == deputado_id)
  )
  ```

## 4. Contratos de API (Pydantic / FastAPI)

**Novo Endpoint:** `GET /api/v1/deputados/{id}/metricas`
**Novo Endpoint (Agregação Geral para Listagem):** `GET /api/v1/deputados/metricas/resumo` (para a tabela/painel comparativo)

**Schemas (`backend/schemas/metricas.py`):**
```python
from pydantic import BaseModel
from typing import List

class CategoriaGasto(BaseModel):
    tipoDespesa: str
    valorTotal: float

class TipoProposicao(BaseModel):
    sigla: str
    quantidade: int

class MetricasDeputado(BaseModel):
    idDeputado: int
    totalGastoCota: float
    topGastos: List[CategoriaGasto]
    totalProposicoesAutor: int
    distribuicaoProposicoes: List[TipoProposicao]
    totalPresencas: int
    totalDiscursos: int
```

## 5. Implementação no Frontend

* **Criação da Rota/Página:** `frontend/src/pages/ComparadorDeputados.tsx`
* **Exibição:** 
  * Tabela de dados ordenável (DataGrid / Table) contendo: `Foto`, `Nome`, `Partido`, `Total Gasto R$`, `Proposições (Autor)`, `Presenças`.
  * Filtros por Estado (UF) e Partido.
  * Respeitar as diretrizes *Mobile-First* estabelecidas no `AGENTS.md` para evitar *overflow* horizontal na tabela (usar *cards* ou scroll isolado no mobile).
* **Hook SEO:** Garantir a chamada de `useSeo()` com título descritivo e neutro: *"Comparador de Parlamentares | Estatísticas e Transparência - QuemVota"*.

## 6. Critérios de Validação (Definition of Done)

1. **Testes Unitários de Backend:**
   * `pytest backend/tests/test_services_metricas.py` deve passar garantindo que as contas de agregação (Soma/Count) batem.
2. **Lint e Formatação:**
   * Executar `ruff check .` e `ruff format --check .`
3. **Teste End-to-End (Frontend):**
   * A nova página `ComparadorDeputados.tsx` deve ser testada pelo Playwright (`BASE_URL=http://localhost npx playwright test tests/dinamica_site.spec.ts`).
   * Não deve haver quebra de layout em resoluções mobile (`sm:`).
4. **Neutro por Design:**
   * Garantir ausência de cores que indiquem "bom/ruim" (ex: evitar usar verde para muitas propostas e vermelho para poucas, pois "muitas propostas" não significa necessariamente qualidade). Usar cores institucionais/neutras.

