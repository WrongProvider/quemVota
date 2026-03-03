import logging
import time
from injest_banco.db.database import SessionLocal
from injest_banco.db.models import Politico
from injest_banco.api_camara import camara_get
from injest_banco.db_upsert import carregar_partidos_por_sigla

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

def rodar_backfill_detalhes():
    logger.info("🔍 Iniciando Backfill: Buscando políticos sem foto ou sem partido...")
    
    with SessionLocal() as db:
        # 1. Carrega os partidos disponíveis no banco
        cache_partidos = carregar_partidos_por_sigla(db)
        
        # 2. Busca apenas quem precisa de atualização (Sem foto OU sem partido)
        # Atenção: Ajuste os nomes das colunas se no seu modelo SQLAlchemy forem diferentes
        politicos_incompletos = db.query(Politico).filter(
            (Politico.url_foto.is_(None)) | 
            (Politico.url_foto == "") | 
            (Politico.partido_id.is_(None))
        ).all()
        
        total = len(politicos_incompletos)
        if total == 0:
            logger.info("✅ Tudo certo! Nenhum político com dados incompletos encontrado.")
            return

        logger.info(f"⚙️ Encontrados {total} políticos precisando de correção. Iniciando...")

        corrigidos = 0
        partidos_nao_encontrados = set()

        for politico in politicos_incompletos:
            id_camara = politico.id_camara
            
            try:
                # Busca o perfil completo detalhado do deputado
                detalhes_api = camara_get(f"/deputados/{id_camara}").get("dados", {})
                
                if not detalhes_api:
                    logger.warning(f"⚠️ Político {id_camara} ({politico.nome}) não retornou dados na API.")
                    continue

                # No endpoint detalhado, as informações atuais ficam no bloco "ultimoStatus"
                status = detalhes_api.get("ultimoStatus", {})
                
                # Atualiza a Foto
                nova_foto = status.get("urlFoto")
                if nova_foto:
                    politico.url_foto = nova_foto
                
                # Atualiza o Partido
                sigla_partido = status.get("siglaPartido")
                if sigla_partido:
                    partido_obj = cache_partidos.get(sigla_partido)
                    if partido_obj:
                        politico.partido_id = partido_obj.id
                    else:
                        partidos_nao_encontrados.add(sigla_partido)
                        logger.debug(f"ℹ️ Partido '{sigla_partido}' do político {politico.nome} não existe no banco.")

                corrigidos += 1
                
                # Commit em lotes pequenos para não perder o trabalho se der erro
                if corrigidos % 50 == 0:
                    db.commit()
                    logger.info(f"🔄 Processados {corrigidos}/{total}...")
                    
                # Rate limit da API
                time.sleep(0.2)

            except Exception as e:
                db.rollback() # Limpa a transação atual para não travar o loop
                logger.error(f"❌ Erro ao atualizar o político {id_camara}: {e}")
                continue

        # Garante o commit do restante
        db.commit()
        
        logger.info("🏁 Backfill de Detalhes Concluído!")
        logger.info(f"📈 {corrigidos} políticos atualizados com sucesso.")
        
        if partidos_nao_encontrados:
            logger.warning(f"🚨 Os seguintes partidos não foram encontrados no seu banco: {', '.join(partidos_nao_encontrados)}")
            logger.warning("Recomendo rodar o passo de Ingestão de Partidos novamente para cadastrá-los!")

if __name__ == "__main__":
    rodar_backfill_detalhes()