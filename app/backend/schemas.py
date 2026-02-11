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


from pydantic import BaseModel
from datetime import datetime

class DespesaResumo(BaseModel):
    ano: int
    mes: int
    total_gasto: float
    qtd_despesas: int

    class Config:
        from_attributes = True

class DespesaDetalheResponse(BaseModel):
    id: int
    data_documento: datetime | None
    tipo_despesa: str
    nome_fornecedor: str
    valor_liquido: float
    url_documento: str | None

    class Config:
        from_attributes = True

class FornecedorRanking(BaseModel):
    nome_fornecedor: str
    total_recebido: float
    qtd_notas: int

    class Config:
        from_attributes = True