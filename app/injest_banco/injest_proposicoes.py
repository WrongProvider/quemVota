from injest_banco.api_camara import camara_get, camara_paginado, buscar_votacao_votos, buscar_votacao_orientacoes

import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from injest_banco.db.database import SessionLocal
from injest_banco.db.models import Proposicao # Importamos o modelo para fazer a query do cache
from injest_banco.db_upsert import (
    upsert_proposicao, upsert_proposicao_autor, upsert_votacao_index,
    upsert_votacao_orientacoes, upsert_votacao_votos, carregar_por_id_camara
)

import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def injest_proposicoes(anos=[2025, 2026]):
    with SessionLocal() as db:
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

                if id_camara_prop in existing_props:
                    continue

                # ==========================================
                # FASE 1: BUSCA NA REDE (APIs) - Sem mexer no DB
                # ==========================================
                autores_data = camara_get(f"/proposicoes/{id_camara_prop}/autores").get("dados", [])
                vots_vinc_data = camara_get(f"/proposicoes/{id_camara_prop}/votacoes").get("dados", [])
                
                votacoes_completas = []
                for v_vinc in vots_vinc_data:
                    id_vot = v_vinc['id']
                    try:
                        # Buscamos tudo da API antes de abrir a transação
                        orientacoes = buscar_votacao_orientacoes(id_vot)
                        votos_gen = buscar_votacao_votos(id_vot)
                        
                        votacoes_completas.append({
                            "resumo": v_vinc,
                            "orientacoes": orientacoes,
                            "votos": list(votos_gen) 
                        })
                    except Exception as e:
                        logger.warning(f"⚠️ Erro ao baixar dados da votação {id_vot}: {e}")
                        continue

                # ==========================================
                # FASE 2: TRANSAÇÃO NO BANCO (Super rápida!)
                # ==========================================
                try:
                    # 1. Salva a Proposição
                    prop_db = upsert_proposicao(db, p_resumo)
                    db.flush() # Aqui a transação começa!

                    # 2. Autores
                    for auth in autores_data:
                        upsert_proposicao_autor(db, prop_db.id, auth, cache_politicos)

                    # 3. Votações vinculadas
                    for vot_data in votacoes_completas:
                        vot_obj = upsert_votacao_index(db, None, vot_data["resumo"])
                        vot_obj.proposicao_id = prop_db.id 
                        db.flush()

                        upsert_votacao_orientacoes(db, vot_obj, {"dados": vot_data["orientacoes"]})
                        upsert_votacao_votos(db, vot_obj, {"dados": vot_data["votos"]}, cache_politicos)

                    db.commit() # Transação fechada em milissegundos!
                    
                    existing_props.add(id_camara_prop)
                    logger.info(f"✅ Prop {p_resumo['siglaTipo']} {p_resumo['numero']} salva e comitada rapidamente.")

                except Exception as e_db:
                    logger.error(f"❌ Erro ao salvar dados no DB para prop {id_camara_prop}: {e_db}")
                    db.rollback() # Limpa a transação em caso de erro

                db.commit()
                
                # Adiciona ao cache em memória para caso venha repetido na paginação
                existing_props.add(id_camara_prop)
                print(f"✅ Prop {p_resumo['siglaTipo']} {p_resumo['numero']} - OK")