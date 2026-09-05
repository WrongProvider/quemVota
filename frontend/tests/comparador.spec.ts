import { test, expect } from "@playwright/test"

test.describe("Comparador Direto de Parlamentares", () => {
  test("deve acessar a página inicial do comparador (/comparar), selecionar dois parlamentares e comparar", async ({
    page,
  }) => {
    const consoleErrors: string[] = []
    page.on("console", (msg) => {
      if (msg.type() === "error") {
        consoleErrors.push(msg.text())
      }
    })

    // 1. Acessa a rota /comparar
    await page.goto("/comparar")

    // Valida título e elementos do landing
    await expect(page.locator("h1")).toContainText("Comparador de Parlamentares")
    await expect(page.getByTestId("seletor-duplo-comparacao")).toBeVisible({ timeout: 10000 })

    // Valida presença dos dois slots de seleção
    const slot1 = page.getByTestId("slot-politico-1")
    const slot2 = page.getByTestId("slot-politico-2")
    await expect(slot1).toBeVisible()
    await expect(slot2).toBeVisible()

    // Botão de comparação deve estar inicialmente desabilitado
    const btnComparar = page.getByTestId("btn-executar-comparacao")
    await expect(btnComparar).toBeDisabled()

    // 2. Busca e seleciona o 1º parlamentar
    const input1 = page.getByTestId("input-busca-politico-1")
    await input1.fill("Alice Portugal")
    // Aguarda dropdown de resultados e clica
    const opcao1 = slot1.locator("button", { hasText: "Alice Portugal" }).first()
    await expect(opcao1).toBeVisible({ timeout: 10000 })
    await opcao1.click()

    // Valida que o parlamentar 1 foi selecionado
    await expect(slot1).toContainText("Alice Portugal")

    // 3. Busca e seleciona o 2º parlamentar
    const input2 = page.getByTestId("input-busca-politico-2")
    await input2.fill("Arthur Lira")
    const opcao2 = slot2.locator("button", { hasText: "Arthur Lira" }).first()
    await expect(opcao2).toBeVisible({ timeout: 10000 })
    await opcao2.click()

    // Valida que o parlamentar 2 foi selecionado
    await expect(slot2).toContainText("Arthur Lira")

    // 4. Botão de comparar agora está habilitado
    await expect(btnComparar).toBeEnabled()

    // Tira screenshot do seletor com ambos selecionados
    await page.screenshot({ path: "test-results/comparador-landing-selected.png" })

    // 5. Executa a comparação
    await btnComparar.click()

    // Valida redirecionamento para a rota com slugs
    await expect(page).toHaveURL(/.*\/comparar\/alice-portugal\/arthur-lira/)
  })

  test("deve renderizar a página de confronto (/comparar/:slug1/:slug2) com métricas de alinhamento e votos", async ({
    page,
  }) => {
    const consoleErrors: string[] = []
    page.on("console", (msg) => {
      if (msg.type() === "error") {
        consoleErrors.push(msg.text())
      }
    })

    // Acessa diretamente a comparação
    await page.goto("/comparar/alice-portugal/arthur-lira")

    // Valida título da página com os dois parlamentares
    await expect(page.locator("h1")).toContainText("Alice")
    await expect(page.locator("h1")).toContainText("Arthur")

    // Valida breadcrumb com link para o comparador
    await expect(page.getByRole("link", { name: "Comparador", exact: true })).toBeVisible({ timeout: 10000 })

    // Valida métricas do confronto (alinhamento em votações)
    await expect(page.locator("text=Alinhamento em Votações")).toBeVisible({ timeout: 15000 })
    await expect(page.locator("text=Taxa de Alinhamento")).toBeVisible()
    await expect(page.locator("text=Votações em Comum")).toBeVisible()

    // Valida presença do botão de inverter lados
    const btnInverter = page.getByTestId("btn-inverter-lados")
    await expect(btnInverter).toBeVisible()

    // Captura screenshot da página de confronto
    await page.screenshot({ path: "test-results/comparador-confronto-fullpage.png", fullPage: true })

    // Valida ausência de erros graves de console
    const criticalErrors = consoleErrors.filter(
      (e) => !e.includes("favicon") && !e.includes("404")
    )
    expect(criticalErrors).toHaveLength(0)
  })

  test("deve navegar para a comparação a partir do atalho no Radar de Afinidades", async ({
    page,
  }) => {
    // Navega para o perfil com radar de afinidades
    await page.goto("/politicos/alice-portugal")

    // Aguarda carregamento inicial do perfil
    await expect(page.locator("h1")).toContainText("Alice Portugal")

    // Aguarda o radar de afinidades (consulta estatística pesada no backend)
    const sectionRadar = page.locator('[data-testid="section-radar-afinidades"]')
    await expect(sectionRadar).toBeVisible({ timeout: 45000 })

    // Localiza o link 'Comparar' dentro de um card do radar
    const linkComparar = sectionRadar.getByRole("link", { name: /Comparar/i }).first()
    await expect(linkComparar).toBeVisible({ timeout: 10000 })

    // Clica no link e valida que foi para a rota de comparação
    await linkComparar.click()
    await expect(page).toHaveURL(/.*\/comparar\/.+/)
  })
})
