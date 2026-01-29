# backend/services.py
from sqlalchemy.orm import Session
from backend.models import Politico


def buscar_politico_por_nome(nome: str, db: Session) -> list[Politico]:
    """
    Busca políticos pelo nome (parcial), somente no banco local
    """
    return (
        db.query(Politico)
        .filter(Politico.nome.ilike(f"%{nome}%"))
        .order_by(Politico.nome.asc())
        .all()
    )


def obter_politico_por_id(id_camara: int, db: Session) -> Politico | None:
    """
    Retorna um político pelo ID da Câmara (chave externa)
    """
    return (
        db.query(Politico)
        .filter(Politico.id_camara == id_camara)
        .first()
    )

def obter_detalhes_deputado(id_camara: int, db: Session) -> Politico | None:
    return (
        db.query(Politico)
        .filter(Politico.id_camara == id_camara)
        .first()
    )

def obter_despesas(id_camara: int, db: Session) -> list[Despesa]:
    return (
        db.query(Despesa)
        .filter(Despesa.id_camara == id_camara)
        .order_by(Despesa.ano.desc(), Despesa.mes.desc())
        .all()
    )

def obter_discursos(id_camara: int, db: Session) -> list[Discurso]:
    return (
        db.query(Discurso)
        .filter(Discurso.id_camara == id_camara)
        .order_by(Discurso.data.desc())
        .all()
    )
