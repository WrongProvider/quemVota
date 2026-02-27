/**
 * linhaTempo.api.ts — Funções de API para a Linha do Tempo parlamentar.
 *
 * Endpoints usados:
 *  - GET /politicos/{id}/despesas/resumo          → resumo mensal (com ?ano=YYYY)
 *  - GET /politicos/{id}/despesas/resumo_completo → histórico + fornecedores + categorias (com ?ano=YYYY)
 *  - GET /politicos/{id}/votacoes                 → últimas votações
 */

import { api } from "./client"

// ─────────────────────────────────────────────────────────────────────────────
// Tipos
// ─────────────────────────────────────────────────────────────────────────────

export interface DespesaResumoMensal {
  readonly ano: number
  readonly mes: number
  readonly total_gasto: number
  readonly qtd_despesas: number
}

export interface DespesaFornecedor {
  readonly nome: string
  readonly total: number
  /**
   * Tipo de despesa mais frequente nas notas fiscais deste fornecedor
   * para o parlamentar consultado. Calculado via window function no backend
   * (rank por contagem de ocorrências, particionado por fornecedor).
   *
   * Pode ser null em fornecedores com apenas uma categoria registrada
   * ou em dados históricos anteriores à adição do campo.
   */
  readonly categoria_principal: string | null
}

export interface DespesaCategoria {
  readonly nome: string
  readonly total: number
}

export interface DespesaResumoCompleto {
  readonly historico_mensal: DespesaResumoMensal[]
  readonly top_fornecedores: DespesaFornecedor[]
  readonly top_categorias: DespesaCategoria[]
}

export interface Votacao {
  readonly data: string
  readonly descricao: string
  readonly voto: string
  readonly resultado?: string
  readonly proposicao?: string
}

// ─────────────────────────────────────────────────────────────────────────────
// Funções de fetch
// ─────────────────────────────────────────────────────────────────────────────

export async function fetchDespesasResumoCompleto(
  politicoId: number,
  ano?: number,
  signal?: AbortSignal,
): Promise<DespesaResumoCompleto> {
  const params: Record<string, unknown> = { limit_meses: 60 }
  if (ano) params.ano = ano
  const { data } = await api.get<DespesaResumoCompleto>(
    `/politicos/${politicoId}/despesas/resumo_completo`,
    { params, signal },
  )
  return data
}

export async function fetchVotacoes(
  politicoId: number,
  signal?: AbortSignal,
): Promise<Votacao[]> {
  const { data } = await api.get<Votacao[]>(
    `/politicos/${politicoId}/votacoes`,
    { params: { limit: 20 }, signal },
  )
  return data
}