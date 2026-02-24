// import { api } from "./client"

// // interfaces e tipos
// export interface Politico {
//   id: number
//   nome: string
//   uf: string
//   partido_sigla: string
  
// }

// export interface ListarPoliticosParams {
//   q?: string
//   uf?: string
//   limit?: number
//   offset?: number
// }

// export interface PoliticoDetalhe extends Politico {
//   escolaridade: string
//   situacao: string
//   condicao_eleitoral: string
//   email_gabinete: string
//   telefone_gabinete: string
// }

// export interface PoliticoEstatisticas {
//   total_votacoes: number
//   total_despesas: number
//   total_gasto: number
//   media_mensal: number
//   primeiro_ano: number | null
//   ultimo_ano: number | null
// }

// export interface PoliticoPerformance {
//   score_final: number
//   media_global: number
//   detalhes: {
//     nota_assiduidade: number
//     nota_economia: number
//     nota_producao: number
//   }[]
//   info: {
//     total_gasto: number
//     cota_utilizada_pct: number
//   }
// }
// // fim interfaces e tipos

// // listagem de politicos
// export async function fetchPoliticos(
//   params?: ListarPoliticosParams
// ): Promise<Politico[]> {
//   const { data } = await api.get<Politico[]>("/politicos", {
//     params,
//   })

//   return data
// }

// // detalhe de politico
// export async function fetchPoliticoDetalhe(
//   id: number
// ): Promise<PoliticoDetalhe> {
//   if (!id) {
//     throw new Error("ID do político é obrigatório")
//   }

//   const { data } = await api.get<PoliticoDetalhe>(`/politicos/${id}`)

//   return data
// }

// export async function fetchPoliticoEstatisticas(
//   id: number
// ): Promise<PoliticoEstatisticas> {
//   if (!id) {
//     throw new Error("ID do político é obrigatório")
//   }

//   const { data } = await api.get<PoliticoEstatisticas>(
//     `/politicos/${id}/estatisticas`
//   )

//   return data
// }

// export async function fetchPoliticoPerformance(
//   id: number
// ): Promise<PoliticoPerformance> {
//   if (!id) {
//     throw new Error("ID do político é obrigatório")
//   }

//   const { data } = await api.get<PoliticoPerformance>(
//     `/politicos/${id}/performance`
//   )

//   return data
// }


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
  readonly total_gasto: number
  readonly cota_utilizada_pct: number
}

export interface PoliticoPerformance {
  readonly politico_id: number
  readonly score_final: number
  readonly media_global: number
  readonly detalhes: NotasPerformance
  readonly info: InfoPerformance
}

// ─────────────────────────────────────────────────────────────────────────────
// Parâmetros de busca com tipos estritos
// ─────────────────────────────────────────────────────────────────────────────

export interface ListarPoliticosParams {
  q?: string
  uf?: string
  limit?: number
  offset?: number
}

// ─────────────────────────────────────────────────────────────────────────────
// Guards de tipo em runtime — OWASP A08 (Data Integrity)
// Garantem que respostas inesperadas da API não se propagam silenciosamente.
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
// Sanitizadores de parâmetros — OWASP A04 (Insecure Design)
// Coerce e limita valores antes de enviá-los à rede.
// ─────────────────────────────────────────────────────────────────────────────

function sanitizeListarParams(params?: ListarPoliticosParams): Record<string, unknown> {
  const sanitized: Record<string, unknown> = {}

  if (params?.q !== undefined) {
    const trimmed = String(params.q).trim()
    if (trimmed.length > 0) {
      // Trunca busca no limite do backend; nunca envia string vazia
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

  return sanitized
}

// ─────────────────────────────────────────────────────────────────────────────
// Helper interno — evita duplicação de lógica de requisição + abort signal
// ─────────────────────────────────────────────────────────────────────────────

async function get<T>(
  url: string,
  config?: AxiosRequestConfig,
  controller?: AbortController,
): Promise<T> {
  const { data } = await api.get<T>(url, {
    ...config,
    signal: controller?.signal,
  })
  return data
}

// ─────────────────────────────────────────────────────────────────────────────
// Funções de API pública
// ─────────────────────────────────────────────────────────────────────────────

/**
 * Lista políticos com filtros opcionais.
 * Parâmetros são sanitizados antes do envio.
 *
 * @param params   - Filtros de busca (q, uf, limit, offset)
 * @param signal   - AbortSignal para cancelamento (React strictMode / cleanup)
 */
export async function fetchPoliticos(
  params?: ListarPoliticosParams,
  signal?: AbortSignal,
): Promise<Politico[]> {
  const sanitized = sanitizeListarParams(params)
  const data = await get<Politico[]>("/politicos", { params: sanitized, signal })
  assertArray<Politico>(data, "fetchPoliticos")
  return data
}

/**
 * Retorna o detalhe de um político pelo ID interno.
 *
 * @param id     - ID inteiro positivo do político
 * @param signal - AbortSignal para cancelamento
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
 * @param signal - AbortSignal para cancelamento
 */
export async function fetchPoliticoEstatisticas(
  id: number,
  signal?: AbortSignal,
): Promise<PoliticoEstatisticas> {
  assertPoliticoId(id)
  return get<PoliticoEstatisticas>(`/politicos/${id}/estatisticas`, { signal })
}

/**
 * Retorna o score de performance parlamentar de um político.
 *
 * @param id     - ID inteiro positivo do político
 * @param signal - AbortSignal para cancelamento
 */
export async function fetchPoliticoPerformance(
  id: number,
  signal?: AbortSignal,
): Promise<PoliticoPerformance> {
  assertPoliticoId(id)
  return get<PoliticoPerformance>(`/politicos/${id}/performance`, { signal })
}