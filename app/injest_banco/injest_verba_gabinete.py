import requests
from bs4 import BeautifulSoup
import logging
import time
from injest_banco.db.database import SessionLocal
from injest_banco.db.models import Politico
from db_upsert import upsert_verba

# Configuração de Logs
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def clean_currency(value_str: str) -> float:
    """Converte '125.478,69' para 125478.69"""
    if not value_str: return 0.0
    clean = value_str.replace('R$', '').replace('.', '').replace(',', '.').strip()
    try:
        return float(clean)
    except ValueError:
        return 0.0

def fetch_verba_html(id_camara: int, ano: int):
    """Faz o scraping da página de verba de gabinete"""
    url = f"https://www.camara.leg.br/deputados/{id_camara}/verba-gabinete?ano={ano}"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
        'Referer': 'https://www.camara.leg.br/'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=20)
        if response.status_code == 200:
            return response.text
        logger.warning(f"⚠️ Status {response.status_code} para ID {id_camara}")
        return None
    except Exception as e:
        logger.error(f"❌ Erro na requisição: {e}")
        return None


def injest_verbas_gabinete(ano: int):
    db = SessionLocal()
    # Pega todos os políticos ativos (ou todos que tenham id_camara)
    politicos = db.query(Politico).filter(Politico.id_camara.isnot(None)).all()
    logger.info(f"🚀 Iniciando ingestão de verbas via HTML para {len(politicos)} políticos...")
    
    for p in politicos:
        try:
            html = fetch_verba_html(p.id_camara, ano)
            if not html: 
                continue

            soup = BeautifulSoup(html, 'html.parser')
            
            # Busca especificamente a tabela do seu print
            tabela = soup.find('table', class_='table-striped')
            if not tabela:
                logger.info(f"ℹ️ Sem dados de verba para {p.nome} em {ano}")
                continue

            # Tenta pegar as linhas do <tbody> (seguro contra thead duplo ou estranho)
            tbody = tabela.find('tbody')
            linhas = tbody.find_all('tr') if tbody else tabela.find_all('tr')[1:]

            contador = 0
            for linha in linhas:
                cols = linha.find_all('td')
                if len(cols) >= 3:
                    mes_texto = cols[0].text.strip()
                    
                    try:
                        # Agora sim: "01" vira 1, "02" vira 2
                        mes_num = int(mes_texto) 
                    except ValueError:
                        continue # Pula se não for um número válido (ex: linha vazia)
                    
                    v_disponivel = clean_currency(cols[1].text)
                    v_gasto = clean_currency(cols[2].text)
                    
                    upsert_verba(db, p.id, ano, mes_num, v_disponivel, v_gasto)
                    contador += 1
            
            if contador > 0:
                db.commit()
                logger.info(f"✅ {p.nome}: {contador} meses processados.")
            else:
                logger.warning(f"❌ {p.nome}: Tabela encontrada, mas dados inválidos.")

            # Pausa para não agredir o servidor
            time.sleep(0.5)  

        except Exception as e:
            db.rollback()
            logger.error(f"❌ Erro ao processar {p.nome}: {e}")
            continue

    db.close()
    logger.info("🏁 Ingestão de verbas finalizada!")