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

export async function fetchPoliticos(
  params?: ListarPoliticosParams
): Promise<Politico[]> {
  const { data } = await api.get<Politico[]>("/politicos", {
    params,
  })

  return data
}
