import requests
import time

API_BASE = "https://dadosabertos.camara.leg.br/api/v2"
HEADERS = {"accept": "application/json"}


def buscar_deputados(pagina=1, itens=100, tentativas=3):
    for tentativa in range(tentativas):
        try:
            resp = requests.get(
                f"{API_BASE}/deputados",
                params={
                    "pagina": pagina,
                    "itens": itens,
                    "ordem": "ASC",
                    "ordenarPor": "nome",
                },
                headers=HEADERS,
                timeout=20,
            )
            resp.raise_for_status()
            return resp.json()
        except requests.RequestException:
            if tentativa == tentativas - 1:
                raise
            time.sleep(2 ** tentativa)