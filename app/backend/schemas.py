from pydantic import BaseModel
from datetime import date
from datetime import datetime
from typing import Optional, List

class PoliticoBase(BaseModel):
    nome: str
    uf: str | None = None

class PoliticoResponse(PoliticoBase):
    id: int
    id_camara: int
    nome: str
    partido_sigla: str | None
    nome_civil: str | None
    escolaridade: str | None
    situacao: str | None
    condicao_eleitoral: str | None
    sexo: str | None
    data_nascimento: date | None
    url_foto: str | None
    uf: str | None
    
    email_gabinete: str | None
    telefone_gabinete: str | None
    
    class Config:
        from_attributes = True

class PoliticoVoto(BaseModel):
    id_votacao: int
    data: date
    proposicao_sigla: str | None
    proposicao_numero: int | None
    proposicao_ano: int | None
    ementa: str | None
    voto: str  # Sim, Não, Obstrução, etc.
    resultado_da_votacao: Optional[str] | None
    tipo_votacao: Optional[str] | None
    uri: str | None

    class Config:
        from_attributes = True

class ItemRanking(BaseModel):
    nome: str
    total: float

class PoliticoDespesaResumo(BaseModel):
    ano: int
    mes: int
    total_gasto: float
    qtd_despesas: int
    class Config:
        from_attributes = True

class PoliticoDespesaResumoCompleto(BaseModel):
    historico_mensal: List[PoliticoDespesaResumo]
    top_fornecedores: List[ItemRanking]
    top_categorias: List[ItemRanking]
    class Config:
        from_attributes = True

class PoliticoDespesaDetalhe(BaseModel):
    id: int
    data_documento: datetime | None
    tipo_despesa: str
    nome_fornecedor: str
    valor_liquido: float
    url_documento: str | None

    class Config:
        from_attributes = True

class PoliticoFornecedor(BaseModel):
    nome_fornecedor: str
    total_recebido: float
    qtd_notas: int

    class Config:
        from_attributes = True


class PoliticoEstatisticasResponse(BaseModel):
    total_votacoes: int
    total_despesas: int
    total_gasto: float
    media_mensal: float
    primeiro_ano: int | None
    ultimo_ano: int | None


class SerieDespesaItem(BaseModel):
    ano: int
    mes: int
    total: float


class VotacaoResumoItem(BaseModel):
    tipo_voto: str
    quantidade: int


class RankingDespesaPolitico(BaseModel):
    politico_id: int
    nome: str
    total_gasto: float

class RankingEmpresaLucro(BaseModel):
    cnpj: str
    nome_fornecedor: str
    total_recebido: float

class KeywordInfo(BaseModel):
    keyword: str
    frequencia: int

class RankingDiscursoPolitico(BaseModel):
    politico_id: int
    nome_politico: str
    sigla_partido: str
    sigla_uf: str
    total_discursos: int
    temas_mais_discutidos: List[KeywordInfo]

