"""
seed_temas_atuacao.py — Seed e vetorização da taxonomia canônica de 20 temas de atuação.

Conforme especificação SPEC-001 (Classificação de Temas de Atuação Parlamentar):
- Insere os 20 temas canônicos na tabela `temasAtuacao`.
- Computa os embeddings de 1024 dimensões com BAAI/bge-m3 normalizados para cosseno.
- Idempotente via on_conflict_do_update (index_elements=["slug"]).
"""

import logging
from typing import Dict, List

from sentence_transformers import SentenceTransformer
from sqlalchemy.dialects.postgresql import insert

from shared.database import SessionLocal
from shared.models_vetorial import TemaAtuacao

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

TEMAS_CANONICOS: List[Dict[str, str]] = [
    {
        "slug": "economia",
        "nome": "Economia",
        "descricao": "Política fiscal, tributária, inflação, comércio, orçamento público e finanças.",
    },
    {
        "slug": "educacao",
        "nome": "Educação",
        "descricao": "Ensino básico, superior, técnico, valorização docente e infraestrutura escolar.",
    },
    {
        "slug": "saude",
        "nome": "Saúde",
        "descricao": "Sistema Único de Saúde (SUS), vigilância sanitária, vacinação e hospitais.",
    },
    {
        "slug": "seguranca-publica",
        "nome": "Segurança Pública",
        "descricao": "Polícias, sistema prisional, combate ao crime organizado e desarmamento.",
    },
    {
        "slug": "trabalho",
        "nome": "Trabalho",
        "descricao": "Relações trabalhistas, CLT, emprego, renda, escala e seguridade laboral.",
    },
    {
        "slug": "direitos-humanos",
        "nome": "Direitos Humanos",
        "descricao": "Cidadania, proteção a minorias, combate à tortura e igualdade racial.",
    },
    {
        "slug": "meio-ambiente",
        "nome": "Meio Ambiente",
        "descricao": "Clima, desmatamento, transição energética, biodiversidade e recursos hídricos.",
    },
    {
        "slug": "infraestrutura",
        "nome": "Infraestrutura",
        "descricao": "Portos, aeroportos, rodovias, ferrovias, telecomunicações e energia.",
    },
    {
        "slug": "tecnologia",
        "nome": "Tecnologia",
        "descricao": "Inteligência artificial, segurança cibernética, proteção de dados e inovação digital.",
    },
    {
        "slug": "agricultura",
        "nome": "Agricultura",
        "descricao": "Agronegócio, agricultura familiar, crédito rural e exportação agropecuária.",
    },
    {
        "slug": "administracao-publica",
        "nome": "Administração Pública",
        "descricao": "Servidores públicos, reforma administrativa, processos e eficiência estatal.",
    },
    {
        "slug": "previdencia",
        "nome": "Previdência",
        "descricao": "Aposentadorias, regimes próprios, pensões e reformas previdenciárias.",
    },
    {
        "slug": "politica-externa",
        "nome": "Política Externa",
        "descricao": "Relações internacionais, diplomacia, tratados e comércio exterior.",
    },
    {
        "slug": "direitos-das-mulheres",
        "nome": "Direitos das Mulheres",
        "descricao": "Combate à violência doméstica, igualdade salarial e saúde da mulher.",
    },
    {
        "slug": "direitos-lgbtqia",
        "nome": "Direitos LGBTQIA+",
        "descricao": "Combate à homotransfobia, direitos civis e proteção legal da diversidade.",
    },
    {
        "slug": "povos-indigenas",
        "nome": "Povos Indígenas",
        "descricao": "Demarcação de terras, preservação cultural e proteção de comunidades tradicionais.",
    },
    {
        "slug": "cultura",
        "nome": "Cultura",
        "descricao": "Patrimônio histórico, incentivo cultural, audiovisual, literatura e artes.",
    },
    {
        "slug": "habitacao",
        "nome": "Habitação",
        "descricao": "Moradia popular, saneamento básico, regularização fundiária e urbanismo.",
    },
    {
        "slug": "transporte",
        "nome": "Transporte",
        "descricao": "Mobilidade urbana, transporte coletivo, trânsito e logística viária.",
    },
    {
        "slug": "combate-a-corrupcao",
        "nome": "Combate à Corrupção",
        "descricao": "Transparência, órgãos de controle, compliance e combate à improbidade.",
    },
]


def seed_temas_atuacao(model_name: str = "BAAI/bge-m3") -> int:
    """Insere e vetoriza os 20 temas canônicos."""
    logger.info("Carregando modelo de embeddings %s...", model_name)
    model = SentenceTransformer(model_name)

    session = SessionLocal()
    total_inseridos = 0

    try:
        for idx, item in enumerate(TEMAS_CANONICOS, start=1):
            texto_para_embedding = f"{item['nome']}: {item['descricao']}"
            vector = model.encode(
                texto_para_embedding, normalize_embeddings=True
            ).tolist()

            stmt = insert(TemaAtuacao).values(
                slug=item["slug"],
                nome=item["nome"],
                descricao=item["descricao"],
                ordem=idx,
                ativo=True,
                embedding=vector,
            )

            stmt_upsert = stmt.on_conflict_do_update(
                index_elements=["slug"],
                set_={
                    "nome": item["nome"],
                    "descricao": item["descricao"],
                    "ordem": idx,
                    "ativo": True,
                    "embedding": vector,
                },
            )

            session.execute(stmt_upsert)
            total_inseridos += 1
            logger.info("Tema processado: [%d/20] %s", idx, item["nome"])

        session.commit()
        logger.info(
            "Sucesso! %d temas canônicos sincronizados em temasAtuacao.",
            total_inseridos,
        )
        return total_inseridos
    except Exception as e:
        session.rollback()
        logger.error("Erro ao sincronizar temas de atuação: %s", e)
        raise
    finally:
        session.close()


if __name__ == "__main__":
    seed_temas_atuacao()
