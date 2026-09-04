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
            p.siglaUF = '{_escape(d.siglaUF or "")}'
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

        # Conecta a proposição se houver
        if v.idProposicao:
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
    session: Session, id_dep1: int, id_dep2: int
) -> List[Dict[str, Any]]:
    """
    Exemplo Cypher 2: Encontra votações comuns onde dois deputados votaram e compara os seus votos.
    Query Cypher:
        MATCH (p1:Politico {id: 101})-[v1:VOTED_IN]->(vt:Votacao)<-[v2:VOTED_IN]-(p2:Politico {id: 102})
        OPTIONAL MATCH (vt)-[:REGARDING]->(pr:Proposicao)
        RETURN vt.id, vt.descricao, v1.voto, v2.voto, pr.siglaTipo + ' ' + toString(pr.numero)
    """
    cypher = f"""
    MATCH (p1:{LABEL_POLITICO} {{id: {id_dep1}}})-[v1:{EDGE_VOTED_IN}]->(vt:{LABEL_VOTACAO})<-[v2:{EDGE_VOTED_IN}]-(p2:{LABEL_POLITICO} {{id: {id_dep2}}})
    OPTIONAL MATCH (vt)-[:{EDGE_REGARDING}]->(pr:{LABEL_PROPOSICAO})
    RETURN vt.id, vt.descricao, v1.voto, v2.voto, pr.siglaTipo, pr.numero, pr.ano
    """
    rows = execute_cypher(
        session,
        cypher,
        "vt_id agtype, desc agtype, voto1 agtype, voto2 agtype, tipo agtype, num agtype, ano agtype",
    )
    results = []
    for r in rows:
        voto1 = _clean_agtype(r[2])
        voto2 = _clean_agtype(r[3])
        results.append(
            {
                "idVotacao": _clean_agtype(r[0]),
                "descricao": _clean_agtype(r[1]),
                "votoDeputado1": voto1,
                "votoDeputado2": voto2,
                "alinhados": (voto1 == voto2 and voto1 != ""),
                "proposicao": f"{_clean_agtype(r[4])} {_clean_agtype(r[5])}/{_clean_agtype(r[6])}"
                if r[4]
                else None,
            }
        )
    return results


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
