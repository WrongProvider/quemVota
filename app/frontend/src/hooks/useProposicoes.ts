/**
 * useProposicoes.ts — Hooks React Query para Proposições e Votações.
 *
 * Exporta:
 *  - useProposicoes(filtros?)             → lista paginada de proposições
 *  - useProposicao(id)                    → detalhe completo de uma proposição
 *  - useVotacoesDaProposicao(id)          → votações de uma proposição
 *  - useVotacoes(filtros?)                → lista paginada de votações
 *  - useVotacao(id)                       → detalhe completo de uma votação
 *
 * Padrão de cache:
 *  - staleTime: 10 min  → não refaz a query se o dado tiver menos de 10 min
 *  - gcTime:    20 min  → mantém o cache em memória por 20 min após desmontar
 *
 * Dados legislativos mudam raramente — esse cache é conservador e seguro.
 */

import { useQuery, type UseQueryResult } from "@tanstack/react-query"
import {
  fetchProposicao,
  fetchProposicoes,
  fetchVotacao,
  fetchVotacoes,
  fetchVotacoesDaProposicao,
  type ProposicaoDetalhe,
  type ProposicaoResponse,
  type ProposicoesFiltros,
  type VotacaoDetalhe,
  type VotacaoResponse,
  type VotacoesFiltros,
} from "../api/proposicoes.api"

// ─────────────────────────────────────────────────────────────────────────────
// Cache keys
//
// Centralizados aqui para garantir consistência entre hooks e facilitar
// invalidação manual (ex: após navegação ou mudança de filtros).
// ─────────────────────────────────────────────────────────────────────────────

export const proposicoesKeys = {
  /** Chave da listagem — muda conforme os filtros mudam */
  lista: (filtros?: ProposicoesFiltros) =>
    ["proposicoes", "lista", filtros ?? {}] as const,

  /** Chave do detalhe — identificada apenas pelo ID */
  detalhe: (id: number) =>
    ["proposicoes", "detalhe", id] as const,

  /** Chave das votações de uma proposição */
  votacoes: (proposicaoId: number) =>
    ["proposicoes", proposicaoId, "votacoes"] as const,
}

export const votacoesKeys = {
  /** Chave da listagem de votações — muda conforme os filtros mudam */
  lista: (filtros?: VotacoesFiltros) =>
    ["votacoes", "lista", filtros ?? {}] as const,

  /** Chave do detalhe de uma votação */
  detalhe: (id: number) =>
    ["votacoes", "detalhe", id] as const,
}

// ─────────────────────────────────────────────────────────────────────────────
// Hooks — Proposições
// ─────────────────────────────────────────────────────────────────────────────

/**
 * Lista proposições com filtros opcionais.
 *
 * A query é refeita automaticamente sempre que `filtros` mudar
 * (React Query compara as keys por referência profunda).
 *
 * @example
 * const { data, isLoading } = useProposicoes({ sigla_tipo: "PL", ano: 2024 })
 */
export function useProposicoes(
  filtros?: ProposicoesFiltros,
): UseQueryResult<ProposicaoResponse[], Error> {
  return useQuery({
    queryKey: proposicoesKeys.lista(filtros),
    queryFn: ({ signal }) => fetchProposicoes(filtros, signal),
    staleTime: 10 * 60 * 1_000,
    gcTime:    20 * 60 * 1_000,
  })
}

/**
 * Detalhe completo de uma proposição — inclui tramitação, autores e temas.
 *
 * A query só dispara se `id` for um inteiro positivo válido.
 * Isso permite usar o hook antes de ter o ID disponível
 * (ex: enquanto aguarda resposta de outra query).
 *
 * @example
 * const { data: proposicao } = useProposicao(id)
 */
export function useProposicao(id: number): UseQueryResult<ProposicaoDetalhe, Error> {
  return useQuery({
    queryKey: proposicoesKeys.detalhe(id),
    queryFn: ({ signal }) => fetchProposicao(id, signal),
    enabled:   Number.isInteger(id) && id > 0,
    staleTime: 10 * 60 * 1_000,
    gcTime:    20 * 60 * 1_000,
  })
}

/**
 * Votações vinculadas a uma proposição específica.
 *
 * Retorna lista vazia se a proposição existir mas ainda não tiver votações.
 * A query só dispara se `proposicaoId` for um inteiro positivo válido.
 *
 * @example
 * const { data: votacoes = [] } = useVotacoesDaProposicao(proposicao.id)
 */
export function useVotacoesDaProposicao(
  proposicaoId: number,
): UseQueryResult<VotacaoResponse[], Error> {
  return useQuery({
    queryKey: proposicoesKeys.votacoes(proposicaoId),
    queryFn: ({ signal }) => fetchVotacoesDaProposicao(proposicaoId, signal),
    enabled:   Number.isInteger(proposicaoId) && proposicaoId > 0,
    staleTime: 10 * 60 * 1_000,
    gcTime:    20 * 60 * 1_000,
  })
}

// ─────────────────────────────────────────────────────────────────────────────
// Hooks — Votações
// ─────────────────────────────────────────────────────────────────────────────

/**
 * Lista votações com filtros opcionais.
 *
 * @example
 * // Votações aprovadas de 2024
 * const { data } = useVotacoes({ ano: 2024, aprovacao: 1 })
 *
 * @example
 * // Votações de PLs
 * const { data } = useVotacoes({ sigla_tipo: "PL" })
 */
export function useVotacoes(
  filtros?: VotacoesFiltros,
): UseQueryResult<VotacaoResponse[], Error> {
  return useQuery({
    queryKey: votacoesKeys.lista(filtros),
    queryFn: ({ signal }) => fetchVotacoes(filtros, signal),
    staleTime: 10 * 60 * 1_000,
    gcTime:    20 * 60 * 1_000,
  })
}

/**
 * Detalhe completo de uma votação — inclui orientações por partido.
 *
 * A query só dispara se `id` for um inteiro positivo válido.
 *
 * @example
 * const { data: votacao } = useVotacao(id)
 * votacao?.orientacoes.map(o => o.sigla_partido_bloco)
 */
export function useVotacao(id: number): UseQueryResult<VotacaoDetalhe, Error> {
  return useQuery({
    queryKey: votacoesKeys.detalhe(id),
    queryFn: ({ signal }) => fetchVotacao(id, signal),
    enabled:   Number.isInteger(id) && id > 0,
    staleTime: 10 * 60 * 1_000,
    gcTime:    20 * 60 * 1_000,
  })
}