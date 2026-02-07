import { api } from "./client"

// timpos de dados retornados pela API
export interface Politico {
  id: number
  nome: string
  uf: string
  partido_sigla: string
}

// função para listar políticos, com suporte a filtros e paginação
export async function listarPoliticos(params?: {
  uf?: string
  limit?: number
  offset?: number
}) {
  const response = await api.get<Politico[]>("/politicos", {
    params,
  })

  return response.data
}
