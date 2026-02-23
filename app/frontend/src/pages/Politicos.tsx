import { useSearchParams, Link } from "react-router-dom"
import { useState } from "react"
import { useDebounce } from "../hooks/useDebounce"
import { usePoliticos } from "../hooks/usePoliticos"
import Header from "../components/Header"
import { Search, SlidersHorizontal, Users, MapPin, ChevronRight, X } from "lucide-react"

const UFs = [
  "AC","AL","AM","AP","BA","CE","DF","ES","GO","MA",
  "MG","MS","MT","PA","PB","PE","PI","PR","RJ","RN",
  "RO","RR","RS","SC","SE","SP","TO",
]

export default function Politicos() {
  const [searchParams] = useSearchParams()
  const initialQ = searchParams.get("q") || ""

  const [search, setSearch] = useState(initialQ)
  const [selectedUF, setSelectedUF] = useState("")
  const [showFilters, setShowFilters] = useState(false)
  const debouncedSearch = useDebounce(search, 400)

  const { data, isLoading, isError } = usePoliticos({
    q: debouncedSearch,
    limit: 200,
  })

  const filtered = selectedUF ? data?.filter((p) => p.uf === selectedUF) : data
  const hasActiveFilters = !!(search || selectedUF)

  return (
    <div className="min-h-screen bg-slate-50 font-sans">
      <Header />

      <main className="pt-20 pb-16">
        <div className="max-w-5xl mx-auto px-4 sm:px-6">

          {/* ── PAGE HEADER ── */}
          <div className="py-10 border-b border-slate-100 mb-8">
            <div className="flex flex-wrap items-end justify-between gap-4">
              <div>
                <p className="text-xs font-medium text-slate-400 uppercase tracking-widest mb-1 font-mono">
                  Câmara dos Deputados
                </p>
                <h1 className="text-3xl md:text-4xl font-bold text-slate-900 leading-tight">
                  Parlamentares
                </h1>
                <p className="text-slate-500 text-sm mt-2 max-w-md leading-relaxed">
                  Explore os dados de desempenho, gastos e discursos dos deputados federais.
                </p>
              </div>

              {!isLoading && filtered && (
                <div className="flex items-center gap-2 px-4 py-2 bg-white border border-slate-200 rounded-xl shadow-sm flex-shrink-0">
                  <Users size={14} className="text-blue-500" />
                  <span className="font-mono font-semibold text-sm text-slate-700">
                    {filtered.length}
                  </span>
                  <span className="text-xs text-slate-400">parlamentares</span>
                </div>
              )}
            </div>
          </div>

          {/* ── SEARCH + FILTER ROW ── */}
          <div className="flex gap-3 mb-3 items-center">
            {/* Search Input */}
            <div className="relative flex-1">
              <Search
                size={17}
                className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400 pointer-events-none"
              />
              <input
                type="text"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Buscar por nome..."
                className="w-full pl-10 pr-4 py-3 border border-slate-200 rounded-xl text-sm bg-white text-slate-800 placeholder-slate-400 shadow-sm focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-500/10 transition-all"
              />
            </div>

            {/* Filter Toggle Button */}
            <button
              onClick={() => setShowFilters((v) => !v)}
              className={`flex items-center gap-2 px-4 py-3 border rounded-xl text-sm font-medium flex-shrink-0 shadow-sm transition-all ${
                showFilters
                  ? "border-blue-500 bg-blue-50 text-blue-600"
                  : "border-slate-200 bg-white text-slate-500 hover:border-blue-400 hover:text-blue-500"
              }`}
            >
              <SlidersHorizontal size={15} />
              <span>Filtrar</span>
              {selectedUF && (
                <span className="flex items-center justify-center w-4 h-4 rounded-full bg-blue-600 text-white text-[10px] font-bold leading-none">
                  1
                </span>
              )}
            </button>
          </div>

          {/* ── FILTER PANEL ── */}
          {showFilters && (
            <div className="bg-white border border-slate-200 rounded-2xl p-5 mb-4 shadow-sm">
              <div className="flex items-center gap-2 mb-3">
                <MapPin size={13} className="text-slate-400" />
                <span className="text-xs font-semibold text-slate-400 uppercase tracking-wide">
                  Filtrar por Estado
                </span>
              </div>
              <div className="flex flex-wrap gap-1.5">
                {UFs.map((uf) => (
                  <button
                    key={uf}
                    onClick={() => setSelectedUF(selectedUF === uf ? "" : uf)}
                    className={`px-3 py-1 rounded-lg border text-xs font-mono transition-all ${
                      selectedUF === uf
                        ? "border-blue-500 bg-blue-600 text-white"
                        : "border-slate-200 bg-white text-slate-500 hover:border-blue-400 hover:text-blue-600 hover:bg-blue-50"
                    }`}
                  >
                    {uf}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* ── ACTIVE FILTERS ── */}
          {hasActiveFilters && (
            <div className="flex items-center gap-2 mb-5 flex-wrap">
              <span className="text-xs text-slate-400">Filtros ativos:</span>

              {search && (
                <span className="inline-flex items-center gap-1.5 px-2.5 py-1 bg-blue-50 text-blue-700 text-xs font-medium rounded-full border border-blue-100">
                  "{search}"
                  <button
                    onClick={() => setSearch("")}
                    className="opacity-60 hover:opacity-100 transition-opacity"
                  >
                    <X size={11} />
                  </button>
                </span>
              )}

              {selectedUF && (
                <span className="inline-flex items-center gap-1.5 px-2.5 py-1 bg-blue-50 text-blue-700 text-xs font-medium font-mono rounded-full border border-blue-100">
                  {selectedUF}
                  <button
                    onClick={() => setSelectedUF("")}
                    className="opacity-60 hover:opacity-100 transition-opacity"
                  >
                    <X size={11} />
                  </button>
                </span>
              )}

              <button
                onClick={() => { setSearch(""); setSelectedUF(""); }}
                className="inline-flex items-center gap-1 px-3 py-1 rounded-full bg-slate-100 text-slate-500 text-xs hover:bg-red-50 hover:text-red-500 transition-colors"
              >
                <X size={10} />
                Limpar tudo
              </button>
            </div>
          )}

          {/* ── ERROR ── */}
          {isError && (
            <div className="text-center py-16">
              <div className="w-14 h-14 rounded-2xl bg-red-50 flex items-center justify-center mx-auto mb-3">
                <span className="text-2xl">⚠️</span>
              </div>
              <p className="font-semibold text-slate-700">Erro ao carregar dados</p>
              <p className="text-sm text-slate-400 mt-1">Tente novamente em alguns instantes.</p>
            </div>
          )}

          {/* ── SKELETON LOADING ── */}
          {isLoading && (
            <ul className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
              {Array.from({ length: 9 }).map((_, i) => (
                <li
                  key={i}
                  className="bg-white border border-slate-200 rounded-2xl p-4 flex items-center gap-4 animate-pulse"
                >
                  <div className="w-[76px] h-[76px] rounded-xl bg-slate-200 flex-shrink-0" />
                  <div className="flex-1 space-y-2">
                    <div className="h-3.5 bg-slate-200 rounded w-3/4" />
                    <div className="h-3 bg-slate-200 rounded w-1/2" />
                  </div>
                </li>
              ))}
            </ul>
          )}

          {/* ── GRID ── */}
          {!isLoading && !isError && (
            <>
              {filtered?.length === 0 ? (
                <div className="text-center py-16">
                  <div className="w-14 h-14 rounded-2xl bg-slate-100 flex items-center justify-center mx-auto mb-3">
                    <Users size={24} className="text-slate-400" />
                  </div>
                  <p className="font-semibold text-slate-700">Nenhum parlamentar encontrado</p>
                  <p className="text-sm text-slate-400 mt-1">Tente ajustar os filtros de busca.</p>
                  <button
                    onClick={() => { setSearch(""); setSelectedUF(""); }}
                    className="inline-flex items-center gap-1 mt-4 px-3 py-1.5 rounded-full bg-slate-100 text-slate-500 text-xs hover:bg-red-50 hover:text-red-500 transition-colors"
                  >
                    <X size={10} /> Limpar filtros
                  </button>
                </div>
              ) : (
                <ul className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
                  {filtered?.map((p) => (
                    <li key={p.id}>
                      <Link
                        to={`/politicos_detalhe/${p.id}`}
                        className="group relative flex items-center gap-4 p-4 bg-white border border-slate-200 rounded-2xl overflow-hidden transition-all duration-200 hover:-translate-y-0.5 hover:border-blue-400 hover:shadow-lg hover:shadow-blue-500/10"
                      >
                        {/* Accent bar */}
                        <div className="absolute top-0 left-0 right-0 h-0.5 bg-gradient-to-r from-blue-500 to-violet-500 opacity-0 group-hover:opacity-100 transition-opacity" />

                        {/* Photo */}
                        <div className="w-[76px] h-[76px] rounded-[14px] overflow-hidden bg-slate-100 border border-slate-200 group-hover:border-blue-200 flex-shrink-0 transition-colors">
                          <img
                            src={p.url_foto}
                            alt={p.nome}
                            loading="lazy"
                            className="w-full h-full object-cover"
                          />
                        </div>

                        {/* Info */}
                        <div className="flex-1 min-w-0">
                          <p className="font-semibold text-[15px] text-slate-800 leading-snug truncate mb-2">
                            {p.nome}
                          </p>
                          <div className="flex items-center gap-1.5 flex-wrap">
                            <span className="font-mono text-[11px] font-semibold text-blue-600 bg-blue-50 px-2 py-0.5 rounded-md border border-blue-100">
                              {p.partido_sigla}
                            </span>
                            <span className="font-mono inline-flex items-center gap-1 text-[11px] text-slate-500 bg-slate-100 px-2 py-0.5 rounded-md">
                              <MapPin size={9} />
                              {p.uf}
                            </span>
                          </div>
                        </div>

                        {/* Arrow */}
                        <ChevronRight
                          size={15}
                          className="flex-shrink-0 text-slate-300 group-hover:text-blue-400 transition-colors"
                        />
                      </Link>
                    </li>
                  ))}
                </ul>
              )}
            </>
          )}

        </div>
      </main>
    </div>
  )
}