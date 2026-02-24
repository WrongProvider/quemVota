import { useQuery } from "@tanstack/react-query"
import { listarPoliticosService, obterPoliticoDetalheService, obterPoliticoEstatisticasService, obterPoliticoPerformanceService } from "../services/politicos.service"
import { useInfiniteQuery } from "@tanstack/react-query"

interface UsePoliticosParams {
  q?: string
  uf?: string
  limit?: number
  offset?: number
}

export function usePoliticos(params?: UsePoliticosParams) {
  return useQuery({
    queryKey: ["politicos", params],
    queryFn: () => listarPoliticosService(params),
    staleTime: 1000 * 60 * 5, // 5 minutos
    gcTime: 1000 * 60 * 10, // cache por 10 minutos
  })
}

export function usePoliticoDetalhe(id: number) {
  return useQuery({
    queryKey: ["politico", id],
    queryFn: () => obterPoliticoDetalheService(id),
    enabled: !!id, // só executa se existir id
    staleTime: 1000 * 60 * 5,
    gcTime: 1000 * 60 * 10,
  })
}

export function usePoliticoEstatisticas(id: number) {
  return useQuery({
    queryKey: ["politico-estatisticas", id],
    queryFn: () => obterPoliticoEstatisticasService(id),
    enabled: !!id,
    staleTime: 1000 * 60 * 5,
    gcTime: 1000 * 60 * 10,
  })
}


export function usePoliticoPerformance(id: number) {
  return useQuery({
    queryKey: ["politico-performance", id],
    queryFn: () => obterPoliticoPerformanceService(id),
    enabled: !!id,
    staleTime: 1000 * 60 * 5,
  })
}