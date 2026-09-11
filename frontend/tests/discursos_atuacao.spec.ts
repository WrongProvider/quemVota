import { test, expect } from "@playwright/test"

test.describe("Discursos & Atuação Legislativa (SPEC-007)", () => {
  test("deve exibir a aba e a seção de discursos em Desktop, permitindo busca e expansão", async ({
    page,
  }) => {
    // Configura viewport Desktop
    await page.setViewportSize({ width: 1280, height: 800 })

    const consoleErrors: string[] = []
    page.on("console", (msg) => {
      if (msg.type() === "error") {
        consoleErrors.push(msg.text())
      }
    })

    // Navega para o perfil de Tabata Amaral (deputado com discursos cadastrados)
    await page.goto("/politicos/tabata-amaral")

    // Aguarda carregar o perfil
    await expect(page.locator("h1")).toContainText("Tabata Amaral", { timeout: 15000 })

    // Valida presença da aba Discursos
    const tabDiscursos = page.locator('[data-testid="tab-discursos"]')
    await expect(tabDiscursos).toBeVisible({ timeout: 10000 })
    await expect(tabDiscursos).toContainText("Discursos")

    // Clica na aba para rolar até a seção
    await tabDiscursos.click()

    // Valida a seção de discursos
    const sectionDiscursos = page.locator('[data-testid="section-discursos"]')
    await expect(sectionDiscursos).toBeVisible({ timeout: 10000 })
    await expect(sectionDiscursos).toContainText("Discursos & Atuação")

    // Valida presença do campo de busca
    const searchInput = page.locator('[data-testid="discursos-search"]')
    await expect(searchInput).toBeVisible()

    // Testa busca de texto
    await searchInput.fill("feminicídio")
    await page.waitForTimeout(500)

    // Clica para expandir o primeiro discurso encontrado
    const togglePrimeiro = page.locator('[data-testid^="discurso-toggle-"]').first()
    await expect(togglePrimeiro).toBeVisible({ timeout: 5000 })
    await togglePrimeiro.click()

    // Valida que o painel expandido exibe correlações
    const expandido = page.locator('[data-testid^="discurso-expandido-"]').first()
    await expect(expandido).toBeVisible({ timeout: 5000 })

    // Valida que não houve overflow horizontal
    const hasHorizontalOverflow = await page.evaluate(() => {
      return document.body.scrollWidth > window.innerWidth
    })
    expect(hasHorizontalOverflow).toBe(false)

    // Valida que não houve erros graves de console
    const criticalErrors = consoleErrors.filter(
      (e) => !e.includes("favicon") && !e.includes("404") && !e.includes("[API][DEV]")
    )
    expect(criticalErrors).toHaveLength(0)
  })

  test("deve ser totalmente responsivo em Mobile (390x844) sem overflow horizontal", async ({
    page,
  }) => {
    // Viewport Mobile padrão
    await page.setViewportSize({ width: 390, height: 844 })

    await page.goto("/politicos/tabata-amaral")
    await expect(page.locator("h1")).toContainText("Tabata Amaral", { timeout: 15000 })

    // Aba de discursos deve estar visível e clicável no nav horizontal
    const tabDiscursos = page.locator('[data-testid="tab-discursos"]')
    await expect(tabDiscursos).toBeVisible()
    await tabDiscursos.click()

    const sectionDiscursos = page.locator('[data-testid="section-discursos"]')
    await expect(sectionDiscursos).toBeVisible({ timeout: 10000 })

    // Verifica ausência de overflow horizontal no mobile
    const hasHorizontalOverflow = await page.evaluate(() => {
      return document.body.scrollWidth > window.innerWidth
    })
    expect(hasHorizontalOverflow).toBe(false)
  })
})
