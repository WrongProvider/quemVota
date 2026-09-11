from injest_banco.database import engine
from sqlalchemy import MetaData, text
import json
with engine.connect() as conn:
    try:
        conn.execute(text("INSERT INTO \"frentesDeputados\" (\"idFrente\", \"idDeputado\") VALUES (-1, -1)"))
    except Exception as e:
        print(type(e), str(e))
