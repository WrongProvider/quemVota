// import { useQuery } from "@tanstack/react-query"
// import { listarPoliticosService, obterPoliticoDetalheService, obterPoliticoEstatisticasService, obterPoliticoPerformanceService } from "../services/politicos.service"
// import { useInfiniteQuery } from "@tanstack/react-query"

// interface UsePoliticosParams {
//   q?: string
//   uf?: string
//   limit?: number
//   offset?: number
// }

// export function usePoliticos(params?: UsePoliticosParams) {
//   return useQuery({
//     queryKey: ["politicos", params],
//     queryFn: () => listarPoliticosService(params),
//     staleTime: 1000 * 60 * 5, // 5 minutos
//     gcTime: 1000 * 60 * 10, // cache por 10 minutos
//   })
// }

// export function usePoliticoDetalhe(id: number) {
//   return useQuery({
//     queryKey: ["politico", id],
//     queryFn: () => obterPoliticoDetalheService(id),
//     enabled: !!id, // só executa se existir id
//     staleTime: 1000 * 60 * 5,
//     gcTime: 1000 * 60 * 10,
//   })
// }

// export function usePoliticoEstatisticas(id: number) {
//   return useQuery({
//     queryKey: ["politico-estatisticas", id],
//     queryFn: () => obterPoliticoEstatisticasService(id),
//     enabled: !!id,
//     staleTime: 1000 * 60 * 5,
//     gcTime: 1000 * 60 * 10,
//   })
// }


// export function usePoliticoPerformance(id: number) {
//   return useQuery({
//     queryKey: ["politico-performance", id],
//     queryFn: () => obterPoliticoPerformanceService(id),
//     enabled: !!id,
//     staleTime: 1000 * 60 * 5,
//   })
// }


/**
 * usePoliticos.ts — Hooks React Query para o domínio de Políticos.
 *
 * Responsabilidade: gerenciar cache, estados de loading/error, cancelamento
 * de requisições e retry com back-off inteligente.
 *
 * OWASP coberto:
 *  - A04 Insecure Design     : retry nunca acontece em erros 4xx (evita
 *    amplificação de requisições inválidas ou de autenticação).
 *  - A09 Logging & Monitoring: erros tipados do serviço chegam à UI via
 *    `error` do hook — sem stack traces ou dados sensíveis expostos.
 */

import { useQuery, type UseQueryResult } from "@tanstack/react-query"
import {
  listarPoliticosService,
  obterPoliticoDetalheService,
  obterPoliticoEstatisticasService,
  obterPoliticoPerformanceService,
  PoliticoServiceError,
} from "../services/politicos.service"
import type {
  ListarPoliticosParams,
  Politico,
  PoliticoDetalhe,
  PoliticoEstatisticas,
  PoliticoPerformance,
} from "../api/politicos.api"

// ─────────────────────────────────────────────────────────────────────────────
// Configurações de cache e retry compartilhadas
// ─────────────────────────────────────────────────────────────────────────────

/** Tempo que os dados são considerados frescos sem refetch */
const STALE_TIME_MS = 5 * 60 * 1_000   // 5 min

/** Tempo que os dados permanecem no cache após o componente desmontar */
const GC_TIME_MS = 10 * 60 * 1_000     // 10 min

/**
 * Política de retry — OWASP A04:
 * Não reenvia requisições com erro 4xx (cliente não vai ter sucesso tentando de novo).
 * Tenta até 2× apenas para erros de rede ou 5xx.
 */
function shouldRetry(failureCount: number, error: unknown): boolean {
  if (error instanceof PoliticoServiceError) {
    // Erros de cliente: não adianta tentar novamente
    if (
      error.kind === "not_found" ||
      error.kind === "unauthorized" ||
      error.kind === "forbidden" ||
      error.kind === "cancelled"
    ) {
      return false
    }
    // Rate limit: respeita o servidor
    if (error.kind === "rate_limited") return false
  }
  return failureCount < 2
}

/** Delay exponencial com jitter para evitar thundering herd */
function retryDelay(attempt: number): number {
  return Math.min(1_000 * 2 ** attempt + Math.random() * 200, 10_000)
}

// ─────────────────────────────────────────────────────────────────────────────
// Chaves de cache — centralizadas para evitar duplicação e facilitar invalidação
// ─────────────────────────────────────────────────────────────────────────────

export const politicoKeys = {
  all: ["politicos"] as const,
  lists: () => [...politicoKeys.all, "list"] as const,
  list: (params?: ListarPoliticosParams) => [...politicoKeys.lists(), params] as const,
  details: () => [...politicoKeys.all, "detail"] as const,
  detail: (id: number) => [...politicoKeys.details(), id] as const,
  estatisticas: (id: number) => [...politicoKeys.detail(id), "estatisticas"] as const,
  performance: (id: number) => [...politicoKeys.detail(id), "performance"] as const,
}

// ─────────────────────────────────────────────────────────────────────────────
// Hooks públicos
// ─────────────────────────────────────────────────────────────────────────────

/**
 * Lista políticos com filtros opcionais.
 * Cancela a requisição automaticamente ao desmontar o componente.
 *
 * @example
 * const { data, isLoading, error } = usePoliticos({ uf: "SP", limit: 50 })
 */
export function usePoliticos(
  params?: ListarPoliticosParams,
): UseQueryResult<Politico[], PoliticoServiceError> {
  return useQuery({
    queryKey: politicoKeys.list(params),
    queryFn: ({ signal }) => listarPoliticosService(params, signal),
    staleTime: STALE_TIME_MS,
    gcTime: GC_TIME_MS,
    retry: shouldRetry,
    retryDelay,
  })
}

/**
 * Retorna o detalhe de um político pelo ID.
 * Desabilitado automaticamente quando `id` é inválido.
 *
 * @example
 * const { data, isLoading, error } = usePoliticoDetalhe(42)
 */
export function usePoliticoDetalhe(
  id: number,
): UseQueryResult<PoliticoDetalhe, PoliticoServiceError> {
  return useQuery({
    queryKey: politicoKeys.detail(id),
    queryFn: ({ signal }) => obterPoliticoDetalheService(id, signal),
    enabled: Number.isInteger(id) && id > 0,
    staleTime: STALE_TIME_MS,
    gcTime: GC_TIME_MS,
    retry: shouldRetry,
    retryDelay,
  })
}

/**
 * Retorna as estatísticas de um político.
 * Desabilitado automaticamente quando `id` é inválido.
 *
 * @example
 * const { data } = usePoliticoEstatisticas(42)
 */
export function usePoliticoEstatisticas(
  id: number,
): UseQueryResult<PoliticoEstatisticas, PoliticoServiceError> {
  return useQuery({
    queryKey: politicoKeys.estatisticas(id),
    queryFn: ({ signal }) => obterPoliticoEstatisticasService(id, signal),
    enabled: Number.isInteger(id) && id > 0,
    staleTime: STALE_TIME_MS,
    gcTime: GC_TIME_MS,
    retry: shouldRetry,
    retryDelay,
  })
}

/**
 * Retorna o score de performance de um político.
 * Desabilitado automaticamente quando `id` é inválido.
 *
 * @example
 * const { data } = usePoliticoPerformance(42)
 */
export function usePoliticoPerformance(
  id: number,
): UseQueryResult<PoliticoPerformance, PoliticoServiceError> {
  return useQuery({
    queryKey: politicoKeys.performance(id),
    queryFn: ({ signal }) => obterPoliticoPerformanceService(id, signal),
    enabled: Number.isInteger(id) && id > 0,
    staleTime: STALE_TIME_MS,
    gcTime: GC_TIME_MS,
    retry: shouldRetry,
    retryDelay,
  })
}