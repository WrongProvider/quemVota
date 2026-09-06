import { test, expect } from "@playwright/test"

test.describe("Filtros de Votações e Seção de Projetos do Parlamentar", () => {
  test("deve exibir e filtrar votações e projetos no perfil do parlamentar", async ({ page }) => {
    // 1. Navega para o perfil de Nikolas Ferreira
    await page.goto("/politicos/nikolas-ferreira")
    await expect(page.locator("h1")).toContainText("Nikolas Ferreira")

    // 2. Valida barra de navegação sticky com a nova aba Projetos
    const tabProjetos = page.getByTestId("tab-projetos")
    await expect(tabProjetos).toBeVisible()

    // 3. Testa navegação até a seção Projetos
    await tabProjetos.click()
    const sectionProjetos = page.getByTestId("section-projetos")
    await expect(sectionProjetos).toBeVisible({ timeout: 10_000 })

    // Valida KPIs
    const kpiTotal = page.getByTestId("kpi-total-proposicoes")
    await expect(kpiTotal).toBeVisible()
    await expect(kpiTotal).toContainText("1.654")

    const kpiAutor = page.getByTestId("kpi-autor-principal")
    await expect(kpiAutor).toContainText("1.471")

    const kpiCoautor = page.getByTestId("kpi-coautor")
    await expect(kpiCoautor).toContainText("183")

    // Valida itens na lista de projetos
    const listaProjetos = page.getByTestId("projetos-list")
    await expect(listaProjetos).toBeVisible()

    // 4. Testa filtro de autoria por Coautor
    const btnCoautor = page.getByTestId("filter-autoria-coautor")
    await btnCoautor.click()

    // Valida que o total sob filtro atualizou para 183
    await expect(kpiTotal).toContainText("183")
    // Botão Limpar Filtros deve aparecer
    const btnLimparProjetos = page.getByTestId("btn-limpar-filtros-projetos")
    await expect(btnLimparProjetos).toBeVisible()

    // 5. Testa busca textual de projetos
    const inputBuscaProjetos = page.getByTestId("input-busca-projetos")
    await inputBuscaProjetos.fill("jornada")
    // Aguarda debounce
    await page.waitForTimeout(600)
    await expect(listaProjetos).toContainText("jornada de trabalho")

    // Limpa filtros de projetos
    await btnLimparProjetos.click()
    await expect(kpiTotal).toContainText("1.654")

    // 6. Testa alternância para a aba de Votações e seus Filtros
    const tabVotacoes = page.getByTestId("tab-votacoes")
    await tabVotacoes.click()

    // Valida alternância através do seletor de sub-abas do contêiner de Atividade Legislativa
    const subTabProjetos = page.getByTestId("tab-sub-projetos")
    await subTabProjetos.click()
    await expect(sectionProjetos).toBeVisible()

    const subTabVotacoes = page.getByTestId("tab-sub-votacoes")
    await subTabVotacoes.click()

    const sectionVotacoes = page.getByTestId("section-votacoes")
    await expect(sectionVotacoes).toBeVisible()

    const inputBuscaVotacoes = page.getByTestId("input-busca-votacoes")
    await expect(inputBuscaVotacoes).toBeVisible()

    // Digita busca textual em votações
    await inputBuscaVotacoes.fill("tributário")
    await page.waitForTimeout(600)

    const badgeVotacoes = page.getByTestId("votacoes-total-badge")
    await expect(badgeVotacoes).toContainText("16 registros")

    const listaVotacoes = page.getByTestId("votacoes-list")
    await expect(listaVotacoes).toContainText("benefícios tributários")

    // Testa filtro por voto
    const selectVoto = page.getByTestId("filter-voto-select")
    await selectVoto.selectOption("Sim")
    await page.waitForTimeout(600)

    // Botão Limpar Filtros em Votações
    const btnLimparVotacoes = page.getByTestId("btn-limpar-filtros-votacoes")
    await expect(btnLimparVotacoes).toBeVisible()
    await btnLimparVotacoes.click()

    // Após limpar, volta para o total de votações
    await expect(badgeVotacoes).toContainText("1.098 registros")
  })

  test("deve buscar tema do momento (escala 6x1), exibir link oficial da câmara e filtrar por tipo e tema em votações", async ({ page }) => {
    // 1. Navega para o perfil de Erika Hilton
    await page.goto("/politicos/erika-hilton")
    await expect(page.locator("h1")).toContainText("Erika Hilton")

    // 2. Acessa a seção de votações
    const tabVotacoes = page.getByTestId("tab-votacoes")
    await tabVotacoes.click()

    const sectionVotacoes = page.getByTestId("section-votacoes")
    await expect(sectionVotacoes).toBeVisible()

    // 3. Valida KPIs de votações
    const kpiTotal = page.getByTestId("kpi-total-votacoes")
    await expect(kpiTotal).toBeVisible()
    const kpiSim = page.getByTestId("kpi-votos-sim")
    await expect(kpiSim).toBeVisible()
    const kpiNao = page.getByTestId("kpi-votos-nao")
    await expect(kpiNao).toBeVisible()

    // 4. Clica no chip do tema do momento "Escala 6x1 (PEC 221)"
    const chip6x1 = page.locator("button", { hasText: "Escala 6x1 (PEC 221)" })
    await expect(chip6x1).toBeVisible()
    await chip6x1.click()
    await page.waitForTimeout(600)

    // Valida que o input de busca foi preenchido e lista filtrou para a PEC 221
    const inputBusca = page.getByTestId("input-busca-votacoes")
    await expect(inputBusca).toHaveValue("escala 6x1")

    const listaVotacoes = page.getByTestId("votacoes-list")
    await expect(listaVotacoes).toContainText("PEC 221/2019")

    // 5. Valida a presença do link oficial para a Câmara dos Deputados
    const linkCamara = listaVotacoes.locator("a[title*='Câmara']").first()
    await expect(linkCamara).toBeVisible()
    await expect(linkCamara).toHaveAttribute("target", "_blank")
    const href = await linkCamara.getAttribute("href")
    expect(href).toMatch(/^https:\/\/(www\.)?camara\.leg\.br/)

    // 6. Testa filtro por Tipo (PEC) e Tema (Trabalho)
    const selectTipo = page.getByTestId("select-tipo-votacao")
    await selectTipo.selectOption("PEC")
    await page.waitForTimeout(400)

    const selectTema = page.getByTestId("select-tema-votacao")
    await selectTema.selectOption("Trabalho")
    await page.waitForTimeout(400)

    await expect(listaVotacoes).toContainText("PEC 221/2019")

    // 7. Limpa filtros e verifica restauração
    const btnLimpar = page.getByTestId("btn-limpar-filtros-votacoes")
    await expect(btnLimpar).toBeVisible()
    await btnLimpar.click()
    await page.waitForTimeout(400)

    await expect(inputBusca).toHaveValue("")
    await expect(selectTipo).toHaveValue("")
    await expect(selectTema).toHaveValue("")
  })
})
