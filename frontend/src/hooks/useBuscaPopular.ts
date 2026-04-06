// src/hooks/useBuscaPopular.ts

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { fetchMaisPesquisados, registrarBusca } from "../api/buscaPopular.api"

export const buscaPopularKeys = {
  maisPesquisados: (limit: number) => ["busca", "mais-pesquisados", limit] as const,
}

export function useMaisPesquisados(limit = 10) {
  return useQuery({
    queryKey: buscaPopularKeys.maisPesquisados(limit),
    queryFn: () => fetchMaisPesquisados(limit),
    staleTime: 5 * 60 * 1_000,  // 5 min — muda devagar
    gcTime:   15 * 60 * 1_000,
  })
}

/** Chame este hook nas páginas de detalhe para registrar visualizações */
export function useRegistrarBusca() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (politicoId: number) => registrarBusca(politicoId),
    onSuccess: () => {
      // Invalida o cache para atualizar o ranking na próxima vez
      queryClient.invalidateQueries({ queryKey: ["busca"] })
    },
  })
}