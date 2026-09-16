from shared.database import SessionLocal
from shared.models import Proposicao, Votacao
from sqlalchemy import exists, select

session = SessionLocal()
q = session.query(Proposicao).filter(exists().where(Votacao.idProposicao == Proposicao.id))
print("Votadas:", q.count())
