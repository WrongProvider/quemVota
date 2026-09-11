"""
test_etl_camara_updates.py
==========================
Testes unitários para as correções do DAG etl_camara:
- Tratamento de 404 como dataset ignorado (_NOT_FOUND) em vez de erro
- Pulo de legislaturas históricas no modo incremental (--update)
- Filtro de legislaturas < 51 em orgaosDeputados
- Deduplicação de colunas para eliminar UserWarning do pandas
"""

from unittest.mock import MagicMock, patch

import pandas as pd

from injest_banco.catalog import Dataset, build_catalog
from injest_banco.client import _NOT_FOUND, CamaraClient
from injest_banco.etl_camara import (
    ANO_ATUAL,
    get_legislatura_atual,
    process_dataset,
    run_etl,
)
from injest_banco.transformers import clean_dataframe, keep_columns


class TestCamaraClient404:
    def test_download_csv_returns_not_found_on_404(self):
        client = CamaraClient(max_retries=1)
        mock_resp = MagicMock()
        mock_resp.status_code = 404
        with patch.object(client.session, "get", return_value=mock_resp):
            res = client.download_csv("http://example.com/test.csv")
            assert res is _NOT_FOUND

    def test_download_csv_zip_returns_not_found_on_404(self):
        client = CamaraClient(max_retries=1)
        mock_resp = MagicMock()
        mock_resp.status_code = 404
        with patch.object(client.session, "get", return_value=mock_resp):
            res = client.download_csv_zip("http://example.com/test.zip")
            assert res is _NOT_FOUND


class TestProcessDatasetAndSkipHistorical:
    def test_process_dataset_skips_historical_year(self):
        ds = Dataset(
            nome="votacoes_2020",
            url_fn=lambda: "http://example.com/votacoes-2020.csv",
            transform_fn=lambda df: [],
            table_name="votacoes",
            conflict_cols=["id"],
            ano_ref=2020,
        )
        client = MagicMock()
        _nome, status, count = process_dataset(
            ds, client, engine=None, skip_historical=True, dry_run=True
        )
        assert status == "skip_hist"
        assert count == 0
        assert not client.download_csv.called

    def test_process_dataset_skips_historical_legislatura(self):
        ds = Dataset(
            nome="orgaosDeputados_L56",
            url_fn=lambda: "http://example.com/orgaosDeputados-L56.csv",
            transform_fn=lambda df: [],
            table_name="orgaos_deputados",
            conflict_cols=["id"],
            leg_ref=56,
        )
        client = MagicMock()
        _nome, status, count = process_dataset(
            ds, client, engine=None, skip_historical=True, dry_run=True, leg_atual=57
        )
        assert status == "skip_hist"
        assert count == 0
        assert not client.download_csv.called

    def test_process_dataset_handles_404_gracefully(self):
        ds = Dataset(
            nome="orgaosDeputados_L50",
            url_fn=lambda: "http://example.com/orgaosDeputados-L50.csv",
            transform_fn=lambda df: [],
            table_name="orgaos_deputados",
            conflict_cols=["id"],
            leg_ref=50,
        )
        client = MagicMock()
        client.download_csv.return_value = _NOT_FOUND
        nome, status, count = process_dataset(
            ds, client, engine=None, skip_historical=False, dry_run=True, leg_atual=57
        )
        assert status == "404"
        assert count == 0
        assert nome == "orgaosDeputados_L50"


class TestRunEtl404NotError:
    def test_run_etl_does_not_fail_on_404(self):
        ds1 = Dataset(
            nome="dataset_ok",
            url_fn=lambda: "http://example.com/ok.csv",
            transform_fn=lambda df: [{"id": 1}],
            table_name="teste",
            conflict_cols=["id"],
            dep_group=0,
        )
        ds2 = Dataset(
            nome="dataset_missing_404",
            url_fn=lambda: "http://example.com/404.csv",
            transform_fn=lambda df: [],
            table_name="teste",
            conflict_cols=["id"],
            dep_group=0,
        )

        client = MagicMock()

        def mock_download(url):
            if "ok.csv" in url:
                return pd.DataFrame([{"id": 1}])
            return _NOT_FOUND

        client.download_csv.side_effect = mock_download

        erros = run_etl(
            [ds1, ds2],
            engine=None,
            client=client,
            dry_run=True,
            workers=1,
        )
        assert erros == [], "Datasets 404 não devem constar como erros"


class TestCatalogLegislaturasFilter:
    def test_build_catalog_filters_legislaturas_below_51(self):
        catalog = build_catalog(anos=[ANO_ATUAL], legislaturas=[1, 10, 50, 51, 56, 57])
        od_names = [
            ds.nome for ds in catalog if ds.nome.startswith("orgaosDeputados_L")
        ]
        assert "orgaosDeputados_L1" not in od_names
        assert "orgaosDeputados_L50" not in od_names
        assert "orgaosDeputados_L51" in od_names
        assert "orgaosDeputados_L56" in od_names
        assert "orgaosDeputados_L57" in od_names


class TestDataFrameDeduplication:
    def test_clean_dataframe_removes_duplicate_columns(self):
        # Cria DataFrame com colunas duplicadas
        df = pd.DataFrame([[1, 2, "texto "]], columns=["colA", "colA", "colB"])
        cleaned = clean_dataframe(df)
        assert not cleaned.columns.duplicated().any()
        assert list(cleaned.columns) == ["colA", "colB"]

    def test_keep_columns_no_warning_with_duplicate_columns(self):
        import warnings

        df = pd.DataFrame(
            [[1, 2, "texto"]],
            columns=["colA", "colA", "colB"],
        )
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            records = keep_columns(df, ["colA", "colB", "colA"])
        assert len(records) == 1
        assert records[0] == {"colA": 1, "colB": "texto"}
        # Não deve haver warnings emitidos pelo pandas sobre colunas não-únicas
        warnings_emitted = [
            w for w in caught if "DataFrame columns are not unique" in str(w.message)
        ]
        assert len(warnings_emitted) == 0


class TestLegislaturaAtual:
    def test_get_legislatura_atual_fallback(self):
        assert get_legislatura_atual(None) == 57

    def test_get_legislatura_atual_from_db(self):
        mock_engine = MagicMock()
        mock_conn = MagicMock()
        mock_engine.connect.return_value.__enter__.return_value = mock_conn
        mock_conn.execute.return_value.fetchone.return_value = (57,)
        assert get_legislatura_atual(mock_engine) == 57
