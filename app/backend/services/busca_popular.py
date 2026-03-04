from sqlalchemy.orm import Session
from sqlalchemy import desc
from backend.models import Politico, BuscaPopular  # ajuste para o seu model
from typing import List


def registrar_busca(db: Session, politico_id: int) -> None:
    """
    Incrementa o contador de buscas de um político.
    Se ainda não existir registro, cria com count=1.
    """
    registro = (
        db.query(BuscaPopular)
        .filter(BuscaPopular.politico_id == politico_id)
        .first()
    )
    if registro:
        registro.count += 1
    else:
        db.add(BuscaPopular(politico_id=politico_id, count=1))
    db.commit()


def obter_mais_pesquisados(db: Session, limit: int = 10) -> List[dict]:
    """
    Retorna os N políticos mais pesquisados com dados desnormalizados
    para evitar múltiplos requests no frontend.
    """
    resultados = (
        db.query(BuscaPopular, Politico)
        .join(Politico, BuscaPopular.politico_id == Politico.id)
        .order_by(desc(BuscaPopular.count))
        .limit(limit)
        .all()
    )

    return [
        {
            "politico_id":   politico.id,
            "nome":          politico.nome,
            "uf":            politico.uf,
            "partido_sigla": politico.partido_sigla,
            "url_foto":      getattr(politico, "url_foto", None),
            "count":         busca.count,
        }
        for busca, politico in resultados
    ]

