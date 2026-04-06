// ============================================
// EXEMPLOS DE USO DOS HOOKS DE RANKING
// ============================================

import {
  useRankingDespesas,
  useRankingLucroEmpresas,
  useRankingDiscursos,
  useRankingPerformance,
  useStatsGeral,
} from "../hooks/useRankings"

// ============================================
// EXEMPLO 1: Página de Ranking de Despesas
// ============================================

export function RankingDespesasPage() {
  const { data, isLoading, error } = useRankingDespesas({
    limit: 100,
    uf: "SP", // Opcional: filtrar por estado
    q: "",    // Opcional: buscar por nome
  })

  if (isLoading) return <div>Carregando ranking...</div>
  if (error) return <div>Erro ao carregar: {error.message}</div>

  return (
    <div>
      <h1>Ranking de Despesas</h1>
      <table>
        <thead>
          <tr>
            <th>Posição</th>
            <th>Nome</th>
            <th>Total Gasto</th>
          </tr>
        </thead>
        <tbody>
          {data?.map((politico, index) => (
            <tr key={politico.politico_id}>
              <td>{index + 1}</td>
              <td>{politico.nome}</td>
              <td>R$ {politico.total_gasto.toLocaleString("pt-BR")}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

// ============================================
// EXEMPLO 2: Ranking com Filtros Dinâmicos
// ============================================

export function RankingComFiltros() {
  const [uf, setUf] = useState<string>("")
  const [busca, setBusca] = useState<string>("")
  
  const { data, isLoading, isFetching } = useRankingDespesas({
    uf: uf || undefined,
    q: busca || undefined,
    limit: 50,
  })

  return (
    <div>
      <div className="filtros">
        <select value={uf} onChange={(e) => setUf(e.target.value)}>
          <option value="">Todos os Estados</option>
          <option value="SP">São Paulo</option>
          <option value="RJ">Rio de Janeiro</option>
          {/* ... outros estados ... */}
        </select>
        
        <input
          type="text"
          placeholder="Buscar por nome..."
          value={busca}
          onChange={(e) => setBusca(e.target.value)}
        />
      </div>

      {isFetching && <div>Atualizando...</div>}
      
      {/* Renderizar resultados */}
      <div>
        {data?.map((item) => (
          <div key={item.politico_id}>{item.nome}</div>
        ))}
      </div>
    </div>
  )
}

// ============================================
// EXEMPLO 3: Dashboard com Stats Gerais
// ============================================

export function DashboardHome() {
  const { data: stats, isLoading } = useStatsGeral()

  if (isLoading) return <div>Carregando estatísticas...</div>

  return (
    <div className="dashboard">
      <div className="stats-cards">
        <div className="card">
          <h3>Média Global de Performance</h3>
          <p className="score">{stats?.media_global.toFixed(2)}</p>
        </div>
        
        <div className="card">
          <h3>Total de Parlamentares</h3>
          <p>{stats?.total_parlamentares}</p>
        </div>
      </div>

      <div className="top-3">
        <h2>Top 3 Parlamentares</h2>
        {stats?.top_3.slice(0, 3).map((politico, index) => (
          <div key={politico.id} className="podium-item">
            <span className="posicao">{index + 1}º</span>
            <img src={politico.foto} alt={politico.nome} />
            <div>
              <h4>{politico.nome}</h4>
              <p>{politico.partido} - {politico.uf}</p>
              <p className="score">Score: {politico.score}</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

// ============================================
// EXEMPLO 4: Ranking de Performance Completo
// ============================================

export function RankingPerformancePage() {
  const { data, isLoading } = useRankingPerformance()

  if (isLoading) return <div>Carregando ranking de performance...</div>

  return (
    <div>
      <h1>Ranking de Performance dos Políticos</h1>
      <p>Score baseado em: Assiduidade (15%), Economia (40%) e Produção (45%)</p>
      
      <div className="ranking-list">
        {data?.map((politico, index) => (
          <div key={politico.id} className="ranking-card">
            <div className="posicao">#{index + 1}</div>
            <img src={politico.foto} alt={politico.nome} />
            
            <div className="info">
              <h3>{politico.nome}</h3>
              <p>{politico.partido} - {politico.uf}</p>
              
              <div className="score-principal">
                Score: {politico.score.toFixed(2)}
              </div>
              
              <div className="notas-detalhadas">
                <div>Assiduidade: {politico.notas.assiduidade.toFixed(2)}</div>
                <div>Produção: {politico.notas.producao.toFixed(2)}</div>
                <div>Economia: {politico.notas.economia.toFixed(2)}</div>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

// ============================================
// EXEMPLO 5: Ranking de Empresas
// ============================================

export function RankingEmpresasPage() {
  const { data, isLoading } = useRankingLucroEmpresas({ limit: 20 })

  if (isLoading) return <div>Carregando...</div>

  return (
    <div>
      <h1>Empresas que Mais Receberam Recursos</h1>
      <table>
        <thead>
          <tr>
            <th>Posição</th>
            <th>Empresa</th>
            <th>CNPJ</th>
            <th>Total Recebido</th>
          </tr>
        </thead>
        <tbody>
          {data?.map((empresa, index) => (
            <tr key={empresa.cnpj}>
              <td>{index + 1}</td>
              <td>{empresa.nome_fornecedor}</td>
              <td>{empresa.cnpj}</td>
              <td>R$ {empresa.total_recebido.toLocaleString("pt-BR")}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

// ============================================
// EXEMPLO 6: Ranking de Discursos com Temas
// ============================================

export function RankingDiscursosPage() {
  const { data, isLoading } = useRankingDiscursos({ limit: 50 })

  if (isLoading) return <div>Carregando...</div>

  return (
    <div>
      <h1>Políticos que Mais Discursam</h1>
      
      {data?.map((politico, index) => (
        <div key={politico.politico_id} className="discurso-card">
          <div className="header">
            <span className="posicao">#{index + 1}</span>
            <h3>{politico.nome_politico}</h3>
            <span>{politico.sigla_partido} - {politico.sigla_uf}</span>
          </div>
          
          <div className="total-discursos">
            {politico.total_discursos} discursos
          </div>
          
          <div className="temas">
            <h4>Temas Mais Discutidos:</h4>
            <div className="tags">
              {politico.temas_mais_discutidos.slice(0, 10).map((tema) => (
                <span key={tema.keyword} className="tag">
                  {tema.keyword} ({tema.frequencia})
                </span>
              ))}
            </div>
          </div>
        </div>
      ))}
    </div>
  )
}

// ============================================
// EXEMPLO 7: Paginação
// ============================================

export function RankingComPaginacao() {
  const [pagina, setPagina] = useState(0)
  const ITEMS_POR_PAGINA = 20

  const { data, isLoading, isFetching } = useRankingDespesas({
    limit: ITEMS_POR_PAGINA,
    offset: pagina * ITEMS_POR_PAGINA,
  })

  return (
    <div>
      <div className="resultados">
        {data?.map((item) => (
          <div key={item.politico_id}>{item.nome}</div>
        ))}
      </div>

      {isFetching && <div>Carregando...</div>}

      <div className="paginacao">
        <button
          onClick={() => setPagina((p) => Math.max(0, p - 1))}
          disabled={pagina === 0 || isFetching}
        >
          Anterior
        </button>
        
        <span>Página {pagina + 1}</span>
        
        <button
          onClick={() => setPagina((p) => p + 1)}
          disabled={!data || data.length < ITEMS_POR_PAGINA || isFetching}
        >
          Próxima
        </button>
      </div>
    </div>
  )
}

// ============================================
// EXEMPLO 8: Atualização Manual (Forçar Refetch)
// ============================================

export function RankingComRefresh() {
  const { data, isLoading, refetch, isFetching } = useRankingPerformance()

  return (
    <div>
      <button 
        onClick={() => refetch()} 
        disabled={isFetching}
      >
        {isFetching ? "Atualizando..." : "Atualizar Ranking"}
      </button>

      {/* Renderizar dados */}
    </div>
  )
}
