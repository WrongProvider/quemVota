"""
sync_graph.py — Sincronização Relacional (PostgreSQL) para Grafo Apache AGE (openCypher).

Converte dados de:
- Deputados → (:Politico {id, idCamara, nome, siglaPartido, siglaUF})
- Proposições → (:Proposicao {id, idCamara, siglaTipo, numero, ano, ementa})
- Votações → (:Votacao {id, idCamara, descricao})
- Temas → (:Tema {id, codTema, tema})

E arestas de relacionamento:
- (:Politico)-[:PROPOSED {proponente, ordem}]->(:Proposicao)
- (:Politico)-[:VOTED_IN {voto}]->(:Votacao)
- (:Proposicao)-[:BELONGS_TO_THEME]->(:Tema)
- (:Votacao)-[:REGARDING]->(:Proposicao)
"""

import argparse
import logging
from pprint import pprint

from shared.database import SessionLocal
from shared.graph import get_graph_stats, init_age_extension, sync_relational_to_graph

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(
        description="Sincroniza PostgreSQL para Apache AGE"
    )
    parser.add_argument(
        "--legislatura",
        type=int,
        default=57,
        help="Filtrar por legislatura (padrão: 57)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Limite de registros por entidade para teste",
    )
    parser.add_argument(
        "--apenas-com-votacoes",
        action="store_true",
        help="Apenas proposições com votações",
    )
    parser.add_argument(
        "--stats-only",
        action="store_true",
        help="Apenas exibe estatísticas atuais do grafo",
    )
    parser.add_argument(
        "--init-only",
        action="store_true",
        help="Apenas inicializa a extensão e o grafo",
    )

    args = parser.parse_args()

    session = SessionLocal()
    try:
        logger.info("Inicializando/verificando extensão e grafo Apache AGE...")
        sucesso = init_age_extension(session)
        if not sucesso:
            logger.error("Falha ao inicializar Apache AGE no PostgreSQL.")
            return

        if args.init_only:
            logger.info("Inicialização do Apache AGE concluída com sucesso.")
            return

        if args.stats_only:
            logger.info("Estatísticas atuais do grafo:")
            stats = get_graph_stats(session)
            pprint(stats)
            return

        logger.info(
            "Iniciando sincronização para o Apache AGE (Legislatura: %s, Limite: %s, Apenas Votadas: %s)...",
            args.legislatura,
            args.limit,
            args.apenas_com_votacoes,
        )

        counts = sync_relational_to_graph(
            session=session,
            batch_limit=args.limit,
            legislatura=args.legislatura,
            apenas_com_votacoes=args.apenas_com_votacoes,
        )

        logger.info("Sincronização concluída com sucesso!")
        pprint(counts)

        logger.info("Estatísticas consolidadas no grafo:")
        stats = get_graph_stats(session)
        pprint(stats)

    except Exception as e:
        logger.error("Erro durante a execução da sincronização: %s", e)
        raise
    finally:
        session.close()


if __name__ == "__main__":
    main()
