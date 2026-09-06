import { test, expect } from "@playwright/test"

test.describe("Rede de Coautoria e Parcerias Legislativas", () => {
  test("deve exibir o painel de coautoria com KPIs, parceiros e amostra de proposições", async ({ page }) => {
    const consoleErrors: string[] = []
    page.on("console", (msg) => {
      if (msg.type() === "error") {
        consoleErrors.push(msg.text())
      }
    })

    // Navega para o perfil do parlamentar com histórico de coautoria
    await page.goto("/politicos/alice-portugal")

    // Aguarda o carregamento do perfil
    await expect(page.locator("h1")).toContainText("Alice Portugal")

    // Ativa a aba de coautoria se o painel estiver em abas
    const tabSubCoautoria = page.locator('[data-testid="tab-sub-coautoria"]')
    if (await tabSubCoautoria.isVisible()) {
      await tabSubCoautoria.click()
    }

    // Localiza a seção de rede de coautoria
    const sectionCoautoria = page.locator('[data-testid="section-rede-coautoria"]')
    await expect(sectionCoautoria).toBeVisible({ timeout: 10000 })

    // Valida título da seção e KPIs
    await expect(sectionCoautoria).toContainText("Rede de Coautoria e Parcerias Legislativas")
    await expect(sectionCoautoria).toContainText("Coautoria Multipartidária")
    await expect(sectionCoautoria).toContainText("Parceiros Distintos")
    await expect(sectionCoautoria).toContainText("Proposições em Parceria")

    // Valida presença dos cards de parceiros
    const cardsParceiro = sectionCoautoria.locator('[data-testid="card-parceiro-coautoria"]')
    await expect(cardsParceiro.first()).toBeVisible({ timeout: 5000 })
    expect(await cardsParceiro.count()).toBeGreaterThan(0)

    // Valida dados detalhados no primeiro card de parceiro
    const primeiroCard = cardsParceiro.first()
    await expect(primeiroCard).toContainText("projetos juntos")
    await expect(primeiroCard).toContainText("Autor Principal")
    await expect(primeiroCard).toContainText("Coautor")

    // Expande a amostra de proposições do primeiro parceiro
    const btnToggle = primeiroCard.locator('button[data-testid^="btn-toggle-proposicoes-"]')
    if (await btnToggle.isVisible()) {
      await btnToggle.click()
      const itensProposicao = primeiroCard.locator('[data-testid="item-proposicao-parceria"]')
      await expect(itensProposicao.first()).toBeVisible({ timeout: 5000 })
      expect(await itensProposicao.count()).toBeGreaterThan(0)
    }

    // Testa filtro de busca por parceiro
    const inputBusca = sectionCoautoria.locator('[data-testid="input-busca-parceiros"]')
    if (await inputBusca.isVisible()) {
      await inputBusca.fill("Daniel")
      await expect(cardsParceiro.first()).toContainText("Daniel")
    }

    // Captura screenshot do painel para evidência visual
    await sectionCoautoria.screenshot({ path: "test-results/rede-coautoria-panel.png" })
    await page.screenshot({ path: "test-results/rede-coautoria-fullpage.png", fullPage: true })

    // Valida ausência de erros graves de console
    const criticalErrors = consoleErrors.filter(
      (e) => !e.includes("favicon") && !e.includes("404")
    )
    expect(criticalErrors).toHaveLength(0)
  })
})
