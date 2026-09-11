import { test, expect } from "@playwright/test"

test.describe("Comparação de Discursos entre Deputados (Anti-Scroll Fatigue)", () => {
  test("deve exibir o bloco com categorias, cards compactos e expansão sob demanda no desktop", async ({
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

    // 1. Valida carrossel de categorias temáticas
    const carrosselCategorias = page.getByTestId("carrossel-categorias-discursos")
    await expect(carrosselCategorias).toBeVisible()
    const pílulaTodas = page.getByTestId("pill-categoria-todas")
    await expect(pílulaTodas).toBeVisible()

    // 2. Inicialmente os cards são compactos (accordion fechado por padrão - anti-fatigue)
    const primeiroCard = blocoDiscursos.getByTestId("card-par-discurso").first()
    await expect(primeiroCard).toBeVisible({ timeout: 5000 })

    // O link para a íntegra não deve estar visível antes da expansão
    const linkIntegraAntes = primeiroCard.getByText("Íntegra do discurso na Câmara")
    await expect(linkIntegraAntes).not.toBeVisible()

    // 3. Usuário clica para expandir e ler mais
    const btnExpandir = primeiroCard.getByTestId("btn-toggle-par-discurso")
    await btnExpandir.click()

    // Agora o conteúdo detalhado e o link para a Câmara devem estar visíveis
    const linkIntegraDepois = primeiroCard.getByText("Íntegra do discurso na Câmara").first()
    await expect(linkIntegraDepois).toBeVisible()
    await expect(primeiroCard).toContainText("Fundamentação factual:")

    // 4. Alterna para a aba de discursos parecidos / convergentes
    await tabConvergentes.click()

    const cardsConvergentes = blocoDiscursos.getByTestId("card-par-discurso")
    await expect(cardsConvergentes.first()).toBeVisible({ timeout: 5000 })
    const totalConv = await cardsConvergentes.count()
    expect(totalConv).toBeGreaterThan(0)

    // Se houver mais de 4 itens, o botão "Ver mais debates" deve existir
    const btnMostrarMais = page.getByTestId("btn-mostrar-mais-discursos")
    if (await btnMostrarMais.isVisible()) {
      await btnMostrarMais.click()
      // Mais cards devem ter sido carregados
      const novoTotal = await cardsConvergentes.count()
      expect(novoTotal).toBeGreaterThan(totalConv)
    }

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

    // Verifica que o carrossel de categorias é visível no mobile
    const carrosselCategorias = page.getByTestId("carrossel-categorias-discursos")
    await expect(carrosselCategorias).toBeVisible()

    // Garante que não há overflow horizontal indesejado
    const hasHorizontalOverflow = await page.evaluate(() => {
      return document.documentElement.scrollWidth > window.innerWidth
    })
    expect(hasHorizontalOverflow).toBe(false)
  })
})
