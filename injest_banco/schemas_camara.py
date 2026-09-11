"""
schemas_camara.py
=================
Schemas Pydantic V2 para sanitização, normalização e validação estrita
dos dados da API e dos arquivos CSV da Câmara dos Deputados.
"""

from __future__ import annotations

import math
import re
from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


def sanitize_text(v: Any) -> str | None:
    """Sanitiza strings: remove null-bytes, espaços extras, strings vazias e 'nan'."""
    if v is None:
        return None
    if isinstance(v, float) and math.isnan(v):
        return None
    s = str(v).replace("\x00", "").strip()
    # Remove aspas externas residuais
    if s.startswith('"') and s.endswith('"') and len(s) >= 2:
        s = s[1:-1].strip()
    s = s.replace('""', '"')
    if not s or s.lower() in ("nan", "none", "null"):
        return None
    return s


def parse_flexible_date(v: Any) -> date | None:
    """Converte strings de data flexíveis (YYYY-MM-DD ou ISO) para objeto date."""
    if v is None:
        return None
    if isinstance(v, date) and not isinstance(v, datetime):
        return v
    if isinstance(v, datetime):
        return v.date()
    s = sanitize_text(v)
    if not s:
        return None
    # Trunca parte de hora se houver
    date_part = s[:10]
    try:
        d = date.fromisoformat(date_part)
        if d.year < 1800 or d.year > datetime.now(timezone.utc).year + 10:
            return None
        return d
    except ValueError:
        return None


def parse_flexible_datetime(v: Any) -> datetime | None:
    """Converte strings ISO para objeto datetime."""
    if v is None:
        return None
    if isinstance(v, datetime):
        return v
    if isinstance(v, date):
        return datetime(v.year, v.month, v.day, tzinfo=timezone.utc)
    s = sanitize_text(v)
    if not s:
        return None
    s = s.replace("Z", "+00:00")
    try:
        # Se for apenas YYYY-MM-DD
        if len(s) == 10:
            d = date.fromisoformat(s)
            return datetime(d.year, d.month, d.day, tzinfo=timezone.utc)
        return datetime.fromisoformat(s)
    except ValueError:
        return None


def parse_flexible_float(v: Any) -> float | None:
    """Converte números brasileiros ('1.234,56'), monetários ('R$ 500,75') ou floats para float."""
    if v is None:
        return None
    if isinstance(v, (int, float)):
        return None if math.isnan(v) else float(v)
    s = sanitize_text(v)
    if not s:
        return None
    # Remove prefixos monetários ou outros caracteres não numéricos exceto dígitos, ponto, vírgula e hífen
    s = re.sub(r"[^\d.,\-]", "", s)
    if not s:
        return None
    # Se contém vírgula, assume padrão BR
    if "," in s:
        s = s.replace(".", "").replace(",", ".")
    else:
        # Se não tem vírgula, remove qualquer ponto adicional exceto o último se houver
        pass
    try:
        return float(s)
    except ValueError:
        return None


def parse_flexible_int(v: Any) -> int | None:
    """Converte para inteiro com segurança."""
    if v is None:
        return None
    if isinstance(v, int):
        return v
    if isinstance(v, float):
        return None if math.isnan(v) else int(v)
    s = sanitize_text(v)
    if not s:
        return None
    try:
        return int(float(s))
    except (ValueError, TypeError):
        return None


class BaseCamaraSchema(BaseModel):
    """Schema base com configurações padrão do Pydantic V2."""

    model_config = ConfigDict(
        populate_by_name=True,
        str_strip_whitespace=True,
        arbitrary_types_allowed=True,
        extra="ignore",
    )


class DeputadoCamaraSchema(BaseCamaraSchema):
    """Validação de dados de Deputados."""

    idCamara: int
    uri: str | None = None
    nome: str
    siglaUf: str | None = Field(None, max_length=2)
    siglaPartido: str | None = None
    idLegislaturaInicial: int | None = None
    idLegislaturaFinal: int | None = None
    nomeCivil: str | None = None
    cpf: str | None = None
    siglaSexo: str | None = Field(None, max_length=1)
    urlRedeSocial: str | None = None
    urlWebsite: str | None = None
    dataNascimento: date | None = None
    dataFalecimento: date | None = None
    ufNascimento: str | None = Field(None, max_length=2)
    municipioNascimento: str | None = None
    escolaridade: str | None = None
    situacao: str | None = None
    condicaoEleitoral: str | None = None
    emailGabinete: str | None = None
    telefoneGabinete: str | None = None
    urlFoto: str | None = None
    slug: str | None = None

    @field_validator(
        "nome",
        "nomeCivil",
        "siglaPartido",
        "escolaridade",
        "situacao",
        "condicaoEleitoral",
        "emailGabinete",
        "telefoneGabinete",
        "urlFoto",
        "municipioNascimento",
        mode="before",
    )
    @classmethod
    def clean_strings(cls, v: Any) -> str | None:
        return sanitize_text(v)

    @field_validator(
        "idCamara", "idLegislaturaInicial", "idLegislaturaFinal", mode="before"
    )
    @classmethod
    def clean_ints(cls, v: Any) -> int | None:
        return parse_flexible_int(v)

    @field_validator("dataNascimento", "dataFalecimento", mode="before")
    @classmethod
    def clean_dates(cls, v: Any) -> date | None:
        return parse_flexible_date(v)


class ProposicaoCamaraSchema(BaseCamaraSchema):
    """Validação de dados de Proposições."""

    idCamara: int
    uri: str | None = None
    siglaTipo: str
    codTipo: int | None = None
    numero: int
    ano: int
    descricaoTipo: str | None = None
    ementa: str | None = None
    ementaDetalhada: str | None = None
    keywords: str | None = None
    dataApresentacao: datetime | None = None
    dataUltimaTramitacao: datetime | None = None
    urlInteiroTeor: str | None = None
    justificativa: str | None = None

    @field_validator(
        "siglaTipo",
        "descricaoTipo",
        "ementa",
        "ementaDetalhada",
        "keywords",
        "urlInteiroTeor",
        "justificativa",
        mode="before",
    )
    @classmethod
    def clean_strings(cls, v: Any) -> str | None:
        return sanitize_text(v)

    @field_validator("idCamara", "codTipo", "numero", "ano", mode="before")
    @classmethod
    def clean_ints(cls, v: Any) -> int | None:
        return parse_flexible_int(v)

    @field_validator("dataApresentacao", "dataUltimaTramitacao", mode="before")
    @classmethod
    def clean_datetimes(cls, v: Any) -> datetime | None:
        return parse_flexible_datetime(v)

    @model_validator(mode="after")
    def validate_coherence(self) -> ProposicaoCamaraSchema:
        """Validação de coerência: tramitação não pode ser anterior à apresentação."""
        if (
            self.dataApresentacao
            and self.dataUltimaTramitacao
            and self.dataUltimaTramitacao < self.dataApresentacao
        ):
            # Corrige ou alerta ajustando para a maior
            self.dataUltimaTramitacao = self.dataApresentacao
        return self


class VotacaoCamaraSchema(BaseCamaraSchema):
    """Validação de dados de Votações."""

    idCamara: str
    uri: str | None = None
    data: date | None = None
    dataHoraRegistro: datetime | None = None
    idOrgaoCamara: int | None = None
    idEventoCamara: int | None = None
    idProposicaoCamara: int | None = None
    siglaOrgao: str | None = None
    aprovacao: bool | None = None
    descricao: str | None = None
    proposicaoObjeto: str | None = None
    uriProposicaoObjeto: str | None = None
    tipoVotacao: str | None = None

    @field_validator(
        "idCamara",
        "siglaOrgao",
        "descricao",
        "proposicaoObjeto",
        "uriProposicaoObjeto",
        "tipoVotacao",
        mode="before",
    )
    @classmethod
    def clean_strings(cls, v: Any) -> str | None:
        return sanitize_text(v)

    @field_validator(
        "idOrgaoCamara", "idEventoCamara", "idProposicaoCamara", mode="before"
    )
    @classmethod
    def clean_ints(cls, v: Any) -> int | None:
        return parse_flexible_int(v)

    @field_validator("data", mode="before")
    @classmethod
    def clean_dates(cls, v: Any) -> date | None:
        return parse_flexible_date(v)

    @field_validator("dataHoraRegistro", mode="before")
    @classmethod
    def clean_datetimes(cls, v: Any) -> datetime | None:
        return parse_flexible_datetime(v)

    @field_validator("aprovacao", mode="before")
    @classmethod
    def clean_booleans(cls, v: Any) -> bool | None:
        if v is None:
            return None
        if isinstance(v, bool):
            return v
        s = str(v).strip().lower()
        if s in ("1", "true", "sim"):
            return True
        if s in ("0", "false", "não", "nao"):
            return False
        return None


class VotacaoVotoSchema(BaseCamaraSchema):
    """Validação de Votos individuais de deputados em votações."""

    idVotacaoCamara: str
    idDeputadoCamara: int
    voto: str
    dataRegistroVoto: datetime | None = None
    siglaPartido: str | None = None
    siglaUf: str | None = Field(None, max_length=2)

    @field_validator(
        "idVotacaoCamara", "voto", "siglaPartido", "siglaUf", mode="before"
    )
    @classmethod
    def clean_strings(cls, v: Any) -> str | None:
        return sanitize_text(v)

    @field_validator("idDeputadoCamara", mode="before")
    @classmethod
    def clean_ints(cls, v: Any) -> int | None:
        return parse_flexible_int(v)

    @field_validator("dataRegistroVoto", mode="before")
    @classmethod
    def clean_datetimes(cls, v: Any) -> datetime | None:
        return parse_flexible_datetime(v)


class DespesaCamaraSchema(BaseCamaraSchema):
    """Validação de dados de Cotas Parlamentares (CEAP / Despesas)."""

    codDocumento: str
    idDeputadoCamara: int
    ano: int
    mes: int
    tipoDespesa: str | None = None
    codTipoDocumento: int | None = None
    dataDocumento: datetime | None = None
    numDocumento: str | None = None
    valorDocumento: float | None = None
    valorGlosa: float | None = None
    valorLiquido: float | None = None
    nomeFornecedor: str | None = None
    cnpjCpfFornecedor: str | None = None
    parcela: int | None = None
    numSubCota: int | None = None
    numEspecificacaoSubCota: int | None = None
    codLote: int | None = None
    numRessarcimento: str | None = None
    urlDocumento: str | None = None

    @field_validator(
        "codDocumento",
        "tipoDespesa",
        "numDocumento",
        "nomeFornecedor",
        "cnpjCpfFornecedor",
        "numRessarcimento",
        "urlDocumento",
        mode="before",
    )
    @classmethod
    def clean_strings(cls, v: Any) -> str | None:
        return sanitize_text(v)

    @field_validator(
        "idDeputadoCamara",
        "ano",
        "mes",
        "codTipoDocumento",
        "parcela",
        "numSubCota",
        "numEspecificacaoSubCota",
        "codLote",
        mode="before",
    )
    @classmethod
    def clean_ints(cls, v: Any) -> int | None:
        return parse_flexible_int(v)

    @field_validator("valorDocumento", "valorGlosa", "valorLiquido", mode="before")
    @classmethod
    def clean_floats(cls, v: Any) -> float | None:
        return parse_flexible_float(v)

    @field_validator("dataDocumento", mode="before")
    @classmethod
    def clean_datetimes(cls, v: Any) -> datetime | None:
        return parse_flexible_datetime(v)


class OrgaoCamaraSchema(BaseCamaraSchema):
    """Validação de dados de Órgãos e Comissões."""

    idCamara: int
    uri: str | None = None
    sigla: str | None = None
    apelido: str | None = None
    nome: str | None = None
    nomePublicacao: str | None = None
    codTipoOrgao: int | None = None
    tipoOrgao: str | None = None
    dataInicio: date | None = None
    dataInstalacao: date | None = None
    dataFim: date | None = None
    dataFimOriginal: date | None = None
    codSituacao: int | None = None
    descricaoSituacao: str | None = None
    casa: str | None = None
    sala: str | None = None
    urlWebsite: str | None = None

    @field_validator(
        "sigla",
        "apelido",
        "nome",
        "nomePublicacao",
        "tipoOrgao",
        "descricaoSituacao",
        "casa",
        "sala",
        "urlWebsite",
        mode="before",
    )
    @classmethod
    def clean_strings(cls, v: Any) -> str | None:
        return sanitize_text(v)

    @field_validator("idCamara", "codTipoOrgao", "codSituacao", mode="before")
    @classmethod
    def clean_ints(cls, v: Any) -> int | None:
        return parse_flexible_int(v)

    @field_validator(
        "dataInicio", "dataInstalacao", "dataFim", "dataFimOriginal", mode="before"
    )
    @classmethod
    def clean_dates(cls, v: Any) -> date | None:
        return parse_flexible_date(v)


class EventoCamaraSchema(BaseCamaraSchema):
    """Validação de dados de Eventos e Sessões."""

    idCamara: int
    uri: str | None = None
    dataHoraInicio: datetime | None = None
    dataHoraFim: datetime | None = None
    situacao: str | None = None
    descricaoTipo: str | None = None
    descricao: str | None = None
    localExterno: str | None = None
    localCamaraPredio: str | None = None
    localCamaraSala: str | None = None
    localCamaraAndar: str | None = None
    localCamaraNome: str | None = None
    urlRegistro: str | None = None

    @field_validator(
        "situacao",
        "descricaoTipo",
        "descricao",
        "localExterno",
        "localCamaraPredio",
        "localCamaraSala",
        "localCamaraAndar",
        "localCamaraNome",
        "urlRegistro",
        mode="before",
    )
    @classmethod
    def clean_strings(cls, v: Any) -> str | None:
        return sanitize_text(v)

    @field_validator("idCamara", mode="before")
    @classmethod
    def clean_ints(cls, v: Any) -> int | None:
        return parse_flexible_int(v)

    @field_validator("dataHoraInicio", "dataHoraFim", mode="before")
    @classmethod
    def clean_datetimes(cls, v: Any) -> datetime | None:
        return parse_flexible_datetime(v)


class PartidoCamaraSchema(BaseCamaraSchema):
    """Validação estrita de dados cadastrais de Partidos Políticos."""

    idCamara: int
    sigla: str
    nome: str
    uri: str | None = None
    numeroEleitoral: int | None = None
    situacao: str | None = None
    totalMembros: int | None = None
    totalPosse: int | None = None
    urlLogo: str | None = None
    urlWebsite: str | None = None
    urlFacebook: str | None = None

    @field_validator(
        "sigla",
        "nome",
        "uri",
        "situacao",
        "urlLogo",
        "urlWebsite",
        "urlFacebook",
        mode="before",
    )
    @classmethod
    def clean_strings(cls, v: Any) -> str | None:
        return sanitize_text(v)

    @field_validator(
        "idCamara", "numeroEleitoral", "totalMembros", "totalPosse", mode="before"
    )
    @classmethod
    def clean_ints(cls, v: Any) -> int | None:
        return parse_flexible_int(v)


class TramitacaoCamaraSchema(BaseCamaraSchema):
    """Validação de passos de tramitação legislativa de proposições."""

    idProposicaoCamara: int
    sequencia: int
    dataHora: datetime
    siglaOrgao: str | None = None
    uriOrgao: str | None = None
    uriUltimoRelator: str | None = None
    regime: str | None = None
    descricaoTramitacao: str | None = None
    codTipoTramitacao: int | None = None
    descricaoSituacao: str | None = None
    codSituacao: int | None = None
    despacho: str | None = None
    url: str | None = None
    ambito: str | None = None
    apreciacao: str | None = None

    @field_validator(
        "siglaOrgao",
        "uriOrgao",
        "uriUltimoRelator",
        "regime",
        "descricaoTramitacao",
        "descricaoSituacao",
        "despacho",
        "url",
        "ambito",
        "apreciacao",
        mode="before",
    )
    @classmethod
    def clean_strings(cls, v: Any) -> str | None:
        return sanitize_text(v)

    @field_validator(
        "idProposicaoCamara",
        "sequencia",
        "codTipoTramitacao",
        "codSituacao",
        mode="before",
    )
    @classmethod
    def clean_ints(cls, v: Any) -> int | None:
        return parse_flexible_int(v)

    @field_validator("dataHora", mode="before")
    @classmethod
    def clean_datetimes(cls, v: Any) -> datetime | None:
        return parse_flexible_datetime(v)


class DeputadoHistoricoSchema(BaseCamaraSchema):
    """Validação de histórico de mandatos, suplências e licenças de deputados."""

    idDeputadoCamara: int
    idLegislatura: int | None = None
    dataInicio: datetime
    dataFim: datetime | None = None
    nome: str | None = None
    siglaPartido: str | None = None
    siglaUF: str | None = None
    idPartido: int | None = None
    condicao: str | None = None
    situacao: str | None = None
    descricao: str | None = None

    @field_validator(
        "nome",
        "siglaPartido",
        "siglaUF",
        "condicao",
        "situacao",
        "descricao",
        mode="before",
    )
    @classmethod
    def clean_strings(cls, v: Any) -> str | None:
        return sanitize_text(v)

    @field_validator("idDeputadoCamara", "idLegislatura", "idPartido", mode="before")
    @classmethod
    def clean_ints(cls, v: Any) -> int | None:
        return parse_flexible_int(v)

    @field_validator("dataInicio", "dataFim", mode="before")
    @classmethod
    def clean_datetimes(cls, v: Any) -> datetime | None:
        return parse_flexible_datetime(v)


class DeputadoMandatoExternoSchema(BaseCamaraSchema):
    """Validação de mandatos externos (cargos anteriores fora da Câmara)."""

    idDeputadoCamara: int
    cargo: str
    siglaUF: str | None = None
    municipio: str | None = None
    anoInicio: int | None = None
    anoFim: int | None = None
    siglaPartidoEleicao: str | None = None
    uriPartidoEleicao: str | None = None

    @field_validator(
        "cargo",
        "siglaUF",
        "municipio",
        "siglaPartidoEleicao",
        "uriPartidoEleicao",
        mode="before",
    )
    @classmethod
    def clean_strings(cls, v: Any) -> str | None:
        return sanitize_text(v)

    @field_validator("idDeputadoCamara", "anoInicio", "anoFim", mode="before")
    @classmethod
    def clean_ints(cls, v: Any) -> int | None:
        return parse_flexible_int(v)


class DiscursoCamaraSchema(BaseCamaraSchema):
    """Validação e sanitização de pronunciamentos e discursos de tribuna."""

    idDeputadoCamara: int
    dataHoraInicio: datetime
    dataHoraFim: datetime | None = None
    tipoDiscurso: str | None = None
    faseEventoTitulo: str | None = None
    sumario: str | None = None
    transcricao: str | None = None
    keywords: str | None = None
    urlTexto: str | None = None
    urlAudio: str | None = None
    urlVideo: str | None = None

    @model_validator(mode="before")
    @classmethod
    def extrair_fase_evento(cls, values: Any) -> Any:
        if isinstance(values, dict):
            fase = values.get("faseEvento")
            if isinstance(fase, dict) and "titulo" in fase:
                values.setdefault("faseEventoTitulo", fase.get("titulo"))
            elif isinstance(fase, str) and not values.get("faseEventoTitulo"):
                values["faseEventoTitulo"] = fase
        return values

    @field_validator(
        "tipoDiscurso",
        "faseEventoTitulo",
        "sumario",
        "transcricao",
        "keywords",
        "urlTexto",
        "urlAudio",
        "urlVideo",
        mode="before",
    )
    @classmethod
    def clean_strings(cls, v: Any) -> str | None:
        return sanitize_text(v)

    @field_validator("idDeputadoCamara", mode="before")
    @classmethod
    def clean_ints(cls, v: Any) -> int | None:
        return parse_flexible_int(v)

    @field_validator("dataHoraInicio", "dataHoraFim", mode="before")
    @classmethod
    def clean_datetimes(cls, v: Any) -> datetime | None:
        return parse_flexible_datetime(v)
