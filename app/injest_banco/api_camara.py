import requests
import time
import logging

# Configuração básica de log para você saber o que está acontecendo no ingest
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

API_BASE = "https://dadosabertos.camara.leg.br/api/v2"
HEADERS = {"accept": "application/json"}

def camara_get(path: str, params=None, tentativas=3):
    """Função base com tratamento de erro e retentativas."""
    url = f"{API_BASE}{path}" if path.startswith("/") else path
    for tentativa in range(tentativas):
        try:
            r = requests.get(url, params=params, headers=HEADERS, timeout=30)
            r.raise_for_status()
            return r.json()
        except requests.RequestException as e:
            if tentativa == tentativas - 1:
                logger.error(f"Erro definitivo em {url}: {e}")
                raise
            wait = 2 ** tentativa
            logger.warning(f"Erro em {url}. Tentando novamente em {wait}s...")
            time.sleep(wait)

def camara_paginado(path: str, params=None):
    """
    Gerador que percorre todas as páginas de um endpoint.
    Útil para /votos, /deputados e /eventos.
    """
    params = params or {}
    params.setdefault("itens", 100)
    params.setdefault("pagina", 1)

    while True:
        dados = camara_get(path, params=params)
        yield from dados.get("dados", [])

        # Verifica se existe link 'next' nos links da API
        next_link = next((l["href"] for l in dados.get("links", []) if l["rel"] == "next"), None)
        if not next_link:
            break
        path = next_link # O link já vem completo
        params = None    # O link 'next' já contém os parâmetros


def buscar_deputados():
    # Retorna todos os deputados atuais (paginado internamente)
    return camara_paginado("/deputados")

def buscar_orgao_detalhe(id_orgao: int):
    return camara_get(f"/orgaos/{id_orgao}").get("dados")

def buscar_orgao_membros(id_orgao: int):
    return camara_paginado(f"/orgaos/{id_orgao}/membros")

def buscar_eventos(data_inicio: str, data_fim: str):
    params = {
        "dataInicio": data_inicio, 
        "dataFim": data_fim, 
        "ordem": "ASC", 
        "ordenarPor": "dataHoraInicio"
    }
    return camara_paginado("/eventos", params=params)

def buscar_votacao_detalhe(id_votacao: str):
    return camara_get(f"/votacoes/{id_votacao}").get("dados")

def buscar_votacao_votos(id_votacao: str):
    # Votos podem ser muitos, melhor usar o paginado
    return camara_paginado(f"/votacoes/{id_votacao}/votos")

def buscar_votacao_orientacoes(id_votacao: str):
    return camara_get(f"/votacoes/{id_votacao}/orientacoes").get("dados", [])