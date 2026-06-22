import hashlib

from sentence_transformers import SentenceTransformer

from shared.database import SessionLocal
from shared.models import Proposicao
from shared.models_vetorial import DocumentEmbedding

model = SentenceTransformer("BAAI/bge-m3")

session = SessionLocal()


def gerar_embeddings():
    proposicoes = session.query(Proposicao).limit(10).all()

    for proposicao in proposicoes:
        print(f"Processando proposição {proposicao.id}")
        texto = f"""
        {proposicao.ementa or ""}
        {proposicao.ementaDetalhada or ""}
        {proposicao.justificativa or ""}
        """
        texto_hash = hashlib.sha256(texto.strip().encode("utf-8")).hexdigest()

        embedding = model.encode(texto, normalize_embeddings=True).tolist()

        registro = DocumentEmbedding(
            tipoEntidade="proposicao",
            idEntidade=proposicao.id,
            textoFonte=texto,
            textoHash=texto_hash,
            embedding=embedding,
            modelo="BAAI/bge-m3",
            dimensao=1024,
        )

        session.add(registro)
    session.commit()


if __name__ == "__main__":
    gerar_embeddings()
    session.close()
