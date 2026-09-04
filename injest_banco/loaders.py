"""
loaders.py
==========
Módulo de persistência e carga em lote (Bulk Upsert) de alta performance
com SQLAlchemy Core para o banco de dados PostgreSQL.
Garante idempotência absoluta (ON CONFLICT) e resolução otimizada de chaves estrangeiras.
"""

from __future__ import annotations

import logging
from typing import Any, Optional

import pandas as pd
from sqlalchemy import MetaData, text
from sqlalchemy.dialects.postgresql import insert as pg_insert

log = logging.getLogger("etl_camara.loaders")

DEFAULT_CHUNK_SIZE = 1_000


def sanitize_row(row: dict[str, Any]) -> dict[str, Any]:
    """Sanitiza NaT/NaN para None compatível com psycopg2/asyncpg."""
    cleaned = {}
    for k, v in row.items():
        if v is None:
            cleaned[k] = None
        else:
            try:
                if pd.isna(v):
                    cleaned[k] = None
                    continue
            except (TypeError, ValueError):
                pass
            cleaned[k] = v
    return cleaned


def bulk_upsert(
    engine: Any,
    table_name: str,
    preserve_cols: Optional[list[str]],
    records: list[dict[str, Any]],
    conflict_cols: list[str],
    chunk_size: int = DEFAULT_CHUNK_SIZE,
) -> int:
    """
    Executa upsert em lote (chunked bulk upsert) via PostgreSQL ON CONFLICT DO UPDATE.
    Se não houver colunas para atualizar, executa ON CONFLICT DO NOTHING.
    """
    if not records:
        return 0

    meta = MetaData()
    meta.reflect(bind=engine, only=[table_name])
    table = meta.tables[table_name]
    _preserve = set(preserve_cols or [])
    total = 0

    for i in range(0, len(records), chunk_size):
        chunk = [sanitize_row(r) for r in records[i : i + chunk_size]]
        if not chunk:
            continue

        stmt = pg_insert(table).values(chunk)
        if conflict_cols:
            update_cols = {
                c.name: stmt.excluded[c.name]
                for c in table.columns
                if c.name not in conflict_cols
                and c.name != "id"
                and c.name not in _preserve
            }
            if update_cols:
                stmt = stmt.on_conflict_do_update(
                    index_elements=conflict_cols, set_=update_cols
                )
            else:
                stmt = stmt.on_conflict_do_nothing(index_elements=conflict_cols)
        else:
            stmt = stmt.on_conflict_do_nothing()

        with engine.begin() as conn:
            conn.execute(stmt)
        total += len(chunk)

    return total


def _fetch_id_map(
    conn: Any,
    table: str,
    camara_id_col: str,
    ids: set[Any],
) -> dict[Any, int]:
    """Busca mapa de idCamara -> id interno em lote."""
    if not ids:
        return {}
    valid_ids = [i for i in ids if i is not None]
    if not valid_ids:
        return {}

    id_map = {}
    chunk_size = 2_000
    for i in range(0, len(valid_ids), chunk_size):
        chunk = valid_ids[i : i + chunk_size]
        # Query parametrizada com ANY
        sql = text(
            f'SELECT "{camara_id_col}", id FROM "{table}" WHERE "{camara_id_col}" = ANY(:ids)'
        )
        rows = conn.execute(sql, {"ids": chunk}).fetchall()
        for r in rows:
            id_map[r[0]] = r[1]
    return id_map


def bulk_resolve_and_insert(
    engine: Any,
    raw_table: str,
    records: list[dict[str, Any]],
    chunk_size: int = DEFAULT_CHUNK_SIZE,
) -> int:
    """
    Resolve chaves estrangeiras (idCamara -> id interno) e insere nas tabelas definitivas
    em operações de lote de alta performance.
    """
    if not records:
        return 0

    inserted_count = 0

    with engine.begin() as conn:
        # ── deputadosOcupacoes ──────────────────────────────────────────────
        if raw_table == "_raw_deputadosOcupacoes":
            dep_camara_ids = {r.get("idDeputadoCamara") for r in records}
            dep_map = _fetch_id_map(conn, "deputados", "idCamara", dep_camara_ids)

            rows_to_insert = []
            for r in records:
                dep_id = dep_map.get(r.get("idDeputadoCamara"))
                if dep_id:
                    row = {k: v for k, v in r.items() if k != "idDeputadoCamara"}
                    row["idDeputado"] = dep_id
                    rows_to_insert.append(sanitize_row(row))

            meta = MetaData()
            meta.reflect(bind=engine, only=["deputadosOcupacoes"])
            tbl = meta.tables["deputadosOcupacoes"]
            for i in range(0, len(rows_to_insert), chunk_size):
                chunk = rows_to_insert[i : i + chunk_size]
                stmt = (
                    pg_insert(tbl)
                    .values(chunk)
                    .on_conflict_do_nothing(constraint="uq_deputado_ocupacao")
                )
                conn.execute(stmt)
                inserted_count += len(chunk)

        # ── deputadosProfissoes ─────────────────────────────────────────────
        elif raw_table == "_raw_deputadosProfissoes":
            dep_camara_ids = {r.get("idDeputadoCamara") for r in records}
            dep_map = _fetch_id_map(conn, "deputados", "idCamara", dep_camara_ids)

            rows_to_insert = []
            for r in records:
                dep_id = dep_map.get(r.get("idDeputadoCamara"))
                if dep_id:
                    row = {k: v for k, v in r.items() if k != "idDeputadoCamara"}
                    row["idDeputado"] = dep_id
                    rows_to_insert.append(sanitize_row(row))

            meta = MetaData()
            meta.reflect(bind=engine, only=["deputadosProfissoes"])
            tbl = meta.tables["deputadosProfissoes"]
            for i in range(0, len(rows_to_insert), chunk_size):
                chunk = rows_to_insert[i : i + chunk_size]
                stmt = pg_insert(tbl).values(chunk).on_conflict_do_nothing()
                conn.execute(stmt)
                inserted_count += len(chunk)

        # ── eventosOrgaos ───────────────────────────────────────────────────
        elif raw_table == "_raw_eventosOrgaos":
            ev_camara_ids = {r.get("idEventoCamara") for r in records}
            og_camara_ids = {r.get("idOrgaoCamara") for r in records}
            ev_map = _fetch_id_map(conn, "eventos", "idCamara", ev_camara_ids)
            og_map = _fetch_id_map(conn, "orgaos", "idCamara", og_camara_ids)

            rows_to_insert = []
            for r in records:
                ev_id = ev_map.get(r.get("idEventoCamara"))
                og_id = og_map.get(r.get("idOrgaoCamara"))
                if ev_id and og_id:
                    rows_to_insert.append({"idEvento": ev_id, "idOrgao": og_id})

            meta = MetaData()
            meta.reflect(bind=engine, only=["eventosOrgaos"])
            tbl = meta.tables["eventosOrgaos"]
            for i in range(0, len(rows_to_insert), chunk_size):
                chunk = rows_to_insert[i : i + chunk_size]
                stmt = pg_insert(tbl).values(chunk).on_conflict_do_nothing()
                conn.execute(stmt)
                inserted_count += len(chunk)

        # ── eventosRequerimentos ────────────────────────────────────────────
        elif raw_table == "_raw_eventosRequerimentos":
            ev_camara_ids = {r.get("idEventoCamara") for r in records}
            ev_map = _fetch_id_map(conn, "eventos", "idCamara", ev_camara_ids)

            rows_to_insert = []
            for r in records:
                ev_id = ev_map.get(r.get("idEventoCamara"))
                if ev_id:
                    rows_to_insert.append(
                        sanitize_row(
                            {
                                "idEvento": ev_id,
                                "tituloRequerimento": r.get("tituloRequerimento"),
                                "uriRequerimento": r.get("uriRequerimento"),
                            }
                        )
                    )

            meta = MetaData()
            meta.reflect(bind=engine, only=["eventosRequerimentos"])
            tbl = meta.tables["eventosRequerimentos"]
            for i in range(0, len(rows_to_insert), chunk_size):
                chunk = rows_to_insert[i : i + chunk_size]
                stmt = pg_insert(tbl).values(chunk).on_conflict_do_nothing()
                conn.execute(stmt)
                inserted_count += len(chunk)

        # ── eventosPresenca ─────────────────────────────────────────────────
        elif raw_table == "_raw_eventosPresenca":
            ev_camara_ids = {r.get("idEventoCamara") for r in records}
            dep_camara_ids = {r.get("idDeputadoCamara") for r in records}
            ev_map = _fetch_id_map(conn, "eventos", "idCamara", ev_camara_ids)
            dep_map = _fetch_id_map(conn, "deputados", "idCamara", dep_camara_ids)

            rows_to_insert = []
            for r in records:
                ev_id = ev_map.get(r.get("idEventoCamara"))
                dep_id = dep_map.get(r.get("idDeputadoCamara"))
                if ev_id and dep_id:
                    rows_to_insert.append(
                        sanitize_row(
                            {
                                "idEvento": ev_id,
                                "idDeputado": dep_id,
                                "dataHoraInicio": r.get("dataHoraInicio"),
                            }
                        )
                    )

            meta = MetaData()
            meta.reflect(bind=engine, only=["eventosPresencaDeputados"])
            tbl = meta.tables["eventosPresencaDeputados"]
            for i in range(0, len(rows_to_insert), chunk_size):
                chunk = rows_to_insert[i : i + chunk_size]
                stmt = pg_insert(tbl).values(chunk).on_conflict_do_nothing()
                conn.execute(stmt)
                inserted_count += len(chunk)

        # ── proposicoesAutores ──────────────────────────────────────────────
        elif raw_table == "_raw_proposicoesAutores":
            prop_camara_ids = {r.get("idProposicaoCamara") for r in records}
            dep_camara_ids = {r.get("idDeputadoCamara") for r in records}
            prop_map = _fetch_id_map(conn, "proposicoes", "idCamara", prop_camara_ids)
            dep_map = _fetch_id_map(conn, "deputados", "idCamara", dep_camara_ids)

            rows_to_insert = []
            for r in records:
                prop_id = prop_map.get(r.get("idProposicaoCamara"))
                dep_id = (
                    dep_map.get(r.get("idDeputadoCamara"))
                    if r.get("idDeputadoCamara")
                    else None
                )
                if prop_id:
                    row = {
                        k: v
                        for k, v in r.items()
                        if k not in ("idProposicaoCamara", "idDeputadoCamara")
                    }
                    row["idProposicao"] = prop_id
                    row["idDeputadoAutor"] = dep_id
                    rows_to_insert.append(sanitize_row(row))

            meta = MetaData()
            meta.reflect(bind=engine, only=["proposicoesAutores"])
            tbl = meta.tables["proposicoesAutores"]
            for i in range(0, len(rows_to_insert), chunk_size):
                chunk = rows_to_insert[i : i + chunk_size]
                stmt = pg_insert(tbl).values(chunk).on_conflict_do_nothing()
                conn.execute(stmt)
                inserted_count += len(chunk)

        # ── proposicoesTemas ────────────────────────────────────────────────
        elif raw_table == "_raw_proposicoesTemas":
            # Primeiro insere novos temas
            unique_temas = {
                (r.get("codTema"), r.get("tema"))
                for r in records
                if r.get("codTema") is not None
            }
            if unique_temas:
                meta = MetaData()
                meta.reflect(bind=engine, only=["temas", "proposicoesTemas"])
                tbl_temas = meta.tables["temas"]
                tbl_ptemas = meta.tables["proposicoesTemas"]

                temas_chunk = [{"codTema": c, "tema": t} for c, t in unique_temas]
                stmt_temas = (
                    pg_insert(tbl_temas)
                    .values(temas_chunk)
                    .on_conflict_do_nothing(index_elements=["codTema"])
                )
                conn.execute(stmt_temas)

                # Busca id dos temas e proposições
                prop_camara_ids = {r.get("idProposicaoCamara") for r in records}
                prop_map = _fetch_id_map(
                    conn, "proposicoes", "idCamara", prop_camara_ids
                )
                tema_map = _fetch_id_map(
                    conn, "temas", "codTema", {c for c, _ in unique_temas}
                )

                rows_to_insert = []
                for r in records:
                    p_id = prop_map.get(r.get("idProposicaoCamara"))
                    t_id = tema_map.get(r.get("codTema"))
                    if p_id and t_id:
                        rows_to_insert.append({"idProposicao": p_id, "idTema": t_id})

                for i in range(0, len(rows_to_insert), chunk_size):
                    chunk = rows_to_insert[i : i + chunk_size]
                    stmt = pg_insert(tbl_ptemas).values(chunk).on_conflict_do_nothing()
                    conn.execute(stmt)
                    inserted_count += len(chunk)

        # ── votacoes ────────────────────────────────────────────────────────
        elif raw_table == "_raw_votacoes":
            og_camara_ids = {r.get("idOrgaoCamara") for r in records}
            ev_camara_ids = {r.get("idEventoCamara") for r in records}
            prop_camara_ids = {r.get("idProposicaoCamara") for r in records}

            og_map = _fetch_id_map(conn, "orgaos", "idCamara", og_camara_ids)
            ev_map = _fetch_id_map(conn, "eventos", "idCamara", ev_camara_ids)
            prop_map = _fetch_id_map(conn, "proposicoes", "idCamara", prop_camara_ids)

            rows_to_insert = []
            for r in records:
                row = {
                    k: v
                    for k, v in r.items()
                    if k
                    not in ("idOrgaoCamara", "idEventoCamara", "idProposicaoCamara")
                }
                row["idOrgao"] = og_map.get(r.get("idOrgaoCamara"))
                row["idEvento"] = ev_map.get(r.get("idEventoCamara"))
                row["idProposicao"] = prop_map.get(r.get("idProposicaoCamara"))
                rows_to_insert.append(sanitize_row(row))

            meta = MetaData()
            meta.reflect(bind=engine, only=["votacoes"])
            tbl = meta.tables["votacoes"]
            for i in range(0, len(rows_to_insert), chunk_size):
                chunk = rows_to_insert[i : i + chunk_size]
                stmt = (
                    pg_insert(tbl)
                    .values(chunk)
                    .on_conflict_do_nothing(index_elements=["idCamara"])
                )
                conn.execute(stmt)
                inserted_count += len(chunk)

        # ── votacoesVotos ───────────────────────────────────────────────────
        elif raw_table == "_raw_votacoesVotos":
            vot_camara_ids = {r.get("idVotacaoCamara") for r in records}
            dep_camara_ids = {r.get("idDeputadoCamara") for r in records}
            vot_map = _fetch_id_map(conn, "votacoes", "idCamara", vot_camara_ids)
            dep_map = _fetch_id_map(conn, "deputados", "idCamara", dep_camara_ids)

            rows_to_insert = []
            for r in records:
                vot_id = vot_map.get(r.get("idVotacaoCamara"))
                dep_id = dep_map.get(r.get("idDeputadoCamara"))
                if vot_id and dep_id:
                    row = {
                        k: v
                        for k, v in r.items()
                        if k not in ("idVotacaoCamara", "idDeputadoCamara")
                    }
                    row["idVotacao"] = vot_id
                    row["idDeputado"] = dep_id
                    rows_to_insert.append(sanitize_row(row))

            meta = MetaData()
            meta.reflect(bind=engine, only=["votacoesVotos"])
            tbl = meta.tables["votacoesVotos"]
            for i in range(0, len(rows_to_insert), chunk_size):
                chunk = rows_to_insert[i : i + chunk_size]
                stmt = (
                    pg_insert(tbl)
                    .values(chunk)
                    .on_conflict_do_nothing(constraint="uq_voto_votacao_deputado")
                )
                conn.execute(stmt)
                inserted_count += len(chunk)

        # ── votacoesOrientacoes ─────────────────────────────────────────────
        elif raw_table == "_raw_votacoesOrientacoes":
            vot_camara_ids = {r.get("idVotacaoCamara") for r in records}
            vot_map = _fetch_id_map(conn, "votacoes", "idCamara", vot_camara_ids)

            rows_to_insert = []
            for r in records:
                vot_id = vot_map.get(r.get("idVotacaoCamara"))
                if vot_id:
                    rows_to_insert.append(
                        sanitize_row(
                            {
                                "idVotacao": vot_id,
                                "siglaOrgao": r.get("siglaOrgao"),
                                "siglaBancada": r.get("siglaBancada"),
                                "uriBancada": r.get("uriBancada"),
                                "orientacao": r.get("orientacao"),
                            }
                        )
                    )

            meta = MetaData()
            meta.reflect(bind=engine, only=["votacoesOrientacoes"])
            tbl = meta.tables["votacoesOrientacoes"]
            for i in range(0, len(rows_to_insert), chunk_size):
                chunk = rows_to_insert[i : i + chunk_size]
                stmt = pg_insert(tbl).values(chunk).on_conflict_do_nothing()
                conn.execute(stmt)
                inserted_count += len(chunk)

        # ── votacoesObjetos ─────────────────────────────────────────────────
        elif raw_table == "_raw_votacoesObjetos":
            vot_camara_ids = {r.get("idVotacaoCamara") for r in records}
            vot_map = _fetch_id_map(conn, "votacoes", "idCamara", vot_camara_ids)

            rows_to_insert = []
            for r in records:
                vot_id = vot_map.get(r.get("idVotacaoCamara"))
                if vot_id:
                    row = {k: v for k, v in r.items() if k != "idVotacaoCamara"}
                    row["idVotacao"] = vot_id
                    rows_to_insert.append(sanitize_row(row))

            meta = MetaData()
            meta.reflect(bind=engine, only=["votacoesObjetos"])
            tbl = meta.tables["votacoesObjetos"]
            for i in range(0, len(rows_to_insert), chunk_size):
                chunk = rows_to_insert[i : i + chunk_size]
                stmt = pg_insert(tbl).values(chunk).on_conflict_do_nothing()
                conn.execute(stmt)
                inserted_count += len(chunk)

        # ── licitacoes* ─────────────────────────────────────────────────────
        elif raw_table in (
            "_raw_licitacoesPedidos",
            "_raw_licitacoesPropostas",
            "_raw_licitacoesItens",
            "_raw_licitacoesContratos",
        ):
            target_table = raw_table.replace("_raw_", "")
            lic_ids = {r.get("idLicitacao") for r in records if r.get("idLicitacao")}
            lic_map = _fetch_id_map(conn, "licitacoes", "idLicitacao", lic_ids)

            rows_to_insert = []
            for r in records:
                lic_id = r.get("idLicitacao")
                if lic_id in lic_map:
                    rows_to_insert.append(sanitize_row(r))

            meta = MetaData()
            meta.reflect(bind=engine, only=[target_table])
            tbl = meta.tables[target_table]
            for i in range(0, len(rows_to_insert), chunk_size):
                chunk = rows_to_insert[i : i + chunk_size]
                stmt = pg_insert(tbl).values(chunk).on_conflict_do_nothing()
                conn.execute(stmt)
                inserted_count += len(chunk)

        # ── orgaosDeputados ─────────────────────────────────────────────────
        elif raw_table == "_raw_orgaosDeputados":
            og_camara_ids = {r.get("idOrgaoCamara") for r in records}
            dep_camara_ids = {r.get("idDeputadoCamara") for r in records}
            og_map = _fetch_id_map(conn, "orgaos", "idCamara", og_camara_ids)
            dep_map = _fetch_id_map(conn, "deputados", "idCamara", dep_camara_ids)

            rows_to_insert = []
            for r in records:
                og_id = og_map.get(r.get("idOrgaoCamara"))
                dep_id = (
                    dep_map.get(r.get("idDeputadoCamara"))
                    if r.get("idDeputadoCamara")
                    else None
                )
                if og_id:
                    row = {
                        k: v
                        for k, v in r.items()
                        if k not in ("idOrgaoCamara", "idDeputadoCamara")
                    }
                    row["idOrgao"] = og_id
                    row["idDeputado"] = dep_id
                    rows_to_insert.append(sanitize_row(row))

            meta = MetaData()
            meta.reflect(bind=engine, only=["orgaosDeputados"])
            tbl = meta.tables["orgaosDeputados"]
            for i in range(0, len(rows_to_insert), chunk_size):
                chunk = rows_to_insert[i : i + chunk_size]
                stmt = pg_insert(tbl).values(chunk).on_conflict_do_nothing()
                conn.execute(stmt)
                inserted_count += len(chunk)

        # ── frentes ─────────────────────────────────────────────────────────
        elif raw_table == "_raw_frentes":
            dep_camara_ids = {
                r.get("coordenador_idCamara")
                for r in records
                if r.get("coordenador_idCamara")
            }
            dep_map = _fetch_id_map(conn, "deputados", "idCamara", dep_camara_ids)

            rows_to_insert = []
            for r in records:
                row = {k: v for k, v in r.items() if k != "coordenador_idCamara"}
                row["coordenador_id"] = dep_map.get(r.get("coordenador_idCamara"))
                rows_to_insert.append(sanitize_row(row))

            meta = MetaData()
            meta.reflect(bind=engine, only=["frentes"])
            tbl = meta.tables["frentes"]
            for i in range(0, len(rows_to_insert), chunk_size):
                chunk = rows_to_insert[i : i + chunk_size]
                stmt = pg_insert(tbl).values(chunk)
                update_cols = {
                    c.name: stmt.excluded[c.name]
                    for c in tbl.columns
                    if c.name not in ("id", "idCamara")
                }
                stmt = stmt.on_conflict_do_update(
                    index_elements=["idCamara"], set_=update_cols
                )
                conn.execute(stmt)
                inserted_count += len(chunk)

        # ── frentesDeputados ────────────────────────────────────────────────
        elif raw_table == "_raw_frentesDeputados":
            fr_camara_ids = {r.get("idFrenteCamara") for r in records}
            dep_camara_ids = {r.get("idDeputadoCamara") for r in records}
            fr_map = _fetch_id_map(conn, "frentes", "idCamara", fr_camara_ids)
            dep_map = _fetch_id_map(conn, "deputados", "idCamara", dep_camara_ids)

            rows_to_insert = []
            for r in records:
                fr_id = fr_map.get(r.get("idFrenteCamara"))
                dep_id = (
                    dep_map.get(r.get("idDeputadoCamara"))
                    if r.get("idDeputadoCamara")
                    else None
                )
                if fr_id:
                    row = {
                        k: v
                        for k, v in r.items()
                        if k not in ("idFrenteCamara", "idDeputadoCamara")
                    }
                    row["idFrente"] = fr_id
                    row["idDeputado"] = dep_id
                    rows_to_insert.append(sanitize_row(row))

            meta = MetaData()
            meta.reflect(bind=engine, only=["frentesDeputados"])
            tbl = meta.tables["frentesDeputados"]
            for i in range(0, len(rows_to_insert), chunk_size):
                chunk = rows_to_insert[i : i + chunk_size]
                stmt = pg_insert(tbl).values(chunk).on_conflict_do_nothing()
                conn.execute(stmt)
                inserted_count += len(chunk)

        # ── gruposMembros ───────────────────────────────────────────────────
        elif raw_table == "_raw_gruposMembros":
            gr_camara_ids = {r.get("idGrupoCamara") for r in records}
            dep_camara_ids = {r.get("idDeputadoCamara") for r in records}
            gr_map = _fetch_id_map(conn, "grupos", "idCamara", gr_camara_ids)
            dep_map = _fetch_id_map(conn, "deputados", "idCamara", dep_camara_ids)

            rows_to_insert = []
            for r in records:
                gr_id = gr_map.get(r.get("idGrupoCamara"))
                dep_id = (
                    dep_map.get(r.get("idDeputadoCamara"))
                    if r.get("idDeputadoCamara")
                    else None
                )
                if gr_id:
                    row = {
                        k: v
                        for k, v in r.items()
                        if k not in ("idGrupoCamara", "idDeputadoCamara")
                    }
                    row["idGrupo"] = gr_id
                    row["idDeputado"] = dep_id
                    rows_to_insert.append(sanitize_row(row))

            meta = MetaData()
            meta.reflect(bind=engine, only=["gruposMembros"])
            tbl = meta.tables["gruposMembros"]
            for i in range(0, len(rows_to_insert), chunk_size):
                chunk = rows_to_insert[i : i + chunk_size]
                stmt = pg_insert(tbl).values(chunk).on_conflict_do_nothing()
                conn.execute(stmt)
                inserted_count += len(chunk)

        # ── gruposHistorico ─────────────────────────────────────────────────
        elif raw_table == "_raw_gruposHistorico":
            gr_camara_ids = {r.get("idGrupoCamara") for r in records}
            gr_map = _fetch_id_map(conn, "grupos", "idCamara", gr_camara_ids)

            rows_to_insert = []
            for r in records:
                gr_id = gr_map.get(r.get("idGrupoCamara"))
                if gr_id:
                    row = {k: v for k, v in r.items() if k != "idGrupoCamara"}
                    row["idGrupo"] = gr_id
                    rows_to_insert.append(sanitize_row(row))

            meta = MetaData()
            meta.reflect(bind=engine, only=["gruposHistorico"])
            tbl = meta.tables["gruposHistorico"]
            for i in range(0, len(rows_to_insert), chunk_size):
                chunk = rows_to_insert[i : i + chunk_size]
                stmt = pg_insert(tbl).values(chunk).on_conflict_do_nothing()
                conn.execute(stmt)
                inserted_count += len(chunk)

        # ── cotas (despesas) ────────────────────────────────────────────────
        elif raw_table == "_raw_cotas":
            dep_camara_ids = {
                r.get("idDeputadoCamara") for r in records if r.get("idDeputadoCamara")
            }
            dep_map = _fetch_id_map(conn, "deputados", "idCamara", dep_camara_ids)

            rows_to_insert = []
            for r in records:
                dep_id = dep_map.get(r.get("idDeputadoCamara"))
                if not dep_id or not r.get("codDocumento"):
                    continue
                row = {k: v for k, v in r.items() if k != "idDeputadoCamara"}
                row["idDeputado"] = dep_id
                rows_to_insert.append(sanitize_row(row))

            meta = MetaData()
            meta.reflect(bind=engine, only=["despesas"])
            tbl = meta.tables["despesas"]
            for i in range(0, len(rows_to_insert), chunk_size):
                chunk = rows_to_insert[i : i + chunk_size]
                stmt = pg_insert(tbl).values(chunk)
                update_cols = {
                    c.name: stmt.excluded[c.name]
                    for c in tbl.columns
                    if c.name not in ("id", "codDocumento")
                }
                stmt = stmt.on_conflict_do_update(
                    index_elements=["codDocumento"], set_=update_cols
                )
                conn.execute(stmt)
                inserted_count += len(chunk)

    return inserted_count
