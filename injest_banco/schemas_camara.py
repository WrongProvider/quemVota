"""
schemas_camara.py
=================
Schemas Pydantic V2 para sanitização, normalização e validação estrita
dos dados da API e dos arquivos CSV da Câmara dos Deputados.
"""

from __future__ import annotations

from datetime import date, datetime
import math
import re
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


def sanitize_text(v: Any) -> Optional[str]:
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


def parse_flexible_date(v: Any) -> Optional[date]:
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
        if d.year < 1800 or d.year > datetime.now().year + 10:
            return None
        return d
    except ValueError:
        return None


def parse_flexible_datetime(v: Any) -> Optional[datetime]:
    """Converte strings ISO para objeto datetime."""
    if v is None:
        return None
    if isinstance(v, datetime):
        return v
    if isinstance(v, date):
        return datetime(v.year, v.month, v.day)
    s = sanitize_text(v)
    if not s:
        return None
    s = s.replace("Z", "+00:00")
    try:
        # Se for apenas YYYY-MM-DD
        if len(s) == 10:
            d = date.fromisoformat(s)
            return datetime(d.year, d.month, d.day)
        return datetime.fromisoformat(s)
    except ValueError:
        return None


def parse_flexible_float(v: Any) -> Optional[float]:
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


def parse_flexible_int(v: Any) -> Optional[int]:
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
    uri: Optional[str] = None
    nome: str
    siglaUf: Optional[str] = Field(None, max_length=2)
    siglaPartido: Optional[str] = None
    idLegislaturaInicial: Optional[int] = None
    idLegislaturaFinal: Optional[int] = None
    nomeCivil: Optional[str] = None
    cpf: Optional[str] = None
    siglaSexo: Optional[str] = Field(None, max_length=1)
    urlRedeSocial: Optional[str] = None
    urlWebsite: Optional[str] = None
    dataNascimento: Optional[date] = None
    dataFalecimento: Optional[date] = None
    ufNascimento: Optional[str] = Field(None, max_length=2)
    municipioNascimento: Optional[str] = None
    escolaridade: Optional[str] = None
    situacao: Optional[str] = None
    condicaoEleitoral: Optional[str] = None
    emailGabinete: Optional[str] = None
    telefoneGabinete: Optional[str] = None
    urlFoto: Optional[str] = None
    slug: Optional[str] = None

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
    def clean_strings(cls, v: Any) -> Optional[str]:
        return sanitize_text(v)

    @field_validator(
        "idCamara", "idLegislaturaInicial", "idLegislaturaFinal", mode="before"
    )
    @classmethod
    def clean_ints(cls, v: Any) -> Optional[int]:
        return parse_flexible_int(v)

    @field_validator("dataNascimento", "dataFalecimento", mode="before")
    @classmethod
    def clean_dates(cls, v: Any) -> Optional[date]:
        return parse_flexible_date(v)


class ProposicaoCamaraSchema(BaseCamaraSchema):
    """Validação de dados de Proposições."""

    idCamara: int
    uri: Optional[str] = None
    siglaTipo: str
    codTipo: Optional[int] = None
    numero: int
    ano: int
    descricaoTipo: Optional[str] = None
    ementa: Optional[str] = None
    ementaDetalhada: Optional[str] = None
    keywords: Optional[str] = None
    dataApresentacao: Optional[datetime] = None
    dataUltimaTramitacao: Optional[datetime] = None
    urlInteiroTeor: Optional[str] = None
    justificativa: Optional[str] = None

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
    def clean_strings(cls, v: Any) -> Optional[str]:
        return sanitize_text(v)

    @field_validator("idCamara", "codTipo", "numero", "ano", mode="before")
    @classmethod
    def clean_ints(cls, v: Any) -> Optional[int]:
        return parse_flexible_int(v)

    @field_validator("dataApresentacao", "dataUltimaTramitacao", mode="before")
    @classmethod
    def clean_datetimes(cls, v: Any) -> Optional[datetime]:
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
    uri: Optional[str] = None
    data: Optional[date] = None
    dataHoraRegistro: Optional[datetime] = None
    idOrgaoCamara: Optional[int] = None
    idEventoCamara: Optional[int] = None
    idProposicaoCamara: Optional[int] = None
    siglaOrgao: Optional[str] = None
    aprovacao: Optional[bool] = None
    descricao: Optional[str] = None
    proposicaoObjeto: Optional[str] = None
    uriProposicaoObjeto: Optional[str] = None
    tipoVotacao: Optional[str] = None

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
    def clean_strings(cls, v: Any) -> Optional[str]:
        return sanitize_text(v)

    @field_validator(
        "idOrgaoCamara", "idEventoCamara", "idProposicaoCamara", mode="before"
    )
    @classmethod
    def clean_ints(cls, v: Any) -> Optional[int]:
        return parse_flexible_int(v)

    @field_validator("data", mode="before")
    @classmethod
    def clean_dates(cls, v: Any) -> Optional[date]:
        return parse_flexible_date(v)

    @field_validator("dataHoraRegistro", mode="before")
    @classmethod
    def clean_datetimes(cls, v: Any) -> Optional[datetime]:
        return parse_flexible_datetime(v)

    @field_validator("aprovacao", mode="before")
    @classmethod
    def clean_booleans(cls, v: Any) -> Optional[bool]:
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
    dataRegistroVoto: Optional[datetime] = None
    siglaPartido: Optional[str] = None
    siglaUf: Optional[str] = Field(None, max_length=2)

    @field_validator(
        "idVotacaoCamara", "voto", "siglaPartido", "siglaUf", mode="before"
    )
    @classmethod
    def clean_strings(cls, v: Any) -> Optional[str]:
        return sanitize_text(v)

    @field_validator("idDeputadoCamara", mode="before")
    @classmethod
    def clean_ints(cls, v: Any) -> Optional[int]:
        return parse_flexible_int(v)

    @field_validator("dataRegistroVoto", mode="before")
    @classmethod
    def clean_datetimes(cls, v: Any) -> Optional[datetime]:
        return parse_flexible_datetime(v)


class DespesaCamaraSchema(BaseCamaraSchema):
    """Validação de dados de Cotas Parlamentares (CEAP / Despesas)."""

    codDocumento: str
    idDeputadoCamara: int
    ano: int
    mes: int
    tipoDespesa: Optional[str] = None
    codTipoDocumento: Optional[int] = None
    dataDocumento: Optional[datetime] = None
    numDocumento: Optional[str] = None
    valorDocumento: Optional[float] = None
    valorGlosa: Optional[float] = None
    valorLiquido: Optional[float] = None
    nomeFornecedor: Optional[str] = None
    cnpjCpfFornecedor: Optional[str] = None
    parcela: Optional[int] = None
    numSubCota: Optional[int] = None
    numEspecificacaoSubCota: Optional[int] = None
    codLote: Optional[int] = None
    numRessarcimento: Optional[str] = None
    urlDocumento: Optional[str] = None

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
    def clean_strings(cls, v: Any) -> Optional[str]:
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
    def clean_ints(cls, v: Any) -> Optional[int]:
        return parse_flexible_int(v)

    @field_validator("valorDocumento", "valorGlosa", "valorLiquido", mode="before")
    @classmethod
    def clean_floats(cls, v: Any) -> Optional[float]:
        return parse_flexible_float(v)

    @field_validator("dataDocumento", mode="before")
    @classmethod
    def clean_datetimes(cls, v: Any) -> Optional[datetime]:
        return parse_flexible_datetime(v)


class OrgaoCamaraSchema(BaseCamaraSchema):
    """Validação de dados de Órgãos e Comissões."""

    idCamara: int
    uri: Optional[str] = None
    sigla: Optional[str] = None
    apelido: Optional[str] = None
    nome: Optional[str] = None
    nomePublicacao: Optional[str] = None
    codTipoOrgao: Optional[int] = None
    tipoOrgao: Optional[str] = None
    dataInicio: Optional[date] = None
    dataInstalacao: Optional[date] = None
    dataFim: Optional[date] = None
    dataFimOriginal: Optional[date] = None
    codSituacao: Optional[int] = None
    descricaoSituacao: Optional[str] = None
    casa: Optional[str] = None
    sala: Optional[str] = None
    urlWebsite: Optional[str] = None

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
    def clean_strings(cls, v: Any) -> Optional[str]:
        return sanitize_text(v)

    @field_validator("idCamara", "codTipoOrgao", "codSituacao", mode="before")
    @classmethod
    def clean_ints(cls, v: Any) -> Optional[int]:
        return parse_flexible_int(v)

    @field_validator(
        "dataInicio", "dataInstalacao", "dataFim", "dataFimOriginal", mode="before"
    )
    @classmethod
    def clean_dates(cls, v: Any) -> Optional[date]:
        return parse_flexible_date(v)


class EventoCamaraSchema(BaseCamaraSchema):
    """Validação de dados de Eventos e Sessões."""

    idCamara: int
    uri: Optional[str] = None
    dataHoraInicio: Optional[datetime] = None
    dataHoraFim: Optional[datetime] = None
    situacao: Optional[str] = None
    descricaoTipo: Optional[str] = None
    descricao: Optional[str] = None
    localExterno: Optional[str] = None
    localCamaraPredio: Optional[str] = None
    localCamaraSala: Optional[str] = None
    localCamaraAndar: Optional[str] = None
    localCamaraNome: Optional[str] = None
    urlRegistro: Optional[str] = None

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
    def clean_strings(cls, v: Any) -> Optional[str]:
        return sanitize_text(v)

    @field_validator("idCamara", mode="before")
    @classmethod
    def clean_ints(cls, v: Any) -> Optional[int]:
        return parse_flexible_int(v)

    @field_validator("dataHoraInicio", "dataHoraFim", mode="before")
    @classmethod
    def clean_datetimes(cls, v: Any) -> Optional[datetime]:
        return parse_flexible_datetime(v)
