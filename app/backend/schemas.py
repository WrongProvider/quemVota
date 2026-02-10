from pydantic import BaseModel
from datetime import date
from datetime import datetime

class PoliticoBase(BaseModel):
    nome: str
    uf: str | None = None


class PoliticoResponse(PoliticoBase):
    id: int
    id_camara: int
    nome: str
    nome_civil: str | None
    sexo: str | None
    data_nascimento: date | None
    url_foto: str | None
    uf: str | None

    class Config:
        from_attributes = True

class VotoPoliticoResponse(BaseModel):
    votacao_id: int
    titulo: str | None
    data: datetime | None
    voto: str

    class Config:
        from_attributes = True