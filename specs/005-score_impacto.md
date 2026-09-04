# SPEC-005 — Índice Multidimensional de Impacto Parlamentar [DEPRECADO / ARQUIVADO]

> [!CAUTION]
> **ESPECIFICAÇÃO ARQUIVADA / DEPRECADA:**
> Esta especificação foi descontinuada em favor do **Princípio da Neutralidade Factual Absoluta** (Seção 1 de `AGENTS.md`).
> O QuemVota não emite notas, índices avaliativos ou scores de 0 a 100 para parlamentares, evitando qualquer juízo de valor ou peso normativo subjetivo. Todas as informações disponibilizadas pela plataforma devem ser puramente factuais, descritivas e auditáveis a partir de dados abertos oficiais.

## 1. Objetivo e Escopo (Histórico)

### Objetivo
Calcular o **Índice de Impacto Parlamentar**, um indicador balanceado de 0 a 100 pontos que mensura a influência legislativa efetiva, a tramitação de projetos e a capacidade de articulação institucional de cada deputado, superando análises puramente quantitativas que equiparam requerimentos simples a reformas estruturais.

### Escopo de Implementação
- **Tarefas de Processamento (Batch):** `tasks/calcular_impacto.py`
- **Serviço de Domínio:** `backend/services/impacto_service.py`
- **Endpoints FastAPI:** `backend/api/v1/politico_api.py` (ou `backend/api/v1/impacto_api.py`)
- **Modelos Utilizados:**
  - `shared.models_vetorial.DeputadoImpacto` (`deputadoImpacto`)
  - `shared.models.Deputado`, `shared.models.Proposicao`, `shared.models.Tramitacao`
  - `shared.models.OrgaoMembro`, `shared.models.Discurso`, `shared.models.Presenca`
- **Testes Obrigatórios:** `backend/tests/test_impacto.py`

### Ambiente de Execução (Git Worktree Obrigatório)
- **Branch:** `feat/spec-005-impacto`
- **Diretório da Worktree:** `.worktrees/spec-005-impacto`
- **Comando de Criação:**
  ```bash
  git worktree add -b feat/spec-005-impacto .worktrees/spec-005-impacto main
  ```
- **Desmonte pós-validação (DoD):**
  ```bash
  git worktree remove .worktrees/spec-005-impacto
  ```

---

## 2. As 5 Dimensões e Fórmulas Matemáticas

O score final é composto por cinco dimensões independentes, normalizadas de **0.00 a 100.00**, armazenadas na tabela `deputadoImpacto`:

### Dimensão 1: Produção Legislativa ($S_{\text{producao}}$) — Peso: 30%
Avalia o peso regulatório das matérias de autoria e das relatorias assumidas:
- Autoria Principal de PEC: **20.0 pontos** cada
- Autoria Principal de PLP ou MPV: **15.0 pontos** cada
- Autoria Principal de PL: **8.0 pontos** cada
- Relatoria em Comissão Especial / Mista / Plenário: **12.0 pontos** cada
- Relatoria em Comissão Permanente: **6.0 pontos** cada
- Coautoria em matérias estruturantes: **2.0 pontos** cada

$$\text{Pontos Brutos} = \sum \text{pesos itens}$$
$$S_{\text{producao}} = \min\left(100.0, \frac{\text{Pontos Brutos}}{\text{Meta Produção (80 pts)}} \times 100.0\right)$$

### Dimensão 2: Tramitação e Eficácia ($S_{\text{tramitacao}}$) — Peso: 30%
Mede a conversão de projetos em normas e o avanço real no processo decisório:
- Parecer favorável aprovado em Comissão: **+10.0 pontos**
- Matéria de autoria aprovada no Plenário da Câmara: **+30.0 pontos**
- Matéria de autoria aprovada no Senado Federal: **+25.0 pontos**
- Norma promulgada / convertida em Lei (sanção): **+35.0 pontos**

$$S_{\text{tramitacao}} = \min\left(100.0, \frac{\text{Pontos Brutos Tramitação}}{\text{Meta Tramitação (60 pts)}} \times 100.0\right)$$

### Dimensão 3: Liderança Institucional ($S_{\text{lideranca}}$) — Peso: 20%
Reconhece o exercício de poder e autoridade formal na Câmara dos Deputados:
- Presidência da Mesa Diretora: **100.0 pontos**
- Membro da Mesa Diretora: **70.0 pontos**
- Presidência de Comissão Permanente, Especial ou CPI: **60.0 pontos**
- Liderança de Bancada, Partido ou Bloco Parlamentar: **50.0 pontos**
- Vice-Presidência de Comissão: **30.0 pontos**

$$S_{\text{lideranca}} = \min(100.0, \text{Cargo de Maior Pontuação} + 0.20 \times \text{Soma dos Demais Cargos})$$

### Dimensão 4: Participação Parlamentar ($S_{\text{participacao}}$) — Peso: 10%
Combina a assiduidade oficial com intervenções em plenário:
- $P_{\text{presenca}}$: Percentual de presença nas sessões deliberativas da Câmara ($0.0 \text{ a } 100.0$).
- $P_{\text{discursos}} = \min\left(100.0, \frac{\text{total de discursos proferidos}}{20} \times 100.0\right)$.

$$S_{\text{participacao}} = (0.70 \times P_{\text{presenca}}) + (0.30 \times P_{\text{discursos}})$$

### Dimensão 5: Fiscalização e Controle ($S_{\text{fiscalizacao}}$) — Peso: 10%
Atuação como fiscalizador dos atos do Poder Executivo:
- Requerimento de Informação a Ministros (RIC): **15.0 pontos** cada
- Requerimento de Audiência Pública aprovado: **10.0 pontos** cada
- Assinatura para criação de CPI: **5.0 pontos** cada

$$S_{\text{fiscalizacao}} = \min\left(100.0, \frac{\text{Pontos Brutos Fiscalização}}{40.0} \times 100.0\right)$$

---

## 3. Consolidação do Score Final

O índice global é a média ponderada das 5 dimensões:

$$Score_{\text{total}} = (0.30 \cdot S_{\text{producao}}) + (0.30 \cdot S_{\text{tramitacao}}) + (0.20 \cdot S_{\text{lideranca}}) + (0.10 \cdot S_{\text{participacao}}) + (0.10 \cdot S_{\text{fiscalizacao}})$$

- Persistir em `deputadoImpacto` com `round(Score, 2)`.
- No campo `detalhes` (JSONB), salvar o breakdown detalhado das métricas que deram origem a cada dimensão para transparência pública e auditoria.

---

## 4. Contratos de API (FastAPI / Pydantic V2)

### Endpoint
`GET /api/v1/politicos/{id}/impacto`

### Parâmetros de Query:
- `idLegislatura` (opcional, `int`, default `57`).

### Schemas Pydantic:
```python
from datetime import datetime
from typing import Any, Optional
from pydantic import BaseModel, Field

class DimensoesImpacto(BaseModel):
    producao: float = Field(..., ge=0.0, le=100.0)
    tramitacao: float = Field(..., ge=0.0, le=100.0)
    lideranca: float = Field(..., ge=0.0, le=100.0)
    participacao: float = Field(..., ge=0.0, le=100.0)
    fiscalizacao: float = Field(..., ge=0.0, le=100.0)

class ImpactoParlamentarResponse(BaseModel):
    idDeputado: int
    idLegislatura: int
    scoreTotal: float = Field(..., ge=0.0, le=100.0, description="Índice global de impacto (0 a 100)")
    dimensoes: DimensoesImpacto
    detalhes: dict[str, Any]
    atualizadoEm: datetime
```

---

## 5. Critérios de Aceite e Verificação Automatizada (DoD)

1. **Cálculo em Lote:**
   ```bash
   python -m tasks.calcular_impacto --limit-deputados 10 --dry-run
   ```
2. **Testes Unitários:**
   ```bash
   pytest backend/tests/test_impacto.py -v
   ```
   *Os testes devem cobrir: cálculo correto de cada dimensão, respeito estrito aos limites [0.00, 100.00] mesmo para deputados com produção zero ou extrema, e salvamento do breakdown no JSONB.*
3. **Linter:**
   ```bash
   ruff check backend/services/impacto_service.py tasks/calcular_impacto.py
   ```
