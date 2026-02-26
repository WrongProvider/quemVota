/**
 * politicos.api.ts — Camada de transporte HTTP para o domínio de Políticos.
 *
 * Responsabilidade única: serializar parâmetros, executar requisições HTTP e
 * deserializar respostas. Nenhuma lógica de negócio aqui.
 *
 * OWASP coberto:
 *  - A03 Sensitive Data Exposure    : `response_model` implícito via tipos
 *    TypeScript; campos não declarados são descartados pelo consumidor.
 *  - A04 Insecure Design            : todos os parâmetros numéricos e de texto
 *    são sanitizados/coercidos antes de chegar à rede.
 *  - A06 Outdated Components        : sem dependências além do axios já usado.
 *  - A08 Data Integrity             : guards de tipo em runtime via funções
 *    `assert*` evitam que dados malformados da API se propaguem silenciosamente.
 */

import { api } from "./client"
import type { AxiosRequestConfig } from "axios"

// ─────────────────────────────────────────────────────────────────────────────
// Constantes de limite — espelham os limites do backend (defesa em profundidade)
// OWASP A04: limites explícitos no cliente evitam requisições abusivas acidentais.
// ─────────────────────────────────────────────────────────────────────────────
const LIMITS = {
  POLITICOS_MAX: 100,
  POLITICOS_MIN: 1,
  UF_LENGTH: 2,
  SEARCH_MAX_LENGTH: 150,
  VOTACOES_MAX: 20,
  DESPESAS_MAX: 20,
  RESUMO_MAX: 60,
  ANO_MIN: 2000,
  ANO_MAX: 2100,
  MES_MIN: 1,
  MES_MAX: 12,
  PARTIDO_LENGTH: 20,
} as const

// ─────────────────────────────────────────────────────────────────────────────
// Tipos e interfaces — contratos explícitos com o backend
// ─────────────────────────────────────────────────────────────────────────────

export interface Politico {
  readonly id: number
  readonly nome: string
  readonly uf: string
  readonly partido_sigla: string
  readonly url_foto?: string
}

export interface PoliticoDetalhe extends Politico {
  readonly escolaridade?: string
  readonly situacao?: string
  readonly condicao_eleitoral?: string
  readonly email_gabinete?: string
  readonly telefone_gabinete?: string
}

export interface PoliticoEstatisticas {
  readonly total_votacoes: number
  readonly total_despesas: number
  readonly total_gasto: number
  readonly media_mensal: number
  readonly primeiro_ano: number | null
  readonly ultimo_ano: number | null
}

export interface NotasPerformance {
  readonly nota_assiduidade: number
  readonly nota_economia: number
  readonly nota_producao: number
}

export interface InfoPerformance {
  readonly valor_cota_mensal: number
  readonly meses_considerados: number
  readonly total_gasto: number
  readonly cota_utilizada_pct: number
}

export interface PoliticoPerformance {
  readonly politico_id: number
  readonly ano: number | null
  readonly score_final: number
  readonly media_global: number
  readonly detalhes: NotasPerformance
  readonly info: InfoPerformance
}

// ─────────────────────────────────────────────────────────────────────────────
// Timeline — espelha a resposta de GET /politicos/{id}/timeline
// ─────────────────────────────────────────────────────────────────────────────

export interface TimelineNotasAno {
  readonly assiduidade: number
  readonly producao: number
  readonly economia: number
}

export interface TimelineEstatisticasAno {
  readonly total_votacoes: number
  readonly total_despesas: number
  readonly total_gasto: number
  readonly media_mensal: number
}

export interface TimelineInfoAno {
  readonly valor_cota_mensal: number
  readonly meses_ativos: number
  readonly cota_total: number
  readonly cota_utilizada_pct: number
}

export interface TimelineEntrada {
  readonly ano: number
  readonly score: number
  readonly notas: TimelineNotasAno
  readonly estatisticas: TimelineEstatisticasAno
  readonly info: TimelineInfoAno
}

// ─────────────────────────────────────────────────────────────────────────────
// Parâmetros de busca com tipos estritos
// ─────────────────────────────────────────────────────────────────────────────

export interface ListarPoliticosParams {
  q?: string
  uf?: string
  limit?: number
  offset?: number
  partido?: string
}

// ─────────────────────────────────────────────────────────────────────────────
// Guards de tipo em runtime — OWASP A08 (Data Integrity)
// ─────────────────────────────────────────────────────────────────────────────

function assertPoliticoId(id: unknown): asserts id is number {
  if (typeof id !== "number" || !Number.isInteger(id) || id <= 0) {
    throw new TypeError(`[politicos.api] ID inválido: "${id}". Deve ser inteiro positivo.`)
  }
}

function assertArray<T>(value: unknown, context: string): asserts value is T[] {
  if (!Array.isArray(value)) {
    throw new TypeError(`[politicos.api] Resposta inválida em "${context}": esperado array.`)
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// Sanitizadores — OWASP A04
// ─────────────────────────────────────────────────────────────────────────────

function sanitizeListarParams(params?: ListarPoliticosParams): Record<string, unknown> {
  const sanitized: Record<string, unknown> = {}

  if (params?.q !== undefined) {
    const trimmed = String(params.q).trim()
    if (trimmed.length > 0) {
      sanitized.q = trimmed.slice(0, LIMITS.SEARCH_MAX_LENGTH)
    }
  }

  if (params?.uf !== undefined) {
    const uf = String(params.uf).trim().toUpperCase().slice(0, LIMITS.UF_LENGTH)
    if (uf.length === LIMITS.UF_LENGTH) {
      sanitized.uf = uf
    }
  }

  if (params?.limit !== undefined) {
    const limit = Math.min(
      Math.max(Math.floor(Number(params.limit)), LIMITS.POLITICOS_MIN),
      LIMITS.POLITICOS_MAX,
    )
    sanitized.limit = limit
  }

  if (params?.offset !== undefined) {
    sanitized.offset = Math.max(Math.floor(Number(params.offset)), 0)
  }

  if (params?.partido !== undefined) {
    const partido = String(params.partido).trim().toUpperCase().slice(0, LIMITS.PARTIDO_LENGTH)
    if (partido.length > 0) {
      sanitized.partido = partido
    }
  }

  return sanitized
}

/**
 * Valida e coerce o parâmetro `ano`.
 * Retorna undefined se o valor não estiver no intervalo permitido.
 */
function sanitizeAno(ano?: number | null): number | undefined {
  if (ano == null) return undefined
  const n = Math.floor(Number(ano))
  if (n >= LIMITS.ANO_MIN && n <= LIMITS.ANO_MAX) return n
  return undefined
}

// ─────────────────────────────────────────────────────────────────────────────
// Helper interno — evita duplicação de lógica de requisição
// ─────────────────────────────────────────────────────────────────────────────

async function get<T>(
  url: string,
  config?: AxiosRequestConfig,
): Promise<T> {
  const { data } = await api.get<T>(url, config)
  return data
}

// ─────────────────────────────────────────────────────────────────────────────
// Funções de API pública
// ─────────────────────────────────────────────────────────────────────────────

/**
 * Lista políticos com filtros opcionais.
 */
export async function fetchPoliticos(
  params?: ListarPoliticosParams,
  signal?: AbortSignal,
): Promise<Politico[]> {
  const sanitized = sanitizeListarParams(params)
  const data = await get<Politico[]>("/politicos/", { params: sanitized, signal })
  assertArray<Politico>(data, "fetchPoliticos")
  return data
}

// ─────────────────────────────────────────────────────────────────────────────
// Infinite scroll
// ─────────────────────────────────────────────────────────────────────────────

export interface PoliticosPage {
  readonly items: Politico[]
  readonly hasMore: boolean
  readonly offset: number
}

export async function fetchPoliticosPage(
  params?: ListarPoliticosParams,
  signal?: AbortSignal,
): Promise<PoliticosPage> {
  const sanitized = sanitizeListarParams(params)
  const limit = (sanitized.limit as number | undefined) ?? 30
  const offset = (sanitized.offset as number | undefined) ?? 0

  const data = await get<Politico[]>("/politicos/", { params: sanitized, signal })
  assertArray<Politico>(data, "fetchPoliticosPage")

  return {
    items: data,
    hasMore: data.length >= limit,
    offset,
  }
}

/**
 * Retorna o detalhe de um político pelo ID interno.
 */
export async function fetchPoliticoDetalhe(
  id: number,
  signal?: AbortSignal,
): Promise<PoliticoDetalhe> {
  assertPoliticoId(id)
  return get<PoliticoDetalhe>(`/politicos/${id}`, { signal })
}

/**
 * Retorna as estatísticas gerais de um político.
 *
 * @param id     - ID inteiro positivo do político
 * @param ano    - Quando fornecido, filtra pelo ano — permite comparação na timeline
 * @param signal - AbortSignal para cancelamento
 */
export async function fetchPoliticoEstatisticas(
  id: number,
  ano?: number | null,
  signal?: AbortSignal,
): Promise<PoliticoEstatisticas> {
  assertPoliticoId(id)
  const params: Record<string, unknown> = {}
  const anoSanitizado = sanitizeAno(ano)
  if (anoSanitizado !== undefined) params.ano = anoSanitizado
  return get<PoliticoEstatisticas>(`/politicos/${id}/estatisticas`, { params, signal })
}

/**
 * Retorna o score de performance parlamentar de um político.
 *
 * @param id     - ID inteiro positivo do político
 * @param ano    - Quando fornecido, calcula o score apenas para aquele ano
 * @param signal - AbortSignal para cancelamento
 */
export async function fetchPoliticoPerformance(
  id: number,
  ano?: number | null,
  signal?: AbortSignal,
): Promise<PoliticoPerformance> {
  assertPoliticoId(id)
  const params: Record<string, unknown> = {}
  const anoSanitizado = sanitizeAno(ano)
  if (anoSanitizado !== undefined) params.ano = anoSanitizado
  return get<PoliticoPerformance>(`/politicos/${id}/performance`, { params, signal })
}

/**
 * Retorna a linha do tempo anual completa do parlamentar.
 * Cada entrada corresponde a um ano com dados registrados no banco.
 *
 * @param id     - ID inteiro positivo do político
 * @param signal - AbortSignal para cancelamento
 */
export async function fetchPoliticoTimeline(
  id: number,
  signal?: AbortSignal,
): Promise<TimelineEntrada[]> {
  assertPoliticoId(id)
  const data = await get<TimelineEntrada[]>(`/politicos/${id}/timeline`, { signal })
  assertArray<TimelineEntrada>(data, "fetchPoliticoTimeline")
  return data
}