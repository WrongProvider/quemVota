import logging
from datetime import date, timedelta

from injest_banco.db.database import SessionLocal
from injest_banco.api_camara import (
    buscar_eventos,
    buscar_evento_detalhe,
    buscar_evento_deputados,
    buscar_evento_pauta,
    buscar_evento_votacoes,
)
from injest_banco.db_upsert import (
    carregar_eventos_indexados,
    upsert_evento_index,
    upsert_evento_detalhado,
    upsert_evento_deputados,
    upsert_evento_pauta,
    upsert_evento_votacoes,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# =========================
# FASE 1 — ÍNDICE DE EVENTOS
# =========================
def ingestar_eventos_index():
    db = SessionLocal()

    try:
        cache = carregar_eventos_indexados(db)
        logger.info("📦 Cache carregado com %s eventos", len(cache))

        fim = date.today()
        inicio = fim - timedelta(days=365 * 4)

        janela = timedelta(days=60)

        atual = inicio
        while atual < fim:
            data_inicio = atual.isoformat()
            data_fim = min(atual + janela, fim).isoformat()

            logger.info("🔎 Buscando eventos %s → %s", data_inicio, data_fim)

            pagina = 1
            while True:
                payload = buscar_eventos(
                    data_inicio=data_inicio,
                    data_fim=data_fim,
                    pagina=pagina,
                    itens=1000,
                )

                dados = payload.get("dados", [])
                if not dados:
                    break

                for evento in dados:
                    upsert_evento_index(db, cache, evento)

                db.commit()

                if not any(l["rel"] == "next" for l in payload.get("links", [])):
                    break

                pagina += 1

            atual += janela

        logger.info("✅ Índice de eventos concluído")

    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


# =========================
# FASE 2 — DETALHE DO EVENTO
# =========================
def ingestar_eventos_detalhados():
    db = SessionLocal()

    try:
        eventos = db.query(Evento).filter(Evento.detalhado.is_(False)).all()
        logger.info("📅 %s eventos para detalhar", len(eventos))

        for evento in eventos:
            logger.info("📅 Detalhando evento %s", evento.id_camara)

            detalhe = buscar_evento_detalhe(evento.id_camara)
            upsert_evento_detalhado(db, evento, detalhe)

            db.commit()

        logger.info("✅ Detalhamento concluído")

    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


# =========================
# FASE 3 — DEPUTADOS
# =========================
def ingestar_eventos_deputados():
    db = SessionLocal()

    try:
        eventos = db.query(Evento).filter(
            Evento.detalhado.is_(True),
            Evento.participantes_importados.is_(False),
        ).all()

        logger.info("👥 %s eventos sem deputados", len(eventos))

        for evento in eventos:
            deputados = buscar_evento_deputados(evento.id_camara)
            upsert_evento_deputados(db, evento, deputados)
            db.commit()

        logger.info("✅ Deputados importados")

    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


# =========================
# FASE 4 — PAUTA
# =========================
def ingestar_eventos_pauta():
    db = SessionLocal()

    try:
        eventos = db.query(Evento).filter(
            Evento.detalhado.is_(True),
            Evento.pauta_importada.is_(False),
        ).all()

        logger.info("📑 %s eventos sem pauta", len(eventos))

        for evento in eventos:
            pauta = buscar_evento_pauta(evento.id_camara)
            upsert_evento_pauta(db, evento, pauta)
            db.commit()

        logger.info("✅ Pautas importadas")

    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


# =========================
# FASE 5 — VOTAÇÕES
# =========================
def ingestar_eventos_votacoes():
    db = SessionLocal()

    try:
        eventos = db.query(Evento).filter(
            Evento.detalhado.is_(True),
            Evento.votacoes_importadas.is_(False),
        ).all()

        logger.info("🗳️ %s eventos sem votações", len(eventos))

        for evento in eventos:
            votacoes = buscar_evento_votacoes(evento.id_camara)
            upsert_evento_votacoes(db, evento, votacoes)
            db.commit()

        logger.info("✅ Votações importadas")

    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


# =========================
# MAIN
# =========================
if __name__ == "__main__":
    ingestar_eventos_index()
    ingestar_eventos_detalhados()
    ingestar_eventos_deputados()
    ingestar_eventos_pauta()
    ingestar_eventos_votacoes()



def ingestar_votacoes_eventos():
    db = SessionLocal()

    try:
        eventos = db.query(Evento).filter(Evento.detalhado.is_(True)).all()

        for evento in eventos:
            payload = buscar_evento_votacoes(evento.id_camara)

            for d in payload.get("dados", []):
                upsert_votacao_index(db, evento, d)

            db.commit()

    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
