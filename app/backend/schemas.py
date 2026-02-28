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

class ItemRankingFornecedor(BaseModel):
    nome: str
    total: float
    categoria_principal: str | None = None

class PoliticoDespesaResumo(BaseModel):
    ano: int
    mes: int
    total_gasto: float
    qtd_despesas: int
    class Config:
        from_attributes = True

class PoliticoDespesaResumoCompleto(BaseModel):
    historico_mensal: List[PoliticoDespesaResumo]
    top_fornecedores: List[ItemRankingFornecedor]
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


# =============================================================================
# SCHEMAS — Proposições e Votações
# =============================================================================
# Adicionar ao final de schemas.py
#
# Modelos cobertos:
#   Proposicao, ProposicaoAutor, Tema, Tramitacao
#   Votacao, OrientacaoVotacao
#
# Convenção do projeto:
#   - from_attributes = True  → permite usar instâncias ORM diretamente
#   - Optional[X] | None      → campos que podem não vir preenchidos do banco
# =============================================================================

# -----------------------------------------------------------------------------
# Blocos reutilizáveis (sub-schemas)
# -----------------------------------------------------------------------------

class AutorResumo(BaseModel):
    """
    Representação enxuta de um autor de proposição.
    Usado dentro de ProposicaoResponse e ProposicaoDetalhe.

    Campos:
      - politico_id: ID interno do político (None se o autor não for um deputado,
                     ex: comissão, Senado, Executivo)
      - nome:        Nome completo do autor
      - tipo:        Tipo de autoria (ex: "Deputado", "Comissão", "Senado")
      - proponente:  True se for o autor principal / proponente da matéria
    """
    politico_id: Optional[int] = None
    nome: str
    tipo: Optional[str] = None
    proponente: Optional[bool] = None

    class Config:
        from_attributes = True


class TemaResumo(BaseModel):
    """
    Tema legislativo associado a uma proposição.
    Vem da tabela `temas` via relação many-to-many `proposicoes_temas`.
    """
    id: int
    cod_tema: Optional[int] = None
    tema: str

    class Config:
        from_attributes = True


class TramitacaoItem(BaseModel):
    """
    Registro de tramitação de uma proposição.
    Representa uma etapa no histórico de movimentação da matéria
    entre órgãos e situações (ex: "Pronta para Pauta", "Aprovada").

    Campos relevantes para o frontend:
      - data_hora:              Momento do registro
      - sigla_orgao:            Órgão responsável naquela etapa (ex: "PLEN", "CCJ")
      - descricao_situacao:     Situação da proposição naquele ponto
      - descricao_tramitacao:   Ação realizada (ex: "Votação em Plenário")
      - despacho:               Texto do despacho (pode ser longo)
      - regime:                 Regime de tramitação (ex: "Urgência", "Ordinário")
      - ambito:                 Onde ocorre (ex: "Câmara", "Senado")
    """
    id: int
    data_hora: Optional[datetime] = None
    sequencia: Optional[int] = None
    sigla_orgao: Optional[str] = None
    regime: Optional[str] = None
    descricao_tramitacao: Optional[str] = None
    descricao_situacao: Optional[str] = None
    despacho: Optional[str] = None
    ambito: Optional[str] = None
    apreciacao: Optional[str] = None

    class Config:
        from_attributes = True


# -----------------------------------------------------------------------------
# Proposições
# -----------------------------------------------------------------------------

class ProposicaoResponse(BaseModel):
    """
    Schema de listagem de proposições.
    Retornado por GET /proposicoes/ — sem tramitação para manter a resposta leve.

    Inclui os autores (ProposicaoAutor) para que o frontend consiga exibir
    o nome do autor diretamente na listagem sem precisar de um segundo request.
    """
    id: int
    id_camara: int

    sigla_tipo: Optional[str] = None          # Ex: "PL", "PEC", "MPV"
    numero: Optional[int] = None
    ano: Optional[int] = None
    descricao_tipo: Optional[str] = None

    ementa: Optional[str] = None
    keywords: Optional[str] = None

    data_apresentacao: Optional[datetime] = None
    url_inteiro_teor: Optional[str] = None

    autores: List[AutorResumo] = []
    temas: List[TemaResumo] = []

    class Config:
        from_attributes = True


class ProposicaoDetalhe(ProposicaoResponse):
    """
    Schema de detalhe completo de uma proposição.
    Retornado por GET /proposicoes/{id} — inclui tramitação completa.

    Herda todos os campos de ProposicaoResponse e adiciona:
      - ementa_detalhada: versão longa da ementa
      - justificativa:    texto de justificativa (pode ser muito longo)
      - tramitacoes:      histórico completo de tramitação, ordenado por data_hora
    """
    ementa_detalhada: Optional[str] = None
    justificativa: Optional[str] = None
    urn_final: Optional[str] = None

    tramitacoes: List[TramitacaoItem] = []

    class Config:
        from_attributes = True


# -----------------------------------------------------------------------------
# Votações
# -----------------------------------------------------------------------------

class OrientacaoPartido(BaseModel):
    """
    Orientação de voto de um partido/bloco em uma votação específica.
    Vem da tabela `orientacoes_votacao`.

    Campos:
      - sigla_partido_bloco: Sigla do partido ou bloco (ex: "PT", "PL", "UNIÃO")
      - orientacao_voto:     Voto orientado (ex: "Sim", "Não", "Libera", "Obstrução")
      - cod_tipo_lideranca:  Tipo de liderança que emitiu a orientação
    """
    sigla_partido_bloco: Optional[str] = None
    cod_tipo_lideranca: Optional[str] = None
    orientacao_voto: Optional[str] = None

    class Config:
        from_attributes = True


class VotacaoResponse(BaseModel):
    """
    Schema de listagem de votações.
    Retornado por GET /votacoes/ — sem orientações para manter a resposta leve.

    Campos:
      - aprovacao:    1 = aprovada, 0 = rejeitada, -1 = indefinido
      - sigla_orgao:  Órgão que realizou a votação (ex: "PLEN")
      - proposicao_*: Dados da proposição vinculada (desnormalizados para evitar join extra)
    """
    id: int
    id_camara: str

    data: Optional[date] = None
    data_hora_registro: Optional[datetime] = None

    tipo_votacao: Optional[str] = None        # "Nominal" ou "Simbólica"
    descricao: Optional[str] = None
    aprovacao: Optional[int] = None           # 1, 0, -1
    sigla_orgao: Optional[str] = None

    # Campos da proposição vinculada (JOIN feito no repositório)
    proposicao_id: Optional[int] = None
    proposicao_sigla: Optional[str] = None    # Ex: "PL"
    proposicao_numero: Optional[int] = None
    proposicao_ano: Optional[int] = None
    proposicao_ementa: Optional[str] = None

    class Config:
        from_attributes = True


class VotacaoDetalhe(VotacaoResponse):
    """
    Schema de detalhe de uma votação.
    Retornado por GET /votacoes/{id} — inclui orientações por partido.

    Herda todos os campos de VotacaoResponse e adiciona:
      - orientacoes: como cada partido/bloco orientou o voto dos seus membros
    """
    orientacoes: List[OrientacaoPartido] = []

    class Config:
        from_attributes = True

class ProposicaoAutorResumo(BaseModel):
    politico_id: Optional[int] = None
    nome: str
    tipo: Optional[str] = None
    proponente: bool = False

    class Config:
        from_attributes = True


class TemaResumoSimples(BaseModel):
    id: int
    tema: str

    class Config:
        from_attributes = True


class ProposicaoParaPolitico(BaseModel):
    # Proposição retornada no endpoint /politicos/{id}/proposicoes.
    # Inclui lista de autores e temas para o frontend poder distinguir
    # autor principal (proponente=True) de coautores.
    id: int
    id_camara: int
    sigla_tipo: Optional[str] = None
    numero: Optional[int] = None
    ano: Optional[int] = None
    descricao_tipo: Optional[str] = None
    ementa: Optional[str] = None
    keywords: Optional[str] = None
    data_apresentacao: Optional[datetime] = None
    url_inteiro_teor: Optional[str] = None
    autores: List[ProposicaoAutorResumo] = []
    temas: List[TemaResumoSimples] = []

    class Config:
        from_attributes = True