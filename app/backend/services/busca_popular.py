from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from backend.models import Deputado, BuscaPopular
from typing import List

async def registrar_busca(db: AsyncSession, deputado_id: int) -> None:
    result = await db.execute(
        select(BuscaPopular).filter(BuscaPopular.idDeputado == deputado_id)
    )
    registro = result.scalar_one_or_none()
    if registro:
        registro.count += 1
    else:
        db.add(BuscaPopular(idDeputado=deputado_id, count=1))
    await db.commit()

async def obter_mais_pesquisados(db: AsyncSession, limit: int = 10) -> List[dict]:
    result = await db.execute(
        select(BuscaPopular, Deputado)
        .join(Deputado, BuscaPopular.idDeputado == Deputado.id)
        .order_by(desc(BuscaPopular.count))
        .limit(limit)
    )
    resultados = result.all()

    return [
        {
            "politico_id":   deputado.id,
            "nome":          deputado.nome,
            "uf":            deputado.siglaUF,
            "partido_sigla": deputado.siglaPartido,
            "url_foto":      deputado.urlFoto,
            "count":         busca.count,
        }
        for busca, deputado in resultados
    ]