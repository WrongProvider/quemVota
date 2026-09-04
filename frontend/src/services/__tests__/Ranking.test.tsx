import { render, screen } from "@testing-library/react"
import { MemoryRouter } from "react-router-dom"
import { describe, it, expect, vi } from "vitest"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"

// Mock dos hooks que chamam a API
vi.mock("../../hooks/useRankings", () => ({
  useRankingDespesas: () => ({ data: null, isLoading: true, error: null }),
  useRankingDiscursos: () => ({ data: null, isLoading: true, error: null }),
  useRankingLucroEmpresas: () => ({ data: null, isLoading: true, error: null }),
}))

import Rankings from "../../pages/Rankings"

function renderWithProviders(ui: React.ReactElement) {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
    },
  })
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter>{ui}</MemoryRouter>
    </QueryClientProvider>
  )
}

describe("Rankings Page", () => {
  it("renderiza o título corretamente", () => {
    renderWithProviders(<Rankings />)
    expect(screen.getByText("Rankings Parlamentares")).toBeInTheDocument()
  })

  it("mostra estado de loading", () => {
    renderWithProviders(<Rankings />)
    expect(screen.getByText("Carregando dados...")).toBeInTheDocument()
  })
})