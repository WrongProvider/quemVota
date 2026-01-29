from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

DATABASE_URL = "postgresql+psycopg2://postgres:postgres@localhost/quemvota"

engine = create_engine(
    DATABASE_URL,
    echo=False,          # mude para True se quiser debug SQL
    future=True
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False
)

Base = declarative_base()

# tabela no banco
from sqlalchemy import Column, Integer, String, Date, CHAR, Text

class Politico(Base):
    __tablename__ = "politicos"

    id = Column(Integer, primary_key=True)
    id_camara = Column(Integer, nullable=False, unique=True, index=True)
    nome = Column(String(150), nullable=False, index=True)
    nome_civil = Column(String(150))
    sexo = Column(CHAR(1))
    data_nascimento = Column(Date)
    uf = Column(CHAR(2))
    url_foto = Column(Text)
    email = Column(String(150))


import requests
from sqlalchemy.orm import Session

API_URL = "https://dadosabertos.camara.leg.br/api/v2/deputados"


def get_ou_cria_politico(
    nome_politico: str,
    db: Session
) -> Politico:

    # 1. Busca pelo nome
    politico = (
        db.query(Politico)
        .filter(Politico.nome.ilike(nome_politico))
        .first()
    )

    if politico:
        return politico

    # 2. API Câmara
    response = requests.get(
        API_URL,
        params={
            "nome": nome_politico,
            "ordem": "ASC",
            "ordenarPor": "nome"
        },
        headers={"accept": "application/json"},
        timeout=10
    )
    response.raise_for_status()

    dados = response.json().get("dados", [])
    if not dados:
        raise ValueError("Político não encontrado")

    dep = dados[0]

    # 3. Persistência
    politico = Politico(
        id_camara=dep["id"],
        nome=dep["nome"],
        uf=dep["siglaUf"],
        url_foto=dep["urlFoto"],
    )

    db.add(politico)
    db.commit()
    db.refresh(politico)

    return politico


