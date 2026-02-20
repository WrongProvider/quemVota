from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, desc, select
from backend.database import get_db
from backend.models import Politico, Voto, Votacao, Despesa, Proposicao
from backend.schemas import PoliticoEstatisticasResponse, PoliticoDespesaResumoCompleto, PoliticoResponse, PoliticoVoto, PoliticoDespesaResumo, PoliticoDespesaDetalhe, PoliticoFornecedor, VotacaoResumoItem, SerieDespesaItem

from fastapi_cache.decorator import cache   

from backend.services.politico_service import PoliticoService
from backend.api.v1.keybuilder import politico_key_builder

router = APIRouter(
    prefix="/politicos",
    tags=["Políticos"]
)

# Cache Key Builder personalizado para as rotas de político
from fastapi.concurrency import run_in_threadpool # Importe isso
from datetime import datetime

@router.get("/", response_model=list[PoliticoResponse])
@cache(expire=3600, key_builder=politico_key_builder)
async def listar_politicos(
    q: str | None = None,
    uf: str | None = None,
    limit: int = 100,
    offset: int = 0,
    db: AsyncSession = Depends(get_db)
):
    service = PoliticoService(db)
    return await service.get_politicos_service(q=q, uf=uf, limit=limit, offset=offset)

@router.get("/{politico_id}", response_model=PoliticoResponse)
@cache(expire=3600, key_builder=politico_key_builder)
async def get_politico(
    politico_id: int,
    db: AsyncSession = Depends(get_db)
):
    service = PoliticoService(db)
    return await service.get_politicos_detalhe_service(politico_id=politico_id)
    
@router.get("/{politico_id}/votacoes", response_model=list[PoliticoVoto])
@cache(expire=86400, key_builder=politico_key_builder)
async def ultimas_votacoes_do_politico(
    politico_id: int, 
    limit: int = 20, 
    db: AsyncSession = Depends(get_db)
):
    print(f"DEBUG: Buscando votações para o politico {politico_id}")
    service = PoliticoService(db)
        
    return await service.get_politicos_votacoes_service(politico_id=politico_id, limit=limit)

@router.get("/{politico_id}/despesas", response_model=list[PoliticoDespesaDetalhe])
@cache(expire=86400, key_builder=politico_key_builder)  # Cache por 24 horas
async def listar_despesas_detalhadas(
    politico_id: int,
    ano: int | None = None,
    mes: int | None = None,
    limit: int = 20,
    db: AsyncSession = Depends(get_db)
):
    """Lista as despesas individuais com paginação."""
   
    service = PoliticoService(db)
    return await service.get_politicos_despesas_services(politico_id=politico_id, ano=ano, mes=mes, limit=limit)

@router.get("/{politico_id}/despesas/resumo", response_model=list[PoliticoDespesaResumo])
@cache(expire=86400, key_builder=politico_key_builder)  # Cache por 24 horas
async def resumo_despesas_do_politico(
    politico_id: int, 
    ano: int | None = None,
    limit: int = 60,
    db: AsyncSession = Depends(get_db)):
    # Agora a função é ASYNC
    print(f"DEBUG: Calculando resumo no banco para o politico {politico_id} {datetime.now().time()}")
    
    service = PoliticoService(db)
    return await service.get_politicos_despesas_resumo_services(politico_id=politico_id, ano=ano, limit=limit)
  

@router.get("/{politico_id}/despesas/resumo_completo", response_model=PoliticoDespesaResumoCompleto)
@cache(expire=86400, key_builder=politico_key_builder)  # Cache por 24 horas
async def resumo_despesas_completo_do_politico(
    politico_id: int, 
    ano: int | None = None,
    limit_meses: int = 60,
    db: AsyncSession = Depends(get_db)):
    # Agora a função é ASYNC
    print(f"DEBUG: Calculando resumo no banco para o politico {politico_id} {datetime.now().time()}")
    
    service = PoliticoService(db)
    return await service.get_politicos_despesas_resumo_completo_services(politico_id=politico_id, ano=ano, limit_meses=limit_meses)
  


@router.get("/{politico_id}/despesas/fornecedores", response_model=list[PoliticoFornecedor])
@cache(expire=86400, key_builder=politico_key_builder)
async def ranking_fornecedores_do_politico(
    politico_id: int, 
    limit: int = 10, 
    db: Session = Depends(get_db)
):
    print(f"DEBUG: Gerando ranking de fornecedores para o politico {politico_id}")
    
    def get_ranking():
        stmt = (
            select(
                Despesa.nome_fornecedor,
                func.sum(Despesa.valor_liquido).label("total_recebido"),
                func.count(Despesa.id).label("qtd_notas")
            )
            .where(Despesa.politico_id == politico_id)
            .group_by(Despesa.nome_fornecedor)
            .order_by(func.sum(Despesa.valor_liquido).desc())
            .limit(limit)
        )

        return db.execute(stmt).mappings().all()

    return await run_in_threadpool(get_ranking)


@router.get("/{politico_id}/estatisticas",response_model=PoliticoEstatisticasResponse
)
@cache(expire=86400, key_builder=politico_key_builder)
async def estatisticas_do_politico(
    politico_id: int,
    db: AsyncSession = Depends(get_db)
):
    service = PoliticoService(db)
    return await service.get_politico_estatisticas_service(politico_id=politico_id)
 

@router.get("/{politico_id}/performance", response_model=dict)
@cache(expire=86400, key_builder=politico_key_builder)
async def performance_do_politico(
    politico_id: int,
    db: AsyncSession = Depends(get_db)
):
    service = PoliticoService(db)
    return await service.get_politico_performance_service(politico_id=politico_id)
