# injest_banco/main.py
import logging
import sys

# Configura o log ANTES de importar os outros módulos
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger(__name__)

# Importações usando o caminho do pacote
from injest_banco.backfill_politicos_detalhes import rodar_backfill_detalhes
from injest_banco.backfill_votacoes_orfas import rodar_backfill_votacoes
from injest_banco.injest_fotos import baixar_e_converter_fotos
from injest_banco.injest_proposicoes import injest_proposicoes
from injest_banco.injest_partidos import injest_partidos
from injest_banco.injest_camara import injest_politicos
from injest_banco.injest_votacoes import injest_votacoes
from injest_banco.injest_despesas import injest_despesas
from injest_banco.injest_presencas import injest_presencas_ano, injest_presencas_dia
from injest_banco.injest_verba_gabinete import injest_verbas_gabinete

def executar_pipeline():
    logger.info("🚀 Iniciando Pipeline de Ingestão de Dados...")
    
    try:
        # 1. Partidos (Base para os outros)
        logger.info("--- Passo 1: Partidos ---")
        injest_partidos()
        
        # 2. Políticos (Dependem dos Partidos)
        logger.info("--- Passo 2: Políticos ---")
        injest_politicos()
        
        # injest_fotos()  # Rodar este script separadamente para evitar sobrecarga e lidar com erros de download
        logger.info("fotos")
        baixar_e_converter_fotos()

        # backfill_politicos_detalhes()  # Roda este script depois de ter os políticos básicos para corrigir os detalhes faltantes (fotos e partidos)
        logger.info("backfill")
        rodar_backfill_detalhes()

        # backfill_votacoes_orfas()  # Roda este script depois de ter as votações e proposições para vincular as votações sem proposição
        logger.info("backfill_votacoes")
        rodar_backfill_votacoes()
    
        # x. Verba de Gabinete (Depende dos Políticos)
        # logger.info("--- Passo 3: Verba de Gabinete ---")
        # injest_verbas_gabinete(ano=2025)  # Você pode ajustar o ano conforme necessário
        
        logger.info("--- Passo 3: Presenças ---")
        # Para as presenças, vamos pegar os últimos 7 dias como exemplo
        # injest_presencas_dia("11/12/2025")  # Você pode ajustar o ano conforme necessário
        injest_presencas_ano(2026)  # Para pegar o ano inteiro de 2025, por exemplo
        # 3. Proposições (Importante rodar antes das votações se quiser vincular contextos)
        logger.info("--- Passo 3: Proposições ---")
        injest_proposicoes(anos=[2025, 2026])
        
        # 3. Votações (Dependem dos Políticos)
        logger.info("--- Passo 3: Votações ---")
        injest_votacoes(dias_atras=365)  # Você pode ajustar o período conforme necessário
        
        # 4. Despesas (Dependem dos Políticos)
        logger.info("--- Passo 4: Despesas ---")
        injest_despesas(anos=[2025, 2026])

        logger.info("✨ Sincronização Completa com Sucesso!")
        
    except Exception as e:
        logger.error(f"❌ Falha crítica no pipeline: {e}", exc_info=True)

if __name__ == "__main__":
    # Esta linha garante que a função rode quando você chamar o módulo
    executar_pipeline()