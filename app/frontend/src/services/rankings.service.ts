import {
  getRankingDespesas,
  getRankingLucroEmpresas,
  getRankingDiscursos,
  getRankingPerformance,
  getStatsGeral,
  type RankingDespesaPolitico,
  type RankingEmpresaLucro,
  type RankingDiscursoPolitico,
  type RankingPerformancePolitico,
  type StatsGeral,
} from "../api/rankings.api"

// ============================================
// TIPOS AUXILIARES PARA A UI
// ============================================

export interface RankingFilters {
  searchTerm?: string
  selectedUF?: string
  limit?: number
  offset?: number
}

export interface PaginationInfo {
  currentPage: number
  itemsPerPage: number
  totalItems: number
  hasNextPage: boolean
  hasPreviousPage: boolean
}

// ============================================
// SERVIÇOS DE RANKING
// ============================================

/**
 * Serviço para Rankings de Performance
 */
export class PerformanceRankingService {
  /**
   * Busca o ranking completo de performance
   * Retorna separado: Top 3 (pódio) e o restante
   */
  static async getPerformanceRanking() {
    const data = await getRankingPerformance()
    
    return {
      top3: data.slice(0, 3),
      rest: data.slice(3, 50), // Top 50 parlamentares
      all: data,
    }
  }

  /**
   * Busca as estatísticas gerais (para dashboard/home)
   */
  static async getStats(): Promise<StatsGeral> {
    return await getStatsGeral()
  }

  /**
   * Calcula a posição de um político no ranking geral
   */
  static async getPoliticoPosition(politicoId: number): Promise<number | null> {
    const ranking = await getRankingPerformance()
    const position = ranking.findIndex(p => p.id === politicoId)
    return position === -1 ? null : position + 1
  }

  /**
   * Filtra políticos pelo score (útil para criar faixas de performance)
   */
  static filterByScore(
    politicos: RankingPerformancePolitico[], 
    minScore: number, 
    maxScore: number = 100
  ): RankingPerformancePolitico[] {
    return politicos.filter(p => p.score >= minScore && p.score <= maxScore)
  }
}

/**
 * Serviço para Rankings de Despesas/Gastos
 */
export class DespesaRankingService {
  /**
   * Busca ranking de despesas com filtros aplicados
   */
  static async getDespesasRanking(filters: RankingFilters = {}) {
    const { searchTerm, selectedUF, limit = 100, offset = 0 } = filters

    const data = await getRankingDespesas({
      q: searchTerm || undefined,
      uf: selectedUF || undefined,
      limit,
      offset,
    })

    return data
  }

  /**
   * Busca apenas os top N gastadores
   */
  static async getTopGastadores(limit: number = 10) {
    return await getRankingDespesas({ limit })
  }

  /**
   * Calcula estatísticas do ranking de despesas
   */
  static calcularEstatisticas(data: RankingDespesaPolitico[]) {
    if (data.length === 0) {
      return {
        total: 0,
        media: 0,
        maior: 0,
        menor: 0,
      }
    }

    const valores = data.map(p => p.total_gasto)
    const total = valores.reduce((acc, val) => acc + val, 0)
    
    return {
      total,
      media: total / valores.length,
      maior: Math.max(...valores),
      menor: Math.min(...valores),
    }
  }

  /**
   * Formata valor monetário para exibição
   */
  static formatarValor(valor: number): string {
    return valor.toLocaleString("pt-BR", {
      style: "currency",
      currency: "BRL",
    })
  }
}

/**
 * Serviço para Rankings de Economia (inverso dos gastos)
 */
export class EconomiaRankingService {
  /**
   * Busca os políticos mais econômicos (menores gastos)
   */
  static async getMaisEconomicos(filters: RankingFilters = {}) {
    const { searchTerm, selectedUF, limit = 100, offset = 0 } = filters

    const data = await getRankingDespesas({
      q: searchTerm || undefined,
      uf: selectedUF || undefined,
      limit,
      offset,
    })

    // Inverte a ordem: menores gastos primeiro
    return data.sort((a, b) => a.total_gasto - b.total_gasto)
  }

  /**
   * Calcula percentual de economia baseado na cota
   * (Cota média de R$ 45.000/mês * 48 meses = R$ 2.160.000 total)
   */
  static calcularPercentualEconomia(gastoTotal: number, cotaTotal: number = 2160000): number {
    const economia = cotaTotal - gastoTotal
    return (economia / cotaTotal) * 100
  }
}

/**
 * Serviço para Rankings de Discursos
 */
export class DiscursoRankingService {
  /**
   * Busca ranking de discursos
   */
  static async getDiscursosRanking(limit: number = 100, offset: number = 0) {
    return await getRankingDiscursos({ limit, offset })
  }

  /**
   * Busca os temas mais frequentes entre todos os políticos
   */
  static getTemasMaisFrequentes(
    data: RankingDiscursoPolitico[], 
    topN: number = 20
  ): Array<{ keyword: string; frequencia: number }> {
    const temasMap = new Map<string, number>()

    data.forEach(politico => {
      politico.temas_mais_discutidos.forEach(tema => {
        const current = temasMap.get(tema.keyword) || 0
        temasMap.set(tema.keyword, current + tema.frequencia)
      })
    })

    return Array.from(temasMap.entries())
      .map(([keyword, frequencia]) => ({ keyword, frequencia }))
      .sort((a, b) => b.frequencia - a.frequencia)
      .slice(0, topN)
  }

  /**
   * Filtra políticos por tema específico
   */
  static filtrarPorTema(
    data: RankingDiscursoPolitico[], 
    tema: string
  ): RankingDiscursoPolitico[] {
    return data.filter(politico =>
      politico.temas_mais_discutidos.some(t => 
        t.keyword.toLowerCase().includes(tema.toLowerCase())
      )
    )
  }
}

/**
 * Serviço para Rankings de Empresas
 */
export class EmpresaRankingService {
  /**
   * Busca ranking de empresas que mais receberam
   */
  static async getEmpresasRanking(limit: number = 100, offset: number = 0) {
    return await getRankingLucroEmpresas({ limit, offset })
  }

  /**
   * Busca apenas o top N empresas
   */
  static async getTopEmpresas(limit: number = 10) {
    return await getRankingLucroEmpresas({ limit })
  }

  /**
   * Calcula estatísticas do ranking de empresas
   */
  static calcularEstatisticas(data: RankingEmpresaLucro[]) {
    if (data.length === 0) {
      return {
        total: 0,
        media: 0,
        maior: 0,
        menor: 0,
      }
    }

    const valores = data.map(e => e.total_recebido)
    const total = valores.reduce((acc, val) => acc + val, 0)
    
    return {
      total,
      media: total / valores.length,
      maior: Math.max(...valores),
      menor: Math.min(...valores),
    }
  }

  /**
   * Formata CNPJ para exibição
   */
  static formatarCNPJ(cnpj: string): string {
    if (!cnpj || cnpj.length !== 14) return cnpj
    
    return cnpj.replace(
      /^(\d{2})(\d{3})(\d{3})(\d{4})(\d{2})$/,
      "$1.$2.$3/$4-$5"
    )
  }
}

/**
 * Serviço de Filtros e Busca
 */
export class FilterService {
  /**
   * Lista de todos os estados brasileiros
   */
  static readonly UFs = [
    "AC", "AL", "AM", "AP", "BA", "CE", "DF", "ES", "GO", "MA",
    "MG", "MS", "MT", "PA", "PB", "PE", "PI", "PR", "RJ", "RN",
    "RO", "RR", "RS", "SC", "SE", "SP", "TO"
  ]

  /**
   * Valida se uma UF é válida
   */
  static isValidUF(uf: string): boolean {
    return this.UFs.includes(uf.toUpperCase())
  }

  /**
   * Normaliza termo de busca
   */
  static normalizarBusca(termo: string): string {
    return termo
      .trim()
      .toLowerCase()
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "") // Remove acentos
  }

  /**
   * Cria query string para URL com filtros
   */
  static buildQueryString(filters: RankingFilters): string {
    const params = new URLSearchParams()
    
    if (filters.searchTerm) params.set("q", filters.searchTerm)
    if (filters.selectedUF) params.set("uf", filters.selectedUF)
    if (filters.limit) params.set("limit", String(filters.limit))
    if (filters.offset) params.set("offset", String(filters.offset))
    
    return params.toString()
  }
}

/**
 * Serviço de Paginação
 */
export class PaginationService {
  /**
   * Calcula informações de paginação
   */
  static calcular(
    currentPage: number, 
    itemsPerPage: number, 
    totalItems: number
  ): PaginationInfo {
    const totalPages = Math.ceil(totalItems / itemsPerPage)
    
    return {
      currentPage,
      itemsPerPage,
      totalItems,
      hasNextPage: currentPage < totalPages - 1,
      hasPreviousPage: currentPage > 0,
    }
  }

  /**
   * Calcula offset para a API
   */
  static getOffset(currentPage: number, itemsPerPage: number): number {
    return currentPage * itemsPerPage
  }
}

/**
 * Serviço de Formatação de Dados
 */
export class FormatService {
  /**
   * Formata valor monetário
   */
  static formatarMoeda(valor: number): string {
    return valor.toLocaleString("pt-BR", {
      style: "currency",
      currency: "BRL",
      minimumFractionDigits: 2,
    })
  }

  /**
   * Formata número com separadores
   */
  static formatarNumero(numero: number): string {
    return numero.toLocaleString("pt-BR")
  }

  /**
   * Formata percentual
   */
  static formatarPercentual(valor: number, casasDecimais: number = 2): string {
    return `${valor.toFixed(casasDecimais)}%`
  }

  /**
   * Trunca texto com reticências
   */
  static truncarTexto(texto: string, maxLength: number): string {
    if (texto.length <= maxLength) return texto
    return texto.substring(0, maxLength) + "..."
  }
}