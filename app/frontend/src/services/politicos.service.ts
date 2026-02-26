/**
 * politicos.service.ts — Camada de serviço para o domínio de Políticos.
 *
 * Responsabilidade: orquestrar chamadas à API, tratar erros de forma
 * centralizada e expor uma interface estável para os hooks/componentes.
 *
 * OWASP coberto:
 *  - A03 Sensitive Data Exposure : erros HTTP não vazam detalhes internos
 *    para camadas superiores; apenas mensagens controladas chegam à UI.
 *  - A04 Insecure Design         : segunda linha de defesa nos limites de
 *    paginação (o sanitizador da API já aplica a primeira).
 *  - A09 Logging & Monitoring    : erros classificados e logados de forma
 *    estruturada sem PII ou stack traces em produção.
 */

import { AxiosError } from "axios"
import {
  fetchPoliticos,
  fetchPoliticosPage,
  fetchPoliticoDetalhe,
  fetchPoliticoEstatisticas,
  fetchPoliticoPerformance,
  fetchPoliticoTimeline,
  type ListarPoliticosParams,
  type Politico,
  type PoliticosPage,
  type PoliticoDetalhe,
  type PoliticoEstatisticas,
  type PoliticoPerformance,
  type TimelineEntrada,
} from "../api/politicos.api"

// ─────────────────────────────────────────────────────────────────────────────
// Erros de domínio — OWASP A03: mensagens controladas, sem vazamento interno
// ─────────────────────────────────────────────────────────────────────────────

export type ApiErrorKind =
  | "not_found"
  | "unauthorized"
  | "forbidden"
  | "rate_limited"
  | "server_error"
  | "network_error"
  | "cancelled"
  | "unknown"

export class PoliticoServiceError extends Error {
  readonly kind: ApiErrorKind
  readonly statusCode?: number

  constructor(message: string, kind: ApiErrorKind, statusCode?: number) {
    super(message)
    this.name = "PoliticoServiceError"
    this.kind = kind
    this.statusCode = statusCode
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// Classificação e normalização de erros — OWASP A03 + A09
// ─────────────────────────────────────────────────────────────────────────────

const HTTP_MESSAGES: Record<number, string> = {
  400: "Requisição inválida. Verifique os parâmetros enviados.",
  401: "Não autorizado. Faça login novamente.",
  403: "Acesso negado.",
  404: "Recurso não encontrado.",
  429: "Muitas requisições. Tente novamente em instantes.",
  500: "Erro interno do servidor. Tente novamente mais tarde.",
  502: "Serviço temporariamente indisponível.",
  503: "Serviço temporariamente indisponível.",
}

function normalizeError(error: unknown, context: string): PoliticoServiceError {
  if (error instanceof Error && error.name === "CanceledError") {
    return new PoliticoServiceError("Requisição cancelada.", "cancelled")
  }

  if (error instanceof AxiosError) {
    const status = error.response?.status

    if (import.meta.env.DEV) {
      console.warn(`[PoliticoService][${context}]`, { status, message: error.message })
    } else {
      console.warn(`[PoliticoService] ${context} — HTTP ${status ?? "sem resposta"}`)
    }

    if (!error.response) {
      return new PoliticoServiceError(
        "Falha de conexão. Verifique sua internet.",
        "network_error",
      )
    }

    const message = HTTP_MESSAGES[status!] ?? "Erro inesperado. Tente novamente."
    const kind: ApiErrorKind =
      status === 404 ? "not_found"
      : status === 401 ? "unauthorized"
      : status === 403 ? "forbidden"
      : status === 429 ? "rate_limited"
      : (status ?? 0) >= 500 ? "server_error"
      : "unknown"

    return new PoliticoServiceError(message, kind, status)
  }

  if (error instanceof TypeError) {
    if (import.meta.env.DEV) console.error(`[PoliticoService][${context}] TypeError:`, error.message)
    return new PoliticoServiceError("Dados recebidos em formato inválido.", "unknown")
  }

  return new PoliticoServiceError("Erro inesperado.", "unknown")
}

// ─────────────────────────────────────────────────────────────────────────────
// Funções de serviço públicas
// ─────────────────────────────────────────────────────────────────────────────

/**
 * Lista políticos com filtros opcionais.
 */
export async function listarPoliticosService(
  params?: ListarPoliticosParams,
  signal?: AbortSignal,
): Promise<Politico[]> {
  try {
    return await fetchPoliticos(params, signal)
  } catch (error) {
    throw normalizeError(error, "listarPoliticosService")
  }
}

/**
 * Retorna uma página de políticos para infinite scroll.
 */
export async function listarPoliticosPageService(
  params?: ListarPoliticosParams,
  signal?: AbortSignal,
): Promise<PoliticosPage> {
  try {
    return await fetchPoliticosPage(params, signal)
  } catch (error) {
    throw normalizeError(error, "listarPoliticosPageService")
  }
}

/**
 * Retorna o detalhe de um político pelo ID.
 */
export async function obterPoliticoDetalheService(
  id: number,
  signal?: AbortSignal,
): Promise<PoliticoDetalhe> {
  try {
    return await fetchPoliticoDetalhe(id, signal)
  } catch (error) {
    throw normalizeError(error, "obterPoliticoDetalheService")
  }
}

/**
 * Retorna as estatísticas de um político.
 *
 * @param id     - ID inteiro positivo
 * @param ano    - Quando fornecido, filtra os dados pelo ano — útil para a timeline
 * @param signal - AbortSignal para cancelamento
 */
export async function obterPoliticoEstatisticasService(
  id: number,
  ano?: number | null,
  signal?: AbortSignal,
): Promise<PoliticoEstatisticas> {
  try {
    return await fetchPoliticoEstatisticas(id, ano, signal)
  } catch (error) {
    throw normalizeError(error, "obterPoliticoEstatisticasService")
  }
}

/**
 * Retorna o score de performance de um político.
 *
 * @param id     - ID inteiro positivo
 * @param ano    - Quando fornecido, calcula o score apenas para aquele ano
 * @param signal - AbortSignal para cancelamento
 */
export async function obterPoliticoPerformanceService(
  id: number,
  ano?: number | null,
  signal?: AbortSignal,
): Promise<PoliticoPerformance> {
  try {
    return await fetchPoliticoPerformance(id, ano, signal)
  } catch (error) {
    throw normalizeError(error, "obterPoliticoPerformanceService")
  }
}

/**
 * Retorna a linha do tempo anual do parlamentar.
 * Cada item contém score, notas detalhadas, estatísticas e info de cota
 * para um ano com dados registrados no banco.
 *
 * @param id     - ID inteiro positivo
 * @param signal - AbortSignal para cancelamento
 */
export async function obterPoliticoTimelineService(
  id: number,
  signal?: AbortSignal,
): Promise<TimelineEntrada[]> {
  try {
    return await fetchPoliticoTimeline(id, signal)
  } catch (error) {
    throw normalizeError(error, "obterPoliticoTimelineService")
  }
}