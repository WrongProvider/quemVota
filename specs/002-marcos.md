# SPEC-002 — Marcos do Mandato

## 1. Objetivo e Escopo

### Objetivo
Identificar e ranquear os acontecimentos de maior relevância legislativa e institucional de um parlamentar durante o mandato (projetos de lei estruturantes, relatorias-chave, presidências de CPIs ou comissões), substituindo métricas puramente quantitativas por avaliação objetiva de impacto institucional e tramitação.

### Escopo de Implementação
- **Tarefas de Processamento (Batch):** `tasks/identificar_marcos.py`
- **Serviço de Domínio:** `backend/services/marco_service.py`
- **Endpoints FastAPI:** `backend/api/v1/politico_api.py` (ou `backend/api/v1/marco_api.py`)
- **Modelos Utilizados:**
  - `shared.models_vetorial.MarcoMandato` (`marcosMandato`)
  - `shared.models.Proposicao`, `shared.models.ProposicaoAutor`
  - `shared.models.Tramitacao`, `shared.models.Discurso`, `shared.models.OrgaoMembro`
- **Testes Obrigatórios:** `backend/tests/test_marcos.py`

### Ambiente de Execução (Git Worktree Obrigatório)
- **Branch:** `feat/spec-002-marcos`
- **Diretório da Worktree:** `.worktrees/spec-002-marcos`
- **Comando de Criação:**
  ```bash
  git worktree add -b feat/spec-002-marcos .worktrees/spec-002-marcos main
  ```
- **Desmonte pós-validação (DoD):**
  ```bash
  git worktree remove .worktrees/spec-002-marcos
  ```

---

## 2. Candidatos a Marco e Definição de Tipos

São elegíveis a marcos do mandato os seguintes tipos de eventos (`TipoMarco` em `shared.models_vetorial`):
1. `proposicao`: PEC, PLP, PL, MPV, PDC ou PRC onde o deputado seja autor ou coautor.
2. `relatoria`: Proposições em que o parlamentar atuou como relator designado (`ultimoStatus_uriRelator`).
3. `cpi`: Participação como presidente ou relator de Comissão Parlamentar de Inquérito.
4. `presidencia_comissao`: Exercício da presidência ou vice-presidência de comissão temática ou especial.
5. `requerimento`: Requerimentos de convocação de ministros ou criação de CPI.

---

## 3. Algoritmo Determinístico de Cálculo de Impacto

Para cada evento candidato de um parlamentar (`idDeputado`) em uma legislatura (`idLegislatura`):

### 1. Pontuação Base por Instrumento ($P_{\text{base}}$)
| Tipo do Evento / Proposição | Pontos ($P_{\text{base}}$) |
|---|---|
| PEC (Proposta de Emenda à Constituição) | 40.0 |
| Presidência ou Relatoria de CPI | 35.0 |
| PLP (Projeto de Lei Complementar) | 30.0 |
| MPV (Medida Provisória) | 25.0 |
| Relatoria em Comissão Especial / Plenário | 25.0 |
| PL (Projeto de Lei Ordinária) | 20.0 |
| Presidência de Comissão Permanente | 20.0 |
| PDC / PRC (Decreto Legislativo ou Resolução) | 15.0 |
| Requerimento de Convocação de Autoridade / CPI | 10.0 |
| Outros Requerimentos / Moções | 2.0 |

### 2. Modificador de Autoria ($M_{\text{papel}}$)
Apenas aplicável a proposições:
- **Autor Principal (proponente 1 ou autor isolado):** $M_{\text{papel}} = 1.0$
- **Coautor nos Primeiros Assinantes (ordem $\le 3$):** $M_{\text{papel}} = 0.6$
- **Demais Coautores:** $M_{\text{papel}} = 0.3$
*(Para relatorias e presidências de órgãos, $M_{\text{papel}} = 1.0$).*

### 3. Bonificações por Tramitação e Sucesso Legislativo ($P_{\text{tramitacao}}$)
Avaliado via histórico de `tramitacoes`:
- Parecer favorável aprovado em Comissão: **+10.0 pontos**
- Aprovado no Plenário da Câmara dos Deputados: **+25.0 pontos**
- Aprovado no Senado Federal: **+20.0 pontos**
- Sancionado e promulgado (transformado em norma jurídica): **+30.0 pontos**

### 4. Bonificação por Citações em Plenário ($P_{\text{discurso}}$)
- Cada menção nominal à proposição ou relatório em discursos de plenário (`shared.models.Discurso`): **+2.0 pontos** (teto máximo acumulado: **15.0 pontos**).

### 5. Fórmula do Score de Impacto e Seleção Top 5
$$Score_{\text{bruto}} = (P_{\text{base}} \times M_{\text{papel}}) + P_{\text{tramitacao}} + P_{\text{discurso}}$$
$$Score_{\text{impacto}} = \min(100.0, \text{round}(Score_{\text{bruto}}, 2))$$

- **Seleção dos Top 5:**
  - Selecionar os 5 maiores eventos ordenados por `scoreImpacto DESC`.
  - Critério de desempate: data de referência mais recente (`dataReferencia DESC`).
  - Atribuir `rank` sequencial de 1 a 5.
  - Persistir em `marcosMandato`, registrando a composição detalhada dos pontos no campo `fatores` (JSONB).

---

## 4. Contratos de API (FastAPI / Pydantic V2)

### Endpoint
`GET /api/v1/politicos/{id}/marcos`

### Parâmetros de Query:
- `idLegislatura` (opcional, `int`, default `57`).
- `limit` (opcional, `int`, default `5`, max `10`).

### Schemas Pydantic:
```python
from datetime import date
from typing import Any, Optional
from pydantic import BaseModel, Field

class FatoresImpacto(BaseModel):
    pontosBase: float
    modificadorPapel: float
    pontosTramitacao: float
    pontosDiscurso: float

class MarcoMandatoResponse(BaseModel):
    id: int
    tipoMarco: str = Field(..., description="proposicao, relatoria, cpi, presidencia_comissao, requerimento")
    titulo: str
    descricao: Optional[str] = None
    dataReferencia: Optional[date] = None
    scoreImpacto: float = Field(..., ge=0.0, le=100.0)
    rank: int = Field(..., ge=1, le=10)
    fatores: FatoresImpacto

class PoliticoMarcosResponse(BaseModel):
    idDeputado: int
    idLegislatura: int
    totalMarcos: int
    marcos: list[MarcoMandatoResponse]
```

---

## 5. Critérios de Aceite e Verificação Automatizada (DoD)

1. **Processamento em Lote:**
   ```bash
   python -m tasks.identificar_marcos --limit-deputados 10 --dry-run
   ```
2. **Testes Unitários:**
   ```bash
   pytest backend/tests/test_marcos.py -v
   ```
   *Os testes devem cobrir: cálculo correto dos modificadores de coautoria, pontuações de sanção e aprovação, ordenação de top 5, e limite superior de 100 pontos.*
3. **Linter:**
   ```bash
   ruff check backend/services/marco_service.py tasks/identificar_marcos.py
   ```
