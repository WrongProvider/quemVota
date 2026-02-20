import {
  fetchPoliticos,
  fetchPoliticoDetalhe,
  fetchPoliticoEstatisticas,
  fetchPoliticoPerformance,
  type ListarPoliticosParams,
  type Politico,
  type PoliticoDetalhe,
  type PoliticoEstatisticas,
  type PoliticoPerformance,
} from "../api/politicos.api"

export async function listarPoliticosService(
  params?: ListarPoliticosParams
): Promise<Politico[]> {
  return await fetchPoliticos(params)
}

export async function obterPoliticoDetalheService(
  id: number
): Promise<PoliticoDetalhe> {
  return await fetchPoliticoDetalhe(id)
}

export async function obterPoliticoEstatisticasService(
  id: number
): Promise<PoliticoEstatisticas> {
  return await fetchPoliticoEstatisticas(id)
}


export async function obterPoliticoPerformanceService(
  id: number
): Promise<PoliticoPerformance> {
  return await fetchPoliticoPerformance(id)
}