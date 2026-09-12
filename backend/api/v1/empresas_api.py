from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from typing import List, Optional
from backend.database import get_db
from shared.models import Despesa, Deputado
from pydantic import BaseModel

router = APIRouter(prefix="/empresas", tags=["Empresas"])

class EmpresaRankingResponse(BaseModel):
    cnpjCpf: str
    nome: str
    totalRecebido: float
    quantidadeNotas: int

@router.get("/ranking", response_model=List[EmpresaRankingResponse])
def get_ranking_empresas(limit: int = 20, offset: int = 0, db: Session = Depends(get_db)):
    resultados = db.query(
        Despesa.cnpjCpfFornecedor,
        func.max(Despesa.nomeFornecedor).label("nome"),
        func.sum(Despesa.valorLiquido).label("total"),
        func.count(Despesa.codDocumento).label("qtd")
    ).filter(
        Despesa.cnpjCpfFornecedor != None,
        Despesa.cnpjCpfFornecedor != ""
    ).group_by(
        Despesa.cnpjCpfFornecedor
    ).order_by(
        desc("total")
    ).limit(limit).offset(offset).all()

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

@router.get("/{cnpj_cpf}/resumo", response_model=EmpresaResumoResponse)
def get_empresa_resumo(cnpj_cpf: str, db: Session = Depends(get_db)):
    # 1. Total e qtd
    agregado = db.query(
        func.max(Despesa.nomeFornecedor).label("nome"),
        func.sum(Despesa.valorLiquido).label("total"),
        func.count(Despesa.codDocumento).label("qtd")
    ).filter(Despesa.cnpjCpfFornecedor == cnpj_cpf).first()

    if not agregado or not agregado.total:
        raise HTTPException(status_code=404, detail="Empresa não encontrada")

    # 2. Partidos
    partidos = db.query(
        Deputado.siglaPartido,
        func.sum(Despesa.valorLiquido).label("total")
    ).join(Deputado, Despesa.idDeputado == Deputado.idCamara)\
     .filter(Despesa.cnpjCpfFornecedor == cnpj_cpf)\
     .group_by(Deputado.siglaPartido)\
     .order_by(desc("total")).all()

    # 3. Deputados
    deputados = db.query(
        Deputado,
        func.sum(Despesa.valorLiquido).label("total")
    ).join(Deputado, Despesa.idDeputado == Deputado.idCamara)\
     .filter(Despesa.cnpjCpfFornecedor == cnpj_cpf)\
     .group_by(Deputado.id)\
     .order_by(desc("total")).limit(10).all()

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

@router.get("/{cnpj_cpf}/notas", response_model=List[NotaResponse])
def get_empresa_notas(cnpj_cpf: str, limit: int = 50, offset: int = 0, db: Session = Depends(get_db)):
    notas = db.query(Despesa, Deputado).join(Deputado, Despesa.idDeputado == Deputado.idCamara)\
              .filter(Despesa.cnpjCpfFornecedor == cnpj_cpf)\
              .order_by(desc(Despesa.dataDocumento))\
              .limit(limit).offset(offset).all()
    
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
