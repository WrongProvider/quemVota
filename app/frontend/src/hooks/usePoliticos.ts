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
  obterPoliticoTimelineService,
  PoliticoServiceError,
} from "../services/politicos.service"
import type {
  ListarPoliticosParams,
  Politico,
  PoliticoDetalhe,
  PoliticoEstatisticas,
  PoliticoPerformance,
  TimelineEntrada,
} from "../api/politicos.api"

// ─────────────────────────────────────────────────────────────────────────────
// Configurações de cache e retry compartilhadas
// ─────────────────────────────────────────────────────────────────────────────

const STALE_TIME_MS = 5 * 60 * 1_000   // 5 min
const GC_TIME_MS    = 10 * 60 * 1_000  // 10 min

/**
 * Política de retry — OWASP A04:
 * Não reenvia requisições com erro 4xx.
 * Tenta até 2× apenas para erros de rede ou 5xx.
 */
function shouldRetry(failureCount: number, error: unknown): boolean {
  if (error instanceof PoliticoServiceError) {
    if (
      error.kind === "not_found"    ||
      error.kind === "unauthorized" ||
      error.kind === "forbidden"    ||
      error.kind === "cancelled"    ||
      error.kind === "rate_limited"
    ) {
      return false
    }
  }
  return failureCount < 2
}

/** Delay exponencial com jitter para evitar thundering herd */
function retryDelay(attempt: number): number {
  return Math.min(1_000 * 2 ** attempt + Math.random() * 200, 10_000)
}

// ─────────────────────────────────────────────────────────────────────────────
// Chaves de cache — centralizadas para facilitar invalidação
// ─────────────────────────────────────────────────────────────────────────────

export const politicoKeys = {
  all:        ["politicos"] as const,
  lists:      () => [...politicoKeys.all, "list"] as const,
  list:       (params?: ListarPoliticosParams) => [...politicoKeys.lists(), params] as const,
  details:    () => [...politicoKeys.all, "detail"] as const,
  detail:     (id: number) => [...politicoKeys.details(), id] as const,
  // ano incluso na chave → cache separado por ano (null = mandato inteiro)
  estatisticas: (id: number, ano?: number | null) =>
    [...politicoKeys.detail(id), "estatisticas", ano ?? "all"] as const,
  performance:  (id: number, ano?: number | null) =>
    [...politicoKeys.detail(id), "performance", ano ?? "all"] as const,
  timeline:     (id: number) => [...politicoKeys.detail(id), "timeline"] as const,
}

// ─────────────────────────────────────────────────────────────────────────────
// Hooks públicos
// ─────────────────────────────────────────────────────────────────────────────

/**
 * Lista políticos com filtros opcionais.
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
 * Retorna as estatísticas de um político, com filtro de ano opcional.
 *
 * Quando `ano` é fornecido, a query key muda — o React Query mantém
 * caches independentes para cada ano e para o mandato completo (ano=null).
 * Isso evita refetch desnecessário ao navegar entre anos já visitados.
 *
 * @param id  - ID inteiro positivo do político
 * @param ano - Ano para filtrar (null ou undefined = mandato completo)
 *
 * @example
 * const { data } = usePoliticoEstatisticas(42)          // mandato inteiro
 * const { data } = usePoliticoEstatisticas(42, 2023)    // apenas 2023
 */
export function usePoliticoEstatisticas(
  id: number,
  ano?: number | null,
): UseQueryResult<PoliticoEstatisticas, PoliticoServiceError> {
  return useQuery({
    queryKey: politicoKeys.estatisticas(id, ano),
    queryFn: ({ signal }) => obterPoliticoEstatisticasService(id, ano, signal),
    enabled: Number.isInteger(id) && id > 0,
    staleTime: STALE_TIME_MS,
    gcTime: GC_TIME_MS,
    retry: shouldRetry,
    retryDelay,
  })
}

/**
 * Retorna o score de performance de um político, com filtro de ano opcional.
 *
 * Mesma estratégia de cache separado por ano que usePoliticoEstatisticas.
 *
 * @param id  - ID inteiro positivo do político
 * @param ano - Ano para filtrar (null ou undefined = mandato completo)
 *
 * @example
 * const { data } = usePoliticoPerformance(42)          // mandato inteiro
 * const { data } = usePoliticoPerformance(42, 2024)    // apenas 2024
 */
export function usePoliticoPerformance(
  id: number,
  ano?: number | null,
): UseQueryResult<PoliticoPerformance, PoliticoServiceError> {
  return useQuery({
    queryKey: politicoKeys.performance(id, ano),
    queryFn: ({ signal }) => obterPoliticoPerformanceService(id, ano, signal),
    enabled: Number.isInteger(id) && id > 0,
    staleTime: STALE_TIME_MS,
    gcTime: GC_TIME_MS,
    retry: shouldRetry,
    retryDelay,
  })
}

/**
 * Retorna a linha do tempo anual completa do parlamentar.
 *
 * Cada entrada representa um ano com dados registrados, incluindo:
 * score de performance, notas detalhadas (assiduidade/economia/produção),
 * estatísticas anuais e informações sobre a cota parlamentar.
 *
 * Os anos disponíveis nesta resposta são usados pelo TimelineSelector
 * no PoliticoDetalhe para montar o seletor de ano.
 *
 * O endpoint raramente muda — staleTime longo para evitar refetch.
 *
 * @param id - ID inteiro positivo do político
 *
 * @example
 * const { data: timeline } = usePoliticoTimeline(42)
 * const anos = timeline?.map(t => t.ano) ?? []
 */
export function usePoliticoTimeline(
  id: number,
): UseQueryResult<TimelineEntrada[], PoliticoServiceError> {
  return useQuery({
    queryKey: politicoKeys.timeline(id),
    queryFn: ({ signal }) => obterPoliticoTimelineService(id, signal),
    enabled: Number.isInteger(id) && id > 0,
    // Timeline histórica muda raramente — 30 min é seguro
    staleTime: 30 * 60 * 1_000,
    gcTime: GC_TIME_MS,
    retry: shouldRetry,
    retryDelay,
  })
}