from pydantic import BaseModel
from datetime import date, datetime
from typing import Optional, List


class PoliticoBase(BaseModel):
    nome: str
    sigla_uf: str | None = None


class MaisPesquisadoSchema(BaseModel):
    politico_id:   int
    nome:          str
    uf:            str | None = None
    partido_sigla: str | None = None
    url_foto:      str | None = None
    count:         int

    class Config:
        from_attributes = True


class PoliticoResponse(PoliticoBase):
    id: int
    id_camara: int
    nome: str
    sigla_uf: str | None = None
    sigla_partido: str | None = None
    nome_civil: str | None = None
    escolaridade: str | None = None
    situacao: str | None = None
    condicao_eleitoral: str | None = None
    sigla_sexo: str | None = None
    data_nascimento: date | None = None
    url_foto: str | None = None
    slug: str | None = None

    email_gabinete: str | None = None
    telefone_gabinete: str | None = None

    class Config:
        from_attributes = True
        populate_by_name = True
        alias_generator = None

    @classmethod
    def model_validate(cls, obj, *args, **kwargs):
        if hasattr(obj, "__dict__") and not isinstance(obj, dict):
            data = {
                "id":                 obj.id,
                "id_camara":          obj.idCamara,
                "nome":               obj.nome,
                "slug":               obj.slug,
                "sigla_uf":           obj.siglaUF,
                "sigla_partido":      obj.siglaPartido,
                "nome_civil":         obj.nomeCivil,
                "escolaridade":       obj.escolaridade,
                "situacao":           obj.situacao,
                "condicao_eleitoral": obj.condicaoEleitoral,
                "sigla_sexo":         obj.siglaSexo,
                "data_nascimento":    obj.dataNascimento,
                "url_foto":           obj.urlFoto,
                "email_gabinete":     obj.emailGabinete,
                "telefone_gabinete":  obj.telefoneGabinete,
            }
            return cls(**data)
        return super().model_validate(obj, *args, **kwargs)


class PoliticoVoto(BaseModel):
    id_votacao: int
    data: date
    proposicao_sigla: str | None = None
    proposicao_numero: int | None = None
    proposicao_ano: int | None = None
    ementa: str | None = None
    voto: str                              # Sim, Não, Obstrução, etc.
    resultado_da_votacao: Optional[str] = None
    tipo_votacao: Optional[str] = None
    uri: str | None = None

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
    data_documento: datetime | None = None
    tipo_despesa: str | None = None
    nome_fornecedor: str | None = None
    valor_liquido: float | None = None
    url_documento: str | None = None

    model_config = {"from_attributes": True, "populate_by_name": True}

    @classmethod
    def model_validate(cls, obj, *args, **kwargs):
        if isinstance(obj, dict):
            return cls(
                id=obj.get("id"),
                data_documento=obj.get("dataDocumento"),
                tipo_despesa=obj.get("tipoDespesa"),
                nome_fornecedor=obj.get("nomeFornecedor"),
                valor_liquido=float(obj["valorLiquido"]) if obj.get("valorLiquido") is not None else None,
                url_documento=obj.get("urlDocumento"),
            )
        return super().model_validate(obj, *args, **kwargs)


class PoliticoFornecedor(BaseModel):
    nome_fornecedor: str
    total_recebido: float
    qtd_notas: int

    class Config:
        from_attributes = True


class PoliticoEstatisticasResponse(BaseModel):
    total_votacoes: int
    total_despesas: int
    # Gastos CEAP (cota parlamentar)
    total_gasto: float
    # Gastos com verba de gabinete (pessoal/funcionarios)
    total_gasto_gabinete: float = 0.0
    # Soma CEAP + gabinete
    total_gasto_combinado: float = 0.0
    media_mensal: float
    primeiro_ano: int | None = None
    ultimo_ano: int | None = None


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

# -----------------------------------------------------------------------------
# Blocos reutilizáveis (sub-schemas)
# -----------------------------------------------------------------------------

class AutorResumo(BaseModel):
    """
    Representação enxuta de um autor de proposição.

    Campos:
      - politico_id: ID interno do deputado (None se autor não for deputado,
                     ex: comissão, Senado, Executivo)
      - nome:        Nome completo do autor  (campo nomeAutor no ORM)
      - tipo:        Tipo de autoria (ex: "Deputado", "Comissão", "Senado")
                     (campo tipoAutor no ORM)
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
    Vem da tabela `temas` via relação many-to-many `proposicoesTemas`.
    """
    id: int
    tema: str

    class Config:
        from_attributes = True


class TramitacaoItem(BaseModel):
    """
    Registro de tramitação de uma proposição.

    Mapeamento ORM → schema:
      dataHora              → data_hora
      siglaOrgao            → sigla_orgao
      descricaoTramitacao   → descricao_tramitacao
      descricaoSituacao     → descricao_situacao
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

    Mapeamento ORM → schema:
      idCamara          → id_camara
      siglaTipo         → sigla_tipo
      descricaoTipo     → descricao_tipo
      dataApresentacao  → data_apresentacao
      urlInteiroTeor    → url_inteiro_teor
    """
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

    autores: List[AutorResumo] = []
    temas: List[TemaResumo] = []

    class Config:
        from_attributes = True


class ProposicaoDetalhe(ProposicaoResponse):
    """
    Schema de detalhe completo de uma proposição.
    Retornado por GET /proposicoes/{id} — inclui tramitação completa.

    Mapeamento ORM → schema adicional:
      ementaDetalhada → ementa_detalhada
      urnFinal        → urn_final
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
    Vem da tabela `votacoesOrientacoes`.

    Mapeamento ORM → schema:
      siglaBancada → sigla_partido_bloco
      orientacao   → orientacao_voto
    """
    sigla_partido_bloco: Optional[str] = None
    orientacao_voto: Optional[str] = None

    class Config:
        from_attributes = True


class VotoDeputado(BaseModel):
    """
    Voto individual de um deputado em uma votação.
    Vem da tabela `votacoesVotos` com join em `deputados`.

    Mapeamento ORM → schema:
      Voto.idDeputado   → politico_id
      Deputado.nome     → nome
      Voto.siglaPartido → sigla_partido
      Voto.siglaUF      → sigla_uf
      Voto.voto         → voto             ("Sim", "Não", "Abstenção", "Obstrução", etc.)
      Voto.dataHoraVoto → data_hora_voto
    """
    politico_id: int
    nome: str
    sigla_partido: Optional[str] = None
    sigla_uf: Optional[str] = None
    voto: str
    data_hora_voto: Optional[datetime] = None

    class Config:
        from_attributes = True


class VotacaoResponse(BaseModel):
    """
    Schema de listagem de votações.
    Retornado por GET /votacoes/ — sem orientações/votos para manter a resposta leve.

    Mapeamento ORM → schema:
      idCamara          → id_camara   (String — ex: "2578879-38")
      dataHoraRegistro  → data_hora_registro
      tipoVotacao       → tipo_votacao
      votosSim          → votos_sim
      votosNao          → votos_nao
      votosOutros       → votos_outros
      siglaOrgao        → sigla_orgao
      idProposicao      → proposicao_id
    """
    id: int
    id_camara: Optional[str] = None   # String no banco (ex: "2578879-38")

    data: Optional[date] = None
    data_hora_registro: Optional[datetime] = None

    tipo_votacao: Optional[str] = None
    descricao: Optional[str] = None
    aprovacao: Optional[int] = None   # 1 aprovada, 0 rejeitada, -1 indefinido

    votos_sim: Optional[int] = None
    votos_nao: Optional[int] = None
    votos_outros: Optional[int] = None

    sigla_orgao: Optional[str] = None

    proposicao_id: Optional[int] = None
    proposicao_sigla: Optional[str] = None
    proposicao_numero: Optional[int] = None
    proposicao_ano: Optional[int] = None
    proposicao_ementa: Optional[str] = None

    class Config:
        from_attributes = True


class VotacaoDetalhe(VotacaoResponse):
    """
    Schema de detalhe de uma votação.
    Retornado por GET /votacoes/{id}.

    Inclui:
      - orientacoes: como cada partido/bloco orientou seus membros
      - votos:       voto nominal de cada deputado presente
    """
    orientacoes: List[OrientacaoPartido] = []
    votos: List[VotoDeputado] = []

    class Config:
        from_attributes = True


# -----------------------------------------------------------------------------
# Proposições vinculadas a um deputado
# -----------------------------------------------------------------------------

class ProposicaoAutorResumo(BaseModel):
    """
    Mapeamento ORM → schema:
      idDeputadoAutor → politico_id
      nomeAutor       → nome
      tipoAutor       → tipo
    """
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
    """
    Proposição retornada no endpoint /politicos/{id}/proposicoes.
    Inclui lista de autores e temas para o frontend poder distinguir
    autor principal (proponente=True) de coautores.
    """
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


# =============================================================================
# SCHEMAS — Atividade Legislativa (endpoint consolidado)
# =============================================================================

class VotacaoResumida(BaseModel):
    """
    Votação na qual o deputado participou com voto nominal.

    Mapeamento ORM → schema:
      Voto.voto            → voto
      Votacao.tipoVotacao  → tipo_votacao
      Votacao.siglaOrgao   → sigla_orgao
      Votacao.idProposicao → proposicao_id
    """
    id_votacao: int
    data: Optional[date] = None

    proposicao_id: Optional[int] = None
    proposicao_sigla: Optional[str] = None
    proposicao_numero: Optional[int] = None
    proposicao_ano: Optional[int] = None
    proposicao_ementa: Optional[str] = None

    voto: str
    aprovacao: Optional[int] = None
    tipo_votacao: Optional[str] = None
    sigla_orgao: Optional[str] = None

    class Config:
        from_attributes = True


class ProposicaoResumida(BaseModel):
    """
    Proposição em que o deputado é autor ou coautor.

    Campos:
      - proponente:   True se for o autor principal/proponente da matéria
      - tipo_autoria: Tipo de autoria registrada (campo tipoAutor no ORM)
      - temas:        Lista de strings para leveza
    """
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

    proponente: bool = False
    tipo_autoria: Optional[str] = None

    temas: List[str] = []

    class Config:
        from_attributes = True


class AtividadeLegislativaResponse(BaseModel):
    """
    Resposta consolidada do endpoint GET /politicos/{id}/atividade-legislativa.
    Retorna votações + proposições do parlamentar em um único request.
    """
    votacoes: List[VotacaoResumida]
    proposicoes: List[ProposicaoResumida]

    total_votacoes: int
    total_proposicoes: int
    limit_votacoes: int
    limit_proposicoes: int
    offset_votacoes: int
    offset_proposicoes: int

    ano: Optional[int] = None

    class Config:
        from_attributes = True