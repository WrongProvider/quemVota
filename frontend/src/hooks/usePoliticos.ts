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

import { useQuery, keepPreviousData, type UseQueryResult } from "@tanstack/react-query"
import {
  listarPoliticosService,
  obterPoliticoDetalheService,
  obterPoliticoEstatisticasService,
  obterPoliticoPerformanceService,
  obterPoliticoTimelineService,
  obterPoliticoDetalheBySlugService,
  obterPoliticoAtividadeService,
  obterComparacaoPoliticosService,
  obterPoliticoTemasService,
  obterFidelidadePartidariaService,
  obterPoliticoAfinidadesService,
  PoliticoServiceError,
} from "../services/politicos.service"
import type {
  ListarPoliticosParams,
  Politico,
  PoliticoDetalhe,
  PoliticoEstatisticas,
  PoliticoPerformance,
  TimelineEntrada,
  AtividadeLegislativaParams,
  AtividadeLegislativaResponse,
  ComparacaoPoliticosGrafoResponse,
  CompararPoliticosParams,
  PoliticoTemasResponse,
  PoliticoTemasParams,
  FidelidadePartidariaResponse,
  FidelidadePartidariaParams,
  AfinidadesPoliticoResponse,
  AfinidadesPoliticoParams,
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
  slug:         (slug: string) => [...politicoKeys.details(), "slug", slug] as const,
  atividade:    (id: number, params?: AtividadeLegislativaParams) =>
    [...politicoKeys.detail(id), "atividade", params ?? {}] as const,
  comparacao:   (idOrSlug1: string | number, idOrSlug2: string | number, params?: CompararPoliticosParams) =>
    [...politicoKeys.all, "comparacao", String(idOrSlug1), String(idOrSlug2), params ?? {}] as const,
  temas:        (idOrSlug: string | number, legislatura?: number) =>
    [...politicoKeys.all, "temas", String(idOrSlug), legislatura ?? 57] as const,
  fidelidade:   (idOrSlug: string | number, limitDivergencias?: number) =>
    [...politicoKeys.all, "fidelidade", String(idOrSlug), limitDivergencias ?? 50] as const,
  afinidades:   (idOrSlug: string | number, params?: AfinidadesPoliticoParams) =>
    [...politicoKeys.all, "afinidades", String(idOrSlug), params ?? {}] as const,
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

/**
 * Retorna o detalhe de um político pelo slug do nome.
 *
 * Só dispara quando `slug` for uma string não-numérica válida.
 * Usa a mesma política de retry e cache dos outros hooks de detalhe.
 *
 * @example
 * const { data } = usePoliticoDetalheBySlug("joao-silva-neto")
 */
export function usePoliticoDetalheBySlug(
  slug: string | undefined,
): UseQueryResult<PoliticoDetalhe, PoliticoServiceError> {
  const isValido = Boolean(
    slug && slug !== "null" && slug !== "undefined" && slug.trim().length > 0
  )
  return useQuery({
    queryKey: politicoKeys.slug(slug ?? ""),
    queryFn: ({ signal }) => obterPoliticoDetalheBySlugService(slug!, signal),
    enabled: isValido,
    staleTime: STALE_TIME_MS,
    gcTime: GC_TIME_MS,
    retry: shouldRetry,
    retryDelay,
  })
}
/**
 * Retorna o histórico de atividade legislativa de um político:
 * votações com o voto individual e proposições de autoria.
 *
 * A query key inclui os parâmetros de paginação e filtro — cada
 * combinação tem cache independente, permitindo navegação entre
 * páginas sem refetch das anteriores.
 *
 * O ano respeita o seletor global do PoliticoDetalhe: quando o usuário
 * filtra por ano, a query refaz automaticamente com o novo contexto.
 *
 * @param id     - ID inteiro positivo do político
 * @param params - Filtros opcionais: ano, limit/offset de votações e proposições
 *
 * @example
 * // Mandato completo, página 1
 * const { data } = usePoliticoAtividade(42)
 *
 * @example
 * // Filtrado por ano, segunda página de votações
 * const { data } = usePoliticoAtividade(42, { ano: 2023, limit_votacoes: 15, offset_votacoes: 15 })
 */
export function usePoliticoAtividade(
  id: number,
  params?: AtividadeLegislativaParams,
): UseQueryResult<AtividadeLegislativaResponse, PoliticoServiceError> {
  return useQuery({
    queryKey: politicoKeys.atividade(id, params),
    queryFn: ({ signal }) => obterPoliticoAtividadeService(id, params, signal),
    enabled: Number.isInteger(id) && id > 0,
    staleTime: STALE_TIME_MS,
    gcTime: GC_TIME_MS,
    retry: shouldRetry,
    retryDelay,
  })
}

/**
 * Compara o posicionamento de votações e alinhamento entre 2 políticos.
 * Prioriza dados do grafo Apache AGE com fallback relacional.
 */
export function useComparacaoPoliticos(
  idOrSlug1?: string | number,
  idOrSlug2?: string | number,
  params?: CompararPoliticosParams,
): UseQueryResult<ComparacaoPoliticosGrafoResponse, PoliticoServiceError> {
  const s1 = String(idOrSlug1 ?? "").trim()
  const s2 = String(idOrSlug2 ?? "").trim()
  const enabled = Boolean(
    s1 &&
    s2 &&
    s1 !== "null" &&
    s2 !== "null" &&
    s1 !== "undefined" &&
    s2 !== "undefined" &&
    s1 !== s2
  )

  return useQuery({
    queryKey: politicoKeys.comparacao(idOrSlug1 ?? "", idOrSlug2 ?? "", params),
    queryFn: ({ signal }) =>
      obterComparacaoPoliticosService(idOrSlug1!, idOrSlug2!, params, signal),
    placeholderData: keepPreviousData,
    enabled,
    staleTime: STALE_TIME_MS,
    gcTime: GC_TIME_MS,
    retry: shouldRetry,
    retryDelay,
  })
}

/**
 * Retorna os temas de atuação parlamentar do político (SPEC-001).
 *
 * Cache de 10 min. Retorna null se não houver classificação disponível (404 gracioso).
 */
export function usePoliticoTemas(
  idOrSlug?: string | number,
  params?: PoliticoTemasParams,
): UseQueryResult<PoliticoTemasResponse | null, PoliticoServiceError> {
  const s = String(idOrSlug ?? "").trim()
  const enabled = Boolean(s && s !== "null" && s !== "undefined")

  return useQuery({
    queryKey: politicoKeys.temas(idOrSlug ?? "", params?.id_legislatura),
    queryFn: ({ signal }) => obterPoliticoTemasService(idOrSlug!, params, signal),
    enabled,
    staleTime: 10 * 60 * 1_000,
    gcTime: 15 * 60 * 1_000,
    retry: false, // 404 significa que o pipeline ainda não processou dados para o parlamentar
  })
}

/**
 * Retorna a fidelidade partidária e divergências em votações nominais.
 *
 * Cache de 10 min. Retorna null se não houver dados/partido (404/400).
 */
export function usePoliticoFidelidade(
  idOrSlug?: string | number,
  params?: FidelidadePartidariaParams,
): UseQueryResult<FidelidadePartidariaResponse | null, PoliticoServiceError> {
  const s = String(idOrSlug ?? "").trim()
  const enabled = Boolean(s && s !== "null" && s !== "undefined")

  return useQuery({
    queryKey: politicoKeys.fidelidade(idOrSlug ?? "", params?.limit_divergencias),
    queryFn: ({ signal }) => obterFidelidadePartidariaService(idOrSlug!, params, signal),
    enabled,
    staleTime: 10 * 60 * 1_000,
    gcTime: 15 * 60 * 1_000,
    retry: false, // 404/400 gracioso
  })
}

/**
 * Retorna os parlamentares com maior convergência e divergência em votações nominais.
 *
 * Cache de 10 min. Retorna null se não houver dados suficientes (404/400 gracioso).
 */
export function usePoliticoAfinidades(
  idOrSlug?: string | number,
  params?: AfinidadesPoliticoParams,
): UseQueryResult<AfinidadesPoliticoResponse | null, PoliticoServiceError> {
  const s = String(idOrSlug ?? "").trim()
  const enabled = Boolean(s && s !== "null" && s !== "undefined")

  return useQuery({
    queryKey: politicoKeys.afinidades(idOrSlug ?? "", params),
    queryFn: ({ signal }) => obterPoliticoAfinidadesService(idOrSlug!, params, signal),
    enabled,
    staleTime: 10 * 60 * 1_000,
    gcTime: 15 * 60 * 1_000,
    retry: false, // 404/400 gracioso
  })
}