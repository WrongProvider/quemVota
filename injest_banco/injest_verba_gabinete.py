"""
injest_banco/injest_verba_gabinete.py — Coleta e ingestão de Verba de Gabinete dos Deputados

Extrai mensalmente os valores disponíveis e gastos de verba de gabinete diretamente
do portal oficial da Câmara dos Deputados (Recursos Humanos / Mandatos):
https://www.camara.leg.br/deputados/{idCamara}/verba-gabinete?ano={ano}

Persiste idempotentemente na tabela 'verbasGabinete' via SQLAlchemy Core upsert.
"""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from decimal import Decimal
import logging
import re
from typing import Any, Optional

from bs4 import BeautifulSoup
from pydantic import BaseModel, Field, field_validator
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from sqlalchemy import create_engine, select
from sqlalchemy.dialects.postgresql import insert

from shared.database import SYNC_URL
from shared.models import Deputado, VerbaGabinete

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger("injest_verba_gabinete")

DEFAULT_WORKERS = 8
BASE_URL = "https://www.camara.leg.br/deputados/{id_camara}/verba-gabinete"
DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)


# ── Schemas de Validação Pydantic V2 ──────────────────────────────────────────


class VerbaGabineteItem(BaseModel):
    """Schema Pydantic V2 para validação e sanitização de uma linha de verba de gabinete."""

    idDeputado: int = Field(gt=0, description="PK interna da tabela deputados")
    idCamara: int = Field(gt=0, description="ID oficial do deputado na Câmara")
    ano: int = Field(ge=2015, le=2030, description="Ano de competência")
    mes: int = Field(ge=1, le=12, description="Mês de competência (1 a 12)")
    valorDisponivel: Decimal = Field(
        ge=0, description="Valor total disponibilizado no mês"
    )
    valorGasto: Decimal = Field(
        ge=0, description="Valor efetivamente liquidado/gasto no mês"
    )

    @field_validator("valorDisponivel", "valorGasto", mode="before")
    @classmethod
    def parse_currency(cls, v: Any) -> Decimal:
        if isinstance(v, (Decimal, int, float)):
            return Decimal(str(v))
        if isinstance(v, str):
            clean = (
                v.replace("R$", "")
                .replace(" ", "")
                .replace(".", "")
                .replace(",", ".")
                .strip()
            )
            if not clean or clean == "-":
                return Decimal("0.00")
            try:
                return Decimal(clean)
            except Exception:
                return Decimal("0.00")
        return Decimal("0.00")


# ── Cliente HTTP Resiliente ───────────────────────────────────────────────────


def build_http_session(pool_maxsize: int = 16) -> requests.Session:
    """Cria uma sessão HTTP com pool de conexões e retries exponenciais."""
    session = requests.Session()
    retries = Retry(
        total=4,
        backoff_factor=0.8,
        status_forcelist=[429, 500, 502, 503, 504],
        raise_on_status=False,
    )
    adapter = HTTPAdapter(
        max_retries=retries,
        pool_connections=pool_maxsize,
        pool_maxsize=pool_maxsize,
    )
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    session.headers.update(
        {
            "User-Agent": DEFAULT_USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
            "Referer": "https://www.camara.leg.br/",
        }
    )
    return session


# ── Parser HTML de Verba de Gabinete ──────────────────────────────────────────


def parse_verba_table(
    html: str,
    id_deputado: int,
    id_camara: int,
    ano: int,
) -> list[VerbaGabineteItem]:
    """
    Analisa o HTML retornado pela Câmara e extrai os registros mensais de verba de gabinete.
    """
    soup = BeautifulSoup(html, "html.parser")
    table = soup.find("table", class_=re.compile(r"table"))
    if not table:
        return []

    items: list[VerbaGabineteItem] = []
    tbody = table.find("tbody")
    rows = tbody.find_all("tr") if tbody else table.find_all("tr")[1:]

    for row in rows:
        cells = [td.get_text(strip=True) for td in row.find_all(["td", "th"])]
        if len(cells) < 3:
            continue

        mes_str = cells[0]
        mes_match = re.search(r"(\d{1,2})", mes_str)
        if not mes_match:
            continue

        try:
            mes_num = int(mes_match.group(1))
            if not (1 <= mes_num <= 12):
                continue

            item = VerbaGabineteItem(
                idDeputado=id_deputado,
                idCamara=id_camara,
                ano=ano,
                mes=mes_num,
                valorDisponivel=cells[1],
                valorGasto=cells[2],
            )
            items.append(item)
        except Exception as exc:
            log.debug(
                "Linha ignorada para deputado %d (%s): %s", id_camara, mes_str, exc
            )
            continue

    return items


def fetch_deputado_verba(
    session: requests.Session,
    deputado: dict[str, Any],
    ano: int,
) -> list[VerbaGabineteItem]:
    """
    Realiza requisição HTTP para a página de verba de gabinete de um deputado.
    """
    id_camara = deputado["idCamara"]
    id_dep = deputado["id"]
    url = f"{BASE_URL.format(id_camara=id_camara)}?ano={ano}"

    try:
        resp = session.get(url, timeout=15)
        if resp.status_code == 404:
            return []
        if resp.status_code != 200:
            log.warning(
                "HTTP %d ao consultar verba deputado %d ano %d",
                resp.status_code,
                id_camara,
                ano,
            )
            return []

        return parse_verba_table(
            resp.text, id_deputado=id_dep, id_camara=id_camara, ano=ano
        )
    except Exception as exc:
        log.error("Erro ao buscar verba do deputado %d ano %d: %s", id_camara, ano, exc)
        return []


# ── Carga no Banco (Upsert Idempotente) ────────────────────────────────────────


def upsert_verbas(engine, items: list[VerbaGabineteItem]) -> int:
    """
    Realiza upsert idempotente dos itens validados de verba de gabinete em lote.
    """
    if not items:
        return 0

    records = [
        {
            "idDeputado": item.idDeputado,
            "idCamara": item.idCamara,
            "ano": item.ano,
            "mes": item.mes,
            "valorDisponivel": item.valorDisponivel,
            "valorGasto": item.valorGasto,
        }
        for item in items
    ]

    CHUNK_SIZE = 500
    total_saved = 0

    with engine.begin() as conn:
        for i in range(0, len(records), CHUNK_SIZE):
            chunk = records[i : i + CHUNK_SIZE]
            stmt = insert(VerbaGabinete).values(chunk)
            stmt = stmt.on_conflict_do_update(
                index_elements=["idDeputado", "ano", "mes"],
                set_={
                    "valorDisponivel": stmt.excluded.valorDisponivel,
                    "valorGasto": stmt.excluded.valorGasto,
                    "idCamara": stmt.excluded.idCamara,
                },
            )
            conn.execute(stmt)
            total_saved += len(chunk)

    return total_saved


# ── Execução Principal ────────────────────────────────────────────────────────


def get_target_deputados(engine, legislatura_min: int = 56) -> list[dict[str, Any]]:
    """
    Retorna deputados aptos a ter verba de gabinete (legislatura 56 em diante: 2019+).
    """
    with engine.connect() as conn:
        stmt = (
            select(Deputado.id, Deputado.idCamara, Deputado.nome)
            .where(
                Deputado.idCamara.isnot(None),
                (
                    (Deputado.idLegislaturaFinal >= legislatura_min)
                    | (Deputado.idLegislaturaInicial >= legislatura_min)
                    | (Deputado.idLegislaturaFinal.is_(None))
                ),
            )
            .order_by(Deputado.idCamara)
        )
        rows = conn.execute(stmt).fetchall()
        return [{"id": r[0], "idCamara": r[1], "nome": r[2]} for r in rows]


def run_verba_gabinete(
    anos: list[int],
    *,
    engine=None,
    workers: int = DEFAULT_WORKERS,
    deputado_id_camara: Optional[int] = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    """
    Executa o pipeline de ingestão de verbas de gabinete para a lista de anos informada.
    """
    if engine is None:
        engine = create_engine(SYNC_URL, pool_pre_ping=True)

    session = build_http_session(pool_maxsize=max(workers * 2, 16))

    if deputado_id_camara:
        with engine.connect() as conn:
            stmt = select(Deputado.id, Deputado.idCamara, Deputado.nome).where(
                Deputado.idCamara == deputado_id_camara
            )
            row = conn.execute(stmt).fetchone()
            if not row:
                log.error(
                    "Deputado com idCamara=%d não encontrado no banco",
                    deputado_id_camara,
                )
                return {"status": "error", "items": 0}
            deputados = [{"id": row[0], "idCamara": row[1], "nome": row[2]}]
    else:
        deputados = get_target_deputados(engine, legislatura_min=56)

    log.info(
        "Iniciando Verba de Gabinete: %d deputados selecionados | anos=%s | workers=%d | dry_run=%s",
        len(deputados),
        anos,
        workers,
        dry_run,
    )

    total_records = 0

    for ano in anos:
        log.info("Coletando Verba de Gabinete para o ano %d...", ano)
        items_ano: list[VerbaGabineteItem] = []

        with ThreadPoolExecutor(max_workers=workers) as pool:
            futures = {
                pool.submit(fetch_deputado_verba, session, dep, ano): dep
                for dep in deputados
            }

            for future in as_completed(futures):
                dep = futures[future]
                try:
                    dep_items = future.result()
                    if dep_items:
                        items_ano.extend(dep_items)
                except Exception as exc:
                    log.error(
                        "Falha ao coletar dados para %s (%d): %s",
                        dep["nome"],
                        dep["idCamara"],
                        exc,
                    )

        log.info("Ano %d: %d registros de verba coletados", ano, len(items_ano))

        if not dry_run and items_ano:
            saved = upsert_verbas(engine, items_ano)
            log.info("Ano %d: %d registros gravados com sucesso no banco", ano, saved)
            total_records += saved
        else:
            total_records += len(items_ano)

    log.info(
        "🏁 Pipeline de Verba de Gabinete concluído — total registros: %d",
        total_records,
    )
    return {"status": "ok", "total_records": total_records}


def main():
    parser = argparse.ArgumentParser(
        description="ETL de Verba de Gabinete da Câmara dos Deputados"
    )
    parser.add_argument(
        "--anos",
        type=int,
        nargs="+",
        default=[datetime.now().year],
        help="Anos a serem processados (padrão: ano atual)",
    )
    parser.add_argument(
        "--deputado",
        type=int,
        default=None,
        help="Filtrar por idCamara de um único deputado para teste rápido",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=DEFAULT_WORKERS,
        help=f"Quantidade de threads concorrentes (padrão: {DEFAULT_WORKERS})",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Apenas faz scraping e validação sem persistir no banco",
    )

    args = parser.parse_args()
    engine = create_engine(SYNC_URL, pool_pre_ping=True)

    run_verba_gabinete(
        anos=args.anos,
        engine=engine,
        workers=args.workers,
        deputado_id_camara=args.deputado,
        dry_run=args.dry_run,
    )


if __name__ == "__main__":
    main()
