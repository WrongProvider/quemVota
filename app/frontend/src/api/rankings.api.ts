import { api } from "./client"

export interface RankingItem {
//   id: number
//   nome: string
//   partido: string
//   uf: string
//   score: number
//   posicao: number
  politico_id: number
  nome: string
  total_gasto: number
}

export async function listarRankings(limit: number = 100): Promise<RankingItem[]> {
  const response = await api.get("/ranking/despesa_politico", {
    params: { limit },
  })
  return response.data
}
