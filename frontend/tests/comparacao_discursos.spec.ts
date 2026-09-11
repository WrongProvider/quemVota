import { test, expect } from "@playwright/test"

test.describe("Comparação de Discursos entre Deputados", () => {
  test("deve exibir o bloco de confronto de discursos com abas divergentes e parecidos no desktop", async ({
    page,
  }) => {
    const consoleErrors: string[] = []
    page.on("console", (msg) => {
      if (msg.type() === "error") {
        consoleErrors.push(msg.text())
      }
    })

    // Navega para a comparação direta entre Tabata Amaral e Nikolas Ferreira
    await page.goto("/comparar/tabata-amaral/nikolas-ferreira")

    // Aguarda carregar o cabeçalho principal
    await expect(page.locator("h1")).toContainText("Tabata")
    await expect(page.locator("h1")).toContainText("Nikolas")

    // Verifica que o bloco de discursos está presente na página
    const blocoDiscursos = page.getByTestId("bloco-comparacao-discursos")
    await expect(blocoDiscursos).toBeVisible({ timeout: 15000 })

    // Valida o título do bloco
    await expect(blocoDiscursos).toContainText("Confronto de Discursos na Tribuna")

    // Valida botões do segmented control
    const tabDivergentes = page.getByTestId("tab-discursos-divergentes")
    const tabConvergentes = page.getByTestId("tab-discursos-convergentes")

    await expect(tabDivergentes).toBeVisible()
    await expect(tabConvergentes).toBeVisible()

    // Inicialmente a aba divergentes está ativa e possui cards
    const cardsDivergentes = blocoDiscursos.getByTestId("card-par-discurso")
    await expect(cardsDivergentes.first()).toBeVisible({ timeout: 5000 })
    const totalDiv = await cardsDivergentes.count()
    expect(totalDiv).toBeGreaterThan(0)

    // Clica na aba de discursos parecidos / convergentes
    await tabConvergentes.click()

    // Verifica cards na aba de convergentes
    const cardsConvergentes = blocoDiscursos.getByTestId("card-par-discurso")
    await expect(cardsConvergentes.first()).toBeVisible({ timeout: 5000 })
    const totalConv = await cardsConvergentes.count()
    expect(totalConv).toBeGreaterThan(0)

    // Valida que não há erros graves no console
    const errosRelevantes = consoleErrors.filter(
      (e) => !e.includes("favicon") && !e.includes("404")
    )
    expect(errosRelevantes).toHaveLength(0)
  })

  test("deve garantir layout responsivo sem overflow horizontal no mobile (390x844)", async ({
    page,
  }) => {
    // Define viewport mobile padrão iPhone 12/13/14
    await page.setViewportSize({ width: 390, height: 844 })

    await page.goto("/comparar/tabata-amaral/nikolas-ferreira")

    const blocoDiscursos = page.getByTestId("bloco-comparacao-discursos")
    await expect(blocoDiscursos).toBeVisible({ timeout: 15000 })

    // Verifica botões de toque >= 44px
    const tabDivergentes = page.getByTestId("tab-discursos-divergentes")
    const boxTab = await tabDivergentes.boundingBox()
    expect(boxTab).not.toBeNull()
    if (boxTab) {
      expect(boxTab.height).toBeGreaterThanOrEqual(44)
    }

    // Garante que não há overflow horizontal indesejado
    const hasHorizontalOverflow = await page.evaluate(() => {
      return document.documentElement.scrollWidth > window.innerWidth
    })
    expect(hasHorizontalOverflow).toBe(false)
  })
})
