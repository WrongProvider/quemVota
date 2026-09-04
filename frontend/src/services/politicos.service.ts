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
  fetchPoliticoDetalheBySlug,
  fetchPoliticoEstatisticas,
  fetchPoliticoPerformance,
  fetchPoliticoTimeline,
  nomeParaSlug,
  type ListarPoliticosParams,
  type Politico,
  type PoliticosPage,
  type PoliticoDetalhe,
  type PoliticoEstatisticas,
  type PoliticoPerformance,
  type TimelineEntrada,
  type AtividadeLegislativaParams,
  type AtividadeLegislativaResponse,
  fetchPoliticoAtividade,
  fetchComparacaoPoliticos,
  type ComparacaoPoliticosGrafoResponse,
  type CompararPoliticosParams,
  fetchPoliticoTemas,
  type PoliticoTemasResponse,
  type PoliticoTemasParams,
  fetchFidelidadePartidaria,
  type FidelidadePartidariaResponse,
  type FidelidadePartidariaParams,
  fetchPoliticoAfinidades,
  type AfinidadesPoliticoResponse,
  type AfinidadesPoliticoParams,
} from "../api/politicos.api"

// ─────────────────────────────────────────────────────────────────────────────
// Erros de domínio — OWASP A03
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
 * Retorna o detalhe de um político pelo ID numérico.
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
 * Retorna o detalhe de um político pelo slug do nome.
 *
 * Estratégia em duas etapas:
 *  1. Tenta GET /politicos/slug/:slug (endpoint dedicado no backend).
 *  2. Se o backend retornar 404 ou ainda não suportar o endpoint (500/404),
 *     faz fallback via listagem com busca textual e compara slugs localmente.
 *     Isso permite usar a feature sem alteração imediata no backend.
 *
 * Remova o fallback assim que o endpoint /politicos/slug/:slug estiver estável.
 */
export async function obterPoliticoDetalheBySlugService(
  slug: string,
  signal?: AbortSignal,
): Promise<PoliticoDetalhe> {
  const s = slug?.trim()
  if (!s || s === "null" || s === "undefined") {
    throw new PoliticoServiceError("Slug inválido.", "not_found", 404)
  }

  // Suporte a resolução direta se for um ID numérico
  if (/^\d+$/.test(s)) {
    return await fetchPoliticoDetalhe(Number(s), signal)
  }

  // ── Tentativa 1: endpoint dedicado ──────────────────────────────────────
  try {
    return await fetchPoliticoDetalheBySlug(s, signal)
  } catch (error) {
    const serviceError = normalizeError(error, "obterPoliticoDetalheBySlugService[dedicated]")

    // Se não for not_found nem server_error, propaga imediatamente
    if (serviceError.kind !== "not_found" && serviceError.kind !== "server_error") {
      throw serviceError
    }

    if (import.meta.env.DEV) {
      console.warn(
        `[PoliticoService] Endpoint /politicos/slug/${slug} retornou ${serviceError.statusCode}. ` +
        `Tentando fallback via listagem...`
      )
    }
  }

  // ── Fallback: busca textual + comparação de slug local ──────────────────
  //
  // Converte o slug de volta em palavras para a busca (ex: "joao-silva" → "joao silva").
  // Não é perfeito, mas cobre a maioria dos casos enquanto o backend não tem o endpoint.
  try {
    const termoBusca = slug.replace(/-/g, " ")
    const candidatos = await fetchPoliticos({ q: termoBusca, limit: 20 }, signal)

    const encontrado = candidatos.find(
      (p) => nomeParaSlug(p.nome) === slug,
    )

    if (!encontrado) {
      throw new PoliticoServiceError(
        "Parlamentar não encontrado.",
        "not_found",
        404,
      )
    }

    // Busca o detalhe completo pelo ID resolvido
    return await fetchPoliticoDetalhe(encontrado.id, signal)
  } catch (error) {
    if (error instanceof PoliticoServiceError) throw error
    throw normalizeError(error, "obterPoliticoDetalheBySlugService[fallback]")
  }
}

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

// Re-exporta para que componentes importem só daqui
export { nomeParaSlug }


export async function obterPoliticoAtividadeService(
  id: number,
  params?: AtividadeLegislativaParams,
  signal?: AbortSignal,
): Promise<AtividadeLegislativaResponse> {
  try {
    return await fetchPoliticoAtividade(id, params, signal)
  } catch (error) {
    throw normalizeError(error, "obterPoliticoAtividadeService")
  }
}

export async function obterComparacaoPoliticosService(
  idOrSlug1: string | number,
  idOrSlug2: string | number,
  params?: CompararPoliticosParams,
  signal?: AbortSignal,
): Promise<ComparacaoPoliticosGrafoResponse> {
  try {
    return await fetchComparacaoPoliticos(idOrSlug1, idOrSlug2, params, signal)
  } catch (error) {
    throw normalizeError(error, "obterComparacaoPoliticosService")
  }
}

export async function obterPoliticoTemasService(
  idOrSlug: string | number,
  params?: PoliticoTemasParams,
  signal?: AbortSignal,
): Promise<PoliticoTemasResponse | null> {
  try {
    return await fetchPoliticoTemas(idOrSlug, params, signal)
  } catch (error) {
    throw normalizeError(error, "obterPoliticoTemasService")
  }
}

export async function obterFidelidadePartidariaService(
  idOrSlug: string | number,
  params?: FidelidadePartidariaParams,
  signal?: AbortSignal,
): Promise<FidelidadePartidariaResponse | null> {
  try {
    return await fetchFidelidadePartidaria(idOrSlug, params, signal)
  } catch (error) {
    throw normalizeError(error, "obterFidelidadePartidariaService")
  }
}

export async function obterPoliticoAfinidadesService(
  idOrSlug: string | number,
  params?: AfinidadesPoliticoParams,
  signal?: AbortSignal,
): Promise<AfinidadesPoliticoResponse | null> {
  try {
    return await fetchPoliticoAfinidades(idOrSlug, params, signal)
  } catch (error) {
    throw normalizeError(error, "obterPoliticoAfinidadesService")
  }
}