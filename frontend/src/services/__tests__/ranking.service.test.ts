import { describe, it, expect } from "vitest"
import { DespesaRankingService, FormatService, FilterService } from "../ranking.service"

describe("FormatService", () => {
  it("formata moeda em reais corretamente", () => {
    const resultado = FormatService.formatarMoeda(1500.5)
    expect(resultado).toBe("R$ 1.500,50")
  })

  it("trunca texto longo", () => {
    const resultado = FormatService.truncarTexto("Texto muito longo aqui", 10)
    expect(resultado).toBe("Texto much...")
  })
})

describe("FilterService", () => {
  it("valida UFs brasileiras corretamente", () => {
    expect(FilterService.isValidUF("SP")).toBe(true)
    expect(FilterService.isValidUF("XX")).toBe(false)
  })
})

describe("DespesaRankingService", () => {
  it("calcula estatísticas de despesas corretamente", () => {
    const dados = [
      { politico_id: 1, nome: "João", total_gasto: 10000 },
      { politico_id: 2, nome: "Maria", total_gasto: 20000 },
    ]

    const stats = DespesaRankingService.calcularEstatisticas(dados)

    expect(stats.total).toBe(30000)
    expect(stats.media).toBe(15000)
    expect(stats.maior).toBe(20000)
    expect(stats.menor).toBe(10000)
  })

  it("retorna zeros para lista vazia", () => {
    const stats = DespesaRankingService.calcularEstatisticas([])
    expect(stats.total).toBe(0)
  })
})