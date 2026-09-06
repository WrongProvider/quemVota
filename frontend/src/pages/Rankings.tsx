import { useState } from "react"
import { Link } from "react-router-dom"
import { useSeo } from "../hooks/useSeo"
import {
  TrendingDown,
  DollarSign,
  FileText,
  Building2,
  Search,
  Filter,
  ChevronRight,
  Loader2,
  Award,
} from "lucide-react"
import {
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

// ─────────────────────────────────────────────────────────────────────────────
// Tipos de abas factuais
// ─────────────────────────────────────────────────────────────────────────────

type ActiveTab = "gastos" | "economia" | "discursos" | "empresas"

const TABS: { id: ActiveTab; label: string; icon: React.ReactNode }[] = [
  { id: "gastos",    label: "Maiores Gastos",  icon: <TrendingDown size={15} /> },
  { id: "economia",  label: "Mais Econômicos", icon: <DollarSign size={15} /> },
  { id: "discursos", label: "Mais Discursos",  icon: <FileText size={15} /> },
  { id: "empresas",  label: "Empresas",        icon: <Building2 size={15} /> },
]

// ─────────────────────────────────────────────────────────────────────────────
// Estados de loading / vazio / erro
// ─────────────────────────────────────────────────────────────────────────────

function EstadoLoading() {
  return (
    <div className="flex items-center justify-center py-20 gap-3 text-slate-400">
      <Loader2 size={20} className="animate-spin" />
      <span className="text-sm">Carregando dados...</span>
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
// Card de ranking de despesas
// ─────────────────────────────────────────────────────────────────────────────

function RankingRow({
  position,
  politico,
  type,
  maxValor,
}: {
  position: number
  politico: any
  type: "gastos" | "economia"
  maxValor?: number
}) {
  const isTop3 = position <= 3
  const linkId = politico.slug ?? politico.politico_id ?? politico.id
  const pct = maxValor && maxValor > 0 ? Math.min(100, (politico.total_gasto / maxValor) * 100) : 0

  return (
    <Link to={`/politicos/${linkId}`} className="no-underline">
      <div className="group px-3.5 sm:px-5 py-3 border-b border-slate-100 last:border-0 hover:bg-slate-50 transition-colors flex items-center gap-2.5 sm:gap-4">
        {/* Posição */}
        <div
          className={`w-7 h-7 rounded-md flex items-center justify-center font-mono font-bold text-xs flex-shrink-0 ${
            isTop3
              ? "bg-slate-900 text-white shadow-2xs"
              : "bg-slate-100 text-slate-600"
          }`}
        >
          {position}
        </div>

        {/* Info com barra proporcional */}
        <div className="flex-1 min-w-0">
          <p className="font-medium text-sm text-slate-900 truncate group-hover:text-blue-700 transition-colors">
            {politico.nome}
          </p>
          {maxValor ? (
            <div className="w-full bg-slate-100 h-1.5 rounded-full mt-1.5 overflow-hidden">
              <div
                className={`h-full rounded-full transition-all duration-300 ${
                  type === "gastos" ? "bg-red-500/80" : "bg-emerald-600/80"
                }`}
                style={{ width: `${pct}%` }}
              />
            </div>
          ) : null}
        </div>

        {/* Valor */}
        <div className="text-right flex-shrink-0">
          <span
            className={`font-mono tabular-nums text-xs sm:text-sm font-bold ${
              type === "gastos" ? "text-slate-900" : "text-emerald-700"
            }`}
          >
            {FormatService.formatarMoeda(politico.total_gasto)}
          </span>
        </div>

        <ChevronRight size={14} className="text-slate-300 group-hover:text-blue-600 transition-colors flex-shrink-0" />
      </div>
    </Link>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// Card de discurso
// ─────────────────────────────────────────────────────────────────────────────

function DiscursoRow({ position, politico }: { position: number; politico: any }) {
  const isTop3 = position <= 3
  const linkId = politico.slug ?? politico.politico_id ?? politico.id

  return (
    <Link to={`/politicos/${linkId}`} className="no-underline">
      <div className="group px-5 py-4 border-b border-slate-100 last:border-0 hover:bg-slate-50 transition-colors">
        <div className="flex items-start gap-4">
          <div
            className={`w-7 h-7 rounded-md flex items-center justify-center font-mono font-bold text-xs flex-shrink-0 mt-0.5 ${
              isTop3
                ? "bg-slate-900 text-white"
                : "bg-slate-100 text-slate-600"
            }`}
          >
            {position}
          </div>

          <div className="flex-1 min-w-0">
            <div className="flex items-center justify-between gap-3 mb-2">
              <div>
                <p className="font-medium text-sm text-slate-900 group-hover:text-blue-700 transition-colors">
                  {politico.nome_politico}
                </p>
                <div className="flex items-center gap-1.5 mt-0.5">
                  <span className="font-mono text-[11px] font-semibold text-slate-500 uppercase">{politico.sigla_partido}</span>
                  <span className="text-slate-300">·</span>
                  <span className="font-mono text-[11px] font-semibold text-slate-500">{politico.sigla_uf}</span>
                </div>
              </div>
              <span className="inline-flex items-center gap-1.5 px-2.5 py-1 bg-slate-100 border border-slate-200 text-slate-700 font-mono text-xs font-semibold rounded-md flex-shrink-0 tabular-nums">
                <FileText size={12} className="text-slate-500" /> {politico.total_discursos}
              </span>
            </div>

            {politico.temas_mais_discutidos?.length > 0 && (
              <div className="flex flex-wrap gap-1.5">
                {politico.temas_mais_discutidos.slice(0, 5).map((tema: any, idx: number) => (
                  <span
                    key={idx}
                    className="text-[11px] text-slate-600 bg-slate-100 border border-slate-200/60 px-2 py-0.5 rounded-sm"
                  >
                    {tema.keyword}
                    <span className="text-slate-400 font-mono ml-1">({tema.frequencia})</span>
                  </span>
                ))}
              </div>
            )}
          </div>
          <ChevronRight size={14} className="text-slate-300 group-hover:text-blue-600 transition-colors flex-shrink-0 mt-2" />
        </div>
      </div>
    </Link>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// Card de empresa
// ─────────────────────────────────────────────────────────────────────────────

function EmpresaRow({
  position,
  empresa,
  maxRecebido,
}: {
  position: number
  empresa: any
  maxRecebido?: number
}) {
  const isTop3 = position <= 3
  const pct = maxRecebido && maxRecebido > 0 ? Math.min(100, (empresa.total_recebido / maxRecebido) * 100) : 0

  return (
    <div className="px-5 py-3.5 border-b border-slate-100 last:border-0 flex items-center gap-4 hover:bg-slate-50/70 transition-colors">
      <div
        className={`w-7 h-7 rounded-md flex items-center justify-center font-mono font-bold text-xs flex-shrink-0 ${
          isTop3
            ? "bg-slate-900 text-white"
            : "bg-slate-100 text-slate-600"
        }`}
      >
        {position}
      </div>

      <div className="w-8 h-8 bg-slate-100 border border-slate-200/80 rounded-lg flex items-center justify-center flex-shrink-0">
        <Building2 size={15} className="text-slate-500" />
      </div>

      <div className="flex-1 min-w-0">
        <p className="font-medium text-sm text-slate-900 truncate">{empresa.nome_fornecedor}</p>
        <div className="flex items-center gap-2 mt-0.5">
          {empresa.cnpj && (
            <span className="text-[11px] text-slate-400 font-mono">{empresa.cnpj}</span>
          )}
        </div>
        {maxRecebido ? (
          <div className="w-full bg-slate-100 h-1.5 rounded-full mt-1.5 overflow-hidden">
            <div
              className="h-full bg-slate-500 rounded-full transition-all duration-300"
              style={{ width: `${pct}%` }}
            />
          </div>
        ) : null}
      </div>

      <div className="text-right flex-shrink-0">
        <span className="font-mono tabular-nums text-sm font-bold text-slate-900">
          {FormatService.formatarMoeda(empresa.total_recebido)}
        </span>
      </div>
    </div>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// Abas factuais
// ─────────────────────────────────────────────────────────────────────────────

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
  const maxValor = data[0]?.total_gasto || 1

  return (
    <>
      <div className="grid grid-cols-1 sm:grid-cols-3 divide-y sm:divide-y-0 sm:divide-x divide-slate-200 border-b border-slate-200 bg-slate-50/50">
        {[
          { label: "Maior gasto individual", value: FormatService.formatarMoeda(stats.maior), color: "text-slate-900" },
          { label: "Média do grupo",          value: FormatService.formatarMoeda(stats.media), color: "text-slate-700" },
          { label: "Total acumulado",        value: FormatService.formatarMoeda(stats.total), color: "text-slate-900" },
        ].map((s) => (
          <div key={s.label} className="px-4 sm:px-5 py-2.5 sm:py-3.5 flex sm:block items-center justify-between sm:text-center">
            <p className="text-[11px] font-medium text-slate-500 uppercase tracking-wider sm:mt-0.5">{s.label}</p>
            <p className={`font-mono font-bold text-xs sm:text-sm tabular-nums ${s.color}`}>{s.value}</p>
          </div>
        ))}
      </div>
      {data.map((p, i) => (
        <RankingRow
          key={p.politico_id}
          position={i + 1}
          politico={{ id: p.politico_id, nome: p.nome, total_gasto: p.total_gasto }}
          type="gastos"
          maxValor={maxValor}
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
  const maxValor = data[data.length - 1]?.total_gasto || 1

  return (
    <>
      <div className="px-5 py-2.5 bg-slate-50 border-b border-slate-200 flex items-center justify-between">
        <p className="text-xs font-medium text-slate-600">
          Listagem ordenada em ordem crescente de utilização da cota (CEAP).
        </p>
        <span className="text-[11px] font-mono text-slate-400">
          {data.length} parlamentares
        </span>
      </div>
      {data.map((p, i) => (
        <RankingRow
          key={p.politico_id}
          position={i + 1}
          politico={{ id: p.politico_id, nome: p.nome, total_gasto: p.total_gasto }}
          type="economia"
          maxValor={maxValor}
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

  const maxRecebido = data[0]?.total_recebido || 1

  return (
    <>
      {data.map((e, i) => (
        <EmpresaRow
          key={e.cnpj}
          position={i + 1}
          empresa={e}
          maxRecebido={maxRecebido}
        />
      ))}
    </>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// Página principal
// ─────────────────────────────────────────────────────────────────────────────

export default function Rankings() {
  const [activeTab, setActiveTab]   = useState<ActiveTab>("gastos")
  const [searchTerm, setSearchTerm] = useState("")
  const [selectedUF, setSelectedUF] = useState("")

  useSeo({
    title: "Rankings Factuais — Gastos, Presença e Discursos | quemvota",
    description:
      "Consulte os dados abertos oficiais da Câmara dos Deputados: maiores e menores gastos de cota parlamentar, discursos proferidos e empresas contratadas.",
    url: "https://www.quemvota.com.br/rankings",
    keywords: "ranking deputados, gastos cota parlamentar, discursos camara, transparencia publica",
  })

  const showFilters = activeTab !== "empresas" && activeTab !== "discursos"

  return (
    <div className="min-h-screen bg-canvas">
      <Header />

      {/* ── Cabeçalho da página ── */}
      <div className="bg-white border-b border-slate-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 py-6 sm:py-8 pt-20 sm:pt-24">
          <p className="text-xs font-semibold tracking-wider uppercase text-blue-700 mb-1">
            Dados Factuais da Câmara dos Deputados
          </p>
          <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-slate-900 mb-1">
            Rankings Parlamentares
          </h1>
          <p className="text-slate-600 text-xs sm:text-sm">
            Métricas factuais de despesas oficiais, discursos em plenário e fornecedores contratados.
          </p>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 py-4 sm:py-6 pb-16">
        <div className="bg-white rounded-xl border border-slate-200/90 shadow-xs overflow-hidden">

          {/* ── Abas ── */}
          <div className="flex border-b border-slate-200 overflow-x-auto bg-slate-50/40">
            {TABS.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center gap-2 px-3.5 sm:px-5 py-3 sm:py-3.5 text-xs sm:text-sm font-medium transition-colors border-b-2 -mb-px whitespace-nowrap flex-shrink-0 cursor-pointer ${
                  activeTab === tab.id
                    ? "border-slate-900 text-slate-900 font-semibold bg-white"
                    : "border-transparent text-slate-500 hover:text-slate-900 hover:bg-slate-100/50"
                }`}
              >
                {tab.icon}
                {tab.label}
              </button>
            ))}
          </div>

          {/* ── Filtros de nome / UF ── */}
          {showFilters && (
            <div className="px-3.5 sm:px-5 py-3 sm:py-3.5 border-b border-slate-200/80 bg-slate-50/30 flex items-center gap-2 sm:gap-3 flex-wrap">
              <div className="relative flex-1 min-w-[160px] sm:min-w-[180px]">
                <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
                <input
                  type="text"
                  placeholder="Buscar parlamentar..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="w-full pl-9 pr-3 py-1.5 text-base sm:text-sm border border-slate-200 rounded-lg bg-white focus:outline-none focus:ring-2 focus:ring-slate-900/10 focus:border-slate-400 transition-all text-slate-800 min-w-0"
                />
              </div>

              <div className="flex items-center gap-2 flex-wrap">
                <Filter size={13} className="text-slate-400" />

                <select
                  value={selectedUF}
                  onChange={(e) => setSelectedUF(e.target.value)}
                  className="text-base sm:text-sm border border-slate-200 rounded-lg px-3 py-1.5 bg-white focus:outline-none focus:ring-2 focus:ring-slate-900/10 focus:border-slate-400 transition-all text-slate-800"
                >
                  <option value="">Todos os estados</option>
                  {FilterService.UFs.map((uf) => (
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
                  className="text-xs text-slate-500 hover:text-red-600 font-medium transition-colors px-2.5 py-1 rounded-md hover:bg-slate-100"
                >
                  Limpar filtros
                </button>
              )}
            </div>
          )}

          {/* ── Conteúdo da aba ── */}
          <div className="pb-2">
            {activeTab === "gastos"    && <RankingGastos    searchTerm={searchTerm} selectedUF={selectedUF} />}
            {activeTab === "economia"  && <RankingEconomia  searchTerm={searchTerm} selectedUF={selectedUF} />}
            {activeTab === "discursos" && <RankingDiscursos />}
            {activeTab === "empresas"  && <RankingEmpresas />}
          </div>

        </div>
      </div>
    </div>
  )
}