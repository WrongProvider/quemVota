# backend/repositories/politicos.py
from sqlalchemy.orm import Session
from backend.models import Politico


def carregar_por_id_camara(db: Session) -> dict[int, Politico]:
    politicos = db.query(Politico).all()
    return {p.id_camara: p for p in politicos}


def upsert_politico(db: Session, cache: dict[int, Politico], dep: dict):
    politico = cache.get(dep["id"])

    if politico:
        politico.nome = dep["nome"]
        politico.uf = dep["siglaUf"]
        politico.url_foto = dep.get("urlFoto")
    else:
        politico = Politico(
            id_camara=dep["id"],
            nome=dep["nome"],
            uf=dep["siglaUf"],
            url_foto=dep.get("urlFoto"),
        )
        db.add(politico)
        cache[dep["id"]] = politico
