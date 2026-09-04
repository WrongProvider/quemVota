"""
backfill_deputados_detalhes.py
──────────────────────────────
Preenche os campos de detalhe da tabela `deputados` que não estão disponíveis
no CSV/listagem paginada e precisam ser buscados um a um via:

    GET /deputados/{id}

Campos preenchidos por este script:
  - nomeCivil
  - dataNascimento
  - siglaSexo         (vem como "sexo" na raiz do JSON)
  - escolaridade
  - situacao          (ultimoStatus.situacao)
  - condicaoEleitoral (ultimoStatus.condicaoEleitoral)
  - siglaUF           (ultimoStatus.siglaUf  — atualiza caso tenha mudado)
  - siglaPartido      (ultimoStatus.siglaPartido — idem)
  - urlFoto           (ultimoStatus.urlFoto   — idem)
  - emailGabinete     (ultimoStatus.gabinete.email)
  - telefoneGabinete  (ultimoStatus.gabinete.telefone)
  - cpf
  - slug              (gerado a partir de nomeCivil, com desambiguação)

Estratégia de execução:
  - Processa TODOS os deputados por padrão (--force) ou apenas os incompletos
  - Busca na API em paralelo (ThreadPoolExecutor) — escrita no banco fica
    sempre em uma única thread, então não há concorrência na conexão
  - Commits em lotes de BATCH_SIZE para não perder progresso em caso de falha;
    se um lote falhar, cai para escrita linha-a-linha pra isolar o registro
    problemático em vez de perder o lote inteiro
  - Rate limit respeitado por worker via SLEEP_BETWEEN_REQUESTS
  - Retry automático já tratado dentro de camara_get()

Uso:
    # Apenas quem está incompleto (padrão)
    python backfill_deputados_detalhes.py

    # Força atualização de todos (útil após uma legislatura nova)
    python backfill_deputados_detalhes.py --force

    # Testa em um subconjunto pequeno antes de rodar tudo
    python backfill_deputados_detalhes.py --limit 20

    # Ajusta o número de threads buscando na API em paralelo
    python backfill_deputados_detalhes.py --workers 8
"""
import argparse
import logging
import re
import time
import unicodedata
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date

# SQLAlchemy Core (Substituindo o ORM)
from sqlalchemy import MetaData, select, update

# Reaproveita a MESMA engine/config usada pelo resto da aplicação, em vez de
# recriar uma a partir de uma DATABASE_URL própria — evita o script apontar
# silenciosamente para um banco diferente do resto do sistema.
from shared.database import sync_engine
# Mantém a importação da sua API
from injest_banco.api_camara import camara_get

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# Configuração
# ─────────────────────────────────────────────────────────────────────────────
BATCH_SIZE = 50
SLEEP_BETWEEN_REQUESTS = 0.25
DEFAULT_WORKERS = 8
LOG_PROGRESS_EVERY = 50

# Campos que o script preenche a partir do endpoint de detalhe. Usados tanto
# para montar o UPDATE quanto para decidir quem está "incompleto" — mantendo
# as duas coisas na mesma lista evita que elas se desalinhem com o tempo.
CAMPOS_DETALHE = [
    "nomeCivil", "dataNascimento", "escolaridade", "situacao",
    "condicaoEleitoral", "urlFoto", "emailGabinete", "telefoneGabinete",
    "cpf", "slug",
]


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────
def _parse_date(valor: str | None) -> date | None:
    if not valor:
        return None
    try:
        return date.fromisoformat(valor[:10])
    except ValueError:
        logger.debug("Data inválida ignorada: %s", valor)
        return None


def generate_slug(text: str | None) -> str | None:
    if not text:
        return None
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("utf-8").lower()
    text = re.sub(r"[^a-z0-9]+", "-", text).strip("-")
    return text


def _is_incompleto(dep_row: dict) -> bool:
    """Verifica um dicionário de linha do banco, em vez de um objeto ORM."""
    return any(not dep_row.get(campo) for campo in CAMPOS_DETALHE)


class SlugDeduper:
    """Garante slugs únicos dentro de uma run, mesmo com deputados homônimos."""

    def __init__(self):
        self._vistos: set[str] = set()

    def gerar(self, nome_civil: str | None, dep_id) -> str | None:
        base = generate_slug(nome_civil)
        if base is None:
            return None
        slug = base
        if slug in self._vistos:
            slug = f"{base}-{dep_id}"
        self._vistos.add(slug)
        return slug


def _buscar_detalhe(dep: dict) -> tuple[dict, dict | None, Exception | None]:
    """Roda em thread de worker: só faz I/O de rede, nunca toca no banco."""
    dep_id = dep.get("idCamara") or dep.get("id")
    try:
        resposta = camara_get(f"/deputados/{dep_id}")
        return dep, resposta, None
    except Exception as e:  # noqa: BLE001 - queremos capturar e reportar, não abortar a run
        return dep, None, e
    finally:
        time.sleep(SLEEP_BETWEEN_REQUESTS)


def _montar_update(dep: dict, resposta_api: dict, slugger: SlugDeduper) -> dict:
    dados = resposta_api["dados"]
    status = dados.get("ultimoStatus") or {}
    gabinete = status.get("gabinete") or {}

    return {
        "id": dep["id"],  # PK — necessária para o SQLAlchemy montar o WHERE do executemany
        "nomeCivil": dados.get("nomeCivil"),
        "dataNascimento": _parse_date(dados.get("dataNascimento")),
        "siglaSexo": dados.get("sexo"),
        "escolaridade": dados.get("escolaridade"),
        "situacao": status.get("situacao"),
        "condicaoEleitoral": status.get("condicaoEleitoral"),
        "siglaUF": status.get("siglaUf"),
        "siglaPartido": status.get("siglaPartido"),
        "urlFoto": status.get("urlFoto"),
        "emailGabinete": gabinete.get("email"),
        "telefoneGabinete": gabinete.get("telefone"),
        "cpf": dados.get("cpf"),
        "slug": slugger.gerar(dados.get("nomeCivil"), dep["id"]),
    }


def _flush_batch(conn, tabela, batch: list[dict]) -> int:
    """Tenta o UPDATE em lote; se falhar, isola o problema linha-a-linha em
    vez de perder o lote inteiro."""
    if not batch:
        return 0
    try:
        conn.execute(update(tabela), batch)
        conn.commit()
        return len(batch)
    except Exception as e:
        logger.warning(f"Lote de {len(batch)} falhou ({e}); tentando linha-a-linha...")
        conn.rollback()
        ok = 0
        for row in batch:
            try:
                conn.execute(update(tabela), [row])
                conn.commit()
                ok += 1
            except Exception as e_row:
                conn.rollback()
                logger.error(f"Falha isolada no deputado id={row['id']}: {e_row}")
        return ok


# ─────────────────────────────────────────────────────────────────────────────
# Entrypoint e Core Logic
# ─────────────────────────────────────────────────────────────────────────────
def run_backfill(force: bool, limit: int | None, workers: int):
    metadata = MetaData()
    metadata.reflect(bind=sync_engine, only=["deputados"])
    tabela_deputados = metadata.tables["deputados"]

    processados = 0
    atualizados = 0
    erros = 0
    sem_dados = 0
    slugger = SlugDeduper()

    with sync_engine.connect() as conn:
        resultados = conn.execute(select(tabela_deputados)).mappings().all()
        alvo = [dep for dep in resultados if force or _is_incompleto(dep)]
        if limit:
            alvo = alvo[:limit]

        logger.info("═" * 60)
        logger.info(f"Iniciando Backfill: {len(alvo)} deputados na fila "
                     f"({workers} workers em paralelo).")

        batch_updates: list[dict] = []

        with ThreadPoolExecutor(max_workers=workers) as pool:
            futures = [pool.submit(_buscar_detalhe, dep) for dep in alvo]

            for future in as_completed(futures):
                dep, resposta_api, erro = future.result()
                processados += 1

                if erro is not None:
                    logger.error(f"Erro ao buscar deputado id={dep.get('id')}: {erro}")
                    erros += 1
                elif not resposta_api or "dados" not in resposta_api:
                    sem_dados += 1
                else:
                    try:
                        batch_updates.append(_montar_update(dep, resposta_api, slugger))
                    except Exception as e:
                        logger.error(f"Erro ao montar update pro deputado id={dep.get('id')}: {e}")
                        erros += 1

                if len(batch_updates) >= BATCH_SIZE:
                    atualizados += _flush_batch(conn, tabela_deputados, batch_updates)
                    batch_updates = []

                if processados % LOG_PROGRESS_EVERY == 0:
                    logger.info(f"Progresso: {processados}/{len(alvo)} processados, "
                                f"{atualizados} atualizados, {erros} erros")

        atualizados += _flush_batch(conn, tabela_deputados, batch_updates)

    logger.info("═" * 60)
    logger.info("🏁 Backfill concluído")
    logger.info("   Deputados no alvo  : %d", len(alvo))
    logger.info("   Processados        : %d", processados)
    logger.info("   Atualizados        : %d", atualizados)
    logger.info("   Sem dados na API   : %d", sem_dados)
    logger.info("   Erros              : %d", erros)
    logger.info("═" * 60)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Backfill dos campos de detalhe.")
    parser.add_argument("--force", action="store_true", default=False, help="Atualiza todos.")
    parser.add_argument("--limit", type=int, default=None,
                         help="Processa só os N primeiros do alvo (útil pra testar).")
    parser.add_argument("--workers", type=int, default=DEFAULT_WORKERS,
                         help="Número de threads buscando na API em paralelo.")
    args = parser.parse_args()

    run_backfill(force=args.force, limit=args.limit, workers=args.workers)
