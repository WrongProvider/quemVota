from sqlalchemy.orm import Session
from sqlalchemy import desc
from backend.models import Deputado, BuscaPopular
from typing import List


def registrar_busca(db: Session, deputado_id: int) -> None:
    """
    Incrementa o contador de buscas de um deputado.
    Se ainda não existir registro, cria com count=1.
    """
    registro = (
        db.query(BuscaPopular)
        .filter(BuscaPopular.idDeputado == deputado_id)
        .first()
    )
    if registro:
        registro.count += 1
    else:
        db.add(BuscaPopular(idDeputado=deputado_id, count=1))
    db.commit()


def obter_mais_pesquisados(db: Session, limit: int = 10) -> List[dict]:
    """
    Retorna os N deputados mais pesquisados com dados desnormalizados
    para evitar múltiplos requests no frontend.
    """
    resultados = (
        db.query(BuscaPopular, Deputado)
        .join(Deputado, BuscaPopular.idDeputado == Deputado.id)
        .order_by(desc(BuscaPopular.count))
        .limit(limit)
        .all()
    )

    return [
        {
            "politico_id":   deputado.id,
            "nome":          deputado.nome,
            "uf":            deputado.siglaUF,
            "partido_sigla": deputado.siglaPartido,
            "url_foto":      deputado.urlFoto,
            "count":         busca.count,
        }
        for busca, deputado in resultados
    ]