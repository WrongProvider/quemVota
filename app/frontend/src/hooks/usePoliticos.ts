import { useQuery } from "@tanstack/react-query"
import { listarPoliticosService, obterPoliticoDetalheService } from "../services/politicos.service"

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
    // staleTime: 1000 * 60 * 5, // 5 minutos
    // gcTime: 1000 * 60 * 10, // cache por 10 minutos
    staleTime: 0, // 5 minutos
    gcTime: 0, // cache por 10 minutos
    refetchOnMount: "always",
  refetchOnWindowFocus: false
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