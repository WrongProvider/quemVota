from pydantic import BaseModel
from typing import Optional
from datetime import date

class PoliticoBase(BaseModel):
    id_camara: int
    nome: str
    uf: str | None = None
    url_foto: str | None = None

    class Config:
        from_attributes = True
