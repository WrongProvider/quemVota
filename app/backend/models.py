from sqlalchemy import Column, Integer, String, Date, CHAR, Text
from backend.database import Base


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
