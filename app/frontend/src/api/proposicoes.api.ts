/**
 * proposicoes.api.ts — Funções de API para Proposições e Votações.
 *
 * Endpoints cobertos:
 *  - GET /proposicoes/                  → lista paginada com filtros
 *  - GET /proposicoes/{id}              → detalhe + tramitação + autores + temas
 *  - GET /proposicoes/{id}/votacoes     → votações de uma proposição
 *  - GET /votacoes/                     → lista paginada com filtros
 *  - GET /votacoes/{id}                 → detalhe + orientações por partido
 */

import { api } from "./client"

// ─────────────────────────────────────────────────────────────────────────────
// Tipos — espelham exatamente os schemas Pydantic do backend
// ─────────────────────────────────────────────────────────────────────────────

/** Autor de uma proposição (deputado, comissão, Senado, Executivo...) */
export interface AutorResumo {
  readonly politico_id: number | null  // null se não for um deputado cadastrado
  readonly nome: string
  readonly tipo: string | null         // "Deputado", "Comissão", "Senado"...
  readonly proponente: boolean | null  // true = autor principal
}

/** Tema legislativo associado a uma proposição */
export interface TemaResumo {
  readonly id: number
  readonly cod_tema: number | null
  readonly tema: string
}

/** Uma etapa no histórico de tramitação de uma proposição */
export interface TramitacaoItem {
  readonly id: number
  readonly data_hora: string | null
  readonly sequencia: number | null
  readonly sigla_orgao: string | null       // "PLEN", "CCJ", "CFT"...
  readonly regime: string | null            // "Urgência", "Ordinário"...
  readonly descricao_tramitacao: string | null
  readonly descricao_situacao: string | null
  readonly despacho: string | null          // texto livre, pode ser longo
  readonly ambito: string | null
  readonly apreciacao: string | null
}

/** Proposição na listagem (sem tramitação para resposta leve) */
export interface ProposicaoResponse {
  readonly id: number
  readonly id_camara: number
  readonly sigla_tipo: string | null        // "PL", "PEC", "MPV"...
  readonly numero: number | null
  readonly ano: number | null
  readonly descricao_tipo: string | null
  readonly ementa: string | null
  readonly keywords: string | null
  readonly data_apresentacao: string | null
  readonly url_inteiro_teor: string | null
  readonly autores: AutorResumo[]
  readonly temas: TemaResumo[]
}

/** Proposição no detalhe — herda tudo de ProposicaoResponse + tramitação */
export interface ProposicaoDetalhe extends ProposicaoResponse {
  readonly ementa_detalhada: string | null
  readonly justificativa: string | null
  readonly urn_final: string | null
  readonly tramitacoes: TramitacaoItem[]
}

/** Orientação de voto de um partido/bloco em uma votação */
export interface OrientacaoPartido {
  readonly sigla_partido_bloco: string | null
  readonly cod_tipo_lideranca: string | null
  readonly orientacao_voto: string | null   // "Sim", "Não", "Libera", "Obstrução"
}

/**
 * Votação na listagem.
 * Já inclui campos da proposição desnormalizados para evitar um segundo request.
 *
 * aprovacao: 1 = aprovada | 0 = rejeitada | -1 = indefinido | null = não disponível
 */
export interface VotacaoResponse {
  readonly id: number
  readonly id_camara: string
  readonly data: string | null
  readonly data_hora_registro: string | null
  readonly tipo_votacao: string | null      // "Nominal" ou "Simbólica"
  readonly descricao: string | null
  readonly aprovacao: 1 | 0 | -1 | null
  readonly sigla_orgao: string | null
  // Proposição vinculada (desnormalizada)
  readonly proposicao_id: number | null
  readonly proposicao_sigla: string | null
  readonly proposicao_numero: number | null
  readonly proposicao_ano: number | null
  readonly proposicao_ementa: string | null
}

/** Votação no detalhe — herda tudo de VotacaoResponse + orientações por partido */
export interface VotacaoDetalhe extends VotacaoResponse {
  readonly orientacoes: OrientacaoPartido[]
}

// ─────────────────────────────────────────────────────────────────────────────
// Parâmetros de filtro — usados nas funções de listagem
// ─────────────────────────────────────────────────────────────────────────────

export interface ProposicoesFiltros {
  q?: string          // busca na ementa
  sigla_tipo?: string // "PL", "PEC", "MPV"...
  ano?: number
  tema_id?: number
  limit?: number      // padrão: 20, máx: 100
  offset?: number
}

export interface VotacoesFiltros {
  ano?: number
  aprovacao?: 1 | 0 | -1  // 1 = aprovada, 0 = rejeitada, -1 = indefinido
  sigla_tipo?: string      // filtra pelo tipo da proposição vinculada
  limit?: number           // padrão: 20, máx: 100
  offset?: number
}

// ─────────────────────────────────────────────────────────────────────────────
// Funções de fetch — Proposições
// ─────────────────────────────────────────────────────────────────────────────

/** Lista proposições com filtros opcionais e paginação */
export async function fetchProposicoes(
  filtros?: ProposicoesFiltros,
  signal?: AbortSignal,
): Promise<ProposicaoResponse[]> {
  const { data } = await api.get<ProposicaoResponse[]>("/proposicoes/", {
    params: { limit: 20, ...filtros },
    signal,
  })
  return data
}

/** Retorna o detalhe completo de uma proposição (com tramitação, autores, temas) */
export async function fetchProposicao(
  id: number,
  signal?: AbortSignal,
): Promise<ProposicaoDetalhe> {
  const { data } = await api.get<ProposicaoDetalhe>(`/proposicoes/${id}`, { signal })
  return data
}

/** Retorna todas as votações vinculadas a uma proposição */
export async function fetchVotacoesDaProposicao(
  proposicaoId: number,
  signal?: AbortSignal,
): Promise<VotacaoResponse[]> {
  const { data } = await api.get<VotacaoResponse[]>(
    `/proposicoes/${proposicaoId}/votacoes`,
    { signal },
  )
  return data
}

// ─────────────────────────────────────────────────────────────────────────────
// Funções de fetch — Votações
// ─────────────────────────────────────────────────────────────────────────────

/** Lista votações com filtros opcionais e paginação */
export async function fetchVotacoes(
  filtros?: VotacoesFiltros,
  signal?: AbortSignal,
): Promise<VotacaoResponse[]> {
  const { data } = await api.get<VotacaoResponse[]>("/votacoes/", {
    params: { limit: 20, ...filtros },
    signal,
  })
  return data
}

/** Retorna o detalhe completo de uma votação (com orientações por partido) */
export async function fetchVotacao(
  id: number,
  signal?: AbortSignal,
): Promise<VotacaoDetalhe> {
  const { data } = await api.get<VotacaoDetalhe>(`/votacoes/${id}`, { signal })
  return data
}