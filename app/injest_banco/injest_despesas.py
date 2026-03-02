import logging
from injest_banco.db.database import SessionLocal
from injest_banco.db.models import Politico
from api_camara import camara_paginado
from db_upsert import upsert_despesa

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def injest_despesas(anos=[2025, 2026]):
    db = SessionLocal()
    politicos = db.query(Politico).all()
    
    for p in politicos:
        try:
            # Conjunto para rastrear o que já foi adicionado NESTA sessão
            docs_na_sessao = set() 
            
            for ano in anos:
                endpoint = f"/deputados/{p.id_camara}/despesas"
                params = {"ano": ano, "ordem": "desc", "ordenarPor": "mes"}

                count = 0
                for d_em_dados in camara_paginado(endpoint, params=params):
                    cod_doc = str(d_em_dados.get("codDocumento", "")).strip()
                    
                    # Se já processamos esse documento agora ou se ele é inválido, pula
                    if not cod_doc or cod_doc in ["0", "None", ""] or cod_doc in docs_na_sessao:
                        continue
                    
                    # Tenta o upsert
                    foi_adicionado = upsert_despesa(db, p.id, d_em_dados, cod_doc)
                    
                    if foi_adicionado:
                        docs_na_sessao.add(cod_doc)
                        count += 1
                
                db.commit() 
                if count > 0:
                    logger.info(f"✅ {count} despesas para {p.nome} em {ano}")

        except Exception as e:
            db.rollback()
            logger.error(f"❌ Erro ao processar {p.nome}: {e}")
            continue 
    db.close()