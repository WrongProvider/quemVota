"""
performance_calc.py — Fonte única da verdade para o cálculo de score parlamentar.

Importado por DeputadoService e RankingService para garantir que ambos
produzam resultados 100% idênticos a partir dos mesmos dados brutos.

Dados brutos esperados (dict ou Mapping):
  - id               int
  - nome             str
  - siglaUF          str | None
  - siglaPartido     str
  - urlFoto          str | None
  - nota_assiduidade float   — (presencas / total_sessoes) * 100, calculado no SQL
  - pontos_producao  float   — soma ponderada de proposições (calculada no SQL/repo)
  - total_gasto      float
  - meses_mandato    int     — meses distintos com despesa registrada
"""

# ---------------------------------------------------------------------------
# Cotas mensais por UF — fonte: Câmara dos Deputados 2025
# ---------------------------------------------------------------------------
_COTAS_POR_UF: dict[str, float] = {
    "AC": 50_426.26, "AL": 46_737.90, "AM": 49_363.92, "AP": 49_168.58,
    "BA": 44_804.65, "CE": 48_245.57, "DF": 36_582.46, "ES": 43_217.71,
    "GO": 41_300.86, "MA": 47_945.49, "MG": 41_886.51, "MS": 46_336.64,
    "MT": 45_221.83, "PA": 48_021.25, "PB": 47_826.36, "PE": 47_470.60,
    "PI": 46_765.57, "PR": 44_665.66, "RJ": 41_553.77, "RN": 48_525.79,
    "RO": 49_466.29, "RR": 51_406.33, "RS": 46_669.70, "SC": 45_671.58,
    "SE": 45_933.06, "SP": 42_837.33, "TO": 45_297.41,
}
_COTA_PADRAO = 40_000.0

# Pesos do score de performance
_PESO_ASSIDUIDADE = 0.15
_PESO_ECONOMIA    = 0.40
_PESO_PRODUCAO    = 0.45

# Meta de pontos de produção por mês para nota máxima (100)
_META_PRODUCAO_MES = 2.0


def resolve_cota_mensal(siglaUF: str | None) -> float:
    """Retorna a cota mensal para a UF informada, com fallback seguro."""
    if siglaUF and siglaUF.upper() in _COTAS_POR_UF:
        return _COTAS_POR_UF[siglaUF.upper()]
    return _COTA_PADRAO


def calcular_score(p: dict, meses_override: int | None = None) -> dict:
    """
    Calcula o score de performance de um parlamentar a partir dos dados brutos.

    Fórmula:
        score = assiduidade × 15% + economia × 40% + produção × 45%

    Args:
        p: dict com os campos brutos do repositório.
        meses_override: quando fornecido, substitui p["meses_mandato"].
            Use para cálculos anuais (timeline), onde meses_mandato deve
            refletir apenas os meses ativos naquele ano (1–12), não o
            mandato inteiro.

    Retorna um dict no formato padrão da API, incluindo chave "_meta"
    com informações auxiliares (removida pelo service antes de expor ao cliente).
    """
    meses = max(meses_override or int(p["meses_mandato"]), 1)

    # --- 1. Assiduidade (0–100): já calculada no SQL ---
    nota_assiduidade = float(p["nota_assiduidade"])

    # --- 2. Produção (0–100, capped): pontos ponderados vs. meta ---
    meta_producao = meses * _META_PRODUCAO_MES
    nota_producao = (
        min((float(p["pontos_producao"]) / meta_producao) * 100, 100.0)
        if meta_producao > 0
        else 0.0
    )

    # --- 3. Economia (0–100): quanto do orçamento total não foi gasto ---
    # Aceita tanto "siglaUF" (novo modelo) quanto "uf" (legado) para compatibilidade
    uf = p.get("siglaUF") or p.get("uf")
    cota_mensal  = resolve_cota_mensal(uf)
    cota_total   = cota_mensal * meses

    # Verba de gabinete: constante nacional (R$ 112.320,26/mês — 2025)
    _VERBA_GABINETE_MENSAL = 112_320.26
    verba_gabinete_total = _VERBA_GABINETE_MENSAL * meses

    gasto_ceap     = float(p["total_gasto"])
    gasto_gabinete = float(p.get("gasto_gabinete") or 0.0)
    gasto_total    = gasto_ceap + gasto_gabinete
    orcamento_total = cota_total + verba_gabinete_total

    # Ausência de dados: todo deputado usa CEAP e verba de gabinete por obrigação
    # institucional. gasto_total = 0 indica dados não registrados, não economia real.
    # Nesses casos aplicamos nota neutra (50) para não inflar artificialmente o score.
    if gasto_total == 0.0:
        nota_economia = 50.0
    elif orcamento_total > 0:
        nota_economia = max(0.0, ((orcamento_total - gasto_total) / orcamento_total) * 100)
    else:
        nota_economia = 50.0

    score_final = (
        nota_assiduidade * _PESO_ASSIDUIDADE
        + nota_economia   * _PESO_ECONOMIA
        + nota_producao   * _PESO_PRODUCAO
    )

    return {
        "id":      p["id"],
        "nome":    p["nome"],
        "uf":      uf,
        "partido": p.get("siglaPartido") or p.get("partido_sigla"),
        "foto":    p.get("urlFoto") or p.get("url_foto"),
        "score":   round(score_final, 2),
        "notas": {
            "assiduidade": round(nota_assiduidade, 2),
            "producao":    round(nota_producao, 2),
            "economia":    round(nota_economia, 2),
        },
        # Campos auxiliares — o service remove antes de expor ao cliente
        "_meta": {
            "cota_mensal":             cota_mensal,
            "cota_total":              cota_total,
            "verba_gabinete_total":    verba_gabinete_total,
            "orcamento_total":         orcamento_total,
            # gasto_ceap mantido como "total_gasto" para retrocompatibilidade
            # com politico_service.py que ainda lê meta["total_gasto"]
            "total_gasto":             gasto_ceap,
            "gasto_ceap":              gasto_ceap,
            "gasto_gabinete":          gasto_gabinete,
            "gasto_total":             gasto_total,
            "meses_mandato":           meses,
            "sem_dados_gastos":        gasto_total == 0.0,
            "orcamento_utilizado_pct": round((gasto_total / orcamento_total) * 100, 2) if orcamento_total > 0 and gasto_total > 0 else 0.0,
            # mantido por retrocompatibilidade
            "cota_utilizada_pct":      round((gasto_ceap / cota_total) * 100, 2) if cota_total > 0 and gasto_ceap > 0 else 0.0,
        },
    }