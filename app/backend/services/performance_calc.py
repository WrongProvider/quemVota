"""
performance_calc.py — Fonte única da verdade para o cálculo de score parlamentar.

Importado por PoliticoService e RankingService para garantir que ambos
produzam resultados 100% idênticos a partir dos mesmos dados brutos.

Dados brutos esperados (dict ou Mapping):
  - id               int
  - nome             str
  - uf               str | None
  - partido_sigla    str
  - url_foto         str | None
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


def resolve_cota_mensal(uf: str | None) -> float:
    """Retorna a cota mensal para a UF informada, com fallback seguro."""
    if uf and uf.upper() in _COTAS_POR_UF:
        return _COTAS_POR_UF[uf.upper()]
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

    # --- 3. Economia (0–100): quanto da cota não foi gasto ---
    cota_mensal   = resolve_cota_mensal(p.get("uf"))
    cota_total    = cota_mensal * meses
    gasto         = float(p["total_gasto"])
    nota_economia = (
        max(0.0, ((cota_total - gasto) / cota_total) * 100)
        if cota_total > 0
        else 0.0
    )

    score_final = (
        nota_assiduidade * _PESO_ASSIDUIDADE
        + nota_economia   * _PESO_ECONOMIA
        + nota_producao   * _PESO_PRODUCAO
    )

    return {
        "id":      p["id"],
        "nome":    p["nome"],
        "uf":      p.get("uf"),
        "partido": p["partido_sigla"],
        "foto":    p.get("url_foto"),
        "score":   round(score_final, 2),
        "notas": {
            "assiduidade": round(nota_assiduidade, 2),
            "producao":    round(nota_producao, 2),
            "economia":    round(nota_economia, 2),
        },
        # Campos auxiliares — o service remove antes de expor ao cliente
        "_meta": {
            "cota_mensal":        cota_mensal,
            "cota_total":         cota_total,
            "total_gasto":        gasto,
            "meses_mandato":      meses,
            "cota_utilizada_pct": round((gasto / cota_total) * 100, 2) if cota_total > 0 else 0.0,
        },
    }