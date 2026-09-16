import re

with open('.worktrees/spec-009-novas-metricas/backend/services/metricas_factuais.py', 'r') as f:
    content = f.read()

new_func = """async def get_resumo_metricas_factuais(db: AsyncSession):
    from shared.models import Deputado, Voto, VotacaoOrientacao

    # 1. Total Gasto por Deputado
    stmt_gastos = select(
        Despesa.idDeputado, func.sum(Despesa.valorLiquido).label("total_gasto")
    ).group_by(Despesa.idDeputado)
    res_gastos = await db.execute(stmt_gastos)
    gastos_dict = {row.idDeputado: float(row.total_gasto or 0.0) for row in res_gastos.all()}

    # 2. Total Proposicoes (Autor)
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

    # 4. Total Discursos
    stmt_disc = select(
        Discurso.idDeputado, func.count(Discurso.id).label("total_disc")
    ).group_by(Discurso.idDeputado)
    res_disc = await db.execute(stmt_disc)
    disc_dict = {row.idDeputado: row.total_disc for row in res_disc.all()}

    # 5. Total Relatorias
    stmt_rel = (
        select(Deputado.id, func.count(Proposicao.id).label("total_rel"))
        .join(Proposicao, Proposicao.ultimoStatus_uriRelator == Deputado.uri)
        .group_by(Deputado.id)
    )
    res_rel = await db.execute(stmt_rel)
    rel_dict = {row.id: row.total_rel for row in res_rel.all()}

    # 6. Fidelidade Partidaria e Votos Nominais
    stmt_fidelidade = select(
        Voto.idDeputado,
        func.count(Voto.id).label("total_votos"),
        func.sum(
            func.case(
                (Voto.voto == VotacaoOrientacao.orientacao, 1),
                else_=0
            )
        ).label("votos_fieis")
    ).select_from(Voto).join(
        VotacaoOrientacao, Voto.idVotacao == VotacaoOrientacao.idVotacao
    ).where(
        VotacaoOrientacao.siglaBancada.like(func.concat('%', Voto.siglaPartido, '%'))
    ).group_by(Voto.idDeputado)
    
    res_fid = await db.execute(stmt_fidelidade)
    fid_dict = {}
    votos_dict = {}
    for row in res_fid.all():
        votos_dict[row.idDeputado] = row.total_votos
        if row.total_votos > 0:
            fid_dict[row.idDeputado] = (row.votos_fieis / row.total_votos) * 100.0
        else:
            fid_dict[row.idDeputado] = None

    # Busca deputados
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
                "totalDiscursos": disc_dict.get(d.id, 0),
                "totalVotosNominais": votos_dict.get(d.id, 0),
                "fidelidadePartidaria": fid_dict.get(d.id, None),
                "totalRelatorias": rel_dict.get(d.id, 0),
            }
        )
    return resultados"""

content = re.sub(r'async def get_resumo_metricas_factuais\(db: AsyncSession\):.*', new_func, content, flags=re.DOTALL)

with open('.worktrees/spec-009-novas-metricas/backend/services/metricas_factuais.py', 'w') as f:
    f.write(content)
