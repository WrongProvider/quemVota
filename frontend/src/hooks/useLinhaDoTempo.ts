/**
 * useLinhaDoTempo.ts — Hooks React Query para a Linha do Tempo parlamentar.
 *
 * Exporta:
 *  - useDespesasResumoCompleto(id, ano?)  → histórico mensal + fornecedores + categorias
 *  - useVotacoes(id)                      → últimas votações
 */

import { useQuery, type UseQueryResult } from "@tanstack/react-query"
import {
  fetchDespesasResumoCompleto,
  fetchVotacoes,
  type DespesaResumoCompleto,
  type Votacao,
} from "../api/linhaTempo.api"

// ─────────────────────────────────────────────────────────────────────────────
// Cache keys
// ─────────────────────────────────────────────────────────────────────────────

export const linhaTempoKeys = {
  despesasResumo: (id: number, ano?: number) =>
    ["politicos", id, "despesas-resumo-completo", ano ?? "todos"] as const,
  votacoes: (id: number) => ["politicos", id, "votacoes"] as const,
}

// ─────────────────────────────────────────────────────────────────────────────
// Hooks
// ─────────────────────────────────────────────────────────────────────────────

export function useDespesasResumoCompleto(
  id: number,
  ano?: number,
): UseQueryResult<DespesaResumoCompleto, Error> {
  return useQuery({
    queryKey: linhaTempoKeys.despesasResumo(id, ano),
    queryFn: ({ signal }) => fetchDespesasResumoCompleto(id, ano, signal),
    enabled: Number.isInteger(id) && id > 0,
    staleTime: 10 * 60 * 1_000,
    gcTime: 20 * 60 * 1_000,
  })
}

export function useVotacoes(id: number): UseQueryResult<Votacao[], Error> {
  return useQuery({
    queryKey: linhaTempoKeys.votacoes(id),
    queryFn: ({ signal }) => fetchVotacoes(id, signal),
    enabled: Number.isInteger(id) && id > 0,
    staleTime: 10 * 60 * 1_000,
    gcTime: 20 * 60 * 1_000,
  })
}
