import xml.etree.ElementTree as ET
import requests
import logging
from datetime import date, datetime, timedelta
import time
from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert
from backend.database import SessionLocal
from backend.models import Politico, Presenca
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Configuração de caminhos
PROGRESS_FILE = "last_date.txt"

def get_last_processed_date(ano_inicio: int):
    """Lê a última data do arquivo ou retorna 01/02 do ano inicial"""
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, "r") as f:
            data_str = f.read().strip()
            if data_str:
                return datetime.strptime(data_str, "%d/%m/%Y").date()
    
    # Se não houver arquivo, começa após o recesso (01/02)
    return date(ano_inicio, 2, 1)

def save_progress(data: date):
    """Salva a data atual no arquivo de controle"""
    with open(PROGRESS_FILE, "w") as f:
        f.write(data.strftime("%d/%m/%Y"))

def fetch_presencas_xml(data_str: str):
    url = "https://www.camara.leg.br/SitCamaraWS/sessoesreunioes.asmx/ListarPresencasDia"
    
    # Parâmetros vazios como o WebService espera
    params = {
        "data": data_str,
        "numMatriculaParlamentar": "",
        "siglaPartido": "",
        "siglaUF": ""
    }
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36'
    }

    try:
        # O requests vai montar a URL corretamente com os & vazios no final
        response = requests.get(url, params=params, headers=headers, timeout=30)
        
        if response.status_code == 200:
            return ET.fromstring(response.content)
        else:
            print(f"Erro {response.status_code}: {response.text}")
            return None
    except Exception as e:
        print(f"Erro na conexão: {e}")
        return None

def get_politico_id_por_nome(db: Session, nome_xml: str):
    """
    O XML vem como 'Nome-Partido/UF'. 
    Tentamos casar com o nome no banco (removendo a parte do partido).
    """
    nome_limpo = nome_xml.split('-')[0].strip()
    # Busca por semelhança (ilike) ou match exato
    p = db.query(Politico).filter(Politico.nome.ilike(f"%{nome_limpo}%")).first()
    return p.id if p else None

def injest_presencas_dia(data_alvo: str):
    db = SessionLocal()
    root = fetch_presencas_xml(data_alvo)
    
    if root == "SEM_SESSAO":
        logger.info(f"☕ {data_alvo}: Recesso ou sem sessão programada.")
        return
    
    if root is None:
        logger.error(f"❌ Erro de conexão no dia {data_alvo}")
        return

    # A data no topo do XML pode vir com hora: '11/12/2025 07:45:01'
    data_sessao_raw = root.find("data").text[:10]
    data_sessao = datetime.strptime(data_sessao_raw, "%d/%m/%Y").date()
    qtde_sessoes = int(root.find("qtdeSessoesDia").text or 0)

    count = 0
    for parl in root.findall(".//parlamentar"):
        nome_parlamentar = parl.find("nomeParlamentar").text
        politico_id = get_politico_id_por_nome(db, nome_parlamentar)
        
        if not politico_id:
            logger.warning(f"Político não encontrado: {nome_parlamentar}")
            continue

        frequencia_dia = parl.find("descricaoFrequenciaDia").text.strip()
        justificativa = parl.find("justificativa").text.strip()

        # Cada parlamentar pode ter várias sessões no mesmo dia
        sessoes = parl.findall(".//sessaoDia")
        for sessao in sessoes:
            desc_sessao = sessao.find("descricao").text.strip()
            frequencia_sessao = sessao.find("frequencia").text.strip()
            
            inicio_raw = sessao.find("inicio").text.strip()
            inicio_dt = datetime.strptime(inicio_raw, "%d/%m/%Y %H:%M:%S")

            # Preparar o Upsert
            stmt = insert(Presenca).values(
                politico_id=politico_id,
                data=data_sessao,
                qtde_sessoes_dia=qtde_sessoes,
                frequencia_dia=frequencia_dia,
                justificativa=justificativa,
                sessao_descricao=desc_sessao,
                sessao_inicio=inicio_dt,
                frequencia_sessao=frequencia_sessao
            )

            # Se já existir (politico + data + sessao), atualiza a frequência
            stmt = stmt.on_conflict_do_update(
                constraint="uq_presenca_sessao",
                set_={
                    "frequencia_dia": stmt.excluded.frequencia_dia,
                    "frequencia_sessao": stmt.excluded.frequencia_sessao,
                    "justificativa": stmt.excluded.justificativa
                }
            )
            
            db.execute(stmt)
            count += 1

    db.commit()
    logger.info(f"✅ Processadas {count} presenças para o dia {data_alvo}")
    db.close()

def injest_presencas_ano(ano: int):
    # Pega onde parou ou começa em 01/02
    data_atual = get_last_processed_date(ano)
    
    # Define o fim (hoje ou fim do ano)
    data_fim = date.today() if ano == date.today().year else date(ano, 12, 31)
    
    logger.info(f"🔄 Retomando processamento a partir de: {data_atual}")

    while data_atual <= data_fim:
        # Pula finais de semana
        if data_atual.weekday() >= 5:
            data_atual += timedelta(days=1)
            continue
            
        data_str = data_atual.strftime("%d/%m/%Y")
        
        try:
            logger.info(f"⏳ Processando: {data_str}")
            sucesso = injest_presencas_dia(data_str)
            
            # Se a função retornar sucesso ou "sem sessão", salvamos o progresso
            save_progress(data_atual)
            
            # Delay "Gente Fina" para evitar bloqueio (2 segundos é seguro)
            time.sleep(2.0) 
            
        except Exception as e:
            logger.error(f"❌ Erro no dia {data_str}: {e}")
            # No caso de erro, não salvamos o progresso para tentar novamente depois
            break # Opcional: para o script para você ver o que houve
            
        data_atual += timedelta(days=1)

    logger.info("🏁 Ciclo de processamento concluído.")
# Teste rápido no final do arquivo:
# if __name__ == "__main__":
#     # Teste um dia que sabidamente teve sessão
#     injest_presencas_dia("11/12/2025")