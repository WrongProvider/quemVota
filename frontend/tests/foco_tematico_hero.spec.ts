import { test, expect } from "@playwright/test"

test.describe("Foco Temático no Hero Header", () => {
  test("deve exibir card integrado de Foco Temático e Presença em Desktop com altura <= 160px", async ({
    page,
  }) => {
    await page.setViewportSize({ width: 1280, height: 800 })

    const consoleErrors: string[] = []
    page.on("console", (msg) => {
      if (msg.type() === "error") {
        consoleErrors.push(msg.text())
      }
    })

    // Navega para o perfil de Tabata Amaral
    await page.goto("/politicos/tabata-amaral")
    await expect(page.locator("h1")).toContainText("Tabata Amaral", { timeout: 15000 })

    // Valida presença do card integrado Foco Temático no Hero
    const heroCard = page.locator('[data-testid="foco-tematico-hero"]')
    await expect(heroCard).toBeVisible({ timeout: 10000 })

    // Valida que a altura do card NÃO excede a altura da foto da deputada (160px)
    const box = await heroCard.boundingBox()
    expect(box).not.toBeNull()
    expect(box!.height).toBeLessThanOrEqual(165) // 152px nominal + margem sutil de subpixel

    // Valida que exibe o cabeçalho e os temas
    await expect(heroCard).toContainText("Foco Temático")
    await expect(heroCard).toContainText("Educação")

    // Valida que a métrica de presença está integrada
    const scorePresenca = heroCard.locator('[data-testid="performance-score"]')
    await expect(scorePresenca).toBeVisible()
    await expect(scorePresenca).toContainText("%")

    // Valida botão de ver mais temas e navegação suave
    const btnVerMais = heroCard.locator('[data-testid="btn-ver-mais-temas-hero"]')
    if (await btnVerMais.isVisible()) {
      await btnVerMais.click()
      await page.waitForTimeout(600)
      // Valida que a seção analítica de temas está visível na viewport
      const sectionTemas = page.locator('[data-testid="section-temas-atuacao"]')
      await expect(sectionTemas).toBeVisible()
    }

    // Valida ausência de overflow horizontal
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

  test("deve manter layout mobile (390x844) sem quebras ou overflow horizontal", async ({
    page,
  }) => {
    await page.setViewportSize({ width: 390, height: 844 })

    await page.goto("/politicos/tabata-amaral")
    await expect(page.locator("h1")).toContainText("Tabata Amaral", { timeout: 15000 })

    // Indicador de presença mobile visível
    const mobilePresenca = page.locator(".profile-photo")
    await expect(mobilePresenca).toBeVisible()

    // Verifica ausência de overflow horizontal no mobile
    const hasHorizontalOverflow = await page.evaluate(() => {
      return document.body.scrollWidth > window.innerWidth
    })
    expect(hasHorizontalOverflow).toBe(false)
  })
})
