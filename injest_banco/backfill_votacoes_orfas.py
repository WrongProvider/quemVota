import argparse
import logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

from shared.database import SessionLocal
from shared.models import Votacao, Proposicao
from injest_banco.api_camara import camara_get

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

SLEEP_BETWEEN_REQUESTS = 0.3
DEFAULT_WORKERS = 8
LOG_PROGRESS_EVERY = 25


def upsert_proposicao(db: SessionLocal, d: dict) -> Proposicao:
    """Realiza o upsert da proposição básica."""
    id_camara = d.get("id")
    prop = db.query(Proposicao).filter_by(id_camara=id_camara).first()

    if not prop:
        prop = Proposicao(id_camara=id_camara)
        db.add(prop)

    prop.uri = d.get("uri")
    prop.sigla_tipo = d.get("siglaTipo")
    prop.cod_tipo = d.get("codTipo")
    prop.numero = d.get("numero")
    prop.ano = d.get("ano")
    prop.descricao_tipo = d.get("descricaoTipo")
    prop.ementa = d.get("ementa")
    prop.data_apresentacao = parse_datetime(d.get("dataApresentacao"))
    prop.url_inteiro_teor = d.get("urlInteiroTeor")

    # Campos que geralmente vêm do /proposicoes/{id} (detalhes)
    if "ementaDetalhada" in d:
        prop.ementa_detalhada = d.get("ementaDetalhada")
    if "keywords" in d:
        prop.keywords = d.get("keywords")
    if "justificativa" in d:
        prop.justificativa = d.get("justificativa")

    return prop
def _buscar_uri_proposicao(votacao):
    """Roda em thread de worker: só faz I/O de rede (lê um atributo já
    carregado do objeto ORM, nunca toca na sessão do banco)."""
    id_votacao = votacao.id_camara
    try:
        detalhes = camara_get(f"/votacoes/{id_votacao}").get("dados", {})
        return votacao, detalhes.get("uriProposicaoObjeto"), None
    except Exception as e:  # noqa: BLE001 - queremos reportar, não abortar a run
        return votacao, None, e
    finally:
        time.sleep(SLEEP_BETWEEN_REQUESTS)


def _extrair_id_prop(uri_prop):
    try:
        return int(uri_prop.split("/")[-1])
    except (ValueError, AttributeError):
        return None


def rodar_backfill_votacoes(limit: int | None = None, workers: int = DEFAULT_WORKERS):
    with SessionLocal() as db:
        votacoes_orfas = db.query(Votacao).filter(Votacao.proposicao_id.is_(None)).all()
        if limit:
            votacoes_orfas = votacoes_orfas[:limit]
        total = len(votacoes_orfas)

        logger.info(f"🚀 Iniciando Backfill: {total} votações sem proposição ({workers} workers).")

        processadas = 0
        vinculadas = 0
        sem_proposicao_na_origem = 0
        erros = 0

        # Cache local: várias votações órfãs costumam apontar pra mesma
        # proposição (ex.: destaques da mesma matéria). Sem isso, cada uma
        # dispara sua própria consulta/download da mesma proposição de novo.
        cache_proposicoes: dict[int, Proposicao] = {}

        # Busca dos detalhes de votação (só leitura na API) roda em paralelo;
        # toda escrita na sessão do SQLAlchemy fica na thread principal, uma
        # de cada vez, porque Session não é thread-safe.
        with ThreadPoolExecutor(max_workers=workers) as pool:
            futures = [pool.submit(_buscar_uri_proposicao, v) for v in votacoes_orfas]

            for future in as_completed(futures):
                votacao, uri_prop, erro_busca = future.result()
                processadas += 1
                id_votacao = votacao.id_camara

                try:
                    if erro_busca is not None:
                        raise erro_busca

                    if not uri_prop:
                        # Votação administrativa (Mesa Diretora, quebra de sessão, etc)
                        sem_proposicao_na_origem += 1
                        logger.debug(f"[{processadas}/{total}] ℹ️ Votação {id_votacao} é administrativa (sem proposição).")
                        continue

                    id_prop_camara = _extrair_id_prop(uri_prop)
                    if id_prop_camara is None:
                        logger.warning(f"[{processadas}/{total}] URI de proposição inesperada na votação {id_votacao}: {uri_prop}")
                        erros += 1
                        continue

                    prop = cache_proposicoes.get(id_prop_camara)
                    if prop is None:
                        prop = db.query(Proposicao).filter_by(id_camara=id_prop_camara).first()

                    if prop is None:
                        logger.info(f"[{processadas}/{total}] ⚡ Proposição {id_prop_camara} em falta. Baixando...")
                        prop_payload = camara_get(f"/proposicoes/{id_prop_camara}").get("dados", {})
                        if prop_payload:
                            prop = upsert_proposicao(db, prop_payload)
                            db.flush()

                    if prop is not None:
                        cache_proposicoes[id_prop_camara] = prop
                        votacao.proposicao_id = prop.id
                        db.commit()
                        vinculadas += 1
                        logger.info(f"[{processadas}/{total}] 🔗 Votação {id_votacao} associada com sucesso à Proposição {id_prop_camara}.")
                    else:
                        erros += 1
                        logger.warning(f"[{processadas}/{total}] Proposição {id_prop_camara} não retornou dados da API.")

                except Exception as e:
                    db.rollback()
                    erros += 1
                    logger.error(f"[{processadas}/{total}] ❌ Erro na votação {id_votacao}: {e}")

                if processadas % LOG_PROGRESS_EVERY == 0:
                    logger.info(f"Progresso: {processadas}/{total} | {vinculadas} vinculadas | {erros} erros")

    logger.info("🏁 Backfill Concluído!")
    logger.info(f"📊 Resumo: {vinculadas} vinculadas | {sem_proposicao_na_origem} eram administrativas | {erros} erros")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Backfill de votações órfãs (sem proposição vinculada).")
    parser.add_argument("--limit", type=int, default=None,
                         help="Processa só as N primeiras votações órfãs (útil pra testar).")
    parser.add_argument("--workers", type=int, default=DEFAULT_WORKERS,
                         help="Número de threads buscando detalhes de votação em paralelo.")
    args = parser.parse_args()

    rodar_backfill_votacoes(limit=args.limit, workers=args.workers)
