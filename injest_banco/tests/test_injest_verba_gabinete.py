"""
test_injest_verba_gabinete.py — Testes unitários para o pipeline de Verba de Gabinete
"""

from decimal import Decimal
import pytest
from pydantic import ValidationError

from injest_banco.injest_verba_gabinete import (
    VerbaGabineteItem,
    parse_verba_table,
)


class TestVerbaGabineteSchema:
    def test_valid_item(self):
        item = VerbaGabineteItem(
            idDeputado=10,
            idCamara=160541,
            ano=2026,
            mes=3,
            valorDisponivel="R$ 165.806,07",
            valorGasto="141.788,09",
        )
        assert item.idDeputado == 10
        assert item.idCamara == 160541
        assert item.ano == 2026
        assert item.mes == 3
        assert item.valorDisponivel == Decimal("165806.07")
        assert item.valorGasto == Decimal("141788.09")

    def test_currency_parsing_edge_cases(self):
        item = VerbaGabineteItem(
            idDeputado=1,
            idCamara=100,
            ano=2024,
            mes=12,
            valorDisponivel="-",
            valorGasto="0,00",
        )
        assert item.valorDisponivel == Decimal("0.00")
        assert item.valorGasto == Decimal("0.00")

    def test_invalid_month_raises(self):
        with pytest.raises(ValidationError):
            VerbaGabineteItem(
                idDeputado=1,
                idCamara=100,
                ano=2024,
                mes=13,  # Invalid month
                valorDisponivel="1000.00",
                valorGasto="500.00",
            )

    def test_invalid_negative_amount_raises(self):
        with pytest.raises(ValidationError):
            VerbaGabineteItem(
                idDeputado=1,
                idCamara=100,
                ano=2024,
                mes=5,
                valorDisponivel="-100.00",
                valorGasto="0.00",
            )


class TestParseVerbaTable:
    def test_parse_valid_html_table(self):
        html = """
        <div class="container">
            <table class="table table-striped table-bordered">
                <thead>
                    <tr><th>Mês</th><th>Valor disponível (R$)</th><th>Valor gasto (R$)</th></tr>
                </thead>
                <tbody>
                    <tr><td>01</td><td>133.170,54</td><td>132.970,88</td></tr>
                    <tr><td>02</td><td>145.991,64</td><td>137.149,96</td></tr>
                    <tr><td>03</td><td>165.806,07</td><td>141.788,09</td></tr>
                </tbody>
            </table>
        </div>
        """
        items = parse_verba_table(html, id_deputado=42, id_camara=204554, ano=2026)
        assert len(items) == 3
        assert items[0].mes == 1
        assert items[0].valorDisponivel == Decimal("133170.54")
        assert items[0].valorGasto == Decimal("132970.88")
        assert items[1].mes == 2
        assert items[2].mes == 3

    def test_parse_html_without_table(self):
        html = "<html><body><p>Nenhum dado disponível para este ano.</p></body></html>"
        items = parse_verba_table(html, id_deputado=42, id_camara=204554, ano=2026)
        assert items == []

    def test_parse_html_with_malformed_rows(self):
        html = """
        <table class="table">
            <tr><td>Mês inválido</td><td>100,00</td></tr>
            <tr><td>Total</td><td>100,00</td><td>100,00</td></tr>
        </table>
        """
        items = parse_verba_table(html, id_deputado=42, id_camara=204554, ano=2026)
        assert items == []
