import argparse
import logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

from sqlalchemy import text

from shared.database import SessionLocal
from injest_banco.api_camara import camara_get

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

SLEEP_BETWEEN_REQUESTS = 0.3
DEFAULT_WORKERS = 8
LOG_PROGRESS_EVERY = 25

QUERY_MISSING = text("""
    SELECT DISTINCT split_part(v."idCamara", '-', 1) as id_camara_faltante
    FROM public.votacoes v
    WHERE v."idProposicao" IS NULL
      AND split_part(v."idCamara", '-', 1) ~ '^[0-9]+$' -- Garante que extraímos apenas números válidos
      AND NOT EXISTS (
          SELECT 1 FROM public.proposicoes p
          WHERE p."idCamara" = CAST(split_part(v."idCamara", '-', 1) AS INTEGER)
      );
""")

INSERT_PROPOSICAO = text("""
    INSERT INTO public.proposicoes ("idCamara", uri, "siglaTipo", numero, ano, ementa)
    VALUES (:idCamara, :uri, :sigla, :num, :ano, :ementa)
    ON CONFLICT ("idCamara") DO NOTHING;
""")

UPDATE_VINCULO = text("""
    UPDATE public.votacoes v
    SET "idProposicao" = p.id
    FROM public.proposicoes p
    WHERE p."idCamara" = CAST(split_part(v."idCamara", '-', 1) AS INTEGER)
      AND v."idProposicao" IS NULL;
""")

# Campos sem os quais não faz sentido inserir a proposição.
CAMPOS_ESSENCIAIS = ("id", "uri", "siglaTipo", "numero", "ano")


def _buscar_proposicao(camara_id: str):
    """Roda em thread de worker: só faz I/O de rede, nunca toca na sessão do banco."""
    try:
        resposta = camara_get(f"/proposicoes/{camara_id}")
        dados = (resposta or {}).get("dados")
        return camara_id, dados, None
    except Exception as e:  # noqa: BLE001 - queremos reportar, não abortar a run
        return camara_id, None, e
    finally:
        time.sleep(SLEEP_BETWEEN_REQUESTS)


def backfill_proposicoes(limit: int | None = None, workers: int = DEFAULT_WORKERS):
    with SessionLocal() as session:
        logger.info("🔍 Identificando IDs de proposições faltantes...")
        missing_ids = [row[0] for row in session.execute(QUERY_MISSING) if row[0]]
        if limit:
            missing_ids = missing_ids[:limit]

        if not missing_ids:
            logger.info("✅ Nenhuma proposição faltante encontrada.")
        else:
            total = len(missing_ids)
            logger.info(f"📦 Encontrados {total} IDs da Câmara. Iniciando coleta na API ({workers} workers)...")

            processadas = 0
            inseridas = 0
            nao_encontradas = 0
            erros = 0

            # Busca na API (I/O puro) roda em paralelo; toda escrita na sessão
            # do SQLAlchemy fica na thread principal, uma de cada vez.
            with ThreadPoolExecutor(max_workers=workers) as pool:
                futures = [pool.submit(_buscar_proposicao, cid) for cid in missing_ids]

                for future in as_completed(futures):
                    camara_id, dados, erro = future.result()
                    processadas += 1

                    try:
                        if erro is not None:
                            raise erro

                        if not dados:
                            nao_encontradas += 1
                            logger.warning(f"[{processadas}/{total}] ⚠️ Proposição idCamara={camara_id} não encontrada na API.")
                            continue

                        if any(dados.get(campo) is None for campo in CAMPOS_ESSENCIAIS):
                            erros += 1
                            logger.warning(f"[{processadas}/{total}] ⚠️ Proposição idCamara={camara_id} veio com campos essenciais "
                                           f"faltando na API, pulando.")
                            continue

                        session.execute(INSERT_PROPOSICAO, {
                            "idCamara": int(dados["id"]),  # O id da API é o nosso idCamara
                            "uri": dados["uri"],
                            "sigla": dados["siglaTipo"],
                            "num": dados["numero"],
                            "ano": dados["ano"],
                            "ementa": dados.get("ementa"),
                        })
                        session.commit()
                        inseridas += 1
                        logger.info(f"[{processadas}/{total}] ✔️ Proposição idCamara={camara_id} processada.")

                    except Exception as e:
                        session.rollback()
                        erros += 1
                        logger.error(f"[{processadas}/{total}] ❌ Erro ao processar idCamara={camara_id}: {e}")

                    if processadas % LOG_PROGRESS_EVERY == 0:
                        logger.info(f"Progresso: {processadas}/{total} | {inseridas} inseridas | {erros} erros")

            logger.info(f"📊 Coleta concluída: {inseridas} inseridas | {nao_encontradas} não encontradas na API | {erros} erros")

        # =====================================================================
        # A MÁGICA DO VÍNCULO ACONTECE AQUI
        # =====================================================================
        # 1. JOIN entre a string extraída da votação e a coluna idCamara da proposição.
        # 2. Pega o p.id (ID local gerado pelo banco) e injeta em v."idProposicao".
        logger.info("⚙️ Vinculando votações às proposições usando o ID local...")
        try:
            result = session.execute(UPDATE_VINCULO)
            session.commit()
            logger.info(f"✅ Sucesso! {result.rowcount} votações foram vinculadas corretamente com os IDs locais.")
        except Exception as e:
            session.rollback()
            logger.error(f"❌ Erro ao atualizar votações: {e}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Backfill de proposições faltantes e vínculo com votações.")
    parser.add_argument("--limit", type=int, default=None,
                         help="Processa só os N primeiros IDs faltantes (útil pra testar).")
    parser.add_argument("--workers", type=int, default=DEFAULT_WORKERS,
                         help="Número de threads buscando proposições na API em paralelo.")
    args = parser.parse_args()

    backfill_proposicoes(limit=args.limit, workers=args.workers)
