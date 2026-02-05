import requests
import time
import logging
import argparse

from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert

from backend.database import SessionLocal
from backend.models import Politico, Despesa

API_BASE = "https://dadosabertos.camara.leg.br/api/v2"
HEADERS = {"accept": "application/json"}

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def buscar_despesas_deputado(
    id_camara: int,
    ano: int,
    pagina: int = 1,
    itens: int = 100,
    tentativas: int = 3,
):
    for tentativa in range(tentativas):
        try:
            response = requests.get(
                f"{API_BASE}/deputados/{id_camara}/despesas",
                params={
                    "ano": ano,
                    "pagina": pagina,
                    "itens": itens,
                    "ordem": "ASC",
                    "ordenarPor": "mes",
                },
                headers=HEADERS,
                timeout=30,
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            if tentativa == tentativas - 1:
                raise e
            time.sleep(2 ** tentativa)

def ingestao_despesas_politico(dep: Politico, anos: list[int]):
    db: Session = SessionLocal()

    try:
        for ano in anos:
            pagina = 1

            while True:
                logger.info(
                    "Deputado %s | Ano %s | Página %s",
                    dep.id_camara,
                    ano,
                    pagina,
                )

                payload = buscar_despesas_deputado(
                    dep.id_camara,
                    ano,
                    pagina,
                )

                dados = payload.get("dados", [])
                if not dados:
                    break

                lista_despesas: list[dict] = []

                for d in dados:
                    lista_despesas.append(
                        {
                            "politico_id": dep.id,
                            "cod_documento": d["codDocumento"],
                            "cod_lote": d["codLote"],
                            "ano": d["ano"],
                            "mes": d["mes"],
                            "data_documento": d.get("dataDocumento"),
                            "tipo_despesa": d.get("tipoDespesa"),
                            "tipo_documento": d.get("tipoDocumento"),
                            "cod_tipo_documento": d.get("codTipoDocumento"),
                            "num_documento": d.get("numDocumento"),
                            "url_documento": d.get("urlDocumento"),
                            "nome_fornecedor": d.get("nomeFornecedor"),
                            "cnpj_cpf_fornecedor": d.get("cnpjCpfFornecedor"),
                            "valor_documento": d.get("valorDocumento"),
                            "valor_liquido": d.get("valorLiquido"),
                            "valor_glosa": d.get("valorGlosa"),
                            "num_ressarcimento": d.get("numRessarcimento"),
                            "parcela": d.get("parcela"),
                        }
                    )

                if lista_despesas:
                    stmt = insert(Despesa).values(lista_despesas)
                    stmt = stmt.on_conflict_do_nothing(
                        index_elements=["politico_id", "cod_documento"]
                    )
                    db.execute(stmt)
                    db.commit()

                links = payload.get("links", [])
                if not any(l["rel"] == "next" for l in links):
                    break

                pagina += 1
                time.sleep(0.2)

        logger.info("✅ Despesas ingeridas para %s", dep.nome)

    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

def runner_ingestao_despesas(anos: list[int], limite: int | None = None):
    db: Session = SessionLocal()

    try:
        query = db.query(Politico)

        if limite:
            query = query.limit(limite)

        politicos = query.all()

        logger.info(
            "🚀 Iniciando ingestão de despesas para %s políticos",
            len(politicos),
        )

        for politico in politicos:
            ingestao_despesas_politico(politico, anos)
            time.sleep(0.5)  # respeita rate limit da API

    finally:
        db.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Ingestão de despesas parlamentares"
    )

    parser.add_argument(
        "--anos",
        nargs="+",
        type=int,
        required=True,
        help="Ano(s) das despesas. Ex: --anos 2023 2024",
    )

    parser.add_argument(
        "--limite",
        type=int,
        help="Limite de políticos processados (debug/teste)",
    )

    args = parser.parse_args()

    runner_ingestao_despesas(
        anos=args.anos,
        limite=args.limite,
    )
