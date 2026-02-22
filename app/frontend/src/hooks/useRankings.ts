import { useQuery, type UseQueryOptions } from "@tanstack/react-query"
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
  type RankingDespesaParams,
  type RankingLucroParams,
  type RankingDiscursoParams,
} from "../api/rankings.api"

// ============================================
// CONFIGURAÇÕES DE CACHE PADRÃO
// ============================================

const CACHE_CONFIG = {
  // Como o backend já cacheia por 24h, podemos usar tempos mais longos no frontend
  staleTime: 1000 * 60 * 30,      // 30 minutos - dados considerados "frescos"
  gcTime: 1000 * 60 * 60 * 2,     // 2 horas - tempo que dados inativos ficam em cache
}

// ============================================
// HOOKS DE RANKING
// ============================================

/**
 * Hook para buscar ranking de despesas de políticos
 * Suporta busca por nome (q) e filtro por UF
 * 
 * @example
 * const { data, isLoading, error } = useRankingDespesas({ uf: "SP", limit: 50 })
 */
export function useRankingDespesas(
  params?: RankingDespesaParams,
  options?: Omit<UseQueryOptions<RankingDespesaPolitico[]>, "queryKey" | "queryFn">
) {
  return useQuery({
    queryKey: ["rankings", "despesas", params],
    queryFn: () => getRankingDespesas(params),
    ...CACHE_CONFIG,
    ...options,
  })
}

/**
 * Hook para buscar ranking de empresas que mais receberam recursos
 * 
 * @example
 * const { data, isLoading } = useRankingLucroEmpresas({ limit: 20 })
 */
export function useRankingLucroEmpresas(
  params?: RankingLucroParams,
  options?: Omit<UseQueryOptions<RankingEmpresaLucro[]>, "queryKey" | "queryFn">
) {
  return useQuery({
    queryKey: ["rankings", "lucro-empresas", params],
    queryFn: () => getRankingLucroEmpresas(params),
    ...CACHE_CONFIG,
    ...options,
  })
}

/**
 * Hook para buscar ranking de discursos
 * Inclui os temas mais discutidos por cada político
 * 
 * @example
 * const { data, isLoading } = useRankingDiscursos({ limit: 100 })
 */
export function useRankingDiscursos(
  params?: RankingDiscursoParams,
  options?: Omit<UseQueryOptions<RankingDiscursoPolitico[]>, "queryKey" | "queryFn">
) {
  return useQuery({
    queryKey: ["rankings", "discursos", params],
    queryFn: () => getRankingDiscursos(params),
    ...CACHE_CONFIG,
    ...options,
  })
}

/**
 * Hook para buscar ranking geral de performance
 * Score baseado em: Assiduidade (15%) + Economia (40%) + Produção (45%)
 * 
 * @example
 * const { data, isLoading } = useRankingPerformance()
 */
export function useRankingPerformance(
  options?: Omit<UseQueryOptions<RankingPerformancePolitico[]>, "queryKey" | "queryFn">
) {
  return useQuery({
    queryKey: ["rankings", "performance"],
    queryFn: getRankingPerformance,
    ...CACHE_CONFIG,
    ...options,
  })
}

/**
 * Hook para buscar estatísticas gerais do sistema
 * Inclui média global, total de parlamentares e top 50
 * Ideal para usar na página inicial
 * 
 * @example
 * const { data, isLoading } = useStatsGeral()
 */
export function useStatsGeral(
  options?: Omit<UseQueryOptions<StatsGeral>, "queryKey" | "queryFn">
) {
  return useQuery({
    queryKey: ["rankings", "stats-geral"],
    queryFn: getStatsGeral,
    ...CACHE_CONFIG,
    ...options,
  })
}

// ============================================
// HOOK GENÉRICO (RETROCOMPATIBILIDADE)
// ============================================

/**
 * Hook genérico para rankings (retrocompatível com código antigo)
 * @deprecated Use os hooks específicos acima para melhor tipagem
 */
export function useRankings(params?: RankingDespesaParams) {
  return useRankingDespesas(params)
}