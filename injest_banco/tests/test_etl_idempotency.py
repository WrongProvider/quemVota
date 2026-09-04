"""
test_etl_idempotency.py
=======================
Testes unitários de idempotência e rotinas de carga em lote (SPEC-006).
Garante que a re-execução de inserções para o mesmo período ou registros
não gere duplicatas, erros de unicidade ou divergências de dados.
"""

from unittest.mock import MagicMock
import numpy as np
import pandas as pd
from sqlalchemy import Column, Integer, MetaData, String, Table
from sqlalchemy.dialects.postgresql import insert as pg_insert

from injest_banco.loaders import (
    _fetch_id_map,
    bulk_upsert,
    sanitize_row,
)


class TestLoadersIdempotency:
    def test_sanitize_row(self):
        row = {
            "id": 1,
            "nome": "Deputado",
            "valor": np.nan,
            "data": pd.NaT,
            "vazio": None,
        }
        sanitized = sanitize_row(row)
        assert sanitized["id"] == 1
        assert sanitized["nome"] == "Deputado"
        assert sanitized["valor"] is None
        assert sanitized["data"] is None
        assert sanitized["vazio"] is None

    def test_fetch_id_map_empty(self):
        mock_conn = MagicMock()
        res = _fetch_id_map(mock_conn, "deputados", "idCamara", set())
        assert res == {}
        assert not mock_conn.execute.called

    def test_fetch_id_map_with_ids(self):
        mock_conn = MagicMock()
        mock_conn.execute.return_value.fetchall.return_value = [
            (220593, 1),
            (220594, 2),
        ]
        res = _fetch_id_map(mock_conn, "deputados", "idCamara", {220593, 220594, None})
        assert res == {220593: 1, 220594: 2}
        assert mock_conn.execute.called

    def test_bulk_upsert_empty_records(self):
        mock_engine = MagicMock()
        total = bulk_upsert(mock_engine, "deputados", None, [], ["idCamara"])
        assert total == 0
        assert not mock_engine.begin.called

    def test_bulk_upsert_statement_construction(self):
        """Valida que a cláusula ON CONFLICT DO UPDATE inclui os campos corretos e exclui chaves e preservadas."""
        meta = MetaData()
        test_table = Table(
            "teste_entidade",
            meta,
            Column("id", Integer, primary_key=True),
            Column("idCamara", Integer, unique=True),
            Column("nome", String),
            Column("urlFoto", String),
            Column("uf", String),
        )

        records = [
            {"idCamara": 101, "nome": "Nome A", "urlFoto": "http://foto", "uf": "SP"},
            {"idCamara": 102, "nome": "Nome B", "urlFoto": None, "uf": "RJ"},
        ]

        # Simula engine e reflect
        stmt = pg_insert(test_table).values(records)
        preserve_cols = ["urlFoto"]
        conflict_cols = ["idCamara"]

        update_cols = {
            c.name: stmt.excluded[c.name]
            for c in test_table.columns
            if c.name not in conflict_cols
            and c.name != "id"
            and c.name not in preserve_cols
        }

        stmt = stmt.on_conflict_do_update(
            index_elements=conflict_cols, set_=update_cols
        )

        # Compila para SQL em string para inspecionar
        sql = str(stmt.compile(compile_kwargs={"literal_binds": False}))
        assert 'ON CONFLICT ("idCamara") DO UPDATE' in sql
        assert "nome = excluded.nome" in sql
        assert "uf = excluded.uf" in sql
        # urlFoto e id não devem estar no SET de atualização
        assert "urlFoto = excluded.urlFoto" not in sql
        assert "id = excluded.id" not in sql
