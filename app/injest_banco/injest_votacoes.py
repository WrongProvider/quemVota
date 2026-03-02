import logging
from datetime import datetime, timedelta
from injest_banco.db.database import SessionLocal
from injest_banco.db.models import Votacao, Evento
from injest_banco.api_camara import (
    camara_get,
    camara_paginado
)
from injest_banco.db_upsert import (
    carregar_por_id_camara,
    upsert_votacao_index,
    upsert_votacao_orientacoes,
    upsert_votacao_votos,
    upsert_evento_minimo # Precisamos garantir que o evento exista antes da votação
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def injest_votacoes(dias_atras=15):
    db = SessionLocal()
    try:
        # 1. Preparação: Cache de políticos para processar os votos sem lag
        cache_politicos = carregar_por_id_camara(db)
        
        # 2. Período de busca
        data_fim = datetime.now().date()
        data_inicio = data_fim - timedelta(days=dias_atras)
        
        logger.info(f"🔎 Iniciando busca de votações de {data_inicio} até {data_fim}")

        # 3. Buscamos eventos que podem conter votações
        # A API da Câmara permite filtrar eventos por data
        params_eventos = {
            "dataInicio": data_inicio.isoformat(),
            "dataFim": data_fim.isoformat(),
            "ordem": "ASC",
            "ordenarPor": "dataHoraInicio"
        }

        for ev_data in camara_paginado("/eventos", params=params_eventos):
            id_evento_api = ev_data['id']
            
            # 4. Buscamos as votações deste evento específico
            # Usamos camara_get porque raramente um evento tem mais de 100 votações (1 página basta)
            res_votacoes = camara_get(f"/eventos/{id_evento_api}/votacoes")
            votacoes_dados = res_votacoes.get("dados", [])

            if not votacoes_dados:
                continue

            # Garantimos que o Evento exista no nosso banco para manter a FK
            evento_obj = upsert_evento_minimo(db, ev_data)
            db.flush()

            for v_resumo in votacoes_dados:
                id_votacao_api = v_resumo['id']

                # LÓGICA INTELIGENTE: Pular se já importamos os votos desta votação
                voto_completo = db.query(Votacao).filter_by(
                    id_camara=id_votacao_api, 
                    votos_importados=True
                ).first()
                
                if voto_completo:
                    logger.info(f"⏩ Votação {id_votacao_api} já processada. Pulando...")
                    continue

                logger.info(f"🗳️ Processando Votação: {v_resumo.get('descricao', id_votacao_api)}")

                # 5. Upsert da Votação (Index)
                votacao_obj = upsert_votacao_index(db, evento_obj, v_resumo)
                
                # --- NOVO BLOCO: BUSCA E CRIAÇÃO SOB DEMANDA DA PROPOSIÇÃO ---
                try:
                    detalhes = camara_get(f"/votacoes/{id_votacao_api}").get("dados", {})
                    uri_prop = detalhes.get("uriProposicaoObjeto")
                    
                    if uri_prop:
                        # Extrai o ID da URL (ex: .../proposicoes/2384758 -> 2384758)
                        id_prop_camara = int(uri_prop.split("/")[-1])
                        
                        # Verifica se a proposição já existe no nosso banco
                        from injest_banco.db.models import Proposicao
                        prop_existe = db.query(Proposicao).filter_by(id_camara=id_prop_camara).first()
                        
                        if not prop_existe:
                            logger.info(f"⚡ Proposição {id_prop_camara} não existe no banco. Baixando sob demanda...")
                            prop_payload = camara_get(f"/proposicoes/{id_prop_camara}").get("dados", {})
                            
                            if prop_payload:
                                from injest_banco.db_upsert import upsert_proposicao
                                prop_existe = upsert_proposicao(db, prop_payload)
                                db.flush()
                        
                        # Agora sim, faz o vínculo
                        if prop_existe:
                            votacao_obj.proposicao_id = prop_existe.id
                            logger.info(f"🔗 Votação {id_votacao_api} vinculada à Proposição {id_prop_camara}")
                            
                except Exception as e_vinculo:
                    logger.warning(f"⚠️ Falha na busca/vínculo da proposição para a votação {id_votacao_api}: {e_vinculo}")
                # --- FIM DO NOVO BLOCO ---
                db.flush()

                # 6. Importar Orientações (Bancadas/Lideranças)
                orientacoes_payload = camara_get(f"/votacoes/{id_votacao_api}/orientacoes")
                upsert_votacao_orientacoes(db, votacao_obj, orientacoes_payload)

                # 7. Importar Votos Individuais 
                # Mudança: Usamos camara_get porque este endpoint NÃO aceita parâmetros de paginação
                logger.info(f"📥 Baixando votos da votação {id_votacao_api}...")
                # No momento de baixar os votos
                votos_payload = camara_get(f"/votacoes/{id_votacao_api}/votos")

                if votos_payload and len(votos_payload.get("dados", [])) > 0:
                    # É NOMINAL - Processa normalmente
                    upsert_votacao_votos(db, votacao_obj, votos_payload, cache_politicos)
                    votacao_obj.tipo_votacao = "Nominal"
                else:
                    # É SIMBÓLICA ou SECRETA - Não há votos individuais
                    logger.info(f"ℹ️ Votação {id_votacao_api} sem registros individuais (Simbólica/Secreta).")
                    votacao_obj.tipo_votacao = "Simbólica/Outros"

                votacao_obj.votos_importados = True
                db.commit() 
                logger.info(f"✅ Votação {id_votacao_api} finalizada com sucesso.")

    except Exception as e:
        db.rollback()
        logger.error(f"❌ Erro crítico na ingestão de votações: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    injest_votacoes()