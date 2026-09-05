import { test, expect } from "@playwright/test"

test.describe("Radar de Afinidades e Divergências de Voto", () => {
  test("deve exibir o radar de afinidades com colunas de convergência e divergência", async ({ page }) => {
    const consoleErrors: string[] = []
    page.on("console", (msg) => {
      if (msg.type() === "error") {
        consoleErrors.push(msg.text())
      }
    })

    // Navega para o perfil do parlamentar com histórico amplo de votações
    await page.goto("/politicos/alice-portugal")

    // Aguarda o carregamento do perfil
    await expect(page.locator("h1")).toContainText("Alice Portugal")

    // Localiza a seção do radar de afinidades
    const sectionRadar = page.locator('[data-testid="section-radar-afinidades"]')
    await expect(sectionRadar).toBeVisible({ timeout: 10000 })

    // Valida título da seção
    await expect(sectionRadar).toContainText("Radar de Afinidades e Divergências de Voto")

    // Valida coluna de maior convergência
    const colConvergencia = sectionRadar.locator('[data-testid="coluna-maior-convergencia"]')
    await expect(colConvergencia).toBeVisible()
    await expect(colConvergencia).toContainText("Maior Convergência de Votos")

    // Valida coluna de maior divergência
    const colDivergencia = sectionRadar.locator('[data-testid="coluna-maior-divergencia"]')
    await expect(colDivergencia).toBeVisible()
    await expect(colDivergencia).toContainText("Maior Divergência de Votos")

    // Valida presença de cards em ambas as colunas
    const cardsConvergencia = colConvergencia.locator('[data-testid="card-afinidade-item"]')
    await expect(cardsConvergencia.first()).toBeVisible({ timeout: 5000 })
    expect(await cardsConvergencia.count()).toBeGreaterThan(0)

    const cardsDivergencia = colDivergencia.locator('[data-testid="card-divergencia-item"]')
    await expect(cardsDivergencia.first()).toBeVisible({ timeout: 5000 })
    expect(await cardsDivergencia.count()).toBeGreaterThan(0)

    // Testa filtro de votações mínimas (ex: 25+ votos)
    const btn25 = sectionRadar.locator('[data-testid="btn-min-votacoes-25"]')
    await expect(btn25).toBeVisible()
    await btn25.click()

    // Valida que os cards continuam visíveis após a filtragem
    await expect(colConvergencia.locator('[data-testid="card-afinidade-item"]').first()).toBeVisible({ timeout: 5000 })

    // Testa toggle de apenas outros partidos
    const checkboxPartidos = sectionRadar.locator('[data-testid="checkbox-outros-partidos"]')
    await expect(checkboxPartidos).toBeVisible()
    await checkboxPartidos.check()

    // Captura screenshot do painel para evidência visual
    await sectionRadar.screenshot({ path: "test-results/radar-afinidades-panel.png" })
    await page.screenshot({ path: "test-results/radar-afinidades-fullpage.png", fullPage: true })

    // Valida ausência de erros graves de console
    const criticalErrors = consoleErrors.filter(
      (e) => !e.includes("favicon") && !e.includes("404")
    )
    expect(criticalErrors).toHaveLength(0)
  })
})
