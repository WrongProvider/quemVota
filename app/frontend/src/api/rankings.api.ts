import { api } from "./client"

// ============================================
// INTERFACES - Baseadas nos Schemas do Backend
// ============================================

export interface RankingDespesaPolitico {
  politico_id: number
  nome: string
  total_gasto: number
}

export interface RankingEmpresaLucro {
  cnpj: string
  nome_fornecedor: string
  total_recebido: number
}

export interface KeywordInfo {
  keyword: string
  frequencia: number
}

export interface RankingDiscursoPolitico {
  politico_id: number
  nome_politico: string
  sigla_partido: string
  sigla_uf: string
  total_discursos: number
  temas_mais_discutidos: KeywordInfo[]
}

export interface NotasPerformance {
  assiduidade: number
  producao: number
  economia: number
}

export interface RankingPerformancePolitico {
  id: number
  nome: string
  uf: string        // campo retornado por performance_calc.py
  partido: string   // campo retornado por performance_calc.py
  foto: string      // campo retornado por performance_calc.py
  score: number
  notas: NotasPerformance
  /** Quantos anos calendário têm dados de despesas para este parlamentar */
  anos_com_dados: number
  /** "baixa" = 1 ano | "media" = 2-3 anos | "alta" = 4+ anos (legislatura completa) */
  confianca: "baixa" | "media" | "alta"
}

export interface StatsGeral {
  /** Aviso sobre limitação de cobertura histórica (leg. 54+, eleitos >= 2010). */
  aviso: string
  media_global: number
  total_parlamentares: number
  top_50: RankingPerformancePolitico[]
}

/**
 * Envelope retornado por GET /ranking/performance_politicos.
 * O campo `aviso` explica a limitação de cobertura histórica (leg. 54+).
 */
export interface PerformanceRankingResponse {
  aviso: string
  total: number
  ranking: RankingPerformancePolitico[]
}

// ============================================
// PARÂMETROS DE BUSCA
// ============================================

export interface RankingDespesaParams {
  q?: string        // Busca por nome
  uf?: string       // Filtro por estado
  limit?: number    // Quantidade de resultados (max 100)
  offset?: number   // Paginação
}

export interface RankingLucroParams {
  limit?: number    // Quantidade de resultados (max 100)
  offset?: number   // Paginação
}

export interface RankingDiscursoParams {
  limit?: number    // Quantidade de resultados (max 500)
  offset?: number   // Paginação
}

// ============================================
// FUNÇÕES DA API
// ============================================

/**
 * Busca o ranking de políticos por despesas totais
 * Endpoint: GET /ranking/despesa_politico
 * Cache: 24 horas no backend
 */
export async function getRankingDespesas(
  params?: RankingDespesaParams
): Promise<RankingDespesaPolitico[]> {
  const { data } = await api.get<RankingDespesaPolitico[]>(
    "/ranking/despesa_politico",
    { params }
  )
  return data
}

/**
 * Busca o ranking de empresas que mais receberam recursos
 * Endpoint: GET /ranking/lucro_empresas
 * Cache: 24 horas no backend
 */
export async function getRankingLucroEmpresas(
  params?: RankingLucroParams
): Promise<RankingEmpresaLucro[]> {
  const { data } = await api.get<RankingEmpresaLucro[]>(
    "/ranking/lucro_empresas",
    { params }
  )
  return data
}

/**
 * Busca o ranking de políticos por quantidade de discursos
 * Inclui os 20 temas mais discutidos por cada político
 * Endpoint: GET /ranking/discursos
 * Cache: 24 horas no backend
 */
export async function getRankingDiscursos(
  params?: RankingDiscursoParams
): Promise<RankingDiscursoPolitico[]> {
  const { data } = await api.get<RankingDiscursoPolitico[]>(
    "/ranking/discursos",
    { params }
  )
  return data
}

/**
 * Busca o ranking geral de performance dos políticos.
 * Score: Assiduidade (15%) + Economia (40%) + Producao (45%)
 * Endpoint: GET /ranking/performance_politicos
 * Cache: 24 horas no backend
 *
 * Retorna envelope com `aviso` (cobertura leg. 54+), `total` e `ranking[]`.
 */
export async function getRankingPerformance(): Promise<PerformanceRankingResponse> {
  const { data } = await api.get<PerformanceRankingResponse>(
    "/ranking/performance_politicos"
  )
  return data
}

/**
 * Busca estatísticas gerais do sistema
 * Inclui: média global, total de parlamentares e top 50
 * Endpoint: GET /ranking/stats/geral
 * Cache: 24 horas no backend
 */
export async function getStatsGeral(): Promise<StatsGeral> {
  const { data } = await api.get<StatsGeral>("/ranking/stats/geral")
  return data
}