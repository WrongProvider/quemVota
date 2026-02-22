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
  uf: string
  partido: string
  foto: string
  score: number
  notas: NotasPerformance
}

export interface StatsGeral {
  media_global: number
  total_parlamentares: number
  top_3: RankingPerformancePolitico[]
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
 * Busca o ranking geral de performance dos políticos
 * Score baseado em: Assiduidade (15%) + Economia (40%) + Produção (45%)
 * Endpoint: GET /ranking/performance_politicos
 * Cache: 24 horas no backend
 */
export async function getRankingPerformance(): Promise<RankingPerformancePolitico[]> {
  const { data } = await api.get<RankingPerformancePolitico[]>(
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