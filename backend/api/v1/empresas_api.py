from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func, desc
from typing import List, Optional
from shared.database import get_db
from shared.models import Despesa, Deputado
from pydantic import BaseModel
from fastapi_cache.decorator import cache

router = APIRouter(prefix="/empresas", tags=["Empresas"])

class EmpresaRankingResponse(BaseModel):
    cnpjCpf: str
    nome: str
    totalRecebido: float
    quantidadeNotas: int

@router.get("/ranking", response_model=List[EmpresaRankingResponse])
@cache(expire=3600)
async def get_ranking_empresas(limit: int = 20, offset: int = 0, db: AsyncSession = Depends(get_db)):
    stmt = (
        select(
            Despesa.cnpjCpfFornecedor,
            func.max(Despesa.nomeFornecedor).label("nome"),
            func.sum(Despesa.valorLiquido).label("total"),
            func.count(Despesa.codDocumento).label("qtd")
        )
        .filter(
            Despesa.cnpjCpfFornecedor != None,
            Despesa.cnpjCpfFornecedor != ""
        )
        .group_by(Despesa.cnpjCpfFornecedor)
        .order_by(desc("total"))
        .limit(limit)
        .offset(offset)
    )
    result = await db.execute(stmt)
    resultados = result.all()

    return [
        {
            "cnpjCpf": r.cnpjCpfFornecedor,
            "nome": r.nome or "NÃO INFORMADO",
            "totalRecebido": float(r.total),
            "quantidadeNotas": r.qtd
        }
        for r in resultados
    ]

class DistPartido(BaseModel):
    partido: str
    total: float

class DistDeputado(BaseModel):
    idDeputado: int
    nomeDeputado: str
    urlFoto: str
    partido: str
    uf: str
    total: float

class EmpresaResumoResponse(BaseModel):
    cnpjCpf: str
    nome: str
    totalRecebido: float
    quantidadeNotas: int
    distribuicaoPartidos: List[DistPartido]
    topDeputados: List[DistDeputado]

@router.get("/{cnpj_cpf:path}/resumo", response_model=EmpresaResumoResponse)
@cache(expire=3600)
async def get_empresa_resumo(cnpj_cpf: str, db: AsyncSession = Depends(get_db)):
    # 1. Total e qtd
    stmt_agregado = (
        select(
            func.max(Despesa.nomeFornecedor).label("nome"),
            func.sum(Despesa.valorLiquido).label("total"),
            func.count(Despesa.codDocumento).label("qtd")
        )
        .filter(Despesa.cnpjCpfFornecedor == cnpj_cpf)
    )
    res_agregado = await db.execute(stmt_agregado)
    agregado = res_agregado.first()

    if not agregado or not agregado.total:
        raise HTTPException(status_code=404, detail="Empresa não encontrada")

    # 2. Partidos
    stmt_partidos = (
        select(
            Deputado.siglaPartido,
            func.sum(Despesa.valorLiquido).label("total")
        )
        .join(Deputado, Despesa.idDeputado == Deputado.idCamara)
        .filter(Despesa.cnpjCpfFornecedor == cnpj_cpf)
        .group_by(Deputado.siglaPartido)
        .order_by(desc("total"))
    )
    res_partidos = await db.execute(stmt_partidos)
    partidos = res_partidos.all()

    # 3. Deputados
    stmt_deputados = (
        select(
            Deputado,
            func.sum(Despesa.valorLiquido).label("total")
        )
        .join(Deputado, Despesa.idDeputado == Deputado.idCamara)
        .filter(Despesa.cnpjCpfFornecedor == cnpj_cpf)
        .group_by(Deputado.id)
        .order_by(desc("total"))
        .limit(10)
    )
    res_deputados = await db.execute(stmt_deputados)
    deputados = res_deputados.all()

    return {
        "cnpjCpf": cnpj_cpf,
        "nome": agregado.nome or "NÃO INFORMADO",
        "totalRecebido": float(agregado.total),
        "quantidadeNotas": agregado.qtd,
        "distribuicaoPartidos": [{"partido": p.siglaPartido or "S/P", "total": float(p.total)} for p in partidos],
        "topDeputados": [
            {
                "idDeputado": d.Deputado.idCamara,
                "nomeDeputado": d.Deputado.nomeEleitoral or d.Deputado.nomeCivil,
                "urlFoto": d.Deputado.urlFoto,
                "partido": d.Deputado.siglaPartido,
                "uf": d.Deputado.siglaUf,
                "total": float(d.total)
            }
            for d in deputados
        ]
    }

class NotaResponse(BaseModel):
    codDocumento: int
    dataDocumento: Optional[str]
    tipoDespesa: str
    valorLiquido: float
    urlDocumento: Optional[str]
    nomeDeputado: str
    idDeputado: int

@router.get("/{cnpj_cpf:path}/notas", response_model=List[NotaResponse])
@cache(expire=3600)
async def get_empresa_notas(cnpj_cpf: str, limit: int = 50, offset: int = 0, db: AsyncSession = Depends(get_db)):
    stmt_notas = (
        select(Despesa, Deputado)
        .join(Deputado, Despesa.idDeputado == Deputado.idCamara)
        .filter(Despesa.cnpjCpfFornecedor == cnpj_cpf)
        .order_by(desc(Despesa.dataDocumento))
        .limit(limit)
        .offset(offset)
    )
    res_notas = await db.execute(stmt_notas)
    notas = res_notas.all()
    
    return [
        {
            "codDocumento": n.Despesa.codDocumento,
            "dataDocumento": n.Despesa.dataDocumento.isoformat() if n.Despesa.dataDocumento else None,
            "tipoDespesa": n.Despesa.tipoDespesa,
            "valorLiquido": float(n.Despesa.valorLiquido),
            "urlDocumento": n.Despesa.urlDocumento,
            "nomeDeputado": n.Deputado.nomeEleitoral or n.Deputado.nomeCivil,
            "idDeputado": n.Deputado.idCamara
        }
        for n in notas
    ]
