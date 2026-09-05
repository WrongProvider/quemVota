// src/api/buscaPopular.api.ts

import { api } from "./client"

export interface MaisPesquisado {
  readonly politico_id:             number
  readonly nome:                    string
  readonly uf:                      string | null
  readonly partido_sigla:           string | null
  readonly url_foto:                string | null
  readonly count:                   number
  readonly slug?:                   string | null
  readonly condicao_eleitoral?:     string | null
  readonly id_legislatura_inicial?: number | null
  readonly id_legislatura_final?:   number | null
  readonly ano_inicio?:             number | null
  readonly ano_fim?:                number | null
}


/** Registra que o usuário visualizou/clicou em um político — fire and forget */
export async function registrarBusca(politicoId: number): Promise<void> {
  try {
    await api.post(`/busca/registrar/${politicoId}`)
  } catch {
    // silencioso — não queremos erros de tracking afetando a UX
  }
}

/** Retorna os N políticos mais pesquisados */
export async function fetchMaisPesquisados(limit = 10): Promise<MaisPesquisado[]> {
  const { data } = await api.get<MaisPesquisado[]>("/busca/mais-pesquisados", {
    params: { limit },
  })
  return data
}