import { api } from "./client"

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