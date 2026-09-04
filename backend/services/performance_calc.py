"""
performance_calc.py — Consolidação de indicadores factuais de mandato parlamentar.

Adere estritamente ao Princípio da Neutralidade Factual Absoluta (AGENTS.md):
Não emite scores unificados, notas avaliativas (0 a 100) ou pesos subjetivos.
Consolida métricas descritivas e auditáveis a partir de dados abertos oficiais da Câmara.

Dados brutos esperados (dict ou Mapping):
  - id               int
  - nome             str
  - siglaUF          str | None
  - siglaPartido     str
  - urlFoto          str | None
  - nota_assiduidade float   — (presencas / total_sessoes) * 100, calculado no SQL
  - pontos_producao  float   — total de proposições com autoria (calculado no SQL/repo)
  - total_gasto      float   — despesas CEAP
  - meses_mandato    int     — meses distintos com despesa registrada
"""

# ---------------------------------------------------------------------------
# Cotas mensais por UF — fonte: Câmara dos Deputados 2025
# ---------------------------------------------------------------------------
_COTAS_POR_UF: dict[str, float] = {
    "AC": 50_426.26,
    "AL": 46_737.90,
    "AM": 49_363.92,
    "AP": 49_168.58,
    "BA": 44_804.65,
    "CE": 48_245.57,
    "DF": 36_582.46,
    "ES": 43_217.71,
    "GO": 41_300.86,
    "MA": 47_945.49,
    "MG": 41_886.51,
    "MS": 46_336.64,
    "MT": 45_221.83,
    "PA": 48_021.25,
    "PB": 47_826.36,
    "PE": 47_470.60,
    "PI": 46_765.57,
    "PR": 44_665.66,
    "RJ": 41_553.77,
    "RN": 48_525.79,
    "RO": 49_466.29,
    "RR": 51_406.33,
    "RS": 46_669.70,
    "SC": 45_671.58,
    "SE": 45_933.06,
    "SP": 42_837.33,
    "TO": 45_297.41,
}
_COTA_PADRAO = 40_000.0


def resolve_cota_mensal(siglaUF: str | None) -> float:
    """Retorna a cota mensal para a UF informada, com fallback seguro."""
    if siglaUF and siglaUF.upper() in _COTAS_POR_UF:
        return _COTAS_POR_UF[siglaUF.upper()]
    return _COTA_PADRAO


def calcular_score(p: dict, meses_override: int | None = None) -> dict:
    """
    Consolida os indicadores de mandato a partir dos dados brutos oficiais.

    Em conformidade com a Neutralidade Factual, não emite scores ou notas ponderadas.
    Retorna métricas factuais desagregadas e transparentes.
    """
    meses = max(meses_override or int(p.get("meses_mandato") or 1), 1)

    # Assiduidade factual (% de presenças nas sessões oficiais deliberativas)
    nota_assiduidade = float(p.get("nota_assiduidade") or 0.0)

    # Produção legislativa (total de proposições com autoria)
    pontos_producao = float(p.get("pontos_producao") or 0.0)

    # Execução orçamentária
    uf = p.get("siglaUF") or p.get("uf")
    cota_mensal = resolve_cota_mensal(uf)
    cota_total = cota_mensal * meses

    # Verba de gabinete: constante nacional (R$ 112.320,26/mês — 2025)
    _VERBA_GABINETE_MENSAL = 112_320.26
    verba_gabinete_total = _VERBA_GABINETE_MENSAL * meses

    gasto_ceap = float(p.get("total_gasto") or 0.0)
    gasto_gabinete = float(p.get("gasto_gabinete") or 0.0)
    gasto_total = gasto_ceap + gasto_gabinete
    orcamento_total = cota_total + verba_gabinete_total

    orcamento_utilizado_pct = (
        round((gasto_total / orcamento_total) * 100, 2)
        if orcamento_total > 0 and gasto_total > 0
        else 0.0
    )
    cota_utilizada_pct = (
        round((gasto_ceap / cota_total) * 100, 2)
        if cota_total > 0 and gasto_ceap > 0
        else 0.0
    )

    return {
        "id": p["id"],
        "nome": p["nome"],
        "uf": uf,
        "partido": p.get("siglaPartido") or p.get("partido_sigla"),
        "foto": p.get("urlFoto") or p.get("url_foto"),
        # Neutralidade Factual: score avaliativo descontinuado
        "score": None,
        "notas": {
            "assiduidade": round(nota_assiduidade, 2),
            "producao": round(pontos_producao, 2),
            "economia": round(100.0 - orcamento_utilizado_pct, 2)
            if orcamento_total > 0
            else 0.0,
        },
        "metricas": {
            "assiduidade_pct": round(nota_assiduidade, 2),
            "total_proposicoes": round(pontos_producao, 2),
            "gasto_ceap": round(gasto_ceap, 2),
            "gasto_gabinete": round(gasto_gabinete, 2),
            "gasto_total": round(gasto_total, 2),
            "orcamento_total": round(orcamento_total, 2),
            "orcamento_utilizado_pct": orcamento_utilizado_pct,
            "cota_utilizada_pct": cota_utilizada_pct,
            "meses_mandato": meses,
        },
        "_meta": {
            "cota_mensal": cota_mensal,
            "cota_total": cota_total,
            "verba_gabinete_total": verba_gabinete_total,
            "orcamento_total": orcamento_total,
            "total_gasto": gasto_ceap,
            "gasto_ceap": gasto_ceap,
            "gasto_gabinete": gasto_gabinete,
            "gasto_total": gasto_total,
            "meses_mandato": meses,
            "sem_dados_gastos": gasto_total == 0.0,
            "orcamento_utilizado_pct": orcamento_utilizado_pct,
            "cota_utilizada_pct": cota_utilizada_pct,
        },
    }
