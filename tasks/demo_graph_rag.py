"""
demo_graph_rag.py — Demonstração interativa de Graph-RAG (pgvector + Apache AGE).

Fluxo Híbrido:
1. Etapa Vetorial (pgvector): Codifica a consulta do usuário em vetor BAAI/bge-m3 (1024-d)
   e busca por k-vizinhos mais próximos (KNN / HNSW) com distância de cosseno.
2. Etapa de Grafo (Apache AGE): A partir das proposições recuperadas pelo pgvector,
   percorre o grafo no PostgreSQL para obter os autores (:PROPOSED), votações vinculadas
   (:REGARDING), votos nominais de parlamentares (:VOTED_IN) e temas (:BELONGS_TO_THEME).
3. Apresentação: Consolida o contexto semântico e estrutural para o usuário.
"""

import argparse
import logging

from sentence_transformers import SentenceTransformer

from shared.database import SessionLocal
from shared.graph import graph_rag_retrieval

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)


def executar_demo_graph_rag(
    query_text: str,
    top_k: int = 5,
    model_name: str = "BAAI/bge-m3",
    ef_search: int = 100,
):
    print("\n" + "=" * 75)
    print("DEMONSTRAÇÃO DE BUSCA HÍBRIDA: PGVECTOR + APACHE AGE (GRAPH-RAG)")
    print("=" * 75)
    print(f'Consulta: "{query_text}"')
    print(f"Top-K Vetorial: {top_k} | HNSW ef_search: {ef_search}")
    print("-" * 75)

    logger.info("Carregando modelo %s...", model_name)
    model = SentenceTransformer(model_name)

    logger.info("Gerando embedding da consulta...")
    query_vector = model.encode(query_text, normalize_embeddings=True).tolist()

    session = SessionLocal()
    try:
        logger.info(
            "Executando recuperação híbrida (pgvector KNN -> Apache AGE Cypher)..."
        )
        resultado = graph_rag_retrieval(
            session=session,
            query_vector=query_vector,
            top_k_vectors=top_k,
            ef_search=ef_search,
        )

        semantic_matches = resultado.get("semantic_matches", [])
        graph_context = resultado.get("graph_context", [])

        print("\n" + "—" * 75)
        print(
            f"1. RESULTADOS VETORIAIS (pgvector) — {len(semantic_matches)} encontrados"
        )
        print("—" * 75)

        if not semantic_matches:
            print("Nenhuma proposição similar encontrada no índice vetorial.")
        else:
            for idx, match in enumerate(semantic_matches, 1):
                prop_id = match.get("idEntidade")
                similarity = match.get("similarity", 0.0)
                distance = match.get("distance", 1.0)
                texto_preview = (match.get("textoFonte") or "").split("\n")[0][:100]
                print(
                    f"  [{idx}] Proposição ID #{prop_id} | Similaridade Cosseno: {similarity:.4f} (Dist: {distance:.4f})"
                )
                print(f"      Ementa/Texto: {texto_preview}...")

        print("\n" + "—" * 75)
        print(
            f"2. CONTEXTO EM GRAFO (Apache AGE openCypher) — {len(graph_context)} conexões"
        )
        print("—" * 75)

        if not graph_context:
            print(
                "Nenhuma conexão de grafo encontrada para as proposições no Apache AGE."
            )
            print(
                "(Dica: execute `python tasks/sync_graph.py` para sincronizar o grafo)"
            )
        else:
            # Agrupa por proposição
            por_proposicao = {}
            for item in graph_context:
                pid = item.get("idProposicao")
                if pid not in por_proposicao:
                    por_proposicao[pid] = {
                        "proposicao": item.get("proposicao"),
                        "ementa": item.get("ementa"),
                        "autores": set(),
                        "temas": set(),
                        "votos": [],
                    }
                if item.get("autor"):
                    autor_desc = item["autor"]
                    if item.get("isProponente") == "true":
                        autor_desc += " (Proponente Principal)"
                    por_proposicao[pid]["autores"].add(autor_desc)
                if item.get("tema"):
                    por_proposicao[pid]["temas"].add(item["tema"])
                if item.get("deputadoVotante") and item.get("voto"):
                    por_proposicao[pid]["votos"].append(
                        f"{item['deputadoVotante']}: {item['voto']}"
                    )

            for pid, dados in por_proposicao.items():
                print(f"\n  * Proposição: {dados['proposicao']} (ID #{pid})")
                print(f"    Ementa: {dados['ementa'][:120]}...")
                if dados["autores"]:
                    print(
                        f"    Autores (:PROPOSED): {', '.join(list(dados['autores'])[:5])}"
                    )
                if dados["temas"]:
                    print(f"    Temas (:BELONGS_TO_THEME): {', '.join(dados['temas'])}")
                if dados["votos"]:
                    print(
                        f"    Amostra de Votos (:VOTED_IN): {', '.join(dados['votos'][:4])}..."
                    )

        print("\n" + "=" * 75 + "\n")
        return resultado

    finally:
        session.close()


def main():
    parser = argparse.ArgumentParser(
        description="Demonstração Graph-RAG (pgvector + Apache AGE)"
    )
    parser.add_argument(
        "--query",
        type=str,
        default="regulamentação da inteligência artificial e proteção de dados",
        help="Texto da consulta para busca semântica e expansão em grafo",
    )
    parser.add_argument(
        "--top-k", type=int, default=5, help="Quantidade de proposições similares"
    )
    parser.add_argument(
        "--model", type=str, default="BAAI/bge-m3", help="Modelo de embeddings"
    )
    parser.add_argument(
        "--ef-search", type=int, default=100, help="Parâmetro HNSW ef_search"
    )

    args = parser.parse_args()
    executar_demo_graph_rag(
        query_text=args.query,
        top_k=args.top_k,
        model_name=args.model,
        ef_search=args.ef_search,
    )


if __name__ == "__main__":
    main()
