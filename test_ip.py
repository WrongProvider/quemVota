import asyncio
from sqlalchemy import create_engine, text
engine = create_engine("postgresql+psycopg2://caneta_azul:Arbitrate-Tipoff-Crimp6@172.21.0.8:5432/quemvota")
with engine.begin() as conn:
    print(conn.execute(text("SELECT id, slug FROM deputados WHERE id IN (648, 822)")).fetchall())
