# SPEC-006 — Modernização, Refatoração e Validação do Pipeline de ETL da Câmara

## 1. Objetivo e Escopo

### Objetivo
Transformar a esteira de extração, transformação e carga (ETL) dos dados abertos da Câmara dos Deputados em uma arquitetura modular, tipada, testável e de alta resiliência, substituindo o script monolítico `etl_camara.py` por módulos especializados com validação estrita de dados via Pydantic V2, reconciliação de registros órfãos e cargas em lote com idempotência absoluta.

### Escopo de Implementação
- **Diretório Alvo:** `injest_banco/`
- **Módulos a Criar/Refatorar:**
  - `injest_banco/client.py`: Cliente HTTP resiliente para a API v2 da Câmara.
  - `injest_banco/schemas_camara.py`: Schemas Pydantic V2 para sanitização e validação de dados da API.
  - `injest_banco/loaders.py`: Rotinas de bulk upsert de alta performance com SQLAlchemy.
  - `injest_banco/reconciler.py`: Rotina periódica de reconciliação de votações e dados órfãos.
  - `injest_banco/etl_camara.py`: Orquestrador simplificado e modularizado.
- **Modelos de Persistência (Leitura e Carga):**
  - `shared.models.Deputado`, `shared.models.Proposicao`, `shared.models.Votacao`, `shared.models.VotacaoVoto`, `shared.models.Despesa`, `shared.models.Discurso`, `shared.models.Orgao`
- **Testes Obrigatórios:** `injest_banco/tests/test_etl_validators.py` e `injest_banco/tests/test_etl_idempotency.py`

### Ambiente de Execução (Git Worktree Obrigatório)
- **Branch:** `feat/spec-006-etl-camara`
- **Diretório da Worktree:** `.worktrees/spec-006-etl-camara`
- **Comando de Criação:**
  ```bash
  git worktree add -b feat/spec-006-etl-camara .worktrees/spec-006-etl-camara main
  ```
- **Desmonte pós-validação (DoD):**
  ```bash
  git worktree remove .worktrees/spec-006-etl-camara
  ```

---

## 2. Arquitetura Modular do ETL

```
injest_banco/
├── client.py           # Cliente HTTP resiliente (Session, rate-limit, Retry-After, exponential backoff)
├── schemas_camara.py   # Validação e sanitização estrita via Pydantic V2 (Camara -> Banco)
├── loaders.py          # Bulk upserts parametrizados via SQLAlchemy Core (chunks de 500-1000)
├── reconciler.py       # Reconciliação de votações órfãs e dados faltantes
├── etl_camara.py       # Ponto de entrada / CLI orquestrador da ingestão
└── tests/              # Testes unitários com mocks de payloads da Câmara
```

---

## 3. Regras de Engenharia e Qualidade de Dados (Data Quality)

### 1. Sanitização e Validação Estrita (Pydantic V2)
Nenhum dado bruto da API deve ser enviado diretamente ao banco de dados sem passar por um schema Pydantic:
- **Campos Vazios:** Strings vazias (`""`) ou valores `"null"` devem ser convertidos para `None`.
- **Sanitização de Texto:** Remover null-bytes (`\x00`), quebras de linha duplicadas e espaços em branco desnecessários em ementas, nomes e despachos.
- **Datas:** Validação e parse obrigatório para objetos `datetime` ou `date`. Rejeitar ou registrar alerta para registros com datas inválidas (ex: datas futuras ou anos inconsistentes como `0001-01-01`).
- **Validação de Coerência:** A data de última tramitação não pode ser anterior à data de apresentação da proposição.

### 2. Resiliência de Rede e Rate Limiting
- Manter conexão persistente via `requests.Session` (com pool de conexões).
- Tratamento automático de status `429 (Too Many Requests)` respeitando o header `Retry-After` ou aplicando backoff exponencial com jitter (espera de $2^n$ segundos).
- Timeout explícito em todas as chamadas HTTP (ex: `timeout=(5.0, 30.0)`).

### 3. Idempotência e Operações em Lote (Bulk Upsert)
- **Batching:** Inserções e atualizações devem ser feitas em chunks de **500 a 1000 registros** usando `insert().on_conflict_do_update()`.
- **Idempotência Absoluta:** O ETL deve poder ser executado repetidas vezes para o mesmo período sem gerar registros duplicados, sem falhar por violação de unicidade e sem alterar o total de registros válidos.
- **Chaves de Conflito:** Informar explicitamente os `index_elements` de cada tabela (ex: `idCamara` em `proposicoes`, `id` em `deputados`, `(idVotacao, idDeputado)` em `votacaoVotos`).

### 4. Reconciliação de Integridade (Dados Órfãos)
- Se um voto referenciar um `idVotacao` inexistente no banco, o reconciliador deve buscar imediatamente os metadados daquela votação na API antes de descartar ou salvar o voto.
- Se uma proposição referenciar autores não cadastrados, disparar ingestão pontual do deputado correspondente.

---

## 4. Schemas de Validação de Exemplo (Pydantic V2)

```python
from datetime import datetime, date
from typing import Optional
from pydantic import BaseModel, Field, field_validator

class ProposicaoCamaraSchema(BaseModel):
    id: int
    uri: str
    siglaTipo: str
    numero: int
    ano: int
    ementa: Optional[str] = None
    ementaDetalhada: Optional[str] = None
    keywords: Optional[str] = None
    dataApresentacao: Optional[datetime] = None

    @field_validator("ementa", "ementaDetalhada", "keywords", mode="before")
    @classmethod
    def sanitize_strings(cls, v: Optional[str]) -> Optional[str]:
        if not v or not isinstance(v, str):
            return None
        cleaned = v.replace("\x00", "").strip()
        return cleaned if cleaned else None
```

---

## 5. Critérios de Aceite e Verificação Automatizada (DoD)

1. **Testes Unitários de Sanitização e Validação:**
   ```bash
   pytest injest_banco/tests/test_etl_validators.py -v
   ```
   *Deve validar rejeição de dados malformatados, conversão de nulos e parsing de datas.*
2. **Teste de Idempotência:**
   ```bash
   pytest injest_banco/tests/test_etl_idempotency.py -v
   ```
   *Deve garantir que executar a carga de 100 itens duas vezes seguidas resulta exatamente na mesma quantidade de registros no banco.*
3. **Dry-Run de Ingestão Parcial:**
   ```bash
   python -m injest_banco.etl_camara --dry-run --limit 20
   ```
4. **Linter e Formatação:**
   ```bash
   ruff check injest_banco/
   ruff format --check injest_banco/
   ```

