import requests
import time

API_BASE = "https://dadosabertos.camara.leg.br/api/v2"
HEADERS = {"accept": "application/json"}


def camara_get(path: str, params=None, tentativas=3):
    for tentativa in range(tentativas):
        try:
            r = requests.get(
                f"{API_BASE}{path}",
                params=params,
                headers=HEADERS,
                timeout=20,
            )
            r.raise_for_status()
            return r.json()
        except requests.RequestException:
            if tentativa == tentativas - 1:
                raise
            time.sleep(2 ** tentativa)


def buscar_deputados():
    return camara_get("/deputados", params={"pagina": 1, "itens": 100, "tentativas": 3})

def buscar_orgaos():
    return camara_get("/orgaos")

def buscar_orgao_detalhe(id_orgao: int):
    return camara_get(f"/orgaos/{id_orgao}")

def buscar_orgao_membros(id_orgao: int):
    return camara_get(f"/orgaos/{id_orgao}/membros")

def buscar_orgao_eventos(id_orgao: int):
    return camara_get(f"/orgaos/{id_orgao}/eventos")

def buscar_eventos(pagina: int = 1, itens: int = 100, tentativas=3):
    for tentativa in range(tentativas):
        try:
            resp = requests.get(
                f"{API_BASE}/eventos",
                params={
                    "pagina": pagina,
                    "itens": itens,
                    "ordem": "DESC",
                    "ordenarPor": "dataHoraInicio",
                },
                headers=HEADERS,
                timeout=30,
            )
            resp.raise_for_status()
            return resp.json()
        except requests.RequestException:
            if tentativa == tentativas - 1:
                raise
            time.sleep(2 ** tentativa)


def buscar_evento_detalhe(id_evento: int, tentativas=3):
    for tentativa in range(tentativas):
        try:
            resp = requests.get(
                f"{API_BASE}/eventos/{id_evento}",
                headers=HEADERS,
                timeout=30,
            )
            resp.raise_for_status()
            return resp.json()["dados"]
        except requests.RequestException:
            if tentativa == tentativas - 1:
                raise
            time.sleep(2 ** tentativa)