/**
 * usePoliticosInfinite.ts — Infinite scroll com busca fuzzy.
 *
 * Estratégia de busca em duas camadas para encontrar "Nikolas" com "Nic":
 *
 * Camada 1 — API com múltiplos termos:
 *   Gera variantes fonéticas do termo digitado e dispara uma query
 *   para cada variante. Os resultados são mesclados e deduplicados.
 *   Exemplo: "nic" → busca "nic" E "nik" em paralelo.
 *
 * Camada 2 — Fuzzy local:
 *   Sobre os resultados retornados pela API, aplica score de similaridade
 *   (substring, fonética, bigramas) para reordenar e filtrar.
 *
 * Isso cobre casos como:
 *   "Nic" → "Nikolas" (variante fonética c→k)
 *   "Joao" → "João" (normalização de acentos)
 *   "Mara" → "Mara Gabrilli" (substring)
 */

import { useInfiniteQuery, useQueries, type UseInfiniteQueryResult } from "@tanstack/react-query"
import { listarPoliticosPageService, listarPoliticosService } from "../services/politicos.service"
import type { PoliticoServiceError } from "../services/politicos.service"
import type { ListarPoliticosParams, Politico, PoliticosPage } from "../api/politicos.api"
import { useMemo } from "react"
import { generatePhoneticVariants, normalizeText, similarityScore } from "./useFuzzySearch"

// ─────────────────────────────────────────────────────────────────────────────
// Constantes
// ─────────────────────────────────────────────────────────────────────────────

export const POLITICOS_PAGE_SIZE = 30

const STALE_TIME_MS = 5 * 60 * 1_000
const GC_TIME_MS    = 10 * 60 * 1_000

// ─────────────────────────────────────────────────────────────────────────────
// Política de retry
// ─────────────────────────────────────────────────────────────────────────────

function shouldRetry(failureCount: number, error: unknown): boolean {
  const e = error as { kind?: string } | null
  if (
    e?.kind === "not_found"    || e?.kind === "unauthorized" ||
    e?.kind === "forbidden"    || e?.kind === "cancelled"    ||
    e?.kind === "rate_limited"
  ) return false
  return failureCount < 2
}

function retryDelay(attempt: number): number {
  return Math.min(1_000 * 2 ** attempt + Math.random() * 200, 10_000)
}

// ─────────────────────────────────────────────────────────────────────────────
// Chave de cache
// ─────────────────────────────────────────────────────────────────────────────

export const politicosInfiniteKeys = {
  all: ["politicos", "infinite"] as const,
  list: (params: Pick<ListarPoliticosParams, "q" | "uf" | "partido">) =>
    [...politicosInfiniteKeys.all, params] as const,
}

// ─────────────────────────────────────────────────────────────────────────────
// Tipos
// ─────────────────────────────────────────────────────────────────────────────

export interface UsePoliticosInfiniteParams {
  q?: string
  uf?: string
  partido?: string
}

// ─────────────────────────────────────────────────────────────────────────────
// Deduplicação de políticos por ID
// ─────────────────────────────────────────────────────────────────────────────

function deduplicarPoliticos(items: Politico[]): Politico[] {
  const seen = new Set<number>()
  return items.filter((p) => {
    if (seen.has(p.id)) return false
    seen.add(p.id)
    return true
  })
}

// ─────────────────────────────────────────────────────────────────────────────
// Hook principal com busca fuzzy
// ─────────────────────────────────────────────────────────────────────────────

/**
 * Busca políticos com infinite scroll e busca fuzzy.
 *
 * Quando há um termo de busca, dispara queries paralelas para cada
 * variante fonética do termo. Os resultados são mesclados, deduplicados
 * e reordenados por score de similaridade.
 *
 * @example
 * const { data, fetchNextPage, hasNextPage } = usePoliticosInfinite({ q: "Nic" })
 * // Encontra "Nikolas" mesmo com "Nic"
 */
export function usePoliticosInfinite(
  params: UsePoliticosInfiniteParams = {},
): UseInfiniteQueryResult<PoliticosPage, PoliticoServiceError> & {
  fuzzyItems?: Politico[]
  isFuzzyLoading?: boolean
} {
  const { q, uf, partido } = params

  // ── Busca paginada normal (sem termo ou com o termo original) ──
  const infiniteQuery = useInfiniteQuery({
    queryKey: politicosInfiniteKeys.list({ q: normalizeText(q ?? ""), uf, partido }),

    queryFn: ({ pageParam, signal }) =>
      listarPoliticosPageService(
        {
          q: q ? normalizeText(q) : undefined,
          uf,
          partido,
          offset: pageParam,
          limit: POLITICOS_PAGE_SIZE,
        },
        signal,
      ),

    initialPageParam: 0,

    getNextPageParam: (lastPage) =>
      lastPage.hasMore
        ? lastPage.offset + lastPage.items.length
        : undefined,

    staleTime: STALE_TIME_MS,
    gcTime: GC_TIME_MS,
    retry: shouldRetry,
    retryDelay,
  })

  // ── Variantes fonéticas para buscas paralelas ──
  const phoneticVariants = useMemo(() => {
    if (!q || q.trim().length < 2) return []
    const normalized = normalizeText(q)
    const variants = generatePhoneticVariants(q)
    // Remove a variante idêntica ao termo normalizado (já coberta pela query principal)
    return variants.filter((v) => v !== normalized)
  }, [q])

  // ── Queries paralelas para cada variante fonética ──
  const variantQueries = useQueries({
    queries: phoneticVariants.map((variant) => ({
      queryKey: ["politicos", "fuzzy-variant", variant, uf, partido],
      queryFn: ({ signal }: { signal: AbortSignal }) =>
        listarPoliticosService(
          { q: variant, uf, partido, limit: POLITICOS_PAGE_SIZE },
          signal,
        ),
      staleTime: STALE_TIME_MS,
      gcTime: GC_TIME_MS,
      retry: shouldRetry,
      retryDelay,
      enabled: phoneticVariants.length > 0,
    })),
  })

  // ── Mescla e reordena por score de similaridade ──
  const fuzzyItems = useMemo(() => {
    if (!q || q.trim().length < 2) return undefined

    // Itens da query principal
    const mainItems = infiniteQuery.data?.pages.flatMap((p) => p.items) ?? []

    // Itens das variantes fonéticas
    const variantItems = variantQueries.flatMap((r) => r.data ?? [])

    // Mescla e deduplica
    const merged = deduplicarPoliticos([...mainItems, ...variantItems])

    // Ordena por score de similaridade com o termo original
    return merged
      .map((p) => ({
        p,
        score: Math.max(
          similarityScore(q, p.nome),
          // Também considera o nome sem acentos
          similarityScore(q, normalizeText(p.nome)),
        ),
      }))
      .filter(({ score }) => score > 0)
      .sort((a, b) => b.score - a.score)
      .map(({ p }) => p)
  }, [q, infiniteQuery.data, variantQueries])

  const isFuzzyLoading =
    infiniteQuery.isLoading || variantQueries.some((r) => r.isLoading)

  return {
    ...infiniteQuery,
    fuzzyItems,
    isFuzzyLoading,
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// Seletor utilitário
// ─────────────────────────────────────────────────────────────────────────────

/**
 * Retorna todos os políticos de todas as páginas carregadas.
 * Quando há busca fuzzy ativa, usa os resultados fuzzy (já mesclados e reordenados).
 */
export function selectAllPoliticos(
  data: UseInfiniteQueryResult<PoliticosPage, PoliticoServiceError>["data"],
  fuzzyItems?: Politico[],
  query?: string,
): Politico[] {
  // Com busca ativa e resultados fuzzy disponíveis, usa os fuzzy
  if (query && query.trim().length >= 2 && fuzzyItems !== undefined) {
    return fuzzyItems
  }
  // Sem busca: usa os dados paginados normalmente
  return data?.pages.flatMap((page) => page.items) ?? []
}