"""
test_etl_validators.py
======================
Testes unitários para sanitização, normalização e validação dos schemas Pydantic V2
da esteira de dados da Câmara dos Deputados (SPEC-006).
"""

from datetime import date, datetime

from injest_banco.schemas_camara import (
    DeputadoCamaraSchema,
    DeputadoHistoricoSchema,
    DeputadoMandatoExternoSchema,
    DespesaCamaraSchema,
    EventoCamaraSchema,
    OrgaoCamaraSchema,
    PartidoCamaraSchema,
    ProposicaoCamaraSchema,
    TramitacaoCamaraSchema,
    VotacaoCamaraSchema,
    VotacaoVotoSchema,
    parse_flexible_date,
    parse_flexible_datetime,
    parse_flexible_float,
    parse_flexible_int,
    sanitize_text,
)


class TestDataSanitization:
    def test_sanitize_text_null_bytes_and_spaces(self):
        assert sanitize_text("  Teste\x00 com null byte  ") == "Teste com null byte"
        assert sanitize_text(' "Texto Entre Aspas" ') == "Texto Entre Aspas"
        assert sanitize_text('""Aspas Duplas""') == '"Aspas Duplas"'

    def test_sanitize_text_empty_and_nan(self):
        assert sanitize_text("") is None
        assert sanitize_text("   ") is None
        assert sanitize_text("nan") is None
        assert sanitize_text("NaN") is None
        assert sanitize_text("None") is None
        assert sanitize_text("null") is None
        assert sanitize_text(None) is None

    def test_parse_flexible_date(self):
        assert parse_flexible_date("2026-03-15") == date(2026, 3, 15)
        assert parse_flexible_date("2026-03-15T14:30:00") == date(2026, 3, 15)
        assert parse_flexible_date(date(2026, 3, 15)) == date(2026, 3, 15)
        assert parse_flexible_date(datetime(2026, 3, 15, 10, 0)) == date(2026, 3, 15)
        # Anos espúrios
        assert parse_flexible_date("0001-01-01") is None
        assert parse_flexible_date("3500-01-01") is None
        assert parse_flexible_date("data_invalida") is None

    def test_parse_flexible_datetime(self):
        dt = parse_flexible_datetime("2026-03-15T10:30:00Z")
        assert dt is not None
        assert dt.year == 2026 and dt.month == 3 and dt.day == 15
        assert dt.hour == 10 and dt.minute == 30

        dt_simple = parse_flexible_datetime("2026-03-15")
        assert dt_simple == datetime(2026, 3, 15, 0, 0)
        assert parse_flexible_datetime(None) is None
        assert parse_flexible_datetime("invalido") is None

    def test_parse_flexible_float(self):
        assert parse_flexible_float("1.234,56") == 1234.56
        assert parse_flexible_float("1234.56") == 1234.56
        assert parse_flexible_float("R$ 500,75") == 500.75
        assert parse_flexible_float(100) == 100.0
        assert parse_flexible_float(None) is None

    def test_parse_flexible_int(self):
        assert parse_flexible_int("123") == 123
        assert parse_flexible_int("123.0") == 123
        assert parse_flexible_int(456) == 456
        assert parse_flexible_int(None) is None
        assert parse_flexible_int("abc") is None


class TestSchemasValidation:
    def test_proposicao_schema_valid(self):
        data = {
            "idCamara": "2485383",
            "uri": "https://dadosabertos.camara.leg.br/api/v2/proposicoes/2485383",
            "siglaTipo": "PL",
            "numero": "1234",
            "ano": "2026",
            "ementa": "  Dispõe sobre transparência pública.\x00 ",
            "dataApresentacao": "2026-02-01T10:00:00",
            "dataUltimaTramitacao": "2026-02-15T15:00:00",
        }
        prop = ProposicaoCamaraSchema.model_validate(data)
        assert prop.idCamara == 2485383
        assert prop.numero == 1234
        assert prop.ano == 2026
        assert prop.ementa == "Dispõe sobre transparência pública."
        assert prop.dataApresentacao == datetime(2026, 2, 1, 10, 0)
        assert prop.dataUltimaTramitacao == datetime(2026, 2, 15, 15, 0)

    def test_proposicao_coherence_adjustment(self):
        """Valida que se tramitação for anterior à apresentação, ajusta para não ficar incoerente."""
        data = {
            "idCamara": 10,
            "siglaTipo": "PL",
            "numero": 100,
            "ano": 2026,
            "dataApresentacao": "2026-05-10T10:00:00",
            "dataUltimaTramitacao": "2026-01-01T10:00:00",  # Incoerente (anterior)
        }
        prop = ProposicaoCamaraSchema.model_validate(data)
        assert prop.dataUltimaTramitacao == prop.dataApresentacao

    def test_deputado_schema_valid(self):
        data = {
            "idCamara": "220593",
            "nome": " Deputado Exemplo ",
            "siglaUf": "SP",
            "siglaPartido": "PARTIDO",
            "dataNascimento": "1980-05-20",
            "urlFoto": "https://imagem.camara.leg.br/foto.jpg",
            "emailGabinete": "dep.exemplo@camara.leg.br",
        }
        dep = DeputadoCamaraSchema.model_validate(data)
        assert dep.idCamara == 220593
        assert dep.nome == "Deputado Exemplo"
        assert dep.siglaUf == "SP"
        assert dep.dataNascimento == date(1980, 5, 20)

    def test_votacao_schema_and_voto(self):
        data_vot = {
            "idCamara": "2485383-7",
            "data": "2026-03-10",
            "dataHoraRegistro": "2026-03-10T16:45:00",
            "aprovacao": "1",
            "descricao": "Votação do PL 1234/2026",
        }
        vot = VotacaoCamaraSchema.model_validate(data_vot)
        assert vot.idCamara == "2485383-7"
        assert vot.aprovacao is True

        data_voto = {
            "idVotacaoCamara": "2485383-7",
            "idDeputadoCamara": "220593",
            "voto": "Sim",
            "dataRegistroVoto": "2026-03-10T16:45:10",
            "siglaPartido": "PARTIDO",
            "siglaUf": "SP",
        }
        voto = VotacaoVotoSchema.model_validate(data_voto)
        assert voto.idDeputadoCamara == 220593
        assert voto.voto == "Sim"

    def test_despesa_schema_valid(self):
        data = {
            "codDocumento": "DOC123456",
            "idDeputadoCamara": "220593",
            "ano": "2026",
            "mes": "2",
            "tipoDespesa": "COMBUSTÍVEIS E LUBRIFICANTES",
            "valorDocumento": "150,50",
            "valorLiquido": "150,50",
            "nomeFornecedor": "POSTO DE GASOLINA LTDA",
            "cnpjCpfFornecedor": "00.000.000/0001-00",
        }
        desp = DespesaCamaraSchema.model_validate(data)
        assert desp.codDocumento == "DOC123456"
        assert desp.valorLiquido == 150.50
        assert desp.ano == 2026
        assert desp.mes == 2

    def test_orgao_and_evento_schemas(self):
        orgao_data = {
            "idCamara": 180,
            "sigla": "CCJC",
            "nome": "Comissão de Constituição e Justiça e de Cidadania",
            "tipoOrgao": "Comissão Permanente",
            "dataInicio": "2023-03-15",
        }
        orgao = OrgaoCamaraSchema.model_validate(orgao_data)
        assert orgao.idCamara == 180
        assert orgao.sigla == "CCJC"
        assert orgao.dataInicio == date(2023, 3, 15)

        evento_data = {
            "idCamara": 70000,
            "dataHoraInicio": "2026-03-20T14:00:00",
            "situacao": "Encerrada",
            "descricaoTipo": "Reunião Deliberativa",
        }
        ev = EventoCamaraSchema.model_validate(evento_data)
        assert ev.idCamara == 70000
        assert ev.situacao == "Encerrada"
        assert ev.dataHoraInicio == datetime(2026, 3, 20, 14, 0)

    def test_partido_schema(self):
        data = {
            "idCamara": "36829",
            "sigla": " PRTB ",
            "nome": " Partido Renovador Trabalhista Brasileiro \x00",
            "uri": "https://dadosabertos.camara.leg.br/api/v2/partidos/36829",
            "numeroEleitoral": "28",
            "situacao": "Ativo",
        }
        p = PartidoCamaraSchema.model_validate(data)
        assert p.idCamara == 36829
        assert p.sigla == "PRTB"
        assert p.nome == "Partido Renovador Trabalhista Brasileiro"
        assert p.numeroEleitoral == 28

    def test_tramitacao_schema(self):
        data = {
            "idProposicaoCamara": "2485383",
            "sequencia": "15",
            "dataHora": "2026-03-12T10:30:00",
            "siglaOrgao": "CCJC",
            "regime": "Ordinária",
            "descricaoTramitacao": "Aprovação de Parecer",
            "codSituacao": "923",
        }
        tram = TramitacaoCamaraSchema.model_validate(data)
        assert tram.idProposicaoCamara == 2485383
        assert tram.sequencia == 15
        assert tram.dataHora == datetime(2026, 3, 12, 10, 30)
        assert tram.siglaOrgao == "CCJC"
        assert tram.codSituacao == 923

    def test_deputado_historico_schema(self):
        data = {
            "idDeputadoCamara": "178387",
            "idLegislatura": "57",
            "dataInicio": "2023-02-01T00:00:00",
            "siglaPartido": "PT",
            "siglaUF": "SC",
            "condicao": "Titular",
            "situacao": "Exercício",
            "descricao": "Posse no mandato",
        }
        hist = DeputadoHistoricoSchema.model_validate(data)
        assert hist.idDeputadoCamara == 178387
        assert hist.idLegislatura == 57
        assert hist.siglaPartido == "PT"
        assert hist.condicao == "Titular"

    def test_deputado_mandato_externo_schema(self):
        data = {
            "idDeputadoCamara": "73827",
            "cargo": "Prefeito(a)",
            "siglaUF": "TO",
            "municipio": "Araguaína",
            "anoInicio": "1983",
            "anoFim": "1987",
            "siglaPartidoEleicao": "PMDB",
        }
        mand = DeputadoMandatoExternoSchema.model_validate(data)
        assert mand.idDeputadoCamara == 73827
        assert mand.cargo == "Prefeito(a)"
        assert mand.anoInicio == 1983
        assert mand.siglaPartidoEleicao == "PMDB"
