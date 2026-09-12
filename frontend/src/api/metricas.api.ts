import { api } from "./client"

export interface CategoriaGasto {
  tipoDespesa: string
  valorTotal: number
}

export interface TipoProposicao {
  sigla: string
  quantidade: number
}

export interface MetricasDeputado {
  idDeputado: number
  totalGastoCota: number
  topGastos: CategoriaGasto[]
  totalProposicoesAutor: number
  distribuicaoProposicoes: TipoProposicao[]
  totalPresencas: number
  totalDiscursos: number
}

export interface ResumoMetricasDeputado {
  idDeputado: number
  nome: string
  partido: string | null
  uf: string | null
  urlFoto: string | null
  totalGastoCota: number
  totalProposicoesAutor: number
  totalPresencas: number
  totalDiscursos: number
  totalVotosNominais: number
  fidelidadePartidaria: number | null
  totalRelatorias: number
}

export async function fetchResumoMetricas(): Promise<ResumoMetricasDeputado[]> {
  const response = await api.get<ResumoMetricasDeputado[]>('/metricas/resumo')
  return response.data
}

export async function fetchMetricasDeputado(id: number): Promise<MetricasDeputado> {
  const response = await api.get<MetricasDeputado>(`/metricas/deputados/${id}`)
  return response.data
}

