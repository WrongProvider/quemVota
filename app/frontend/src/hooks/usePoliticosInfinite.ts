import { useInfiniteQuery, type UseInfiniteQueryResult } from "@tanstack/react-query"
import { listarPoliticosPageService } from "../services/politicos.service"
import type { PoliticoServiceError } from "../services/politicos.service"
import type { ListarPoliticosParams, Politico, PoliticosPage } from "../api/politicos.api"

// ─────────────────────────────────────────────────────────────────────────────
// Constantes
// ─────────────────────────────────────────────────────────────────────────────

/** Itens por página — deve bater com o limite enviado na queryFn abaixo */
export const POLITICOS_PAGE_SIZE = 30

const STALE_TIME_MS = 5 * 60 * 1_000
const GC_TIME_MS    = 10 * 60 * 1_000

// ─────────────────────────────────────────────────────────────────────────────
// Política de retry — espelho do usePoliticos.ts
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
  list: (params: Pick<ListarPoliticosParams, "q" | "uf">) =>
    [...politicosInfiniteKeys.all, params] as const,
}

// ─────────────────────────────────────────────────────────────────────────────
// Tipos
// ─────────────────────────────────────────────────────────────────────────────

export interface UsePoliticosInfiniteParams {
  q?: string
  uf?: string
}

// ─────────────────────────────────────────────────────────────────────────────
// Hook público
// ─────────────────────────────────────────────────────────────────────────────

/**
 * Busca políticos de forma incremental (infinite scroll).
 *
 * O backend retorna array puro; o envelope { items, hasMore, offset } é
 * construído em fetchPoliticosPage no cliente. Quando hasMore=false, o
 * React Query sabe que não há mais páginas.
 *
 * @example
 * const { data, fetchNextPage, hasNextPage } = usePoliticosInfinite({ q })
 * const items = selectAllPoliticos(data)
 */
export function usePoliticosInfinite(
  params: UsePoliticosInfiniteParams = {},
): UseInfiniteQueryResult<PoliticosPage, PoliticoServiceError> {
  const { q, uf, partido } = params

  return useInfiniteQuery({
    queryKey: politicosInfiniteKeys.list({ q, uf, partido }),

    queryFn: ({ pageParam, signal }) =>
      listarPoliticosPageService(
        { q, uf, partido, offset: pageParam, limit: POLITICOS_PAGE_SIZE },
        signal,
      ),

    initialPageParam: 0,

    /**
     * Próximo offset = offset atual + itens recebidos.
     * Retorna undefined quando hasMore=false (fim dos dados).
     */
    getNextPageParam: (lastPage) =>
      lastPage.hasMore
        ? lastPage.offset + lastPage.items.length
        : undefined,

    staleTime: STALE_TIME_MS,
    gcTime: GC_TIME_MS,
    retry: shouldRetry,
    retryDelay,
  })
}

// ─────────────────────────────────────────────────────────────────────────────
// Seletor utilitário
// ─────────────────────────────────────────────────────────────────────────────

/**
 * Achata todas as páginas em uma lista única de políticos.
 *
 * @example
 * const { data } = usePoliticosInfinite({ q })
 * const politicos = selectAllPoliticos(data)
 */
export function selectAllPoliticos(
  data: UseInfiniteQueryResult<PoliticosPage, PoliticoServiceError>["data"],
): Politico[] {
  return data?.pages.flatMap((page) => page.items) ?? []
}