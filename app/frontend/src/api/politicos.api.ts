import { api } from "./client"

// interfaces e tipos
export interface Politico {
  id: number
  nome: string
  uf: string
  partido_sigla: string
  
}

export interface ListarPoliticosParams {
  q?: string
  uf?: string
  limit?: number
  offset?: number
}

export interface PoliticoDetalhe extends Politico {
  escolaridade: string
  situacao: string
  condicao_eleitoral: string
  email_gabinete: string
  telefone_gabinete: string
}

export interface PoliticoEstatisticas {
  total_votacoes: number
  total_despesas: number
  total_gasto: number
  media_mensal: number
  primeiro_ano: number | null
  ultimo_ano: number | null
}

export interface PoliticoPerformance {
  score_final: number
  media_global: number
  detalhes: {
    nota_assiduidade: number
    nota_economia: number
    nota_producao: number
  }[]
  info: {
    total_gasto: number
    cota_utilizada_pct: number
  }
}
// fim interfaces e tipos

// listagem de politicos
export async function fetchPoliticos(
  params?: ListarPoliticosParams
): Promise<Politico[]> {
  const { data } = await api.get<Politico[]>("/politicos", {
    params,
  })

  return data
}

// detalhe de politico
export async function fetchPoliticoDetalhe(
  id: number
): Promise<PoliticoDetalhe> {
  if (!id) {
    throw new Error("ID do político é obrigatório")
  }

  const { data } = await api.get<PoliticoDetalhe>(`/politicos/${id}`)

  return data
}

export async function fetchPoliticoEstatisticas(
  id: number
): Promise<PoliticoEstatisticas> {
  if (!id) {
    throw new Error("ID do político é obrigatório")
  }

  const { data } = await api.get<PoliticoEstatisticas>(
    `/politicos/${id}/estatisticas`
  )

  return data
}

export async function fetchPoliticoPerformance(
  id: number
): Promise<PoliticoPerformance> {
  if (!id) {
    throw new Error("ID do político é obrigatório")
  }

  const { data } = await api.get<PoliticoPerformance>(
    `/politicos/${id}/performance`
  )

  return data
}