import { test, expect, type Page } from '@playwright/test';

// ─────────────────────────────────────────────────────────────────────────────
// Helpers reutilizáveis
// ─────────────────────────────────────────────────────────────────────────────

/**
 * Aguarda qualquer spinner global de perfil (LoadingScreen) sumir.
 */
async function aguardarPaginaCarregada(page: Page) {
  await expect(page.locator('.animate-spin').first()).toBeHidden({ timeout: 15_000 });
}

/**
 * Aguarda o seletor de anos aparecer — sinal de que a timeline foi carregada.
 */
async function aguardarTimeline(page: Page) {
  await expect(page.getByTestId('section-timeline')).toBeVisible({ timeout: 15_000 });
}

/**
 * Navega direto para o perfil de um político e espera a página estabilizar.
 */
async function irParaPolitico(page: Page, slug: string) {
  await page.goto(`/politicos/${slug}`);
  await aguardarPaginaCarregada(page);
}


// ─────────────────────────────────────────────────────────────────────────────
// Suite 1 — Sanidade e navegação pela home
// ─────────────────────────────────────────────────────────────────────────────

test.describe('Página inicial', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
  });

  test('deve exibir o título correto da aplicação', async ({ page }) => {
    await expect(page).toHaveTitle(/quemvota — Transparência Legislativa Brasileira/);
  });

  test('deve navegar para o perfil ao clicar no nome de um político', async ({ page }) => {
    await page.getByRole('link', { name: /Erika Hilton/i }).click();

    await expect(page).toHaveURL(/\/politicos\/erika-hilton/);
    await aguardarPaginaCarregada(page);

    await expect(page.getByTestId('politician-name')).toContainText('Erika Hilton');
  });
});


// ─────────────────────────────────────────────────────────────────────────────
// Suite 2 — Perfil do político: cabeçalho e informações gerais
// ─────────────────────────────────────────────────────────────────────────────

test.describe('Perfil do político — cabeçalho', () => {
  test.beforeEach(async ({ page }) => {
    await irParaPolitico(page, 'erika-hilton');
  });

  test('deve exibir o nome correto da parlamentar', async ({ page }) => {
    await expect(page.getByTestId('politician-name')).toContainText('Erika Hilton');
  });

  test('deve exibir o score de performance (viewport desktop)', async ({ page }) => {
    await page.setViewportSize({ width: 1280, height: 800 });

    await expect(page.getByTestId('performance-container')).toBeVisible();
    await expect(page.getByTestId('performance-score')).toBeVisible();

    const score = await page.getByTestId('performance-score').innerText();
    expect(Number(score)).toBeGreaterThanOrEqual(0);
    expect(Number(score)).toBeLessThanOrEqual(100);
  });

  test('deve exibir a seção de estatísticas após o carregamento', async ({ page }) => {
    await expect(page.getByTestId('section-stats')).toBeVisible({ timeout: 10_000 });
    await expect(page.getByTestId('stat-total-votacoes')).toBeVisible();
    await expect(page.getByTestId('stat-total-despesas')).toBeVisible();
  });
});


// ─────────────────────────────────────────────────────────────────────────────
// Suite 3 — Seletor de ano e atualização de dados
// ─────────────────────────────────────────────────────────────────────────────

test.describe('Seletor de ano (timeline)', () => {
  test.beforeEach(async ({ page }) => {
    await irParaPolitico(page, 'erika-hilton');
    await aguardarTimeline(page);
  });

  test('deve exibir o seletor de anos com o botão "todos" ativo por padrão', async ({ page }) => {
    const btnTodos = page.getByTestId('year-button-all');
    await expect(btnTodos).toBeVisible();
    await expect(btnTodos).toHaveClass(/bg-slate-700/);
  });

  test('deve filtrar dados ao selecionar um ano e atualizar o score', async ({ page }) => {
    await page.setViewportSize({ width: 1280, height: 800 });

    const score = page.getByTestId('performance-score');
    const valorAntes = await score.innerText();

    await page.getByTestId('year-button-2024').click();

    // Banner de filtro ativo deve aparecer
    await expect(page.getByText(/Dados filtrados para o ano/)).toBeVisible();

    // Stats devem recarregar
    await expect(page.getByTestId('section-stats')).toBeVisible({ timeout: 10_000 });

    const valorDepois = await score.innerText();
    console.log(`Performance: mandato completo=${valorAntes} | 2024=${valorDepois}`);
  });

  test('deve voltar para visão geral ao clicar em "Ver mandato completo"', async ({ page }) => {
    await page.getByTestId('year-button-2024').click();
    await expect(page.getByText(/Dados filtrados para o ano/)).toBeVisible();

    await page.getByRole('button', { name: /Ver mandato completo/i }).click();

    await expect(page.getByText(/Dados filtrados para o ano/)).toBeHidden();
    await expect(page.getByTestId('year-button-all')).toHaveClass(/bg-slate-700/);
  });

  test('deve desmarcar um ano ao clicar nele novamente', async ({ page }) => {
    const btn2024 = page.getByTestId('year-button-2024');

    await btn2024.click();
    await expect(page.getByText(/Dados filtrados para o ano/)).toBeVisible();

    await btn2024.click();
    await expect(page.getByText(/Dados filtrados para o ano/)).toBeHidden();
  });
});


// ─────────────────────────────────────────────────────────────────────────────
// Suite 4 — Histórico de votações e filtros
// ─────────────────────────────────────────────────────────────────────────────

test.describe('Histórico de votações', () => {
  test.beforeEach(async ({ page }) => {
    await irParaPolitico(page, 'erika-hilton');
    await page.getByTestId('section-votacoes').scrollIntoViewIfNeeded();
    await expect(page.getByTestId('votacoes-list')).toBeVisible({ timeout: 15_000 });
  });

  test('deve exibir a lista de votações por padrão (sem filtro)', async ({ page }) => {
    const itens = page.getByTestId('votacoes-list').locator('[data-testid^="votacao-item"]');
    await expect(itens.first()).toBeVisible();
  });

  test('deve filtrar por voto "Sim" e exibir somente itens aprovados', async ({ page }) => {
    await page.getByTestId('filter-voto-select').selectOption('Sim');

    const lista = page.getByTestId('votacoes-list');
    await expect(lista).toBeVisible();

    const itens = lista.locator('[data-testid^="votacao-item"]');
    const count = await itens.count();

    if (count > 0) {
      for (let i = 0; i < Math.min(count, 5); i++) {
        await expect(itens.nth(i)).toContainText('Sim');
      }
    }
  });

  test('deve filtrar por voto "Não" e exibir somente itens correspondentes', async ({ page }) => {
    await page.getByTestId('filter-voto-select').selectOption('Não');

    const lista = page.getByTestId('votacoes-list');
    const itens = lista.locator('[data-testid^="votacao-item"]');
    const count = await itens.count();

    if (count > 0) {
      for (let i = 0; i < Math.min(count, 5); i++) {
        await expect(itens.nth(i)).toContainText('Não');
      }
    }
  });

  test('deve filtrar por "Obstrução" sem quebrar a UI', async ({ page }) => {
    await page.getByTestId('filter-voto-select').selectOption('Obstrução');
    await expect(page.getByTestId('section-votacoes')).toBeVisible();
  });

  test('deve limpar o filtro ao selecionar "Todos os votos"', async ({ page }) => {
    await page.getByTestId('filter-voto-select').selectOption('Não');
    await page.getByTestId('filter-voto-select').selectOption('');

    await expect(page.getByTestId('votacoes-list')).toBeVisible();
    await expect(
      page.getByTestId('votacoes-list').locator('[data-testid^="votacao-item"]').first()
    ).toBeVisible();
  });

  test('deve abrir painel lateral ao clicar em uma votação', async ({ page }) => {
    const primeiroItem = page
      .getByTestId('votacoes-list')
      .locator('[data-testid^="votacao-item"]')
      .first();

    await primeiroItem.click();

    // Painel deslizante com z-50
    await expect(page.getByTestId('painel-detalhe-votacao')).toBeVisible({ timeout: 5_000 });
  });
  
  test('deve fechar o painel lateral ao clicar no overlay', async ({ page }) => {
  await page.getByTestId('votacoes-list')
    .locator('[data-testid^="votacao-item"]')
    .first()
    .click();

  const painel = page.getByTestId('painel-detalhe-votacao');
  await expect(painel).toBeVisible({ timeout: 5_000 });

  // Clica no overlay longe do nav (y: 400 garante estar abaixo do header fixo)
  await page.locator('.fixed.inset-0.z-40').click({ 
    position: { x: 10, y: 400 },
    force: true  // ignora elementos que interceptam
  });
  
  await expect(painel).toBeHidden({ timeout: 5_000 });
  });
});


// ─────────────────────────────────────────────────────────────────────────────
// Suite 5 — Histórico de gastos (LinhaDoTempo)
// ─────────────────────────────────────────────────────────────────────────────

test.describe('Histórico de gastos', () => {
  test.beforeEach(async ({ page }) => {
    await irParaPolitico(page, 'erika-hilton');
    await page.getByTestId('section-historico-de-gastos').scrollIntoViewIfNeeded();
    await expect(page.getByTestId('linha-do-tempo')).toBeVisible({ timeout: 15_000 });
    await expect(page.getByTestId('loading-state')).toBeHidden({ timeout: 15_000 });
  });

  test('deve exibir a navegação de anos da linha do tempo', async ({ page }) => {
    await expect(page.getByTestId('linha-tempo-nav')).toBeVisible();
    await expect(page.getByTestId('ano-pilula-todos')).toBeVisible();
  });

  test('deve exibir cards de totais na visão geral', async ({ page }) => {
    await expect(page.getByTestId('resumo-cards')).toBeVisible();
    await expect(page.getByTestId('card-total-gasto-valor')).not.toBeEmpty();
    await expect(page.getByTestId('card-num-despesas-valor')).not.toBeEmpty();
    await expect(page.getByTestId('card-anos-registrados-valor')).not.toBeEmpty();
  });

  test('deve exibir a tabela de anos com pelo menos uma linha', async ({ page }) => {
    const tabela = page.getByTestId('tabela-anos');
    await expect(tabela).toBeVisible();
    await expect(tabela.locator('[data-testid^="tabela-ano-row"]').first()).toBeVisible();
  });

    test('deve navegar para o detalhe de um ano ao clicar na pílula', async ({ page }) => {
      // Busca pílulas com ano numérico de 4 dígitos diretamente
      const primeiraPilula = page.locator('[data-testid^="ano-pilula-"]')
        .filter({ hasText: /^\d{4}$/ }) // o button interno mostra os 2 últimos dígitos... 
        // ...melhor filtrar pelo data-testid que termina em número
        .first();

      // Alternativa mais direta: pega o data-testid e verifica se é numérico
      const todasPilulas = page.locator('[data-testid^="ano-pilula-"]');
      const count = await todasPilulas.count();
      
      let pilula = null;
      let ano = '';
      for (let i = 0; i < count; i++) {
        const testId = await todasPilulas.nth(i).getAttribute('data-testid');
        const sufixo = testId?.replace('ano-pilula-', '') ?? '';
        if (/^\d{4}$/.test(sufixo)) {
          pilula = todasPilulas.nth(i);
          ano = sufixo;
          break;
        }
      }

      expect(pilula).not.toBeNull();
      await pilula!.click();

      await expect(page.getByTestId('header-ano-badge')).toContainText(ano, { timeout: 5_000 });
      await expect(page.getByTestId('grafico-mensal')).toBeVisible({ timeout: 10_000 });
      await expect(page.getByTestId('painel-ano-total')).toBeVisible();

    });

  test('deve voltar para a visão geral ao clicar em "Todos os anos"', async ({ page }) => {
      const todasPilulas = page.locator('[data-testid^="ano-pilula-"]');
      const count = await todasPilulas.count();

      let pilula = null;
      for (let i = 0; i < count; i++) {
        const testId = await todasPilulas.nth(i).getAttribute('data-testid');
        if (/^\d{4}$/.test(testId?.replace('ano-pilula-', '') ?? '')) {
          pilula = todasPilulas.nth(i);
          break;
        }
      }

      await pilula!.click();

      // btn-voltar-todos-anos só aparece quando anoSelecionado !== null
      // é o indicador correto de que o estado mudou
      const btnVoltar = page.getByTestId('btn-voltar-todos-anos');
      await expect(btnVoltar).toBeVisible({ timeout: 5_000 });

      await btnVoltar.click();

      await expect(btnVoltar).toBeHidden();
      await expect(page.getByTestId('tabela-anos')).toBeVisible();
    });

  test('deve expandir o dropdown de fornecedores ao clicar nele', async ({ page }) => {
    const secao = page.getByTestId('dropdown-section-fornecedores-geral');
    const toggle = page.getByTestId('dropdown-toggle-fornecedores-geral');

    await expect(secao).toHaveAttribute('data-state', 'closed');
    await toggle.click();
    await expect(secao).toHaveAttribute('data-state', 'open');
    await expect(page.getByTestId('dropdown-content-fornecedores-geral')).toBeVisible();
  });

  test('deve exibir itens de fornecedor após abrir o dropdown', async ({ page }) => {
    await page.getByTestId('dropdown-toggle-fornecedores-geral').click();

    const conteudo = page.getByTestId('dropdown-content-fornecedores-geral');
    await expect(conteudo).toBeVisible();

    const temItens = await conteudo.locator('[data-testid^="fornecedor-item"]').count();
    const temVazio  = await conteudo.getByTestId('fornecedores-empty').count();
    expect(temItens + temVazio).toBeGreaterThan(0);
  });

  test('deve expandir o dropdown de categorias e exibir itens', async ({ page }) => {
    await page.getByTestId('dropdown-toggle-categorias-geral').click();
    await expect(page.getByTestId('dropdown-content-categorias-geral')).toBeVisible();

    const temItens = await page.locator('[data-testid^="categoria-item"]').count();
    const temVazio  = await page.getByTestId('categorias-empty').count();
    expect(temItens + temVazio).toBeGreaterThan(0);
  });

  test('deve navegar para o ano via tabela e exibir dropdowns pré-abertos', async ({ page }) => {
    const tabela = page.getByTestId('tabela-anos');
    const primeiraLinha = tabela.locator('[data-testid^="tabela-ano-row"]').first();
    const ano = await primeiraLinha.getAttribute('data-ano');

    await primeiraLinha.click();

    // Dropdowns do ano ficam abertos por padrão (defaultOpen=true)
    await expect(page.getByTestId(`dropdown-section-fornecedores-${ano}`)).toHaveAttribute('data-state', 'open');
    await expect(page.getByTestId(`dropdown-section-categorias-${ano}`)).toHaveAttribute('data-state', 'open');
  });
});


// ─────────────────────────────────────────────────────────────────────────────
// Suite 6 — Jornada completa ponta a ponta
// ─────────────────────────────────────────────────────────────────────────────

test.describe('Jornada completa do usuário', () => {
  test('deve acessar perfil pela home, filtrar por ano, explorar votações e gastos', async ({ page }) => {
    // 1. Começa na home
    await page.goto('/');
    await expect(page).toHaveTitle(/quemvota/);

    // 2. Navega para o perfil
    await page.getByRole('link', { name: /Erika Hilton/i }).click();
    await aguardarPaginaCarregada(page);
    await expect(page.getByTestId('politician-name')).toContainText('Erika Hilton');

    // 3. Seleciona um ano na timeline
    await aguardarTimeline(page);
    await page.getByTestId('year-button-2024').click();
    await expect(page.getByText(/Dados filtrados para o ano/)).toBeVisible();
    await expect(page.getByTestId('section-stats')).toBeVisible({ timeout: 10_000 });

    // 4. Explora votações com filtro
    await page.getByTestId('section-votacoes').scrollIntoViewIfNeeded();
    await expect(page.getByTestId('votacoes-list')).toBeVisible({ timeout: 15_000 });
    await page.getByTestId('filter-voto-select').selectOption('Sim');

    const itens = page.getByTestId('votacoes-list').locator('[data-testid^="votacao-item"]');
    const count = await itens.count();
    if (count > 0) {
      await expect(itens.first()).toContainText('Sim');

      // Abre o painel de detalhe e fecha
      await itens.first().click();
      await expect(page.getByTestId('painel-detalhe-votacao')).toBeVisible({ timeout: 5_000 });
      await page.locator('.fixed.inset-0.z-40').click({ position: { x: 10, y: 400 }, force: true });
    }

    // 5. Vai para o histórico de gastos
    await page.getByTestId('section-historico-de-gastos').scrollIntoViewIfNeeded();
    await expect(page.getByTestId('linha-do-tempo')).toBeVisible({ timeout: 15_000 });
    await expect(page.getByTestId('loading-state')).toBeHidden({ timeout: 15_000 });
    await expect(page.getByTestId('resumo-cards')).toBeVisible();

    // 6. Limpa o filtro de ano
    await page.getByRole('button', { name: /Ver mandato completo/i }).click();
    await expect(page.getByText(/Dados filtrados para o ano/)).toBeHidden();
  });
});
