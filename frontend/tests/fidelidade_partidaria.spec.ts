import { test, expect } from "@playwright/test"

test.describe("Fidelidade Partidária nas Votações Nominais", () => {
  test("deve exibir o painel de fidelidade partidária com métricas e divergências", async ({ page }) => {
    const consoleErrors: string[] = []
    page.on("console", (msg) => {
      if (msg.type() === "error") {
        consoleErrors.push(msg.text())
      }
    })

    // Navega para o perfil de parlamentar com histórico de votações orientadas
    await page.goto("/politicos/alice-portugal")

    // Aguarda o carregamento do perfil
    await expect(page.locator("h1")).toContainText("Alice Portugal")

    // Localiza a seção de fidelidade partidária
    const sectionFidelidade = page.locator('[data-testid="section-fidelidade-partidaria"]')
    await expect(sectionFidelidade).toBeVisible({ timeout: 10000 })

    // Valida título, badge de bancada e métricas factuais
    await expect(sectionFidelidade).toContainText("Fidelidade Partidária nas Votações")
    await expect(sectionFidelidade).toContainText("Bancada PCdoB")
    await expect(sectionFidelidade).toContainText("97.2%")
    await expect(sectionFidelidade).toContainText("2.508")
    await expect(sectionFidelidade).toContainText("73")
    await expect(sectionFidelidade).toContainText("2.581")

    // Expande a lista de matérias divergentes
    const btnToggle = sectionFidelidade.locator('[data-testid="btn-toggle-divergencias"]')
    await expect(btnToggle).toBeVisible()
    await btnToggle.click()

    // Valida a exibição dos cards de divergência
    const cardsDivergencia = sectionFidelidade.locator('[data-testid="card-materia-divergente"]')
    await expect(cardsDivergencia.first()).toBeVisible({ timeout: 5000 })
    expect(await cardsDivergencia.count()).toBeGreaterThan(0)

    // Valida presença de badges de voto individual e orientação da liderança
    await expect(cardsDivergencia.first()).toContainText("Deputado:")
    await expect(cardsDivergencia.first()).toContainText("PCdoB:")

    // Testa filtro de busca por matéria
    const inputBusca = sectionFidelidade.locator('[data-testid="input-busca-divergencias"]')
    if (await inputBusca.isVisible()) {
      await inputBusca.fill("PEP")
      // Aguarda filtragem
      await expect(sectionFidelidade.locator('[data-testid="card-materia-divergente"]').first()).toContainText("PEP")
    }

    // Tira screenshot do painel para auditoria visual
    await sectionFidelidade.screenshot({ path: "test-results/fidelidade-partidaria-panel.png" })
    await page.screenshot({ path: "test-results/fidelidade-partidaria-fullpage.png", fullPage: true })

    // Valida ausência de erros graves de console
    const criticalErrors = consoleErrors.filter(
      (e) => !e.includes("favicon") && !e.includes("404")
    )
    expect(criticalErrors).toHaveLength(0)
  })
})
