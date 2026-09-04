# AGENTS.md — Diretrizes de Engenharia para Agentes Autônomos (QuemVota)

Bem-vindo ao repositório do **QuemVota**. Este documento define os princípios fundamentais, padrões de engenharia, limites de escopo e protocolos de execução obrigatórios para qualquer agente de inteligência artificial (Antigravity CLI `agy`, IDE Agents, Subagents e Pipelines Multiagente) atuando neste código.

---

## 1. Princípio da Neutralidade Factual Absoluta

O QuemVota tem como compromisso basilar a **transparência pública e a neutralidade descritiva**:
- **Apenas fatos observáveis:** Descreva exclusivamente votações nominais, autoria de proposições, presenças e relatorias registradas oficialmente.
- **Zero julgamento de valor:** É estritamente proibido emitir elogios, críticas, atribuições de motivação ("com intuito eleitoreiro", "em defesa do povo") ou juízos morais.
- **Sem adjetivos avaliativos:** Proibido o uso de adjetivos como *notável*, *pífio*, *polêmico*, *exemplar*, *retrocesso*, *avanço*. Utilize formulações factuais: *"A proposição tramitou por 14 meses e recebeu parecer favorável na comissão X"*.
- **Ausência de Scores e Rótulos Avaliativos:** É estritamente proibido criar índices unificados, notas de 0 a 100 ou rankings normativos que rotulem parlamentares como "melhores/piores" ou "excelentes/críticos". Apresente métricas factuais desagregadas (taxa de presença, total de gastos em R$, utilização orçamentária, quantidade e autoria de proposições) para que o próprio cidadão tire suas conclusões.
- **Rastreabilidade:** Toda informação gerada deve poder ser referenciada por identificadores únicos (`id` da proposição, `id` da votação, `id` do deputado na API da Câmara dos Deputados).

---

## 2. Estrutura do Repositório e Limites de Escopo (Boundaries)

Para evitar conflitos de merge e desvios de arquitetura, cada agente deve atuar estritamente dentro da sua fronteira de arquivos:

```
quemVota/
├── AGENTS.md                # Diretrizes mestras para agentes (este arquivo)
├── specs/                   # Especificações técnicas e contratos das features de IA (001 a 005)
├── shared/                  # Camada compartilhada de persistência e modelos (models.py, models_vetorial.py)
├── backend/                 # API FastAPI (endpoints v1, services de cálculo, schemas Pydantic)
├── frontend/                # Interface web (React + TypeScript + Vite)
├── injest_banco/            # Pipeline de ETL e sincronização com a API da Câmara dos Deputados
├── embeddings/              # Geração de vetores semânticos (modelo BAAI/bge-m3)
├── tasks/                   # Scripts de processamento em lote para cálculo de temas e marcos
└── orchestrator.py          # Orquestrador de execução concorrente de agentes
```

### Regras de Fronteira por Especialidade:
- **Agente de Backend (`agent/backend`):** Modifica exclusivamente `backend/`. Consome modelos de `shared/`. NÃO edita tabelas em `shared/models.py` diretamente sem validação de migração.
- **Agente de Frontend (`agent/frontend`):** Modifica exclusivamente `frontend/`. Respeita estritamente os contratos OpenAPI/Pydantic fornecidos pelo backend. É obrigatório validar qualquer implementação ou alteração com testes end-to-end (E2E) utilizando o MCP do Playwright.
- **Agente de ETL (`agent/etl`):** Especialista em Engenharia de Dados Legislativos. Modifica `injest_banco/` e `tasks/`. Responsável pela refatoração modular de scripts de ingestão (`etl_camara.py`), validação estrita de dados com Pydantic V2, resiliência HTTP (backoff, rate-limits), tratamento de registros órfãos e garantia de idempotência total (`ON CONFLICT`) em todas as inserções no PostgreSQL.
- **Agente de IA/Vetorial (`agent/ai`):** Modifica `embeddings/`, `shared/models_vetorial.py` e `shared/vector_search.py`.
- **Agente de QA/Gatekeeper (`agent/qa-validation`):** Valida a integração de ponta a ponta, roda testes unitários e linting. Não introduz novas features.

---

## 3. Padrões de Código e Convenções Técnicas

### Python:
- **Versão:** Python 3.10+
- **Tipagem Estrita:** Todas as funções devem ter type hints completos (`from typing import Optional, List, Dict...` ou sintaxe moderna `list[str]`, `str | None`).
- **Validação de Dados:** Use Pydantic V2 para todos os schemas de entrada/saída de APIs e jobs.
- **Qualidade de Código:** Antes de concluir qualquer tarefa, execute:
  ```bash
  ruff check .
  ruff format --check .
  ```

### Diretrizes Especializadas para o Pipeline de ETL (`injest_banco/`):
O especialista em ETL da Câmara deve atuar ativamente na modernização, qualidade e robustez da esteira de dados:
1. **Refatoração e Modularização do `etl_camara.py`:**
   - Decompor progressivamente o script monolítico em submódulos coesos:
     - `injest_banco/collectors/`: Clientes de requisição com paginação inteligente, retentativas com backoff exponencial e respeito a rate-limits (HTTP 429).
     - `injest_banco/validators/`: Modelos Pydantic V2 para sanitização, normalização de tipos e rejeição de dados corrompidos antes da gravação.
     - `injest_banco/loaders/`: Funções de carga em lote (`batch upsert`) de alta performance via SQLAlchemy Core / bulk operations.
2. **Validação Estrita de Dados (Data Quality & Cleansing):**
   - Sanitização de strings (remoção de null-bytes, espaços extras, quebras de linha espúrias e encoding incorreto).
   - Validação de coerência temporal (ex: data de tramitação não pode ser anterior à data de apresentação da proposição).
   - Reconciliação de integridade referencial: tratamento sistemático de votações órfãs, deputados sem legislatura e proposições sem autor.
3. **Idempotência e Performance de Banco:**
   - Proibido executar `INSERT` unitário em loops de milhares de itens. Utilizar batches (chunks de 500 a 2000 registros).
   - Todo upsert deve declarar explicitamente `index_elements` correspondentes às chaves únicas.
4. **Observabilidade e Logs Estruturados:**
   - Proibido o uso de `print()` solto em scripts de produção. Utilize o módulo `logging` com níveis semânticos (`DEBUG`, `INFO`, `WARNING`, `ERROR`).
   - Métricas de execução estruturadas ao final de cada execução: registros lidos da API, registros validados, inseridos, atualizados e descartados por inconsistência.

### Banco de Dados & pgvector:
- **ORM Canônico:** Utilize exclusivamente SQLAlchemy com os modelos definidos em:
  - `shared/models.py` (dados relacionais da Câmara)
  - `shared/models_vetorial.py` (dados semânticos, vetoriais e índices HNSW)
- **Segurança SQL:** NUNCA concatene strings em queries brutas. Use sempre queries parametrizadas (`%s`, `:param`) ou queries via SQLAlchemy ORM / Core.
- **Idempotência em Upserts:** Ao utilizar `insert(...).on_conflict_do_update(...)`, informe explicitamente os `index_elements` correspondentes às chaves de unicidade (ex: `index_elements=["tipoEntidade", "idEntidade", "modelo"]`).
- **Modelo de Embeddings:** O modelo padrão obrigatório é `BAAI/bge-m3` com dimensão fixa de **1024**, normalizado para distância por cosseno (`vector_cosine_ops`).

### Frontend & Testes End-to-End Obrigatórios (Playwright MCP):
- **Stack:** React + TypeScript + Vite.
- **Validação E2E Mandatória:** Qualquer implementação, refatoração ou nova funcionalidade no frontend (`frontend/`) **DEVE** obrigatoriamente passar por validação com testes end-to-end (E2E) utilizando o MCP do Playwright antes de ser concluída.
- **Protocolo de Validação:**
  1. **Disponibilidade do Ambiente:** Assegurar que a aplicação frontend (e APIs dependentes, se necessário) esteja em execução no ambiente local (`npm run dev` ou build de preview).
  2. **Interação Real via MCP:** Empregar as ferramentas do MCP do Playwright (`navigate`, `click`, `fill`, etc.) para simular a navegação e o fluxo completo do usuário nas telas modificadas.
  3. **Verificação de Integridade:** Checar logs de console (ausência de erros de JavaScript e chamadas HTTP com status de erro) e validar visualmente/estruturalmente os elementos e respostas da interface.

### Orquestração Mandatória no Apache Airflow:
**Regra Obrigatória de Automação e Recorrência:**
Toda vez que for criado ou alterado um script de ETL (`injest_banco/`), enriquecimento, vetorização semântica (`embeddings/`), cálculo de temas/scores/grafos (`tasks/`) ou qualquer rotina batch que precise ser executada periodicamente ou mais de uma vez em produção, é **estritamente obrigatório** orquestrá-lo em uma DAG no Apache Airflow (`airflow/dags/`).
- **Idempotência Obrigatória:** O script deve poder rodar repetidas vezes sem duplicar dados ou causar falhas (`ON CONFLICT`, detecção de pendências).
- **Alinhamento de Ambiente:** O script deve ser compatível com execução via `uv run python ...` ou `BashOperator` dentro do container do Airflow (`airflow-common`), garantindo que diretórios necessários estejam devidamente montados como volumes no `deploy/docker-compose.yml`.
- **Validação:** Qualquer inclusão ou alteração de DAG deve ter a sintaxe validada (`python -m py_compile airflow/dags/*.py`) e ser testada no scheduler do Airflow.

---



## 4. Como Executar Tarefas a partir de Specs (`specs/`)

Quando designado para implementar uma spec (`specs/001-temas.md` a `specs/005-score_impacto.md`):

1. **Leitura Completa:** Leia atentamente a especificação correspondente.
2. **Criação Mandatória de Git Worktree:** NUNCA implemente na branch `main` diretamente. Crie uma worktree isolada:
   ```bash
   git worktree add -b feat/spec-XXX-nome .worktrees/spec-XXX main
   ```
3. **Respeito às Fórmulas:** Não invente pesos, parâmetros ou regras alternativas. Aplique exatamente as fórmulas e pesos especificados no documento.
4. **Persistência nos Modelos Existentes:** Mapeie as saídas para as tabelas já modeladas em `shared/models_vetorial.py`.
5. **Verificação Automatizada (Definition of Done):** Uma tarefa só é considerada completa quando todos os comandos descritos na seção **Critérios de Validação** da spec passarem com sucesso (ex: `pytest backend/tests/test_...py`).
6. **Finalização e Limpeza:** Após commit na branch da feature, desmonte a worktree:
   ```bash
   git worktree remove .worktrees/spec-XXX
   ```

---

## 5. Protocolo Obrigatório de Git Worktrees e Versionamento

O uso de **Git Worktrees é obrigatório** para todo e qualquer agente autônomo. Isso garante que múltiplos agentes possam operar simultaneamente sem sobreposição de estado, sem bloqueios de arquivo e sem sujeira na branch de desenvolvimento:

### Ciclo de Vida da Worktree para Agentes:
1. **Inicialização:**
   ```bash
   mkdir -p .worktrees
   git worktree add -b <nome-da-branch> .worktrees/<id-da-tarefa> main
   ```
2. **Execução:**
   - O agente deve operar com seu diretório de trabalho (`cwd`) exclusivamente dentro da pasta da worktree (`.worktrees/<id-da-tarefa>`).
   - Todos os arquivos criados ou modificados devem residir na worktree.
3. **Commit Padronizado:**
   - Seguir Conventional Commits (`feat:`, `fix:`, `test:`).
   - Proibido commitar arquivos temporários, logs (`*.log`), caches (`.ruff_cache`, `.pytest_cache`) ou `.env`.
4. **Limpeza e Descarte Seguro:**
   - Nunca deixe worktrees órfãs. Após validação e merge/PR, execute:
     ```bash
     git worktree remove --force .worktrees/<id-da-tarefa>
     ```

---

## 6. Validação de Infraestrutura, Containers e Deploy (Docker)

Qualquer agente que alterar dependências (`pyproject.toml`, `uv.lock`, `package.json`), Dockerfiles, migrations ou scripts de infraestrutura DEVE garantir a integridade do ambiente conteinerizado antes de reportar conclusão:

### 1. Validação Sintática do Compose:
Garante que o arquivo de orquestração não contém erros de sintaxe ou variáveis faltantes:
```bash
docker compose -f deploy/docker-compose.yml config --quiet
```

### 2. Validação de Build sem Cache (Dry-Run de Imagem):
- **Backend / API:** Se alterar `backend/`, `shared/` ou `pyproject.toml`:
  ```bash
  docker build -f backend/Dockerfile.api -t quemvota_api:test .
  ```
- **Frontend:** Se alterar `frontend/` ou `package.json`:
  ```bash
  docker build -f frontend/Dockerfile -t quemvota_frontend:test ./frontend
  ```

### 3. Integridade de Healthchecks e Startup:
- Nenhum container pode entrar em estado de crash loop (`Restarting` ou `Exit 1`).
- Os serviços com healthcheck (`api`, `postgres`, `valkey`, `airflow-webserver`) devem atingir o status **`healthy`**:
  ```bash
  # Verificação de status dos containers ativos
  docker compose ps
  # Verificação direta do healthcheck da API
  curl -f http://localhost:8000/ || curl -f http://localhost:8000/docs
  ```

### 4. Alinhamento com o Script de Deploy (`deploy/deploy.sh`):
O deploy contínuo em produção na VPS executa a atualização in-place sem reiniciar os bancos:
```bash
docker compose up -d --build --no-deps api frontend nginx
```
Qualquer alteração feita por agentes deve ser compatível com reinicializações sem downtime de banco e sem dependência de intervenção manual no terminal do servidor.


