import asyncio
from sqlalchemy import create_engine, text
engine = create_engine("postgresql+psycopg2://caneta_azul:Arbitrate-Tipoff-Crimp6@localhost:5432/quemvota")
chunk = [{"id": 648, "slug": "anibal-gomes-1"}, {"id": 822, "slug": "norma-ayub-1"}]
with engine.begin() as conn:
    conn.execute(text("UPDATE deputados SET slug = :slug WHERE id = :id"), chunk)
with engine.begin() as conn:
    print(conn.execute(text("SELECT id, slug FROM deputados WHERE id IN (648, 822)")).fetchall())
