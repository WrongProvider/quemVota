# backend/injest/injest_camara.py
import logging
from injest_banco.db.database import SessionLocal
# Use camara_paginado para garantir que pega todos os 513 deputados
from injest_banco.api_camara import camara_paginado 
from injest_banco.db_upsert import (
    carregar_por_id_camara,
    upsert_politico,
    carregar_partidos_por_sigla
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def injest_politicos():
    db = SessionLocal()
    try:
        # 1. Carregamos os caches
        cache_politicos = carregar_por_id_camara(db)
        cache_partidos = carregar_partidos_por_sigla(db) 
        
        logger.info(f"Caches carregados: {len(cache_politicos)} políticos, {len(cache_partidos)} partidos")

        contador = 0
        # 2. Mudança aqui: usando o endpoint direto no paginado
        for dep_api in camara_paginado("/deputados"):
            sigla_api = dep_api.get("siglaPartido")
            partido_obj = cache_partidos.get(sigla_api)
            
            # 3. O upsert_politico já cuida de verificar se existe ou cria novo
            upsert_politico(db, cache_politicos, dep_api, partido_obj)
            
            contador += 1
            if contador % 100 == 0:
                logger.info(f"Processando... {contador} deputados")

        db.commit()
        logger.info(f"✅ Ingestão finalizada: {contador} políticos processados.")

    except Exception as e:
        db.rollback()
        logger.error(f"❌ Erro na ingestão: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    injest_politicos()