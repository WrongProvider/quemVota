import requests
from bs4 import BeautifulSoup
import logging
import time
from sqlalchemy.orm import Session # Importado para tipagem correta
from injest_banco.db.database import SessionLocal
from injest_banco.db.models import Deputado, VerbaGabinete
from sqlalchemy.dialects.postgresql import insert

# Configuração de Logs
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def upsert_verba(db: Session, idDeputado: int, ano: int, mes: int, disponivel: float, gasto: float):
    """Faz um Upsert nativo (muito mais rápido) e salva na hora"""
    
    # 1. Monta a instrução de INSERT
    stmt = insert(VerbaGabinete).values(
        idDeputado=idDeputado,
        ano=ano,
        mes=mes,
        valorDisponivel=disponivel,
        valorGasto=gasto
    )

    # 2. Define o que fazer em caso de conflito (quando já existe)
    # 'stmt.excluded' refere-se aos dados novos que tentamos inserir
    stmt = stmt.on_conflict_do_update(
        index_elements=['idDeputado', 'ano', 'mes'], # Colunas que definem a "duplicidade"
        set_={
            'valorDisponivel': stmt.excluded.valorDisponivel,
            'valorGasto': stmt.excluded.valorGasto
        }
    )

    # 3. Executa a query montada e commita imediatamente
    db.execute(stmt)
    db.commit()

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
    with SessionLocal() as db:
        # Filtro: Deputados da legislatura 54 em diante
        deputados = db.query(Deputado).filter(
            Deputado.idCamara.isnot(None),
            Deputado.idLegislaturaInicial >= 54
        ).all()
        
        logger.info(f"🚀 Processando {len(deputados)} deputados (Leg. 54+) para o ano {ano}...")
        
        for p in deputados:
            try:
                html = fetch_verba_html(p.idCamara, ano)
                if not html: 
                    continue

                soup = BeautifulSoup(html, 'html.parser')
                tabela = soup.find('table', class_='table-striped')
                
                if not tabela:
                    continue

                tbody = tabela.find('tbody')
                linhas = tbody.find_all('tr') if tbody else tabela.find_all('tr')[1:]

                for linha in linhas:
                    cols = linha.find_all('td')
                    if len(cols) >= 3:
                        try:
                            mes_num = int(cols[0].text.strip())
                            v_disponivel = clean_currency(cols[1].text)
                            v_gasto = clean_currency(cols[2].text)
                            
                            # Faz o upsert e comita na hora
                            upsert_verba(db, p.id, ano, mes_num, v_disponivel, v_gasto)
                        except ValueError:
                            continue
                
                logger.info(f"✅ {p.nome} (ID:{p.idCamara}) processado e salvo.")
                time.sleep(0.3)

            except Exception as e:
                # O rollback agora afeta apenas o que não foi "commitado" ainda
                db.rollback()
                logger.error(f"❌ Erro em {p.nome}: {e}")

if __name__ == "__main__":
    anos = list(range(2015, 2026))
    for a in anos:
        injest_verbas_gabinete(a)