import hashlib

from sentence_transformers import SentenceTransformer
from sqlalchemy.dialects.postgresql import insert
from shared.database import SessionLocal
from shared.models import Proposicao
from shared.models_vetorial import DocumentEmbedding

model = SentenceTransformer("BAAI/bge-m3")

session = SessionLocal()


def gerar_embeddings():
    proposicoes = session.query(Proposicao).outerjoin(
                DocumentEmbedding,
                (DocumentEmbedding.idEntidade == Proposicao.id) &
                (DocumentEmbedding.tipoEntidade == "proposicao") &
        (DocumentEmbedding.modelo == "BAAI/bge-m3")
    ).filter(DocumentEmbedding.id.is_(None)).limit(10).all()

    if not proposicoes:
        print("Nenhuma proposição encontrada para processar.")
        return

    for proposicao in proposicoes:
        print(f"Processando proposição {proposicao.id}")
        texto = f"""
        {proposicao.ementa or ""}
        {proposicao.ementaDetalhada or ""}
        {proposicao.justificativa or ""}
        """
        texto_hash = hashlib.sha256(texto.strip().encode("utf-8")).hexdigest()

        embedding = model.encode(texto, normalize_embeddings=True).tolist()

        stmt = insert(DocumentEmbedding).values(
            tipoEntidade="proposicao",
            idEntidade=proposicao.id,
            textoFonte=texto,
            textoHash=texto_hash,
            embedding=embedding,
            modelo="BAAI/bge-m3",
            dimensao=1024,
        )

        stmt_up = stmt.on_conflict_do_update(
            index_elements=[],
            set_={
                "textoFonte": texto,
                "textoHash": texto_hash,
                "embedding": embedding,
                "modelo": "BAAI/bge-m3",
                "dimensao": 1024,
            },
        )
        session.execute(stmt_up)
    session.commit()


if __name__ == "__main__":
    gerar_embeddings()
    session.close()
