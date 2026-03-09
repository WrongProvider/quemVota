import { useState } from "react"
import { Link } from "react-router-dom"
import {
  TrendingUp,
  TrendingDown,
  DollarSign,
  FileText,
  Award,
  Building2,
  Search,
  Filter,
  ChevronRight,
  Loader2,
  MapPin,
} from "lucide-react"
import {
  useRankingPerformance,
  useRankingDespesas,
  useRankingDiscursos,
  useRankingLucroEmpresas,
} from "../hooks/useRankings"
import Header from "../components/Header"
import {
  DespesaRankingService,
  FormatService,
  FilterService,
} from "../services/rankings.service"

const PATH_FOTOS = "/fotos_politicos/"

// ─────────────────────────────────────────────────────────────────────────────
// Tipos de abas
// ─────────────────────────────────────────────────────────────────────────────

type ActiveTab = "performance" | "gastos" | "economia" | "empresas" | "discursos"

const TABS: { id: ActiveTab; label: string; icon: React.ReactNode }[] = [
  { id: "performance", label: "Melhor Performance", icon: <TrendingUp size={15} /> },
  { id: "gastos",      label: "Maiores Gastos",     icon: <TrendingDown size={15} /> },
  { id: "economia",    label: "Mais Econômicos",    icon: <DollarSign size={15} /> },
  { id: "discursos",   label: "Mais Discursos",     icon: <FileText size={15} /> },
  { id: "empresas",    label: "Empresas",           icon: <Building2 size={15} /> },
]

// ─────────────────────────────────────────────────────────────────────────────
// Estados de loading / vazio / erro
// ─────────────────────────────────────────────────────────────────────────────

function EstadoLoading() {
  return (
    <div className="flex items-center justify-center py-20 gap-3 text-slate-400">
      <Loader2 size={20} className="animate-spin" />
      <span className="text-sm">Carregando ranking...</span>
    </div>
  )
}

function EstadoVazio({ mensagem }: { mensagem: string }) {
  return (
    <div className="flex flex-col items-center justify-center py-20 text-center text-slate-400">
      <Award size={36} className="mb-3 opacity-30" />
      <p className="text-sm">{mensagem}</p>
    </div>
  )
}

function EstadoErro({ mensagem }: { mensagem: string }) {
  return (
    <div className="flex flex-col items-center justify-center py-20 text-center">
      <p className="text-sm font-semibold text-slate-600">Erro ao carregar dados</p>
      <p className="text-xs text-slate-400 mt-1">{mensagem}</p>
    </div>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// Pódio top 3
// ─────────────────────────────────────────────────────────────────────────────

function PodioCard({ politico, position }: { politico: any; position: number }) {
  const medals = ["🥇", "🥈", "🥉"]
  const ringColors = ["ring-yellow-400", "ring-slate-400", "ring-amber-600"]
  const badgeColors = [
    "bg-yellow-400 text-white",
    "bg-slate-400 text-white",
    "bg-amber-600 text-white",
  ]

  return (
    <Link to={`/politicos_detalhe/${politico.id}`} className="no-underline">
      <div className="group px-5 py-4 border-b border-slate-100 hover:bg-slate-50 transition-colors flex items-center gap-4">
        {/* Posição */}
        <div className="w-9 h-9 rounded-full bg-amber-50 border border-amber-100 flex items-center justify-center text-lg flex-shrink-0">
          {medals[position - 1]}
        </div>

        {/* Foto */}
        <div className={`w-12 h-12 rounded-xl overflow-hidden bg-slate-100 border-2 ring-2 ${ringColors[position - 1]} flex-shrink-0`}>
          <img
            src={`${PATH_FOTOS}${politico.id}.jpg`}
            alt={politico.nome}
            className="w-full h-full object-cover"
          />
        </div>

        {/* Info */}
        <div className="flex-1 min-w-0">
          <p className="font-semibold text-sm text-slate-800 truncate">{politico.nome}</p>
          <div className="flex items-center gap-1.5 mt-1 flex-wrap">
            <span className="font-mono text-[11px] font-semibold text-blue-600 bg-blue-50 px-1.5 py-0.5 rounded border border-blue-100">
              {politico.partido}
            </span>
            <span className="font-mono inline-flex items-center gap-1 text-[11px] text-slate-500 bg-slate-100 px-1.5 py-0.5 rounded">
              <MapPin size={9} /> {politico.uf}
            </span>
          </div>
        </div>

        {/* Score */}
        <div className="text-right flex-shrink-0">
          <div className={`inline-flex items-center justify-center px-3 py-1 rounded-lg text-sm font-bold ${badgeColors[position - 1]}`}>
            {politico.score.toFixed(1)}
          </div>
          <p className="text-[10px] text-slate-400 mt-0.5 text-center">score</p>
        </div>

        <ChevronRight size={14} className="text-slate-300 group-hover:text-blue-400 transition-colors flex-shrink-0" />
      </div>
    </Link>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// Card de ranking padrão
// ─────────────────────────────────────────────────────────────────────────────

function RankingRow({
  position,
  politico,
  type,
}: {
  position: number
  politico: any
  type: "performance" | "gastos" | "economia"
}) {
  const isTop3 = position <= 3

  return (
    <Link to={`/politicos_detalhe/${politico.id}`} className="no-underline">
      <div className="group px-5 py-3.5 border-b border-slate-100 last:border-0 hover:bg-slate-50 transition-colors flex items-center gap-4">
        {/* Posição */}
        <div
          className={`w-8 h-8 rounded-full flex items-center justify-center font-mono font-bold text-xs flex-shrink-0 ${
            isTop3
              ? "bg-amber-50 text-amber-600 border border-amber-200"
              : "bg-slate-100 text-slate-500"
          }`}
        >
          {position}
        </div>

        {/* Foto (apenas performance) */}
        {type === "performance" && (
          <div className="w-10 h-10 rounded-xl overflow-hidden bg-slate-100 border border-slate-200 flex-shrink-0">
            <img
              src={`${PATH_FOTOS}${politico.id}.jpg`}
              alt={politico.nome}
              className="w-full h-full object-cover"
            />
          </div>
        )}

        {/* Info */}
        <div className="flex-1 min-w-0">
          <p className="font-semibold text-sm text-slate-800 truncate">{politico.nome}</p>
          {type === "performance" && (
            <div className="flex items-center gap-1.5 mt-0.5">
              <span className="font-mono text-[11px] text-slate-500">{politico.partido}</span>
              <span className="text-slate-300">·</span>
              <span className="font-mono text-[11px] text-slate-500">{politico.uf}</span>
            </div>
          )}
        </div>

        {/* Valor */}
        <div className="text-right flex-shrink-0">
          {type === "performance" && (
            <span className="font-mono text-sm font-bold text-blue-600">
              {politico.score.toFixed(1)}
            </span>
          )}
          {(type === "gastos" || type === "economia") && (
            <span
              className={`font-mono text-sm font-bold ${
                type === "gastos" ? "text-red-500" : "text-emerald-600"
              }`}
            >
              {FormatService.formatarMoeda(politico.total_gasto)}
            </span>
          )}
        </div>

        <ChevronRight size={13} className="text-slate-300 group-hover:text-blue-400 transition-colors flex-shrink-0" />
      </div>
    </Link>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// Card de discurso
// ─────────────────────────────────────────────────────────────────────────────

function DiscursoRow({ position, politico }: { position: number; politico: any }) {
  const isTop3 = position <= 3

  return (
    <Link to={`/politicos_detalhe/${politico.politico_id}`} className="no-underline">
      <div className="group px-5 py-4 border-b border-slate-100 last:border-0 hover:bg-slate-50 transition-colors">
        <div className="flex items-start gap-4">
          {/* Posição */}
          <div
            className={`w-8 h-8 rounded-full flex items-center justify-center font-mono font-bold text-xs flex-shrink-0 mt-0.5 ${
              isTop3
                ? "bg-amber-50 text-amber-600 border border-amber-200"
                : "bg-slate-100 text-slate-500"
            }`}
          >
            {position}
          </div>

          <div className="flex-1 min-w-0">
            <div className="flex items-center justify-between gap-3 mb-2">
              <div>
                <p className="font-semibold text-sm text-slate-800">{politico.nome_politico}</p>
                <div className="flex items-center gap-1.5 mt-0.5">
                  <span className="font-mono text-[11px] text-slate-500">{politico.sigla_partido}</span>
                  <span className="text-slate-300">·</span>
                  <span className="font-mono text-[11px] text-slate-500">{politico.sigla_uf}</span>
                </div>
              </div>
              <span className="inline-flex items-center gap-1.5 px-3 py-1 bg-blue-50 border border-blue-100 text-blue-700 text-xs font-semibold rounded-lg flex-shrink-0">
                <FileText size={11} /> {politico.total_discursos}
              </span>
            </div>

            {politico.temas_mais_discutidos?.length > 0 && (
              <div className="flex flex-wrap gap-1.5">
                {politico.temas_mais_discutidos.slice(0, 5).map((tema: any, idx: number) => (
                  <span
                    key={idx}
                    className="text-[11px] text-slate-500 bg-slate-100 px-2 py-0.5 rounded-md"
                  >
                    {tema.keyword}
                    <span className="text-slate-400 ml-1">({tema.frequencia})</span>
                  </span>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </Link>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// Card de empresa
// ─────────────────────────────────────────────────────────────────────────────

function EmpresaRow({ position, empresa }: { position: number; empresa: any }) {
  const isTop3 = position <= 3

  return (
    <div className="px-5 py-3.5 border-b border-slate-100 last:border-0 flex items-center gap-4">
      <div
        className={`w-8 h-8 rounded-full flex items-center justify-center font-mono font-bold text-xs flex-shrink-0 ${
          isTop3
            ? "bg-amber-50 text-amber-600 border border-amber-200"
            : "bg-slate-100 text-slate-500"
        }`}
      >
        {position}
      </div>

      <div className="w-9 h-9 bg-slate-100 rounded-xl flex items-center justify-center flex-shrink-0">
        <Building2 size={16} className="text-slate-500" />
      </div>

      <div className="flex-1 min-w-0">
        <p className="font-semibold text-sm text-slate-800 truncate">{empresa.nome_fornecedor}</p>
        {empresa.cnpj && (
          <p className="text-[11px] text-slate-400 font-mono mt-0.5">{empresa.cnpj}</p>
        )}
      </div>

      <span className="font-mono text-sm font-bold text-emerald-600 flex-shrink-0">
        {FormatService.formatarMoeda(empresa.total_recebido)}
      </span>
    </div>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// Conteúdo de cada aba
// ─────────────────────────────────────────────────────────────────────────────

function RankingPerformance() {
  const { data, isLoading, error } = useRankingPerformance()

  if (isLoading) return <EstadoLoading />
  if (error) return <EstadoErro mensagem={error.message} />

  const ranking = data?.ranking ?? []
  if (!ranking.length) return <EstadoVazio mensagem="Nenhum dado de performance disponível." />

  const top3 = ranking.slice(0, 3)
  const rest = ranking.slice(3, 50)

  return (
    <>
      {/* Aviso de cobertura histórica */}
      {data?.aviso && (
        <div className="px-5 py-3 bg-blue-50/70 border-b border-blue-100 flex items-start gap-2.5">
          <span className="text-blue-400 flex-shrink-0 mt-0.5">ℹ️</span>
          <p className="text-[11px] text-blue-700 leading-relaxed">{data.aviso}</p>
        </div>
      )}

      {/* Pódio */}
      <div className="border-b border-slate-100">
        <div className="px-5 py-2.5 bg-amber-50/60 border-b border-amber-100">
          <p className="text-[11px] font-semibold text-amber-700 uppercase tracking-wide">
            🏆 Pódio — Top 3
          </p>
        </div>
        {top3.map((p, i) => (
          <PodioCard key={p.id} politico={p} position={i + 1} />
        ))}
      </div>

      {/* Restante */}
      {rest.map((p, i) => (
        <RankingRow key={p.id} position={i + 4} politico={p} type="performance" />
      ))}
    </>
  )
}

function RankingGastos({ searchTerm, selectedUF }: { searchTerm: string; selectedUF: string }) {
  const { data, isLoading, error } = useRankingDespesas({
    q: searchTerm || undefined,
    uf: selectedUF || undefined,
    limit: 100,
  })

  if (isLoading) return <EstadoLoading />
  if (error) return <EstadoErro mensagem={error.message} />
  if (!data?.length) return <EstadoVazio mensagem="Nenhum resultado encontrado." />

  const stats = DespesaRankingService.calcularEstatisticas(data)

  return (
    <>
      {/* Stats resumo */}
      <div className="grid grid-cols-3 divide-x divide-slate-100 border-b border-slate-100">
        {[
          { label: "Maior gasto",  value: FormatService.formatarMoeda(stats.maior), color: "text-red-500" },
          { label: "Média",        value: FormatService.formatarMoeda(stats.media), color: "text-amber-600" },
          { label: "Total geral",  value: FormatService.formatarMoeda(stats.total), color: "text-purple-600" },
        ].map((s) => (
          <div key={s.label} className="px-5 py-3 text-center">
            <p className={`font-mono font-bold text-sm ${s.color}`}>{s.value}</p>
            <p className="text-[11px] text-slate-400 mt-0.5">{s.label}</p>
          </div>
        ))}
      </div>
      {data.map((p, i) => (
        <RankingRow
          key={p.politico_id}
          position={i + 1}
          politico={{ id: p.politico_id, nome: p.nome, total_gasto: p.total_gasto }}
          type="gastos"
        />
      ))}
    </>
  )
}

function RankingEconomia({ searchTerm, selectedUF }: { searchTerm: string; selectedUF: string }) {
  const { data: rawData, isLoading, error } = useRankingDespesas({
    q: searchTerm || undefined,
    uf: selectedUF || undefined,
    limit: 100,
  })

  if (isLoading) return <EstadoLoading />
  if (error) return <EstadoErro mensagem={error.message} />
  if (!rawData?.length) return <EstadoVazio mensagem="Nenhum resultado encontrado." />

  const data = [...rawData].sort((a, b) => a.total_gasto - b.total_gasto)

  return (
    <>
      <div className="px-5 py-3 bg-emerald-50/60 border-b border-emerald-100">
        <p className="text-[11px] font-semibold text-emerald-700 uppercase tracking-wide">
          💡 Ordenado do menor para o maior gasto total
        </p>
      </div>
      {data.map((p, i) => (
        <RankingRow
          key={p.politico_id}
          position={i + 1}
          politico={{ id: p.politico_id, nome: p.nome, total_gasto: p.total_gasto }}
          type="economia"
        />
      ))}
    </>
  )
}

function RankingDiscursos() {
  const { data, isLoading, error } = useRankingDiscursos({ limit: 100 })

  if (isLoading) return <EstadoLoading />
  if (error) return <EstadoErro mensagem={error.message} />
  if (!data?.length) return <EstadoVazio mensagem="Nenhum dado de discursos disponível." />

  return (
    <>
      {data.map((p, i) => (
        <DiscursoRow key={p.politico_id} position={i + 1} politico={p} />
      ))}
    </>
  )
}

function RankingEmpresas() {
  const { data, isLoading, error } = useRankingLucroEmpresas({ limit: 100 })

  if (isLoading) return <EstadoLoading />
  if (error) return <EstadoErro mensagem={error.message} />
  if (!data?.length) return <EstadoVazio mensagem="Nenhum dado de empresas disponível." />

  return (
    <>
      {data.map((e, i) => (
        <EmpresaRow key={e.cnpj} position={i + 1} empresa={e} />
      ))}
    </>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// Página principal
// ─────────────────────────────────────────────────────────────────────────────

export default function Rankings() {
  const [activeTab, setActiveTab] = useState<ActiveTab>("performance")
  const [searchTerm, setSearchTerm] = useState("")
  const [selectedUF, setSelectedUF] = useState("")

  const showFilters = activeTab !== "empresas" && activeTab !== "discursos"

  return (
    <div style={{ fontFamily: "'DM Sans', sans-serif" }} className="min-h-screen bg-gray-50">
      <Header />

      {/* ── Cabeçalho da página ── */}
      <div className="bg-white border-b border-slate-200">
        <div className="max-w-7xl mx-auto px-6 py-8 pt-24">
          <p className="text-xs font-semibold tracking-widest uppercase text-blue-600 mb-2">
            Câmara dos Deputados
          </p>
          <h1
            style={{ fontFamily: "'Fraunces', serif" }}
            className="text-3xl font-bold text-slate-900 mb-1"
          >
            Rankings Parlamentares
          </h1>
          <p className="text-slate-500 text-sm">
            Confira os parlamentares em destaque nas principais métricas de desempenho.
          </p>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-6 py-6 pb-16">
        <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">

          {/* ── Abas ── */}
          <div className="flex border-b border-slate-200 overflow-x-auto">
            {TABS.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center gap-2 px-5 py-4 text-sm font-semibold transition-colors border-b-2 -mb-px whitespace-nowrap flex-shrink-0 ${
                  activeTab === tab.id
                    ? "border-blue-500 text-blue-600"
                    : "border-transparent text-slate-500 hover:text-slate-700"
                }`}
              >
                {tab.icon}
                {tab.label}
              </button>
            ))}
          </div>

          {/* ── Filtros (apenas abas com políticos, exceto discursos) ── */}
          {showFilters && (
            <div className="px-5 py-4 border-b border-slate-100 bg-slate-50/50 flex items-center gap-3 flex-wrap">
              <div className="relative flex-1 min-w-[200px]">
                <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
                <input
                  type="text"
                  placeholder="Buscar parlamentar..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="w-full pl-9 pr-3 py-2 text-sm border border-slate-200 rounded-lg bg-white focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-400 transition-all text-slate-600"
                />
              </div>

              <div className="flex items-center gap-2">
                <Filter size={13} className="text-slate-400" />
                <select
                  value={selectedUF}
                  onChange={(e) => setSelectedUF(e.target.value)}
                  className="text-sm border border-slate-200 rounded-lg px-3 py-2 bg-white focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-400 transition-all text-slate-600"
                >
                  <option value="">Todos os estados</option>
                  {FilterService.UFs.map((uf) => (
                    <option key={uf} value={uf}>{uf}</option>
                  ))}
                </select>
              </div>

              {(searchTerm || selectedUF) && (
                <button
                  onClick={() => { setSearchTerm(""); setSelectedUF("") }}
                  className="text-xs text-slate-500 hover:text-red-500 font-medium transition-colors px-2 py-1 rounded-lg hover:bg-red-50"
                >
                  Limpar
                </button>
              )}
            </div>
          )}

          {/* ── Conteúdo da aba ── */}
          <div>
            {activeTab === "performance" && <RankingPerformance />}
            {activeTab === "gastos"      && <RankingGastos searchTerm={searchTerm} selectedUF={selectedUF} />}
            {activeTab === "economia"    && <RankingEconomia searchTerm={searchTerm} selectedUF={selectedUF} />}
            {activeTab === "discursos"   && <RankingDiscursos />}
            {activeTab === "empresas"    && <RankingEmpresas />}
          </div>

        </div>
      </div>
    </div>
  )
}