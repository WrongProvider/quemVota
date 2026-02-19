import {
  fetchPoliticos,
  fetchPoliticoDetalhe,
  type ListarPoliticosParams,
  type Politico,
  type PoliticoDetalhe,
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