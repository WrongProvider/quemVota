import {
  fetchPoliticos,
  fetchPoliticoDetalhe,
  fetchPoliticoEstatisticas,
  type ListarPoliticosParams,
  type Politico,
  type PoliticoDetalhe,
  type PoliticoEstatisticas,
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