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
import sys
from pathlib import Path
from pprint import pprint

_repo_root = Path(__file__).resolve().parent.parent
if str(_repo_root) not in sys.path:
    sys.path.insert(0, str(_repo_root))

from shared.database import SessionLocal
from shared.graph import (
    get_graph_stats,
    init_age_extension,
    sync_relational_to_graph,
)

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
        default=None,
        help="Filtrar por legislatura específica (ex: 57, 56, 55)",
    )
    parser.add_argument(
        "--ano-inicio", type=int, default=None, help="Ano inicial (ex: 2019)"
    )
    parser.add_argument(
        "--ano-fim", type=int, default=None, help="Ano final (ex: 2025)"
    )
    parser.add_argument(
        "--pre-2026",
        action="store_true",
        help="Sincroniza todo o histórico pré-2026 (ano_fim=2025)",
    )
    parser.add_argument(
        "--todas-legislaturas",
        action="store_true",
        help="Sincroniza todas as legislaturas registradas no banco",
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

    # Define defaults inteligentes
    legislatura = args.legislatura
    ano_inicio = args.ano_inicio
    ano_fim = args.ano_fim

    if args.pre_2026:
        ano_fim = ano_fim or 2025
        # Se nenhuma legislatura específica foi informada, mantém legislatura=None para cobrir todo o histórico
    elif (
        not args.todas_legislaturas
        and legislatura is None
        and ano_inicio is None
        and ano_fim is None
    ):
        # Padrão padrão para execução simples: legislatura 57 (atual)
        legislatura = 57

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
            "Iniciando sincronização para o Apache AGE (Legislatura: %s, Anos: %s..%s, Limite: %s, Apenas Votadas: %s)...",
            legislatura or "Todas",
            ano_inicio or "Início",
            ano_fim or "Fim",
            args.limit,
            args.apenas_com_votacoes,
        )

        counts = sync_relational_to_graph(
            session=session,
            batch_limit=args.limit,
            legislatura=legislatura,
            ano_inicio=ano_inicio,
            ano_fim=ano_fim,
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
