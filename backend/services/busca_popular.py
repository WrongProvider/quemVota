from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, extract
from sqlalchemy.orm import aliased
from shared.models import Deputado, BuscaPopular, Legislatura, Voto, OrgaoDeputado

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
    LegIni = aliased(Legislatura, name="leg_ini")
    LegFim = aliased(Legislatura, name="leg_fim")

    stmt = (
        select(
            BuscaPopular,
            Deputado,
            extract("year", LegIni.dataInicio).label("ano_inicio"),
            extract("year", LegFim.dataFim).label("ano_fim"),
        )
        .join(Deputado, BuscaPopular.idDeputado == Deputado.id)
        .outerjoin(LegIni, LegIni.idLegislatura == Deputado.idLegislaturaInicial)
        .outerjoin(LegFim, LegFim.idLegislatura == Deputado.idLegislaturaFinal)
        .order_by(desc(BuscaPopular.count))
        .limit(limit)
    )

    result = await db.execute(stmt)
    resultados = result.all()

    items = []
    for busca, deputado, ano_ini, ano_fim in resultados:
        uf = deputado.siglaUF
        partido = deputado.siglaPartido

        if not uf or not partido:
            voto_stmt = (
                select(Voto.siglaPartido, Voto.siglaUF)
                .where(Voto.idDeputado == deputado.id, Voto.siglaPartido.isnot(None))
                .order_by(Voto.id.desc())
                .limit(1)
            )
            voto_res = await db.execute(voto_stmt)
            row = voto_res.first()
            if row:
                if not partido and row[0]:
                    partido = row[0]
                if not uf and row[1]:
                    uf = row[1]

        if not uf or not partido:
            orgao_stmt = (
                select(OrgaoDeputado.siglaPartido, OrgaoDeputado.siglaUF)
                .where(OrgaoDeputado.idDeputado == deputado.id, OrgaoDeputado.siglaPartido.isnot(None))
                .order_by(OrgaoDeputado.id.desc())
                .limit(1)
            )
            orgao_res = await db.execute(orgao_stmt)
            row_o = orgao_res.first()
            if row_o:
                if not partido and row_o[0]:
                    partido = row_o[0]
                if not uf and row_o[1]:
                    uf = row_o[1]

        items.append(
            {
                "politico_id": deputado.id,
                "nome": deputado.nome,
                "uf": uf,
                "partido_sigla": partido,
                "url_foto": deputado.urlFoto,
                "count": busca.count,
                "slug": deputado.slug or None,
                "condicao_eleitoral": deputado.condicaoEleitoral,
                "id_legislatura_inicial": deputado.idLegislaturaInicial,
                "id_legislatura_final": deputado.idLegislaturaFinal,
                "ano_inicio": int(ano_ini) if ano_ini is not None else None,
                "ano_fim": int(ano_fim) if ano_fim is not None else None,
            }
        )

    return items