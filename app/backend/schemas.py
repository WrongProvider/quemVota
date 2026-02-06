from pydantic import BaseModel
from datetime import date

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