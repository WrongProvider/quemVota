import { useQuery } from "@tanstack/react-query"
import { listarPoliticosService } from "../services/politicos.service"

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
