import {
  fetchPoliticos,
  type ListarPoliticosParams,
  type Politico,
} from "../api/politicos.api"

export async function listarPoliticosService(
  params?: ListarPoliticosParams
): Promise<Politico[]> {
  return fetchPoliticos(params)
}
