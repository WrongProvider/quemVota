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

    // Valida que a sub-aba de discursos dentro de Atividade Legislativa está selecionada
    const tabSubDiscursos = page.locator('[data-testid="tab-sub-discursos"]')
    await expect(tabSubDiscursos).toBeVisible({ timeout: 10000 })
    await expect(tabSubDiscursos).toHaveAttribute("aria-selected", "true")

    // Valida a seção de discursos
    const sectionDiscursos = page.locator('[data-testid="section-discursos"]')
    await expect(sectionDiscursos).toBeVisible({ timeout: 10000 })
    await expect(sectionDiscursos).toContainText("Discursos & Atuação")

    // Testa alternância de sub-abas dentro de Atividade Legislativa
    const tabSubVotacoes = page.locator('[data-testid="tab-sub-votacoes"]')
    await tabSubVotacoes.click()
    await expect(page.locator('[data-testid="section-votacoes"]')).toBeVisible()
    await expect(sectionDiscursos).toBeHidden()

    // Retorna para a sub-aba de discursos
    await tabSubDiscursos.click()
    await expect(sectionDiscursos).toBeVisible()
    await expect(page.locator('[data-testid="section-votacoes"]')).toBeHidden()

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

  test("deve permitir digitação fluida no campo de busca sem perda de foco e exibir empty state sem sumir a tela", async ({
    page,
  }) => {
    await page.setViewportSize({ width: 1280, height: 800 })

    await page.goto("/politicos/tabata-amaral")
    await expect(page.locator("h1")).toContainText("Tabata Amaral", { timeout: 15000 })

    const tabDiscursos = page.locator('[data-testid="tab-discursos"]')
    await expect(tabDiscursos).toBeVisible({ timeout: 10000 })
    await tabDiscursos.click()

    const sectionDiscursos = page.locator('[data-testid="section-discursos"]')
    await expect(sectionDiscursos).toBeVisible({ timeout: 10000 })

    const searchInput = page.locator('[data-testid="discursos-search"]')
    await expect(searchInput).toBeVisible()

    // Clica no input e digita caractere por caractere (simulando digitação real com delay)
    await searchInput.click()
    await searchInput.pressSequentially("educação", { delay: 60 })

    // Valida que o input manteve o foco e o valor completo foi digitado sem interrupção
    await expect(searchInput).toBeFocused()
    await expect(searchInput).toHaveValue("educação")

    // Aguarda debounce e carregamento
    await page.waitForTimeout(600)
    await expect(sectionDiscursos).toBeVisible()

    // Testa digitação de termo inexistente com mais de 3 caracteres
    await searchInput.fill("")
    await searchInput.pressSequentially("termoinexistente999", { delay: 50 })
    await expect(searchInput).toHaveValue("termoinexistente999")

    // Aguarda debounce e resposta vazia
    await page.waitForTimeout(600)

    // A tela/seção NUNCA pode sumir do DOM
    await expect(sectionDiscursos).toBeVisible()
    await expect(sectionDiscursos).toContainText('Nenhum pronunciamento encontrado para "termoinexistente999"')

    // Clica no botão 'Limpar busca'
    const btnLimpar = page.locator('[data-testid="limpar-busca-discursos"]')
    await expect(btnLimpar).toBeVisible()
    await btnLimpar.click()

    // Valida que a busca foi resetada e os discursos retornaram
    await expect(searchInput).toHaveValue("")
    await expect(sectionDiscursos).toBeVisible()
    const togglePrimeiro = page.locator('[data-testid^="discurso-toggle-"]').first()
    await expect(togglePrimeiro).toBeVisible({ timeout: 5000 })
  })
})

