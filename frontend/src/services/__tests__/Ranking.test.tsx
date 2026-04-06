import { render, screen } from "@testing-library/react"
import { MemoryRouter } from "react-router-dom"
import { describe, it, expect, vi } from "vitest"

// Mock dos hooks que chamam a API
vi.mock("../hooks/useRankings", () => ({
  useRankingPerformance: () => ({ data: null, isLoading: true, error: null }),
  useRankingDespesas: () => ({ data: null, isLoading: true, error: null }),
  useRankingDiscursos: () => ({ data: null, isLoading: true, error: null }),
  useRankingLucroEmpresas: () => ({ data: null, isLoading: true, error: null }),
}))

import Rankings from "../pages/Rankings"

describe("Rankings Page", () => {
  it("renderiza o título corretamente", () => {
    render(
      <MemoryRouter>
        <Rankings />
      </MemoryRouter>
    )
    expect(screen.getByText("Rankings Parlamentares")).toBeInTheDocument()
  })

  it("mostra estado de loading", () => {
    render(
      <MemoryRouter>
        <Rankings />
      </MemoryRouter>
    )
    expect(screen.getByText("Carregando rankings...")).toBeInTheDocument()
  })
})