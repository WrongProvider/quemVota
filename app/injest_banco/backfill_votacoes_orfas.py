import logging
import time
from backend.database import SessionLocal
from backend.models import Votacao, Proposicao
from api_camara import camara_get
from db_upsert import upsert_proposicao

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

def rodar_backfill():
    db = SessionLocal()
    
    # Procura todas as votações que ainda não têm uma proposição associada
    votações_orfas = db.query(Votacao).filter(Votacao.proposicao_id.is_(None)).all()
    total = len(votações_orfas)
    
    logger.info(f"🚀 Iniciando Backfill: Foram encontradas {total} votações sem proposição.")
    
    processadas = 0
    vinculadas = 0
    sem_proposicao_na_origem = 0

    for votacao in votações_orfas:
        processadas += 1
        id_votacao = votacao.id_camara
        
        try:
            # 1. Busca os detalhes da votação na API
            detalhes = camara_get(f"/votacoes/{id_votacao}").get("dados", {})
            uri_prop = detalhes.get("uriProposicaoObjeto")
            
            if uri_prop:
                # 2. Extrai o ID da Proposição
                id_prop_camara = int(uri_prop.split("/")[-1])
                
                # 3. Verifica se a proposição já existe no nosso banco
                prop_existe = db.query(Proposicao).filter_by(id_camara=id_prop_camara).first()
                
                if not prop_existe:
                    logger.info(f"[{processadas}/{total}] ⚡ Proposição {id_prop_camara} em falta. A descarregar...")
                    prop_payload = camara_get(f"/proposicoes/{id_prop_camara}").get("dados", {})
                    
                    if prop_payload:
                        prop_existe = upsert_proposicao(db, prop_payload)
                        db.flush()
                
                # 4. Faz o vínculo
                if prop_existe:
                    votacao.proposicao_id = prop_existe.id
                    db.commit()
                    vinculadas += 1
                    logger.info(f"[{processadas}/{total}] 🔗 Votação {id_votacao} associada com sucesso à Proposição {id_prop_camara}.")
            else:
                # É uma votação administrativa (Mesa Diretora, quebra de sessão, etc)
                sem_proposicao_na_origem += 1
                logger.debug(f"[{processadas}/{total}] ℹ️ Votação {id_votacao} é administrativa (sem proposição).")
                
            # Pequena pausa para evitar bloqueios da API (Rate Limit)
            time.sleep(0.3)
            
        except Exception as e:
            db.rollback()
            logger.error(f"[{processadas}/{total}] ❌ Erro na votação {id_votacao}: {e}")
            continue

    db.close()
    
    logger.info("🏁 Backfill Concluído!")
    logger.info(f"📊 Resumo: {vinculadas} vinculadas | {sem_proposicao_na_origem} eram administrativas.")

if __name__ == "__main__":
    rodar_backfill()