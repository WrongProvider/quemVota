import logging
import argparse
from backend.database import SessionLocal
from backend.models import Partido, PartidoMembro, PartidoLider, Politico
# Importamos apenas o que realmente existe no seu api_camara.py
from api_camara import (
    camara_get, 
    camara_paginado
)
from db_upsert import carregar_por_id_camara, parse_datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def injest_partidos(limite: int | None = None):
    db = SessionLocal()
    try:
        # Cache de políticos para vincular membros e líderes sem fazer SELECT toda hora
        cache_politicos = carregar_por_id_camara(db)
        total = 0

        # O camara_paginado já lida com o loop de páginas da API
        for p_resumo in camara_paginado("/partidos"):
            logger.info(f"🏛️ Processando {p_resumo['sigla']}...")

            # 1. Busca detalhes do partido
            # Note que usamos camara_get direto no endpoint de detalhes
            res_detalhe = camara_get(f"/partidos/{p_resumo['id']}")
            detalhe = res_detalhe["dados"]
            
            partido = upsert_partido_db(detalhe, db)
            db.flush() # Gera o ID do banco para os relacionamentos abaixo

            # 2. Processa Membros (Histórico) usando o caminho do endpoint
            for m in camara_paginado(f"/partidos/{partido.id_camara}/membros"):
                politico = cache_politicos.get(m["id"])
                if politico:
                    vincular_membro(db, partido, politico)

            # 3. Processa Líderes
            for l in camara_paginado(f"/partidos/{partido.id_camara}/lideres"):
                politico = cache_politicos.get(l["id"])
                upsert_lider(db, partido, politico, l)

            db.commit()
            total += 1
            if limite and total >= limite: 
                break

        logger.info("✅ Ingestão de partidos finalizada")
    except Exception as e:
        db.rollback()
        logger.error(f"Erro na ingestão de partidos: {e}")
        raise
    finally:
        db.close()

def upsert_partido_db(dados, db):
    partido = db.query(Partido).filter_by(id_camara=dados["id"]).first()
    if not partido:
        partido = Partido(id_camara=dados["id"])
        db.add(partido)
    
    partido.nome = dados.get("nome")
    partido.sigla = dados.get("sigla")
    partido.numero_eleitoral = dados.get("numeroEleitoral")
    partido.uri = dados.get("uri")
    
    status = dados.get("status", {})
    partido.situacao = status.get("situacao")
    partido.total_membros = status.get("totalMembros")
    partido.total_posse = status.get("totalPosse")
    
    partido.url_logo = dados.get("urlLogo")
    partido.url_website = dados.get("urlWebSite")
    
    return partido

def vincular_membro(db, partido, politico):
    existe = db.query(PartidoMembro).filter_by(
        partido_id=partido.id, 
        politico_id=politico.id
    ).first()
    
    if not existe:
        db.add(PartidoMembro(partido_id=partido.id, politico_id=politico.id))

def upsert_lider(db, partido, politico, d):
    # Líderes podem mudar, então validamos pelo título e datas
    existe = db.query(PartidoLider).filter_by(
        partido_id=partido.id,
        politico_id=politico.id if politico else None,
        cod_titulo=d.get("codTitulo")
    ).first()

    if not existe:
        lider = PartidoLider(
            partido_id=partido.id,
            politico_id=politico.id if politico else None,
            cod_titulo=d.get("codTitulo"),
            titulo=d.get("titulo"),
            data_inicio=parse_datetime(d.get("dataInicio")),
            data_fim=parse_datetime(d.get("dataFim"))
        )
        db.add(lider)

if __name__ == "__main__":
    injest_partidos()