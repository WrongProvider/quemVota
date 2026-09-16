import asyncio
import time
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy import text
from sqlalchemy.orm import sessionmaker

async def main():
    engine = create_async_engine("postgresql+asyncpg://postgres:postgres@localhost:5432/quemvota")
    async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    async with async_session() as db:
        t0 = time.time()
        res = await db.execute(text("""
            SELECT 
                v."idDeputado",
                COUNT(v.id) AS total_votos,
                SUM(CASE WHEN v.voto = o.orientacao THEN 1 ELSE 0 END) AS votos_fieis
            FROM "votacoesVotos" v
            JOIN "votacoesOrientacoes" o ON v."idVotacao" = o."idVotacao"
            WHERE o."siglaBancada" LIKE '%' || v."siglaPartido" || '%'
            GROUP BY v."idDeputado"
        """))
        print(f"Time: {time.time() - t0}")
        print(res.all()[:5])
asyncio.run(main())
