from api_camara import camara_get, camara_paginado, buscar_votacao_votos, buscar_votacao_orientacoes

import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from injest_banco.db.database import SessionLocal
from injest_banco.db.models import Proposicao # Importamos o modelo para fazer a query do cache
from db_upsert import (
    upsert_proposicao, upsert_proposicao_autor, upsert_votacao_index,
    upsert_votacao_orientacoes, upsert_votacao_votos, carregar_por_id_camara
)

import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def injest_proposicoes(anos=[2025, 2026]):
    db = SessionLocal()
    cache_politicos = carregar_por_id_camara(db)
    
    # 🚀 O CACHE: Busca todos os IDs de proposições já salvos no banco
    # Fazemos uma query que traz apenas a coluna id_camara para economizar RAM
    logger.info("🔍 Montando cache de proposições já existentes...")
    existing_props = {p[0] for p in db.query(Proposicao.id_camara).all()}
    logger.info(f"📦 Cache montado! {len(existing_props)} proposições prontas para serem puladas.")
    
    for ano in anos:
        logger.info(f"📅 Iniciando busca de proposições do ano {ano}...")
        params = {"ano": ano, "ordem": "DESC", "ordenarPor": "id"}
        proposicoes = camara_paginado("/proposicoes", params=params)

        for p_resumo in proposicoes:
            id_camara_prop = p_resumo['id']

            # 🛑 VERIFICAÇÃO DO CACHE: Se já existe, pula para a próxima!
            if id_camara_prop in existing_props:
                # print(f"⏭️ Prop {p_resumo['siglaTipo']} {p_resumo['numero']} - Já no banco. Pulando.")
                continue

            # 1. Salva a Proposição
            prop_db = upsert_proposicao(db, p_resumo)
            db.flush()

            # 2. Autores
            autores_data = camara_get(f"/proposicoes/{id_camara_prop}/autores")
            for auth in autores_data.get("dados", []):
                upsert_proposicao_autor(db, prop_db.id, auth, cache_politicos)

            # 3. Votações vinculadas a esta proposição específica
            try:
                vots_vinc = camara_get(f"/proposicoes/{id_camara_prop}/votacoes")
                for v_vinc in vots_vinc.get("dados", []):
                    try:
                        # Upsert da Votação vinculada
                        vot_obj = upsert_votacao_index(db, None, v_vinc)
                        vot_obj.proposicao_id = prop_db.id 
                        db.flush()

                        id_vot = v_vinc['id']
                        
                        # Orientações
                        orientacoes = buscar_votacao_orientacoes(id_vot)
                        upsert_votacao_orientacoes(db, vot_obj, {"dados": orientacoes})

                        # Votos
                        votos_gen = buscar_votacao_votos(id_vot)
                        lista_votos = list(votos_gen) 
                        upsert_votacao_votos(db, vot_obj, {"dados": lista_votos}, cache_politicos)

                    except Exception as e_vot:
                        logger.warning(f"⚠️ Pulando detalhes da votação {v_vinc.get('id')}: {e_vot}")
                        db.rollback()
                        continue

            except Exception as e_prop_vots:
                logger.error(f"❌ Erro ao buscar lista de votações da prop {id_camara_prop}: {e_prop_vots}")
            
            db.commit()
            
            # Adiciona ao cache em memória para caso venha repetido na paginação
            existing_props.add(id_camara_prop)
            print(f"✅ Prop {p_resumo['siglaTipo']} {p_resumo['numero']} - OK")

    db.close()