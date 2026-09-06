import { test, expect } from "@playwright/test"
import * as path from "path"

const ARTIFACT_DIR = "/home/smok1ng_sn4ke/.gemini/antigravity/brain/8898d3a5-d1bc-47b3-903b-8eeaa4f0333f"

test.describe("Otimizações Mobile Anti-Scroll Fatigue (Galaxy S25)", () => {
  test("deve renderizar apenas 2 votações, filtros sanfona, 2 projetos e 2 conexões no mobile (360x780)", async ({ page }) => {
    await page.setViewportSize({ width: 360, height: 780 })

    await page.goto("/politicos/erika-hilton")
    await page.waitForLoadState("networkidle")

    // Ir para a seção de votações
    const tabVotacoes = page.getByTestId("tab-votacoes")
    await tabVotacoes.click()

    const listaVotacoes = page.getByTestId("votacoes-list")
    await expect(listaVotacoes).toBeVisible({ timeout: 10_000 })

    // Verificar se não há overflow horizontal indesejado
    const hasHorizontalOverflow = await page.evaluate(() => {
      return document.documentElement.scrollWidth > window.innerWidth || document.body.scrollWidth > window.innerWidth
    })
    expect(hasHorizontalOverflow).toBeFalsy()

    // 1. Votações em Plenário: apenas 2 cards por padrão no mobile
    const cardsVotacao = listaVotacoes.locator('[data-testid^="votacao-item-"]')
    await expect(cardsVotacao).toHaveCount(2)

    // O botão de toggle de filtros avançados deve estar visível no mobile
    const btnToggleFiltros = page.getByTestId("btn-toggle-filtros-avancados")
    await expect(btnToggleFiltros).toBeVisible()

    // Botão de paginação deve estar visível e funcional
    const btnProximaVotacao = page.getByTestId("btn-votacoes-proxima")
    await expect(btnProximaVotacao).toBeVisible()

    // Screenshot do mobile na aba Votações
    await page.screenshot({
      path: path.join(ARTIFACT_DIR, "mobile_s25_votacoes.png"),
      fullPage: false,
    })

    // 2. Aba Projetos e Proposições
    const subTabProjetos = page.getByTestId("tab-sub-projetos")
    await subTabProjetos.click()
    await page.waitForTimeout(600)

    const listaProjetos = page.getByTestId("projetos-list")
    await expect(listaProjetos).toBeVisible({ timeout: 10_000 })

    const cardsProjetos = listaProjetos.locator('[data-testid^="proposicao-card-"]')
    await expect(cardsProjetos).toHaveCount(2)

    const btnToggleFiltrosProjetos = page.getByTestId("btn-toggle-filtros-projetos")
    await expect(btnToggleFiltrosProjetos).toBeVisible()

    const btnProximaProjetos = page.getByTestId("btn-projetos-proxima")
    await expect(btnProximaProjetos).toBeVisible()

    // Screenshot do mobile na aba Projetos
    await page.screenshot({
      path: path.join(ARTIFACT_DIR, "mobile_s25_projetos.png"),
      fullPage: false,
    })

    // 3. Conexões e Alinhamentos Políticos: Radar de Afinidades (2 itens por coluna no mobile)
    const tabConexoes = page.getByTestId("tab-conexoes")
    await tabConexoes.click()
    await page.waitForTimeout(600)

    const subTabAfinidades = page.getByTestId("tab-sub-afinidades")
    await subTabAfinidades.click()

    const cardAlinhados = page.getByTestId("card-afinidade-item")
    await expect(cardAlinhados).toHaveCount(2)

    const cardDivergentes = page.getByTestId("card-divergencia-item")
    await expect(cardDivergentes).toHaveCount(2)

    const btnMaisAlinhados = page.getByTestId("btn-mostrar-mais-alinhados")
    await expect(btnMaisAlinhados).toBeVisible()
    await btnMaisAlinhados.click()
    await expect(cardAlinhados).toHaveCount(4)

    // 4. Mudar para Aba Rede de Coautoria
    const subTabCoautoria = page.getByTestId("tab-sub-coautoria")
    await subTabCoautoria.click()
    await page.waitForTimeout(600)

    const cardsParceiros = page.getByTestId("card-parceiro-coautoria")
    await expect(cardsParceiros).toHaveCount(2)

    // 5. Mudar para Aba Fidelidade Partidária
    const subTabFidelidade = page.getByTestId("tab-sub-fidelidade")
    await subTabFidelidade.click()
    await page.waitForTimeout(600)

    const btnVerDivergencias = page.getByTestId("btn-toggle-divergencias")
    if (await btnVerDivergencias.isVisible()) {
      await btnVerDivergencias.click()
      const cardsDivergencias = page.getByTestId("card-materia-divergente")
      await expect(cardsDivergencias).toHaveCount(2)
    }

    // Screenshot de conexões mobile
    await page.screenshot({
      path: path.join(ARTIFACT_DIR, "mobile_s25_conexoes.png"),
      fullPage: false,
    })
  })

  test("deve exibir mais dados em tela desktop (1280x800) com filtros abertos", async ({ page }) => {
    await page.setViewportSize({ width: 1280, height: 800 })

    await page.goto("/politicos/erika-hilton")
    await page.waitForLoadState("networkidle")

    const tabVotacoes = page.getByTestId("tab-votacoes")
    await tabVotacoes.click()

    const listaVotacoes = page.getByTestId("votacoes-list")
    await expect(listaVotacoes).toBeVisible({ timeout: 10_000 })

    // Votações no desktop exibe 10 cards por padrão
    const cardsVotacao = listaVotacoes.locator('[data-testid^="votacao-item-"]')
    await expect(cardsVotacao).toHaveCount(10)

    // Filtros no desktop estão sempre abertos
    const selectTipo = page.getByTestId("select-tipo-votacao")
    await expect(selectTipo).toBeVisible()

    // Screenshot do desktop Votações
    await page.screenshot({
      path: path.join(ARTIFACT_DIR, "desktop_1280_votacoes.png"),
      fullPage: false,
    })

    // Projetos no desktop exibe 10 cards por padrão
    const subTabProjetos = page.getByTestId("tab-sub-projetos")
    await subTabProjetos.click()
    await page.waitForTimeout(600)

    const listaProjetos = page.getByTestId("projetos-list")
    await expect(listaProjetos).toBeVisible({ timeout: 10_000 })

    const cardsProjetos = listaProjetos.locator('[data-testid^="proposicao-card-"]')
    await expect(cardsProjetos).toHaveCount(10)

    // Screenshot do desktop Projetos
    await page.screenshot({
      path: path.join(ARTIFACT_DIR, "desktop_1280_projetos.png"),
      fullPage: false,
    })

    // Radar de afinidades no desktop exibe até 10 itens
    const tabConexoes = page.getByTestId("tab-conexoes")
    await tabConexoes.click()
    await page.waitForTimeout(600)

    const subTabAfinidades = page.getByTestId("tab-sub-afinidades")
    await subTabAfinidades.click()

    const cardAlinhados = page.getByTestId("card-afinidade-item")
    await expect(cardAlinhados).toHaveCount(10)
  })
})
