import { test, expect } from "@playwright/test"

test.describe("Temas de Atuação Parlamentar (SPEC-001)", () => {
  test("deve exibir o painel de temas na página do deputado e permitir interação", async ({ page }) => {
    const consoleErrors: string[] = []
    page.on("console", (msg) => {
      console.log(`[BROWSER ${msg.type().toUpperCase()}]`, msg.text())
      if (msg.type() === "error") {
        consoleErrors.push(msg.text())
      }
    })
    page.on("requestfailed", (req) => {
      console.log("[REQUEST FAILED]", req.method(), req.url(), req.failure()?.errorText)
    })
    page.on("response", (res) => {
      if (res.status() >= 400) {
        console.log(`[HTTP ${res.status()}]`, res.url())
      }
    })

    // Navega para o perfil do deputado com temas calculados
    await page.goto("http://localhost:4173/politicos/lucas-abrahao")

    // Aguarda o carregamento do perfil
    await expect(page.locator("h1")).toContainText("Lucas Abrahao")

    // Localiza a seção de temas
    const sectionTemas = page.locator('[data-testid="section-temas-atuacao"]')
    await expect(sectionTemas).toBeVisible({ timeout: 10000 })

    // Valida título e badge
    await expect(sectionTemas).toContainText("Foco Temático da Atuação")
    await expect(sectionTemas).toContainText("temas identificados")

    // Valida presença dos temas retornados pela API
    await expect(sectionTemas).toContainText("Educação")
    await expect(sectionTemas).toContainText("Economia")
    await expect(sectionTemas).toContainText("Meio Ambiente")

    // Valida tema em destaque inicial (Rank 1: Educação)
    await expect(sectionTemas).toContainText("#1 no ranking")
    await expect(sectionTemas).toContainText("13.4%")

    // Clica no chip do segundo tema para testar interatividade
    const chipEconomia = sectionTemas.getByRole("button", { name: /Economia/i })
    await chipEconomia.click()

    // Valida atualização do card de destaque
    await expect(sectionTemas).toContainText("#2 no ranking")
    await expect(sectionTemas).toContainText("13.3%")

    // Tira screenshot de página inteira para auditoria visual
    await page.screenshot({ path: "test-results/temas-atuacao-fullpage.png", fullPage: true })

    // Valida que não houve erros graves de console
    const criticalErrors = consoleErrors.filter(
      (e) => !e.includes("favicon") && !e.includes("404")
    )
    expect(criticalErrors).toHaveLength(0)
  })
})
