"""
reconciler.py
=============
Rotinas de reconciliação de integridade referencial e dados órfãos da Câmara.
Identifica e resolve:
  - Votações sem proposição vinculada (proposicao_id is None)
  - Votos ou eventos com registros pais faltantes
"""

from __future__ import annotations

import logging
from typing import Any, Optional

from sqlalchemy import text

from injest_banco.client import CamaraClient

log = logging.getLogger("etl_camara.reconciler")


def reconcile_orphan_votacoes(
    engine: Any,
    client: Optional[CamaraClient] = None,
    limit: Optional[int] = None,
) -> dict[str, int]:
    """
    Localiza votações com 'idProposicao' nulo e tenta buscar na API REST
    /votacoes/{id} o campo 'uriProposicaoObjeto' para vincular à proposição correspondente.
    """
    client = client or CamaraClient()
    stats = {"total_orfas": 0, "vinculadas": 0, "administrativas": 0, "erros": 0}

    with engine.begin() as conn:
        query_sql = 'SELECT id, "idCamara" FROM votacoes WHERE "idProposicao" IS NULL'
        if limit:
            query_sql += f" LIMIT {limit}"
        rows = conn.execute(text(query_sql)).fetchall()

    stats["total_orfas"] = len(rows)
    if not rows:
        log.info("✔ Nenhuma votação órfã encontrada no banco.")
        return stats

    log.info("🔍 Reconciliando %d votações órfãs...", len(rows))

    for row in rows:
        v_id, id_camara = row[0], row[1]
        try:
            detalhes = client.get_votacao_detalhes(str(id_camara))
            if not detalhes:
                stats["erros"] += 1
                continue

            uri_prop = detalhes.get("uriProposicaoObjeto")
            if not uri_prop:
                stats["administrativas"] += 1
                continue

            try:
                id_prop_camara = int(str(uri_prop).split("/")[-1])
            except (ValueError, IndexError):
                stats["erros"] += 1
                continue

            with engine.begin() as conn:
                prop_id = conn.execute(
                    text('SELECT id FROM proposicoes WHERE "idCamara" = :p LIMIT 1'),
                    {"p": id_prop_camara},
                ).scalar()

                if prop_id:
                    conn.execute(
                        text('UPDATE votacoes SET "idProposicao" = :p WHERE id = :v'),
                        {"p": prop_id, "v": v_id},
                    )
                    stats["vinculadas"] += 1
                else:
                    # Busca metadados da proposição na API se ausente
                    prop_detalhes = client.get_proposicao_detalhes(id_prop_camara)
                    if prop_detalhes:
                        # Insere a proposição básica para preservar FK
                        ins_sql = text(
                            'INSERT INTO proposicoes ("idCamara", uri, "siglaTipo", numero, ano, ementa) '
                            "VALUES (:id, :uri, :sigla, :num, :ano, :ementa) "
                            'ON CONFLICT ("idCamara") DO NOTHING RETURNING id'
                        )
                        new_prop_id = conn.execute(
                            ins_sql,
                            {
                                "id": id_prop_camara,
                                "uri": prop_detalhes.get("uri"),
                                "sigla": prop_detalhes.get("siglaTipo"),
                                "num": prop_detalhes.get("numero") or 0,
                                "ano": prop_detalhes.get("ano") or 0,
                                "ementa": prop_detalhes.get("ementa"),
                            },
                        ).scalar()
                        if new_prop_id:
                            conn.execute(
                                text(
                                    'UPDATE votacoes SET "idProposicao" = :p WHERE id = :v'
                                ),
                                {"p": new_prop_id, "v": v_id},
                            )
                            stats["vinculadas"] += 1

        except Exception as exc:
            log.warning("Erro ao reconciliar votação %s: %s", id_camara, exc)
            stats["erros"] += 1

    log.info(
        "🏁 Reconciliação concluída: %d vinculadas | %d administrativas | %d erros",
        stats["vinculadas"],
        stats["administrativas"],
        stats["erros"],
    )
    return stats
