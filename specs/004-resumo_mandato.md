# SPEC-004 — Resumo Automatizado do Mandato

## 1. Objetivo e Escopo

### Objetivo
Gerar sínteses textuais de 2 a 4 parágrafos sobre a trajetória de cada parlamentar durante a legislatura, estruturadas exclusivamente a partir de dados consolidados (temas prioritários da SPEC-001, marcos de impacto da SPEC-002, assiduidade oficial e cargos ocupados), mantendo estrita neutralidade descritiva e zero alucinação.

### Escopo de Implementação
- **Tarefas de Processamento (Batch):** `tasks/gerar_resumos.py`
- **Serviço de Domínio:** `backend/services/resumo_service.py`
- **Endpoints FastAPI:** `backend/api/v1/politico_api.py` (ou `backend/api/v1/resumo_api.py`)
- **Tabela de Persistência:** `deputadoResumo` (ou `resumoIa`)
  - Colunas: `idDeputado`, `idLegislatura`, `resumoTexto`, `modelo`, `versaoPrompt`, `validado`, `updatedAt`
- **Testes Obrigatórios:** `backend/tests/test_resumo.py`

### Ambiente de Execução (Git Worktree Obrigatório)
- **Branch:** `feat/spec-004-resumo`
- **Diretório da Worktree:** `.worktrees/spec-004-resumo`
- **Comando de Criação:**
  ```bash
  git worktree add -b feat/spec-004-resumo .worktrees/spec-004-resumo main
  ```
- **Desmonte pós-validação (DoD):**
  ```bash
  git worktree remove .worktrees/spec-004-resumo
  ```

---

## 2. Dados de Entrada Estruturados (Grounding)

O resumo NÃO pode ser gerado a partir de perguntas abertas à web. O gerador consome exclusivamente um payload JSON estrito extraído do banco:

```json
{
  "deputado": {
    "nome": "Nome Parlamentar",
    "partido": "SIGLA",
    "uf": "UF",
    "presencaPercentual": 92.4,
    "totalProposicoesAutoria": 14
  },
  "temasPrioritarios": [
    {"tema": "Trabalho", "percentual": 38.5},
    {"tema": "Direitos Humanos", "percentual": 24.1},
    {"tema": "Educação", "percentual": 15.2}
  ],
  "marcosPrincipais": [
    {"titulo": "PEC 00/202X - Redução de Jornada", "papel": "Primeiro Autor", "situacao": "Em tramitação na CCJ"},
    {"titulo": "Relatoria do PL 0000/202X", "papel": "Relator", "situacao": "Aprovado na Comissão"}
  ],
  "cargosComissoes": [
    {"cargo": "Presidente", "orgao": "Comissão de Direitos Humanos"}
  ]
}
```

---

## 3. Diretrizes Invioláveis de Neutralidade e Guardrails

### Regras de Negócio:
1. **Zero Adjetivos Avaliativos:** Proibido o uso de adjetivos positivos (*destacado*, *notável*, *corajoso*, *exemplar*, *firme*) ou negativos (*pífio*, *omisso*, *fraco*, *radical*, *vergonhoso*).
2. **Zero Especulação de Motivos:** Nunca justificar ações com *"visando a reeleição"*, *"atendendo a pressões"* ou *"em defesa do povo"*.
3. **Fidelidade Factual Estrita:** Se um dado não estiver presente no JSON de entrada, ele não deve ser mencionado. Não citar proposições que não constem na lista oficial.

### Validador Automático Pós-Geração (Safety Filter):
Todo texto gerado deve passar por uma função de validação antes de ser gravado no banco de dados. Caso contenha qualquer termo da lista negra léxica, o resumo é descartado e o job registra erro:
```python
TERMOS_PROIBIDOS = {
    "excelente", "pífio", "corajoso", "vergonhoso", "destacado", "revolucionário",
    "radical", "traidor", "herói", "salvador", "incompetente", "brilhante",
    "exemplar", "decepcionante", "louvável", "lamentável", "autoritário"
}
```

---

## 4. Prompt Base e Formato de Saída

### System Prompt
```text
Você é um analista institucional do QuemVota encarregado de redigir sínteses parlamentares estritamente descritivas, neutras e factuais.

Suas regras inegociáveis:
1. Responda em Português do Brasil.
2. Baseie-se UNICAMENTE nos dados JSON informados no prompt.
3. Não use adjetivos qualificativos ou juízos de valor (proibido dizer que algo é "importante", "histórico", "polêmico" ou "negativo").
4. Formate a saída em texto puro (sem negritos, asteriscos ou hashtags), em até 3 parágrafos:
   - Parágrafo 1: Descrição dos temas predominantes e frequência de presença em sessões.
   - Parágrafo 2: Principais proposições e relatorias registradas nos dados.
   - Parágrafo 3: Cargos exercidos em órgãos e comissões (se houver).
```

---

## 5. Contratos de API (FastAPI / Pydantic V2)

### Endpoint
`GET /api/v1/politicos/{id}/resumo`

### Schemas Pydantic:
```python
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

class ResumoMandatoResponse(BaseModel):
    idDeputado: int
    idLegislatura: int
    resumo: str = Field(..., description="Texto neutro e factual do mandato (2 a 4 parágrafos)")
    modeloGerador: str
    atualizadoEm: datetime

class StatusGeracaoResumo(BaseModel):
    idDeputado: int
    sucesso: bool
    mensagem: str
```

---

## 6. Critérios de Aceite e Verificação Automatizada (DoD)

1. **Geração e Validação com Amostra:**
   ```bash
   python -m tasks.gerar_resumos --limit 5 --dry-run
   ```
2. **Testes Unitários:**
   ```bash
   pytest backend/tests/test_resumo.py -v
   ```
   *Os testes devem cobrir: rejeição de textos com termos proibidos pelo filtro de neutralidade, validação de estrutura em parágrafos e resposta 404 quando o parlamentar ainda não tiver resumo computado.*
3. **Linter:**
   ```bash
   ruff check backend/services/resumo_service.py tasks/gerar_resumos.py
   ```
