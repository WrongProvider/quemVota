from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from sqlalchemy.exc import SQLAlchemyError
import logging

from shared.models import (
    Despesa,
    Proposicao,
    ProposicaoAutor,
    PresencaDeputado,
    Discurso,
)
from backend.schemas import (
    CategoriaGasto,
    TipoProposicao,
    MetricasDeputado,
)

logger = logging.getLogger(__name__)


async def get_metricas_factuais(db: AsyncSession, deputado_id: int) -> MetricasDeputado:
    try:
        # 1. Total Gasto
        stmt_total_gasto = select(func.sum(Despesa.valorLiquido)).where(
            Despesa.idDeputado == deputado_id
        )
        res_total_gasto = await db.execute(stmt_total_gasto)
        total_gasto = res_total_gasto.scalar() or 0.0

        # Top Gastos
        stmt_top_gastos = (
            select(Despesa.tipoDespesa, func.sum(Despesa.valorLiquido).label("total"))
            .where(Despesa.idDeputado == deputado_id)
            .group_by(Despesa.tipoDespesa)
            .order_by(desc("total"))
            .limit(5)
        )
        res_top_gastos = await db.execute(stmt_top_gastos)
        top_gastos = [
            CategoriaGasto(
                tipoDespesa=row[0] or "Não informado", valorTotal=float(row[1] or 0.0)
            )
            for row in res_top_gastos.all()
        ]

        # 2. Produção Legislativa
        stmt_total_prop = (
            select(func.count(Proposicao.id))
            .join(ProposicaoAutor, Proposicao.id == ProposicaoAutor.idProposicao)
            .where(
                ProposicaoAutor.idDeputadoAutor == deputado_id,
                ProposicaoAutor.proponente.is_(True),
            )
        )
        res_total_prop = await db.execute(stmt_total_prop)
        total_proposicoes = res_total_prop.scalar() or 0

        stmt_dist_prop = (
            select(Proposicao.siglaTipo, func.count(Proposicao.id).label("total"))
            .join(ProposicaoAutor, Proposicao.id == ProposicaoAutor.idProposicao)
            .where(
                ProposicaoAutor.idDeputadoAutor == deputado_id,
                ProposicaoAutor.proponente.is_(True),
            )
            .group_by(Proposicao.siglaTipo)
            .order_by(desc("total"))
        )
        res_dist_prop = await db.execute(stmt_dist_prop)
        dist_prop = [
            TipoProposicao(sigla=row[0] or "N/A", quantidade=row[1] or 0)
            for row in res_dist_prop.all()
        ]

        # 3. Assiduidade
        stmt_presencas = select(func.count(PresencaDeputado.id)).where(
            PresencaDeputado.idDeputado == deputado_id
        )
        res_presencas = await db.execute(stmt_presencas)
        total_presencas = res_presencas.scalar() or 0

        # 4. Discursos
        stmt_discursos = select(func.count(Discurso.id)).where(
            Discurso.idDeputado == deputado_id
        )
        res_discursos = await db.execute(stmt_discursos)
        total_discursos = res_discursos.scalar() or 0

        return MetricasDeputado(
            idDeputado=deputado_id,
            totalGastoCota=float(total_gasto),
            topGastos=top_gastos,
            totalProposicoesAutor=total_proposicoes,
            distribuicaoProposicoes=dist_prop,
            totalPresencas=total_presencas,
            totalDiscursos=total_discursos,
        )

    except SQLAlchemyError as e:
        logger.exception(f"Erro ao buscar metricas factuais do deputado {deputado_id}")
        raise e


async def get_resumo_metricas_factuais(db: AsyncSession):
    # Retorna uma lista de métricas factuais sumarizadas (Apenas o total)
    # Por limitações de performance, podemos agregar tudo em queries separadas e fazer join na memoria,
    # ou retornar apenas um esqueleto. Como há muitos deputados, uma query otimizada é necessária.
    # Mas para o escopo inicial e como o banco não deve estar colossal em qtd de políticos (513 deputados ativos):

    # 1. Total Gasto por Deputado
    stmt_gastos = select(
        Despesa.idDeputado, func.sum(Despesa.valorLiquido).label("total_gasto")
    ).group_by(Despesa.idDeputado)
    res_gastos = await db.execute(stmt_gastos)
    gastos_dict = {
        row.idDeputado: float(row.total_gasto or 0.0) for row in res_gastos.all()
    }

    # 2. Total Proposicoes
    stmt_prop = (
        select(
            ProposicaoAutor.idDeputadoAutor,
            func.count(Proposicao.id).label("total_prop"),
        )
        .join(Proposicao, Proposicao.id == ProposicaoAutor.idProposicao)
        .where(ProposicaoAutor.proponente.is_(True))
        .group_by(ProposicaoAutor.idDeputadoAutor)
    )
    res_prop = await db.execute(stmt_prop)
    prop_dict = {row.idDeputadoAutor: row.total_prop for row in res_prop.all()}

    # 3. Total Presencas
    stmt_pres = select(
        PresencaDeputado.idDeputado, func.count(PresencaDeputado.id).label("total_pres")
    ).group_by(PresencaDeputado.idDeputado)
    res_pres = await db.execute(stmt_pres)
    pres_dict = {row.idDeputado: row.total_pres for row in res_pres.all()}

    # Busca deputados
    from shared.models import Deputado
    from sqlalchemy.orm import selectinload

    stmt_dep = select(Deputado).options(selectinload(Deputado.partido)).limit(600)
    res_dep = await db.execute(stmt_dep)
    deputados = res_dep.scalars().all()

    resultados = []
    for d in deputados:
        resultados.append(
            {
                "idDeputado": d.id,
                "nome": d.nome,
                "partido": d.siglaPartido,
                "uf": d.siglaUF,
                "urlFoto": d.urlFoto,
                "totalGastoCota": gastos_dict.get(d.id, 0.0),
                "totalProposicoesAutor": prop_dict.get(d.id, 0),
                "totalPresencas": pres_dict.get(d.id, 0),
            }
        )
    return resultados
