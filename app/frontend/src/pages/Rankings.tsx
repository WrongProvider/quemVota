import { useState } from "react"
import { Link } from "react-router-dom"
import { 
  TrendingUp, 
  TrendingDown, 
  DollarSign, 
  FileText, 
  Award,
  Building2,
  Filter,
  Search
} from "lucide-react"

// Hooks customizados
import {
  useRankingPerformance,
  useRankingDespesas,
  useRankingDiscursos,
  useRankingLucroEmpresas,
} from "../hooks/useRankings"

import Header from "../components/Header"
// Serviços
import {
  DespesaRankingService,
  EconomiaRankingService,
  FilterService,
  FormatService,
} from "../services/rankings.service"

export default function Rankings() {
  const [activeTab, setActiveTab] = useState<"performance" | "gastos" | "economia" | "empresas" | "discursos">("performance")
  const [searchTerm, setSearchTerm] = useState("")
  const [selectedUF, setSelectedUF] = useState("")

  return (
    <>
      <Header />
        <div className="max-w-7xl mx-auto p-8 font-sans">
          {/* HEADER */}
          <div className="mb-8">
            <h1 className="text-4xl font-bold mb-2 text-slate-800 flex items-center gap-3">
              <Award size={40} className="text-amber-500" />
              Rankings Parlamentares
            </h1>
            <p className="text-lg text-slate-500">
              Confira os parlamentares em destaque nas principais métricas de desempenho
            </p>
          </div>

          {/* TABS DE NAVEGAÇÃO */}
          <div className="flex gap-2 mb-8 border-b-2 border-slate-200 overflow-x-auto pb-2">
            <TabButton
              active={activeTab === "performance"}
              onClick={() => setActiveTab("performance")}
              icon={<TrendingUp size={20} />}
              label="Melhor Performance"
            />
            <TabButton
              active={activeTab === "gastos"}
              onClick={() => setActiveTab("gastos")}
              icon={<TrendingDown size={20} />}
              label="Maiores Gastos"
            />
            <TabButton
              active={activeTab === "economia"}
              onClick={() => setActiveTab("economia")}
              icon={<DollarSign size={20} />}
              label="Mais Econômicos"
            />
            <TabButton
              active={activeTab === "discursos"}
              onClick={() => setActiveTab("discursos")}
              icon={<FileText size={20} />}
              label="Mais Discursos"
            />
            <TabButton
              active={activeTab === "empresas"}
              onClick={() => setActiveTab("empresas")}
              icon={<Building2 size={20} />}
              label="Empresas Beneficiadas"
            />
          </div>

          {/* FILTROS (apenas para rankings de políticos) */}
          {activeTab !== "empresas" && (
            <div className="flex gap-4 mb-8 flex-wrap items-center">
              <div className="flex-1 min-w-[250px]">
                <div className="relative">
                  <Search 
                    size={20} 
                    className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" 
                  />
                  <input
                    type="text"
                    placeholder="Buscar parlamentar..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="w-full py-3 px-4 pl-11 border-2 border-slate-200 rounded-lg text-base focus:outline-none focus:border-blue-500 transition-colors"
                  />
                </div>
              </div>

              <div className="flex items-center gap-2">
                <Filter size={20} className="text-slate-500" />
                <select
                  value={selectedUF}
                  onChange={(e) => setSelectedUF(e.target.value)}
                  className="py-3 px-4 border-2 border-slate-200 rounded-lg text-base bg-white cursor-pointer focus:outline-none focus:border-blue-500 transition-colors"
                >
                  <option value="">Todos os Estados</option>
                  {FilterService.UFs.map(uf => (
                    <option key={uf} value={uf}>{uf}</option>
                  ))}
                </select>
              </div>

              {(searchTerm || selectedUF) && (
                <button
                  onClick={() => {
                    setSearchTerm("")
                    setSelectedUF("")
                  }}
                  className="py-3 px-6 bg-slate-100 rounded-lg cursor-pointer text-sm font-medium hover:bg-slate-200 transition-colors"
                >
                  Limpar Filtros
                </button>
              )}
            </div>
          )}

          {/* CONTEÚDO DOS RANKINGS */}
          <div>
            {activeTab === "performance" && <RankingPerformance />}
            {activeTab === "gastos" && <RankingGastos searchTerm={searchTerm} selectedUF={selectedUF} />}
            {activeTab === "economia" && <RankingEconomia searchTerm={searchTerm} selectedUF={selectedUF} />}
            {activeTab === "discursos" && <RankingDiscursos />}
            {activeTab === "empresas" && <RankingEmpresas />}
          </div>
        </div>
    </>
  ) 
}

// ========== COMPONENTES DOS RANKINGS ==========

function RankingPerformance() {
  const { data, isLoading, error } = useRankingPerformance()

  if (isLoading) return <LoadingState />
  if (error) return <ErrorState message={error.message} />
  if (!data) return null

  const top3 = data.slice(0, 3)
  const rest = data.slice(3, 50)

  return (
    <div>
      {/* PÓDIO TOP 3 */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-12">
        {top3.map((politico, index) => (
          <PodiumCard 
            key={politico.id} 
            politico={politico} 
            position={index + 1}
          />
        ))}
      </div>

      {/* RANKING COMPLETO */}
      <h3 className="text-2xl font-bold mb-6 text-slate-800">
        Top 50 Parlamentares
      </h3>
      <div className="flex flex-col gap-3">
        {rest.map((politico, index) => (
          <RankingCard
            key={politico.id}
            position={index + 4}
            politico={politico}
            type="performance"
          />
        ))}
      </div>
    </div>
  )
}

function RankingGastos({ searchTerm, selectedUF }: { searchTerm: string; selectedUF: string }) {
  const { data, isLoading, error } = useRankingDespesas({
    q: searchTerm || undefined,
    uf: selectedUF || undefined,
    limit: 100,
  })

  if (isLoading) return <LoadingState />
  if (error) return <ErrorState message={error.message} />
  if (!data || data.length === 0) return <EmptyState message="Nenhum resultado encontrado" />

  // Calcula estatísticas
  const stats = DespesaRankingService.calcularEstatisticas(data)

  return (
    <div>
      {/* CARDS DE ESTATÍSTICAS */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
        <StatCard 
          label="Maior Gasto" 
          value={FormatService.formatarMoeda(stats.maior)}
          color="text-red-500"
        />
        <StatCard 
          label="Média de Gastos" 
          value={FormatService.formatarMoeda(stats.media)}
          color="text-amber-500"
        />
        <StatCard 
          label="Total Gasto" 
          value={FormatService.formatarMoeda(stats.total)}
          color="text-purple-500"
        />
      </div>

      {/* LISTA DE RANKING */}
      <div className="flex flex-col gap-3">
        {data.map((politico, index) => (
          <RankingCard
            key={politico.politico_id}
            position={index + 1}
            politico={{
              id: politico.politico_id,
              nome: politico.nome,
              total_gasto: politico.total_gasto
            }}
            type="gastos"
          />
        ))}
      </div>
    </div>
  )
}

function RankingEconomia({ searchTerm, selectedUF }: { searchTerm: string; selectedUF: string }) {
  const { data: rawData, isLoading, error } = useRankingDespesas({
    q: searchTerm || undefined,
    uf: selectedUF || undefined,
    limit: 100,
  })

  if (isLoading) return <LoadingState />
  if (error) return <ErrorState message={error.message} />
  if (!rawData || rawData.length === 0) return <EmptyState message="Nenhum resultado encontrado" />

  // Ordena do menor para o maior gasto (mais econômicos primeiro)
  const data = [...rawData].sort((a, b) => a.total_gasto - b.total_gasto)

  return (
    <div>
      <div className="bg-emerald-50 border-2 border-emerald-500 rounded-lg p-4 mb-8">
        <p className="text-emerald-900 text-sm">
          💡 <strong>Ranking dos Mais Econômicos:</strong> Parlamentares ordenados do menor para o maior gasto total.
        </p>
      </div>

      <div className="flex flex-col gap-3">
        {data.map((politico, index) => (
          <RankingCard
            key={politico.politico_id}
            position={index + 1}
            politico={{
              id: politico.politico_id,
              nome: politico.nome,
              total_gasto: politico.total_gasto
            }}
            type="economia"
          />
        ))}
      </div>
    </div>
  )
}

function RankingDiscursos() {
  const { data, isLoading, error } = useRankingDiscursos({ limit: 100 })

  if (isLoading) return <LoadingState />
  if (error) return <ErrorState message={error.message} />
  if (!data) return null

  return (
    <div className="flex flex-col gap-4">
      {data.map((politico, index) => (
        <DiscursoCard 
          key={politico.politico_id} 
          position={index + 1} 
          politico={politico} 
        />
      ))}
    </div>
  )
}

function RankingEmpresas() {
  const { data, isLoading, error } = useRankingLucroEmpresas({ limit: 100 })

  if (isLoading) return <LoadingState />
  if (error) return <ErrorState message={error.message} />
  if (!data) return null

  return (
    <div className="flex flex-col gap-3">
      {data.map((empresa, index) => (
        <EmpresaCard 
          key={empresa.cnpj} 
          position={index + 1} 
          empresa={empresa} 
        />
      ))}
    </div>
  )
}

// ========== CARDS DE RANKING ==========

function PodiumCard({ politico, position }: { politico: any; position: number }) {
  const medals = ["🥇", "🥈", "🥉"]
  const borderColors = ["border-yellow-400", "border-gray-400", "border-amber-600"]
  const bgColors = ["bg-yellow-400", "bg-gray-400", "bg-amber-600"]
  
  return (
    <Link to={`/politicos_detalhe/${politico.id}`} className="no-underline">
      <div className={`bg-white border-4 ${borderColors[position - 1]} rounded-xl p-6 transition-all duration-200 cursor-pointer relative overflow-hidden hover:-translate-y-1 hover:shadow-2xl`}>
        {/* MEDAL BADGE */}
        <div className="absolute -top-2 -right-2 text-5xl">
          {medals[position - 1]}
        </div>

        {/* FOTO */}
        {politico.foto && (
          <div className={`w-24 h-24 rounded-full overflow-hidden mx-auto mb-4 border-4 ${borderColors[position - 1]}`}>
            <img 
              src={politico.foto} 
              alt={politico.nome}
              className="w-full h-full object-cover"
            />
          </div>
        )}

        {/* INFO */}
        <h3 className="text-xl font-bold mb-2 text-center text-slate-800">
          {politico.nome}
        </h3>
        
        <p className="text-center text-slate-500 mb-4 text-sm">
          {politico.partido} • {politico.uf}
        </p>

        {/* SCORE */}
        <div className={`${bgColors[position - 1]} text-white p-3 rounded-lg text-center`}>
          <div className="text-3xl font-bold">
            {politico.score.toFixed(2)}
          </div>
          <div className="text-xs opacity-90">
            Score de Performance
          </div>
        </div>

        {/* NOTAS DETALHADAS */}
        <div className="mt-4 grid grid-cols-3 gap-2 text-xs">
          <div className="text-center">
            <div className="font-semibold text-slate-800">
              {politico.notas.assiduidade.toFixed(1)}
            </div>
            <div className="text-slate-500">Assiduidade</div>
          </div>
          <div className="text-center">
            <div className="font-semibold text-slate-800">
              {politico.notas.producao.toFixed(1)}
            </div>
            <div className="text-slate-500">Produção</div>
          </div>
          <div className="text-center">
            <div className="font-semibold text-slate-800">
              {politico.notas.economia.toFixed(1)}
            </div>
            <div className="text-slate-500">Economia</div>
          </div>
        </div>
      </div>
    </Link>
  )
}

function RankingCard({ position, politico, type }: { 
  position: number; 
  politico: any; 
  type: "performance" | "gastos" | "economia"
}) {
  const isTop3 = position <= 3
  
  return (
    <Link to={`/politicos_detalhe/${politico.id}`} className="no-underline">
      <div className="bg-white border-2 border-slate-200 rounded-lg p-4 px-6 flex items-center gap-6 transition-all duration-200 cursor-pointer hover:border-blue-500 hover:shadow-lg">
        {/* POSIÇÃO */}
        <div className={`w-12 h-12 ${isTop3 ? 'bg-amber-100 text-amber-500' : 'bg-slate-100 text-slate-500'} rounded-full flex items-center justify-center font-bold text-xl flex-shrink-0`}>
          {position}
        </div>

        {/* FOTO (apenas para performance) */}
        {type === "performance" && politico.foto && (
          <div className="w-12 h-12 rounded-full overflow-hidden flex-shrink-0">
            <img 
              src={politico.foto} 
              alt={politico.nome}
              className="w-full h-full object-cover"
            />
          </div>
        )}

        {/* INFORMAÇÕES */}
        <div className="flex-1 min-w-0">
          <h4 className="text-lg font-semibold mb-1 text-slate-800 truncate">
            {politico.nome}
          </h4>
          {type === "performance" && (
            <p className="text-sm text-slate-500">
              {politico.partido} • {politico.uf}
            </p>
          )}
        </div>

        {/* VALOR/SCORE */}
        <div className="text-right flex-shrink-0">
          {type === "performance" && (
            <div>
              <div className="text-2xl font-bold text-blue-500">
                {politico.score.toFixed(2)}
              </div>
              <div className="text-xs text-slate-500">
                Score
              </div>
            </div>
          )}
          {(type === "gastos" || type === "economia") && (
            <div className={`text-xl font-bold ${type === "gastos" ? 'text-red-500' : 'text-emerald-500'}`}>
              {FormatService.formatarMoeda(politico.total_gasto)}
            </div>
          )}
        </div>
      </div>
    </Link>
  )
}

function DiscursoCard({ position, politico }: { position: number; politico: any }) {
  const isTop3 = position <= 3
  
  return (
    <Link to={`/politico/${politico.politico_id}`} className="no-underline">
      <div className="bg-white border-2 border-slate-200 rounded-lg p-6 transition-all duration-200 cursor-pointer hover:border-blue-500 hover:shadow-lg">
        <div className="flex items-start gap-6">
          {/* POSIÇÃO */}
          <div className={`w-12 h-12 ${isTop3 ? 'bg-amber-100 text-amber-500' : 'bg-slate-100 text-slate-500'} rounded-full flex items-center justify-center font-bold text-xl flex-shrink-0`}>
            {position}
          </div>

          <div className="flex-1">
            {/* NOME E INFO */}
            <div className="mb-4">
              <h4 className="text-lg font-semibold mb-1 text-slate-800">
                {politico.nome_politico}
              </h4>
              <p className="text-sm text-slate-500">
                {politico.sigla_partido} • {politico.sigla_uf}
              </p>
            </div>

            {/* TOTAL DE DISCURSOS */}
            <div className="inline-block bg-blue-100 text-blue-800 py-2 px-4 rounded-md font-semibold mb-4">
              <FileText size={16} className="inline mr-2" />
              {politico.total_discursos} discursos
            </div>

            {/* TEMAS MAIS DISCUTIDOS */}
            {politico.temas_mais_discutidos && politico.temas_mais_discutidos.length > 0 && (
              <div>
                <p className="text-xs text-slate-500 mb-2 font-medium">
                  Principais temas:
                </p>
                <div className="flex flex-wrap gap-2">
                  {politico.temas_mais_discutidos.slice(0, 5).map((tema: any, idx: number) => (
                    <span
                      key={idx}
                      className="bg-slate-100 text-slate-700 py-1 px-3 rounded-full text-xs font-medium"
                    >
                      {tema.keyword} ({tema.frequencia})
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </Link>
  )
}

function EmpresaCard({ position, empresa }: { position: number; empresa: any }) {
  const isTop3 = position <= 3
  
  return (
    <div className="bg-white border-2 border-slate-200 rounded-lg p-4 px-6 flex items-center gap-6">
      {/* POSIÇÃO */}
      <div className={`w-12 h-12 ${isTop3 ? 'bg-amber-100 text-amber-500' : 'bg-slate-100 text-slate-500'} rounded-full flex items-center justify-center font-bold text-xl flex-shrink-0`}>
        {position}
      </div>

      {/* ÍCONE EMPRESA */}
      <div className="w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center flex-shrink-0">
        <Building2 size={24} className="text-blue-800" />
      </div>

      {/* INFORMAÇÕES */}
      <div className="flex-1 min-w-0">
        <h4 className="text-lg font-semibold mb-1 text-slate-800 truncate">
          {empresa.nome_fornecedor}
        </h4>
        {empresa.cnpj && (
          <p className="text-xs text-slate-500 font-mono">
            CNPJ: {empresa.cnpj}
          </p>
        )}
      </div>

      {/* VALOR */}
      <div className="text-right flex-shrink-0">
        <div className="text-2xl font-bold text-emerald-500">
          {FormatService.formatarMoeda(empresa.total_recebido)}
        </div>
      </div>
    </div>
  )
}

// ========== COMPONENTES AUXILIARES ==========

function TabButton({ active, onClick, icon, label }: {
  active: boolean
  onClick: () => void
  icon: React.ReactNode
  label: string
}) {
  return (
    <button
      onClick={onClick}
      className={`flex items-center gap-2 py-3 px-6 border-none rounded-t-lg cursor-pointer font-medium text-sm transition-all duration-200 whitespace-nowrap
        ${active 
          ? 'bg-blue-500 text-white font-semibold' 
          : 'bg-transparent text-slate-500 hover:bg-slate-100'
        }`}
    >
      {icon}
      {label}
    </button>
  )
}

function StatCard({ label, value, color }: { label: string; value: string; color: string }) {
  return (
    <div className="bg-white border-2 border-slate-200 rounded-lg p-6 text-center">
      <div className={`text-3xl font-bold ${color} mb-2`}>
        {value}
      </div>
      <div className="text-sm text-slate-500 font-medium">
        {label}
      </div>
    </div>
  )
}

function LoadingState() {
  return (
    <div className="text-center py-16 px-8 text-slate-500">
      <div className="w-12 h-12 border-4 border-slate-200 border-t-blue-500 rounded-full mx-auto mb-4 animate-spin" />
      <p>Carregando rankings...</p>
    </div>
  )
}

function ErrorState({ message }: { message: string }) {
  return (
    <div className="text-center py-16 px-8 bg-red-50 rounded-lg text-red-900">
      <p className="text-lg font-semibold mb-2">
        Erro ao carregar dados
      </p>
      <p className="text-sm">{message}</p>
    </div>
  )
}

function EmptyState({ message }: { message: string }) {
  return (
    <div className="text-center py-16 px-8 bg-slate-100 rounded-lg text-slate-500">
      <p className="text-lg font-semibold">
        {message}
      </p>
    </div>
  )
}