"""
graph.py — Módulo Apache AGE para Grafo de Conhecimento e Graph-RAG

Implementa o grafo de conhecimento no PostgreSQL utilizando Apache AGE, conectando:
- Politicos (Deputados) (:Politico)
- Votações (:Votacao)
- Proposições (:Proposicao)
- Temas (:Tema)

Arestas:
- (Politico)-[:VOTED_IN {voto: str}]->(Votacao)
- (Politico)-[:PROPOSED {proponente: bool}]->(Proposicao)
- (Proposicao)-[:BELONGS_TO_THEME]->(Tema)
- (Votacao)-[:REGARDING]->(Proposicao)
"""

import logging
from typing import Any, Dict, List, Optional
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from shared.models import Deputado, Proposicao, Tema, Votacao, ProposicaoAutor
from shared.vector_search import vector_knn_search

logger = logging.getLogger(__name__)

GRAPH_NAME = "quemvota_graph"

# Vertices (Labels)
LABEL_POLITICO = "Politico"
LABEL_VOTACAO = "Votacao"
LABEL_PROPOSICAO = "Proposicao"
LABEL_TEMA = "Tema"

# Edges (Relationships)
EDGE_VOTED_IN = "VOTED_IN"
EDGE_PROPOSED = "PROPOSED"
EDGE_BELONGS_TO_THEME = "BELONGS_TO_THEME"
EDGE_REGARDING = "REGARDING"


def init_age_extension(session: Session) -> bool:
    """
    Inicializa a extensão Apache AGE no PostgreSQL, ajusta o search_path e cria o grafo `quemvota_graph`.
    Retorna True se bem-sucedido.
    """
    try:
        session.execute(text("CREATE EXTENSION IF NOT EXISTS age;"))
        session.execute(text("LOAD 'age';"))
        session.execute(text('SET search_path = ag_catalog, "$user", public;'))

        # Verifica se o grafo já existe
        check_graph = session.execute(
            text("SELECT count(*) FROM ag_catalog.ag_graph WHERE name = :name"),
            {"name": GRAPH_NAME},
        ).scalar()

        if not check_graph:
            session.execute(
                text("SELECT ag_catalog.create_graph(:name)"),
                {"name": GRAPH_NAME},
            )
            logger.info(f"Grafo '{GRAPH_NAME}' criado com sucesso no Apache AGE.")
        session.commit()
        return True
    except Exception as e:
        session.rollback()
        logger.warning(
            f"Extensão ou Grafo Apache AGE não disponível / erro ao inicializar: {e}"
        )
        return False


def ensure_age_loaded(session: Session) -> None:
    """Garante que a extensão age está carregada na sessão do PostgreSQL."""
    try:
        conn = session.connection()
        conn.exec_driver_sql("LOAD 'age';")
        conn.exec_driver_sql('SET search_path = ag_catalog, "$user", public;')
    except Exception as e:
        logger.debug(f"Aviso ao carregar Apache AGE: {e}")


def execute_cypher(
    session: Session,
    cypher_query: str,
    columns_spec: str = "result agtype",
    params: Optional[Dict[str, Any]] = None,
) -> List[Any]:
    """
    Executa uma consulta Cypher sobre o grafo Apache AGE.
    Exemplo de chamada:
        execute_cypher(session, "MATCH (p:Politico) RETURN p.nome", "nome agtype")
    """
    ensure_age_loaded(session)
    sql = f"""
    SELECT * FROM ag_catalog.cypher('{GRAPH_NAME}', $$
        {cypher_query}
    $$) as ({columns_spec});
    """
    try:
        conn = session.connection()
        if params:
            res = conn.exec_driver_sql(sql, params)
        else:
            res = conn.exec_driver_sql(sql)
        return res.fetchall()
    except Exception as e:
        logger.error(f"Erro ao executar Cypher: {e}")
        raise


async def execute_cypher_async(
    session: AsyncSession,
    cypher_query: str,
    columns_spec: str = "result agtype",
    params: Optional[Dict[str, Any]] = None,
) -> List[Any]:
    """
    Executa uma consulta Cypher sobre o grafo Apache AGE de forma assíncrona (AsyncSession).
    """
    conn = await session.connection()
    await conn.exec_driver_sql("LOAD 'age';")
    await conn.exec_driver_sql("SET search_path = ag_catalog, public;")
    sql = f"""
    SELECT * FROM ag_catalog.cypher('{GRAPH_NAME}', $$
        {cypher_query}
    $$) as ({columns_spec});
    """
    try:
        if params:
            res = await conn.exec_driver_sql(sql, params)
        else:
            res = await conn.exec_driver_sql(sql)
        return res.fetchall()
    except Exception as e:
        logger.error(f"Erro ao executar Cypher async: {e}")
        raise


def sync_relational_to_graph(
    session: Session,
    batch_limit: Optional[int] = None,
    legislatura: Optional[int] = None,
    apenas_com_votacoes: bool = False,
) -> Dict[str, int]:
    """
    Sincroniza registros relacionais do PostgreSQL para o grafo Apache AGE.
    Cria vértices (:Politico), (:Votacao), (:Proposicao), (:Tema)
    e relacionamentos (:VOTED_IN), (:PROPOSED), (:BELONGS_TO_THEME), (:REGARDING).
    Permite filtrar por legislatura (ex: 57 para 2023-2027) para sincronização ágil.
    """
    ensure_age_loaded(session)
    counts = {"politicos": 0, "proposicoes": 0, "votacoes": 0, "temas": 0, "arestas": 0}

    # 1. Sincroniza Temas
    temas = session.query(Tema).all()
    for t in temas:
        cypher = f"""
        MERGE (tm:{LABEL_TEMA} {{id: {t.id}}})
        SET tm.codTema = {t.codTema or 0}, tm.tema = '{_escape(t.tema or "")}'
        """
        try:
            execute_cypher(session, cypher)
            counts["temas"] += 1
        except Exception:
            pass

    # 2. Sincroniza Deputados (Políticos)
    q_dep = session.query(Deputado)
    if legislatura:
        q_dep = q_dep.filter(Deputado.idLegislaturaFinal == legislatura)
    if batch_limit:
        q_dep = q_dep.limit(batch_limit)
    deputados = q_dep.all()
    dep_ids_set = {d.id for d in deputados}

    for d in deputados:
        cypher = f"""
        MERGE (p:{LABEL_POLITICO} {{id: {d.id}}})
        SET p.idCamara = {d.idCamara or 0},
            p.nome = '{_escape(d.nome or "")}',
            p.siglaPartido = '{_escape(d.siglaPartido or "")}',
            p.siglaUF = '{_escape(d.siglaUF or "")}',
            p.urlFoto = '{_escape(d.urlFoto or "")}'
        """
        try:
            execute_cypher(session, cypher)
            counts["politicos"] += 1
        except Exception:
            pass

    # 3. Sincroniza Proposições & Relação com Temas
    q_prop = session.query(Proposicao)
    if legislatura == 57:
        q_prop = q_prop.filter(Proposicao.ano >= 2023)
    elif legislatura == 56:
        q_prop = q_prop.filter(Proposicao.ano.between(2019, 2022))

    if apenas_com_votacoes:
        q_prop = q_prop.filter(Proposicao.votacoes.any())

    q_prop = q_prop.order_by(Proposicao.ano.desc().nullslast(), Proposicao.id.desc())

    if batch_limit:
        q_prop = q_prop.limit(batch_limit)
    proposicoes = q_prop.all()

    for pr in proposicoes:
        cypher_pr = f"""
        MERGE (p:{LABEL_PROPOSICAO} {{id: {pr.id}}})
        SET p.idCamara = {pr.idCamara or 0},
            p.siglaTipo = '{_escape(pr.siglaTipo or "")}',
            p.numero = {pr.numero or 0},
            p.ano = {pr.ano or 0},
            p.ementa = '{_escape((pr.ementa or "")[:200])}'
        """
        try:
            execute_cypher(session, cypher_pr)
            counts["proposicoes"] += 1
        except Exception:
            pass

        # Conecta a temas
        for tm in pr.temas:
            cypher_edge = f"""
            MATCH (p:{LABEL_PROPOSICAO} {{id: {pr.id}}}), (t:{LABEL_TEMA} {{id: {tm.id}}})
            MERGE (p)-[:{EDGE_BELONGS_TO_THEME}]->(t)
            """
            try:
                execute_cypher(session, cypher_edge)
                counts["arestas"] += 1
            except Exception:
                pass

    # 4. Sincroniza Autoria de Proposições (:PROPOSED)
    q_aut = session.query(ProposicaoAutor).filter(
        ProposicaoAutor.idDeputadoAutor.isnot(None)
    )
    if dep_ids_set:
        q_aut = q_aut.filter(ProposicaoAutor.idDeputadoAutor.in_(dep_ids_set))
    if batch_limit:
        q_aut = q_aut.limit(batch_limit)
    autores = q_aut.all()
    for aut in autores:
        prop_bool = "true" if aut.proponente else "false"
        cypher_aut = f"""
        MATCH (p:{LABEL_POLITICO} {{id: {aut.idDeputadoAutor}}}), (pr:{LABEL_PROPOSICAO} {{id: {aut.idProposicao}}})
        MERGE (p)-[:{EDGE_PROPOSED} {{proponente: {prop_bool}, ordem: {aut.ordemAssinatura or 1}}}]->(pr)
        """
        try:
            execute_cypher(session, cypher_aut)
            counts["arestas"] += 1
        except Exception:
            pass

    # 5. Sincroniza Votações & Votos (:VOTED_IN, :REGARDING)
    q_vot = session.query(Votacao)
    if legislatura == 57:
        q_vot = q_vot.filter(Votacao.data >= "2023-02-01")
    elif legislatura == 56:
        q_vot = q_vot.filter(Votacao.data.between("2019-02-01", "2023-01-31"))
    if batch_limit:
        q_vot = q_vot.limit(batch_limit)
    votacoes = q_vot.all()

    for v in votacoes:
        cypher_v = f"""
        MERGE (vt:{LABEL_VOTACAO} {{id: {v.id}}})
        SET vt.idCamara = '{_escape(v.idCamara or "")}',
            vt.descricao = '{_escape((v.descricao or "")[:200])}'
        """
        try:
            execute_cypher(session, cypher_v)
            counts["votacoes"] += 1
        except Exception:
            pass

        # Conecta a proposição e seus temas se houver
        if v.idProposicao:
            pr_obj = v.proposicao
            if pr_obj:
                cypher_reg = f"""
                MERGE (vt:{LABEL_VOTACAO} {{id: {v.id}}})
                MERGE (pr:{LABEL_PROPOSICAO} {{id: {v.idProposicao}}})
                SET pr.idCamara = {pr_obj.idCamara or 0},
                    pr.siglaTipo = '{_escape(pr_obj.siglaTipo or "")}',
                    pr.numero = {pr_obj.numero or 0},
                    pr.ano = {pr_obj.ano or 0},
                    pr.ementa = '{_escape((pr_obj.ementa or "")[:200])}'
                MERGE (vt)-[:{EDGE_REGARDING}]->(pr)
                """
                try:
                    execute_cypher(session, cypher_reg)
                    counts["arestas"] += 1
                except Exception:
                    pass

                for tm in pr_obj.temas:
                    cypher_tm = f"""
                    MATCH (pr:{LABEL_PROPOSICAO} {{id: {v.idProposicao}}}), (t:{LABEL_TEMA} {{id: {tm.id}}})
                    MERGE (pr)-[:{EDGE_BELONGS_TO_THEME}]->(t)
                    """
                    try:
                        execute_cypher(session, cypher_tm)
                        counts["arestas"] += 1
                    except Exception:
                        pass
            else:
                cypher_reg = f"""
                MATCH (vt:{LABEL_VOTACAO} {{id: {v.id}}}), (pr:{LABEL_PROPOSICAO} {{id: {v.idProposicao}}})
                MERGE (vt)-[:{EDGE_REGARDING}]->(pr)
                """
                try:
                    execute_cypher(session, cypher_reg)
                    counts["arestas"] += 1
                except Exception:
                    pass

        # Votos dos deputados
        for voto in v.votos:
            if voto.idDeputado and (not dep_ids_set or voto.idDeputado in dep_ids_set):
                cypher_voto = f"""
                MATCH (p:{LABEL_POLITICO} {{id: {voto.idDeputado}}}), (vt:{LABEL_VOTACAO} {{id: {v.id}}})
                MERGE (p)-[:{EDGE_VOTED_IN} {{voto: '{_escape(voto.voto or "")}'}}]->(vt)
                """
                try:
                    execute_cypher(session, cypher_voto)
                    counts["arestas"] += 1
                except Exception:
                    pass

    session.commit()
    return counts


def get_graph_stats(session: Session) -> Dict[str, Any]:
    """Retorna estatísticas consolidadas de nós e arestas do grafo Apache AGE."""
    ensure_age_loaded(session)
    stats: Dict[str, Any] = {
        "nodes": {},
        "edges": {},
        "total_nodes": 0,
        "total_edges": 0,
    }
    try:
        node_counts = execute_cypher(
            session,
            "MATCH (n) RETURN labels(n), count(n)",
            "lbl agtype, cnt agtype",
        )
        for r in node_counts:
            lbl = _clean_agtype(r[0])
            cnt_str = _clean_agtype(r[1])
            cnt = int(cnt_str) if cnt_str.isdigit() else 0
            stats["nodes"][lbl] = cnt
            stats["total_nodes"] += cnt

        edge_counts = execute_cypher(
            session,
            "MATCH ()-[r]->() RETURN type(r), count(r)",
            "rel agtype, cnt agtype",
        )
        for r in edge_counts:
            rel = _clean_agtype(r[0])
            cnt_str = _clean_agtype(r[1])
            cnt = int(cnt_str) if cnt_str.isdigit() else 0
            stats["edges"][rel] = cnt
            stats["total_edges"] += cnt
    except Exception as e:
        logger.warning(f"Não foi possível extrair estatísticas do grafo: {e}")
    return stats


# ===========================================================================
# CONSULTAS CYPHER EXEMPLES & GRAPH-RAG
# ===========================================================================


def cypher_sample_politicos_por_tema(
    session: Session, tema_nome: str
) -> List[Dict[str, Any]]:
    """
    Exemplo Cypher 1: Busca deputados que propuseram proposições dentro de um determinado tema.
    Query Cypher:
        MATCH (p:Politico)-[:PROPOSED]->(pr:Proposicao)-[:BELONGS_TO_THEME]->(t:Tema)
        WHERE t.tema CONTAINS 'Economia'
        RETURN p.nome, p.siglaPartido, pr.siglaTipo, pr.numero, pr.ano, t.tema
    """
    cypher = f"""
    MATCH (p:{LABEL_POLITICO})-[:{EDGE_PROPOSED}]->(pr:{LABEL_PROPOSICAO})-[:{EDGE_BELONGS_TO_THEME}]->(t:{LABEL_TEMA})
    WHERE t.tema CONTAINS '{_escape(tema_nome)}'
    RETURN p.nome, p.siglaPartido, pr.siglaTipo, pr.numero, pr.ano, t.tema
    """
    rows = execute_cypher(
        session,
        cypher,
        "nome agtype, partido agtype, tipo agtype, numero agtype, ano agtype, tema agtype",
    )
    results = []
    for r in rows:
        results.append(
            {
                "nome": _clean_agtype(r[0]),
                "partido": _clean_agtype(r[1]),
                "proposicao": f"{_clean_agtype(r[2])} {_clean_agtype(r[3])}/{_clean_agtype(r[4])}",
                "tema": _clean_agtype(r[5]),
            }
        )
    return results


def cypher_sample_alinhamento_votos(
    session: Session,
    id_dep1: int,
    id_dep2: int,
    tema: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Exemplo Cypher 2: Encontra votações comuns onde dois deputados votaram e compara os seus votos,
    com suporte a filtro opcional por tema legislativo.
    """
    if tema:
        cypher = f"""
        MATCH (p1:{LABEL_POLITICO} {{id: {id_dep1}}})-[v1:{EDGE_VOTED_IN}]->(vt:{LABEL_VOTACAO})<-[v2:{EDGE_VOTED_IN}]-(p2:{LABEL_POLITICO} {{id: {id_dep2}}})
        MATCH (vt)-[:{EDGE_REGARDING}]->(pr:{LABEL_PROPOSICAO})-[:{EDGE_BELONGS_TO_THEME}]->(t:{LABEL_TEMA})
        WHERE toLower(t.tema) CONTAINS toLower('{_escape(tema)}')
        RETURN vt.id, vt.descricao, v1.voto, v2.voto, pr.siglaTipo, pr.numero, pr.ano, pr.ementa, t.tema
        """
    else:
        cypher = f"""
        MATCH (p1:{LABEL_POLITICO} {{id: {id_dep1}}})-[v1:{EDGE_VOTED_IN}]->(vt:{LABEL_VOTACAO})<-[v2:{EDGE_VOTED_IN}]-(p2:{LABEL_POLITICO} {{id: {id_dep2}}})
        OPTIONAL MATCH (vt)-[:{EDGE_REGARDING}]->(pr:{LABEL_PROPOSICAO})
        OPTIONAL MATCH (pr)-[:{EDGE_BELONGS_TO_THEME}]->(t:{LABEL_TEMA})
        RETURN vt.id, vt.descricao, v1.voto, v2.voto, pr.siglaTipo, pr.numero, pr.ano, pr.ementa, t.tema
        """
    rows = execute_cypher(
        session,
        cypher,
        "vt_id agtype, descricao agtype, voto1 agtype, voto2 agtype, tipo agtype, num agtype, ano agtype, ementa agtype, tema agtype",
    )
    votes_map: Dict[int, Dict[str, Any]] = {}
    for r in rows:
        id_vot = int(_clean_agtype(r[0])) if _clean_agtype(r[0]).isdigit() else 0
        tema_val = _clean_agtype(r[8])
        if id_vot not in votes_map:
            voto1 = _clean_agtype(r[2])
            voto2 = _clean_agtype(r[3])
            tipo = _clean_agtype(r[4])
            num = _clean_agtype(r[5])
            ano = _clean_agtype(r[6])
            prop = f"{tipo} {num}/{ano}" if tipo else None
            votes_map[id_vot] = {
                "id_votacao": id_vot,
                "descricao": _clean_agtype(r[1]),
                "voto_politico1": voto1,
                "voto_politico2": voto2,
                "alinhados": (
                    voto1.strip().lower() == voto2.strip().lower() and voto1 != ""
                ),
                "proposicao": prop,
                "ementa": _clean_agtype(r[7]),
                "tema": tema_val if tema_val else None,
                "temas": [tema_val] if tema_val else [],
            }
        else:
            if tema_val and tema_val not in votes_map[id_vot]["temas"]:
                votes_map[id_vot]["temas"].append(tema_val)

    return list(votes_map.values())


async def cypher_sample_alinhamento_votos_async(
    session: AsyncSession,
    id_dep1: int,
    id_dep2: int,
    tema: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Versão assíncrona para consultar alinhamento de votos no Apache AGE via AsyncSession,
    com suporte a filtro opcional por tema legislativo.
    """
    if tema:
        cypher = f"""
        MATCH (p1:{LABEL_POLITICO} {{id: {id_dep1}}})-[v1:{EDGE_VOTED_IN}]->(vt:{LABEL_VOTACAO})<-[v2:{EDGE_VOTED_IN}]-(p2:{LABEL_POLITICO} {{id: {id_dep2}}})
        MATCH (vt)-[:{EDGE_REGARDING}]->(pr:{LABEL_PROPOSICAO})-[:{EDGE_BELONGS_TO_THEME}]->(t:{LABEL_TEMA})
        WHERE toLower(t.tema) CONTAINS toLower('{_escape(tema)}')
        RETURN vt.id, vt.descricao, v1.voto, v2.voto, pr.siglaTipo, pr.numero, pr.ano, pr.ementa, t.tema
        """
    else:
        cypher = f"""
        MATCH (p1:{LABEL_POLITICO} {{id: {id_dep1}}})-[v1:{EDGE_VOTED_IN}]->(vt:{LABEL_VOTACAO})<-[v2:{EDGE_VOTED_IN}]-(p2:{LABEL_POLITICO} {{id: {id_dep2}}})
        OPTIONAL MATCH (vt)-[:{EDGE_REGARDING}]->(pr:{LABEL_PROPOSICAO})
        OPTIONAL MATCH (pr)-[:{EDGE_BELONGS_TO_THEME}]->(t:{LABEL_TEMA})
        RETURN vt.id, vt.descricao, v1.voto, v2.voto, pr.siglaTipo, pr.numero, pr.ano, pr.ementa, t.tema
        """
    rows = await execute_cypher_async(
        session,
        cypher,
        "vt_id agtype, descricao agtype, voto1 agtype, voto2 agtype, tipo agtype, num agtype, ano agtype, ementa agtype, tema agtype",
    )
    votes_map: Dict[int, Dict[str, Any]] = {}
    for r in rows:
        id_vot = int(_clean_agtype(r[0])) if _clean_agtype(r[0]).isdigit() else 0
        tema_val = _clean_agtype(r[8])
        if id_vot not in votes_map:
            voto1 = _clean_agtype(r[2])
            voto2 = _clean_agtype(r[3])
            tipo = _clean_agtype(r[4])
            num = _clean_agtype(r[5])
            ano = _clean_agtype(r[6])
            prop = f"{tipo} {num}/{ano}" if tipo else None
            votes_map[id_vot] = {
                "id_votacao": id_vot,
                "descricao": _clean_agtype(r[1]),
                "voto_politico1": voto1,
                "voto_politico2": voto2,
                "alinhados": (
                    voto1.strip().lower() == voto2.strip().lower() and voto1 != ""
                ),
                "proposicao": prop,
                "ementa": _clean_agtype(r[7]),
                "tema": tema_val if tema_val else None,
                "temas": [tema_val] if tema_val else [],
            }
        else:
            if tema_val and tema_val not in votes_map[id_vot]["temas"]:
                votes_map[id_vot]["temas"].append(tema_val)

    return list(votes_map.values())


async def cypher_rede_coautoria_async(
    session: AsyncSession,
    politico_id: int,
    limit: int = 20,
) -> List[Dict[str, Any]]:
    """
    Consulta no Apache AGE a rede de coautoria legislativa de um parlamentar.
    Identifica outros deputados que apresentaram matérias conjuntamente.
    """
    cypher = f"""
    MATCH (p1:{LABEL_POLITICO} {{id: {politico_id}}})-[aut1:{EDGE_PROPOSED}]->(pr:{LABEL_PROPOSICAO})<-[aut2:{EDGE_PROPOSED}]-(p2:{LABEL_POLITICO})
    WHERE p2.id <> {politico_id}
    OPTIONAL MATCH (pr)-[:{EDGE_BELONGS_TO_THEME}]->(t:{LABEL_TEMA})
    RETURN p2.id, p2.nome, coalesce(p2.siglaPartido, p2.partido), coalesce(p2.siglaUF, p2.uf), p2.slug, aut1.proponente, aut2.proponente, pr.id, pr.siglaTipo, pr.numero, pr.ano, pr.ementa, t.tema, coalesce(p1.siglaPartido, p1.partido), p2.idCamara, p2.urlFoto
    """
    rows = await execute_cypher_async(
        session,
        cypher,
        "p2_id agtype, p2_nome agtype, p2_partido agtype, p2_uf agtype, p2_slug agtype, aut1_prop agtype, aut2_prop agtype, pr_id agtype, pr_tipo agtype, pr_num agtype, pr_ano agtype, pr_ementa agtype, tema agtype, p1_partido agtype, p2_id_camara agtype, p2_url_foto agtype",
    )

    parceiros_map: Dict[int, Dict[str, Any]] = {}
    props_por_parceiro: Dict[int, Dict[int, Dict[str, Any]]] = {}
    temas_por_parceiro: Dict[int, Dict[str, int]] = {}

    for r in rows:
        p2_id_str = _clean_agtype(r[0])
        if not p2_id_str.isdigit():
            continue
        p2_id = int(p2_id_str)
        p2_nome = _clean_agtype(r[1])
        p2_partido = _clean_agtype(r[2])
        p2_uf = _clean_agtype(r[3])
        p2_slug = _clean_agtype(r[4])
        aut1_prop = str(_clean_agtype(r[5])).lower() in ("true", "1")
        aut2_prop = str(_clean_agtype(r[6])).lower() in ("true", "1")
        pr_id_str = _clean_agtype(r[7])
        pr_id = int(pr_id_str) if pr_id_str.isdigit() else 0
        pr_tipo = _clean_agtype(r[8])
        pr_num = _clean_agtype(r[9])
        pr_ano = _clean_agtype(r[10])
        pr_ementa = _clean_agtype(r[11])
        tema_val = _clean_agtype(r[12])
        p1_partido = _clean_agtype(r[13])
        p2_id_camara_str = _clean_agtype(r[14])
        p2_id_camara = int(p2_id_camara_str) if p2_id_camara_str.isdigit() else None
        p2_url_foto = _clean_agtype(r[15]) or None
        url_foto = p2_url_foto or (
            f"https://www.camara.leg.br/internet/deputado/bandep/{p2_id_camara}.jpg"
            if p2_id_camara
            else None
        )

        if p2_id not in parceiros_map:
            parceiros_map[p2_id] = {
                "politico": {
                    "id": p2_id,
                    "nome": p2_nome,
                    "slug": p2_slug or None,
                    "sigla_partido": p2_partido or None,
                    "sigla_uf": p2_uf or None,
                    "url_foto": url_foto,
                },
                "mesmo_partido": (
                    bool(
                        p1_partido
                        and p2_partido
                        and p1_partido.upper() == p2_partido.upper()
                    )
                ),
            }
            props_por_parceiro[p2_id] = {}
            temas_por_parceiro[p2_id] = {}

        if pr_id and pr_id not in props_por_parceiro[p2_id]:
            props_por_parceiro[p2_id][pr_id] = {
                "id": pr_id,
                "sigla_tipo": pr_tipo or None,
                "numero": int(pr_num) if pr_num.isdigit() else None,
                "ano": int(pr_ano) if pr_ano.isdigit() else None,
                "ementa": pr_ementa or None,
                "p1_era_principal": aut1_prop,
                "p2_era_principal": aut2_prop,
            }

        if tema_val:
            temas_por_parceiro[p2_id][tema_val] = (
                temas_por_parceiro[p2_id].get(tema_val, 0) + 1
            )

    resultados = []
    for p2_id, info in parceiros_map.items():
        props = list(props_por_parceiro[p2_id].values())
        total_juntos = len(props)
        como_principal = sum(1 for p in props if p["p1_era_principal"])
        como_coautor = sum(
            1 for p in props if p["p2_era_principal"] and not p["p1_era_principal"]
        )
        temas_ordenados = sorted(
            temas_por_parceiro[p2_id].keys(),
            key=lambda t: temas_por_parceiro[p2_id][t],
            reverse=True,
        )
        amostra = [
            {
                "id": p["id"],
                "sigla_tipo": p["sigla_tipo"],
                "numero": p["numero"],
                "ano": p["ano"],
                "ementa": p["ementa"],
                "proponente_principal_id": politico_id
                if p["p1_era_principal"]
                else p2_id,
            }
            for p in props[:5]
        ]
        resultados.append(
            {
                "politico": info["politico"],
                "total_proposicoes_juntos": total_juntos,
                "proposicoes_como_autor_principal": como_principal,
                "proposicoes_como_coautor": como_coautor,
                "mesmo_partido": info["mesmo_partido"],
                "temas_comuns": temas_ordenados[:5],
                "amostra_proposicoes": amostra,
            }
        )

    resultados.sort(key=lambda x: x["total_proposicoes_juntos"], reverse=True)
    return resultados[:limit]


async def cypher_afinidades_voto_async(
    session: AsyncSession,
    politico_id: int,
    min_comuns: int = 10,
    apenas_outros_partidos: bool = False,
    limit: int = 10,
) -> Dict[str, Any]:
    """
    Analisa a afinidade e oposição de votações nominais de um parlamentar em relação
    a todos os outros parlamentares no grafo Apache AGE.
    """
    cypher = f"""
    MATCH (p1:{LABEL_POLITICO} {{id: {politico_id}}})-[v1:{EDGE_VOTED_IN}]->(vt:{LABEL_VOTACAO})<-[v2:{EDGE_VOTED_IN}]-(p2:{LABEL_POLITICO})
    WHERE p2.id <> {politico_id}
    RETURN p2.id, p2.nome, coalesce(p2.siglaPartido, p2.partido), coalesce(p2.siglaUF, p2.uf), p2.slug, coalesce(p1.siglaPartido, p1.partido), v1.voto, v2.voto, vt.id, p2.idCamara, p2.urlFoto
    """
    rows = await execute_cypher_async(
        session,
        cypher,
        "p2_id agtype, p2_nome agtype, p2_partido agtype, p2_uf agtype, p2_slug agtype, p1_partido agtype, v1_voto agtype, v2_voto agtype, vt_id agtype, p2_id_camara agtype, p2_url_foto agtype",
    )

    dep_stats: Dict[int, Dict[str, Any]] = {}
    bancada_stats: Dict[str, Dict[str, int]] = {}

    for r in rows:
        p2_id_str = _clean_agtype(r[0])
        if not p2_id_str.isdigit():
            continue
        p2_id = int(p2_id_str)
        p2_nome = _clean_agtype(r[1])
        p2_partido = _clean_agtype(r[2])
        p2_uf = _clean_agtype(r[3])
        p2_slug = _clean_agtype(r[4])
        p1_partido = _clean_agtype(r[5])
        voto1 = _clean_agtype(r[6]).strip().lower()
        voto2 = _clean_agtype(r[7]).strip().lower()
        p2_id_camara_str = _clean_agtype(r[9])
        p2_id_camara = int(p2_id_camara_str) if p2_id_camara_str.isdigit() else None
        p2_url_foto = _clean_agtype(r[10]) or None
        url_foto = p2_url_foto or (
            f"https://www.camara.leg.br/internet/deputado/bandep/{p2_id_camara}.jpg"
            if p2_id_camara
            else None
        )

        if p2_id not in dep_stats:
            dep_stats[p2_id] = {
                "politico": {
                    "id": p2_id,
                    "nome": p2_nome,
                    "slug": p2_slug or None,
                    "sigla_partido": p2_partido or None,
                    "sigla_uf": p2_uf or None,
                    "url_foto": url_foto,
                },
                "mesmo_partido": (
                    bool(
                        p1_partido
                        and p2_partido
                        and p1_partido.upper() == p2_partido.upper()
                    )
                ),
                "total": 0,
                "alinhados": 0,
            }

        dep_stats[p2_id]["total"] += 1
        alinhou = voto1 == voto2 and voto1 != ""
        if alinhou:
            dep_stats[p2_id]["alinhados"] += 1

        if p2_partido:
            sigla_bancada = p2_partido.upper()
            if sigla_bancada not in bancada_stats:
                bancada_stats[sigla_bancada] = {"total": 0, "alinhados": 0}
            bancada_stats[sigla_bancada]["total"] += 1
            if alinhou:
                bancada_stats[sigla_bancada]["alinhados"] += 1

    candidatos = []
    for info in dep_stats.values():
        total = info["total"]
        if total < min_comuns:
            continue
        if apenas_outros_partidos and info["mesmo_partido"]:
            continue
        alinhados = info["alinhados"]
        divergentes = total - alinhados
        taxa = round((alinhados / total) * 100.0, 1) if total > 0 else 0.0
        candidatos.append(
            {
                "politico": info["politico"],
                "total_votacoes_comuns": total,
                "votos_alinhados": alinhados,
                "votos_divergentes": divergentes,
                "taxa_alinhamento": taxa,
                "mesmo_partido": info["mesmo_partido"],
            }
        )

    mais_alinhados = sorted(
        candidatos,
        key=lambda x: (x["taxa_alinhamento"], x["total_votacoes_comuns"]),
        reverse=True,
    )[:limit]
    mais_divergentes = sorted(
        candidatos, key=lambda x: (x["taxa_alinhamento"], -x["total_votacoes_comuns"])
    )[:limit]

    bancadas_resumo = []
    for sigla, bdata in bancada_stats.items():
        btotal = bdata["total"]
        baln = bdata["alinhados"]
        if btotal >= 5:
            btaxa = round((baln / btotal) * 100.0, 1)
            bancadas_resumo.append(
                {
                    "sigla_partido": sigla,
                    "total_votacoes": btotal,
                    "votos_alinhados": baln,
                    "taxa_alinhamento": btaxa,
                }
            )
    bancadas_resumo.sort(key=lambda x: x["taxa_alinhamento"], reverse=True)

    return {
        "min_votacoes_comuns": min_comuns,
        "mais_alinhados": mais_alinhados,
        "mais_divergentes": mais_divergentes,
        "alinhamento_por_bancada": bancadas_resumo,
    }


async def cypher_grafo_proposicao_async(
    session: AsyncSession,
    proposicao_id: int,
) -> Optional[Dict[str, Any]]:
    """
    Consulta o ecossistema completo de uma proposição no Apache AGE:
    autores, coautores, temas e votações associadas.
    """
    cypher = f"""
    MATCH (pr:{LABEL_PROPOSICAO} {{id: {proposicao_id}}})
    OPTIONAL MATCH (p:{LABEL_POLITICO})-[aut:{EDGE_PROPOSED}]->(pr)
    OPTIONAL MATCH (pr)-[:{EDGE_BELONGS_TO_THEME}]->(t:{LABEL_TEMA})
    OPTIONAL MATCH (vt:{LABEL_VOTACAO})-[:{EDGE_REGARDING}]->(pr)
    RETURN pr.id, pr.siglaTipo, pr.numero, pr.ano, pr.ementa,
           p.id, p.nome, coalesce(p.siglaPartido, p.partido), coalesce(p.siglaUF, p.uf), p.slug, aut.proponente,
           t.tema, vt.id, vt.data, vt.descricao, vt.aprovacao, p.idCamara, p.urlFoto
    """
    rows = await execute_cypher_async(
        session,
        cypher,
        "pr_id agtype, pr_tipo agtype, pr_num agtype, pr_ano agtype, pr_ementa agtype, p_id agtype, p_nome agtype, p_partido agtype, p_uf agtype, p_slug agtype, aut_prop agtype, t_tema agtype, vt_id agtype, vt_data agtype, vt_desc agtype, vt_aprov agtype, p_id_camara agtype, p_url_foto agtype",
    )
    if not rows:
        return None

    pr_info: Dict[str, Any] = {}
    autor_proponente = None
    coautores_map: Dict[int, Dict[str, Any]] = {}
    temas_set = set()
    votacoes_map: Dict[int, Dict[str, Any]] = {}

    for r in rows:
        pr_id = int(_clean_agtype(r[0])) if _clean_agtype(r[0]).isdigit() else 0
        tipo = _clean_agtype(r[1])
        num = _clean_agtype(r[2])
        ano = _clean_agtype(r[3])
        ementa = _clean_agtype(r[4])

        if not pr_info:
            pr_info = {
                "id_proposicao": pr_id,
                "proposicao": f"{tipo} {num}/{ano}" if tipo else f"Proposição #{pr_id}",
                "ementa": ementa or None,
            }

        p_id_str = _clean_agtype(r[5])
        if p_id_str.isdigit():
            p_id = int(p_id_str)
            p_id_camara_str = _clean_agtype(r[16])
            p_id_camara = int(p_id_camara_str) if p_id_camara_str.isdigit() else None
            p_url_foto = _clean_agtype(r[17]) or None
            url_foto = p_url_foto or (
                f"https://www.camara.leg.br/internet/deputado/bandep/{p_id_camara}.jpg"
                if p_id_camara
                else None
            )
            p_dict = {
                "id": p_id,
                "nome": _clean_agtype(r[6]),
                "sigla_partido": _clean_agtype(r[7]) or None,
                "sigla_uf": _clean_agtype(r[8]) or None,
                "slug": _clean_agtype(r[9]) or None,
                "url_foto": url_foto,
            }
            is_prop = str(_clean_agtype(r[10])).lower() in ("true", "1")
            if is_prop and not autor_proponente:
                autor_proponente = p_dict
            elif p_id not in coautores_map:
                coautores_map[p_id] = p_dict

        tema_str = _clean_agtype(r[11])
        if tema_str:
            temas_set.add(tema_str)

        vt_id_str = _clean_agtype(r[12])
        if vt_id_str.isdigit():
            vt_id = int(vt_id_str)
            if vt_id not in votacoes_map:
                vt_aprov = _clean_agtype(r[15])
                votacoes_map[vt_id] = {
                    "id_votacao": vt_id,
                    "data": _clean_agtype(r[13]) or None,
                    "descricao": _clean_agtype(r[14]) or None,
                    "aprovacao": int(vt_aprov)
                    if vt_aprov.lstrip("-").isdigit()
                    else None,
                    "votos_sim": None,
                    "votos_nao": None,
                    "votos_outros": None,
                    "orientacoes": [],
                }

    pr_info["autor_proponente"] = autor_proponente
    pr_info["coautores"] = list(coautores_map.values())
    pr_info["temas"] = sorted(temas_set)
    pr_info["votacoes"] = list(votacoes_map.values())
    return pr_info


def graph_rag_retrieval(
    session: Session,
    query_vector: List[float],
    top_k_vectors: int = 5,
    ef_search: int = 100,
) -> Dict[str, Any]:
    """
    Pipelines de Graph-RAG (Recuperação Híbrida Vetor + Grafo):
    1. Etapa Vetorial (pgvector): Executa busca KNN por cosseno para identificar as proposições
       conceitualmente mais similares à consulta do usuário.
    2. Etapa de Grafo (Apache AGE): A partir das proposições recuperadas via pgvector,
       percorre o grafo para extrair:
       - Deputados autores/coautores (:PROPOSED)
       - Posicionamento em votações (:VOTED_IN)
       - Temas transversais associados (:BELONGS_TO_THEME)
    3. Fusão de Contexto: Consolida o grafo estruturado + embeddings semânticos em um payload
       enriquecido pronto para injeção no prompt do LLM.
    """
    # 1. Recupera proposições mais similares via pgvector KNN
    vector_matches = vector_knn_search(
        session,
        query_vector=query_vector,
        limit=top_k_vectors,
        ef_search=ef_search,
        tipo_entidade="proposicao",
    )

    if not vector_matches:
        return {"semantic_matches": [], "graph_context": []}

    prop_ids = [m["idEntidade"] for m in vector_matches]

    # 2. Travessia de Grafo no Apache AGE para os IDs recuperados
    graph_results = []
    for prop_id in prop_ids:
        cypher = f"""
        MATCH (pr:{LABEL_PROPOSICAO} {{id: {prop_id}}})
        OPTIONAL MATCH (p:{LABEL_POLITICO})-[aut:{EDGE_PROPOSED}]->(pr)
        OPTIONAL MATCH (pr)-[:{EDGE_BELONGS_TO_THEME}]->(t:{LABEL_TEMA})
        OPTIONAL MATCH (p_voto:{LABEL_POLITICO})-[v:{EDGE_VOTED_IN}]->(vt:{LABEL_VOTACAO})-[:{EDGE_REGARDING}]->(pr)
        RETURN pr.id, pr.siglaTipo, pr.numero, pr.ano, pr.ementa,
               p.nome, aut.proponente, t.tema, p_voto.nome, v.voto
        """
        try:
            rows = execute_cypher(
                session,
                cypher,
                "id agtype, tipo agtype, num agtype, ano agtype, ementa agtype, autor agtype, prop agtype, tema agtype, dep_voto agtype, voto agtype",
            )
            for r in rows:
                graph_results.append(
                    {
                        "idProposicao": _clean_agtype(r[0]),
                        "proposicao": f"{_clean_agtype(r[1])} {_clean_agtype(r[2])}/{_clean_agtype(r[3])}",
                        "ementa": _clean_agtype(r[4]),
                        "autor": _clean_agtype(r[5]),
                        "isProponente": _clean_agtype(r[6]),
                        "tema": _clean_agtype(r[7]),
                        "deputadoVotante": _clean_agtype(r[8]),
                        "voto": _clean_agtype(r[9]),
                    }
                )
        except Exception as e:
            logger.warning(
                f"Não foi possível recuperar contexto no AGE para proposicao {prop_id}: {e}"
            )

    return {
        "semantic_matches": vector_matches,
        "graph_context": graph_results,
    }


def _escape(val: str) -> str:
    return (
        val.replace("'", "''")
        .replace("\\", "\\\\")
        .replace("\n", " ")
        .replace("\r", "")
    )


def _clean_agtype(val: Any) -> Any:
    if val is None:
        return ""
    s = str(val).strip()
    if s.startswith('"') and s.endswith('"'):
        s = s[1:-1]
    return s
