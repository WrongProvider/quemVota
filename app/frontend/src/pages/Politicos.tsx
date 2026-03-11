import { useSearchParams, Link } from "react-router-dom"
import { useState, useEffect, useRef, useMemo } from "react"
import { useDebounce } from "../hooks/useDebounce"
import {
  usePoliticosInfinite,
  selectAllPoliticos,
  POLITICOS_PAGE_SIZE,
} from "../hooks/usePoliticosInfinite"
import { useSeo } from "../hooks/useSeo"
import Header from "../components/Header"
import {
  Search,
  SlidersHorizontal,
  Users,
  MapPin,
  ChevronRight,
  X,
  Loader2,
} from "lucide-react"

const UFs = [
  "AC","AL","AM","AP","BA","CE","DF","ES","GO","MA",
  "MG","MS","MT","PA","PB","PE","PI","PR","RJ","RN",
  "RO","RR","RS","SC","SE","SP","TO",
]

const Partidos = [
  "REPUBLICANOS","SOLIDARIEDADE","UNIÃO","PCdoB","PDT","PL","PODE",
  "PP","PRD","PSB","PSD","PSDB","PSOL","PT","PV","REDE","AVANTE",
  "CIDADANIA","MDB","NOVO",
]

const PATH_FOTOS = "/fotos_politicos/"

export default function Politicos() {
  const [searchParams] = useSearchParams()
  const initialQ = searchParams.get("q") || ""

  const [search, setSearch]               = useState(initialQ)
  const [selectedUF, setSelectedUF]       = useState("")
  const [selectedPartido, setSelectedPartido] = useState("")
  const [showFilters, setShowFilters]     = useState(false)
  const debouncedSearch = useDebounce(search, 400)

  useSeo({
    title: "Parlamentares — Deputados Federais | quemvota",
    description:
      "Pesquise e filtre todos os deputados federais em exercício. Veja presença, gastos, votações e score de performance de cada parlamentar.",
    url: "https://www.quemvota.com.br/politicos",
    keywords: "lista de deputados, parlamentares brasileiros, câmara dos deputados, deputado federal",
  })

  const sentinelRef = useRef<HTMLDivElement>(null)

  const {
    data,
    isLoading,
    isError,
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
    fuzzyItems,
    isFuzzyLoading,
  } = usePoliticosInfinite({ q: debouncedSearch, uf: selectedUF, partido: selectedPartido })

  // Usa fuzzy quando há busca ativa, paginado quando não há
  const allPoliticos = useMemo(
    () => selectAllPoliticos(data, fuzzyItems, debouncedSearch),
    [data, fuzzyItems, debouncedSearch],
  )

  const hasActiveFilters = !!(search || selectedUF || selectedPartido)

  // Infinite scroll só faz sentido sem busca ativa (busca fuzzy já retorna tudo)
  const shouldInfiniteScroll = !debouncedSearch

  useEffect(() => {
    if (!shouldInfiniteScroll) return
    const el = sentinelRef.current
    if (!el) return
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting && hasNextPage && !isFetchingNextPage) fetchNextPage()
      },
      { rootMargin: "300px" },
    )
    observer.observe(el)
    return () => observer.disconnect()
  }, [hasNextPage, isFetchingNextPage, fetchNextPage, shouldInfiniteScroll])

  function clearFilters() {
    setSearch("")
    setSelectedUF("")
    setSelectedPartido("")
  }

  const showLoading = debouncedSearch ? isFuzzyLoading : isLoading

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
            Parlamentares
          </h1>
          <p className="text-slate-500 text-sm">
            Explore os dados de desempenho, gastos e discursos dos deputados federais.
          </p>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-6 py-6 pb-16">
        <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">

          {/* ── Barra de busca e filtros ── */}
          <div className="px-5 py-4 border-b border-slate-100 bg-slate-50/50">
            <div className="flex gap-3 items-center">
              <div className="relative flex-1">
                <Search
                  size={14}
                  className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400"
                />
                <input
                  type="text"
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  placeholder="Buscar por nome... (ex: Nic, Joao, Mara)"
                  className="w-full pl-9 pr-3 py-2 text-sm border border-slate-200 rounded-lg bg-white focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-400 transition-all text-slate-800 placeholder-slate-400"
                />
              </div>

              <button
                onClick={() => setShowFilters((v) => !v)}
                className={`flex items-center gap-2 px-4 py-2 border rounded-lg text-sm font-medium flex-shrink-0 transition-all ${
                  showFilters
                    ? "border-blue-400 bg-blue-50 text-blue-600"
                    : "border-slate-200 bg-white text-slate-500 hover:border-blue-400 hover:text-blue-500"
                }`}
              >
                <SlidersHorizontal size={14} />
                Filtrar
                {(selectedUF || selectedPartido) && (
                  <span className="flex items-center justify-center w-4 h-4 rounded-full bg-blue-600 text-white text-[10px] font-bold leading-none">
                    {[selectedUF, selectedPartido].filter(Boolean).length}
                  </span>
                )}
              </button>

              {/* Contador */}
              {!showLoading && allPoliticos.length > 0 && (
                <div className="flex items-center gap-1.5 px-3 py-2 bg-white border border-slate-200 rounded-lg flex-shrink-0">
                  <Users size={13} className="text-blue-500" />
                  <span className="font-mono font-semibold text-sm text-slate-700">
                    {allPoliticos.length}
                  </span>
                  <span className="text-xs text-slate-400 hidden sm:inline">parlamentares</span>
                </div>
              )}
            </div>

            {/* ── Painel de filtros ── */}
            {showFilters && (
              <div className="mt-4 space-y-4">
                <div>
                  <div className="flex items-center gap-1.5 mb-2">
                    <MapPin size={12} className="text-slate-400" />
                    <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wide">
                      Estado (UF)
                    </span>
                  </div>
                  <div className="flex flex-wrap gap-1.5">
                    {UFs.map((uf) => (
                      <button
                        key={uf}
                        onClick={() => setSelectedUF(selectedUF === uf ? "" : uf)}
                        className={`px-2.5 py-1 rounded-lg border text-xs font-mono transition-all ${
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

                <div>
                  <div className="flex items-center gap-1.5 mb-2">
                    <Users size={12} className="text-slate-400" />
                    <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wide">
                      Partido
                    </span>
                  </div>
                  <div className="flex flex-wrap gap-1.5">
                    {Partidos.map((partido) => (
                      <button
                        key={partido}
                        onClick={() => setSelectedPartido(selectedPartido === partido ? "" : partido)}
                        className={`px-2.5 py-1 rounded-lg border text-xs font-mono transition-all ${
                          selectedPartido === partido
                            ? "border-blue-500 bg-blue-600 text-white"
                            : "border-slate-200 bg-white text-slate-500 hover:border-blue-400 hover:text-blue-600 hover:bg-blue-50"
                        }`}
                      >
                        {partido}
                      </button>
                    ))}
                  </div>
                </div>
              </div>
            )}

            {/* ── Filtros ativos ── */}
            {hasActiveFilters && (
              <div className="flex items-center gap-2 mt-3 flex-wrap">
                <span className="text-[11px] text-slate-400">Ativos:</span>
                {search && (
                  <span className="inline-flex items-center gap-1.5 px-2 py-0.5 bg-blue-50 text-blue-700 text-xs font-medium rounded-full border border-blue-100">
                    "{search}"
                    <button onClick={() => setSearch("")} className="opacity-60 hover:opacity-100">
                      <X size={10} />
                    </button>
                  </span>
                )}
                {selectedUF && (
                  <span className="inline-flex items-center gap-1.5 px-2 py-0.5 bg-blue-50 text-blue-700 text-xs font-mono font-medium rounded-full border border-blue-100">
                    {selectedUF}
                    <button onClick={() => setSelectedUF("")} className="opacity-60 hover:opacity-100">
                      <X size={10} />
                    </button>
                  </span>
                )}
                {selectedPartido && (
                  <span className="inline-flex items-center gap-1.5 px-2 py-0.5 bg-blue-50 text-blue-700 text-xs font-mono font-medium rounded-full border border-blue-100">
                    {selectedPartido}
                    <button onClick={() => setSelectedPartido("")} className="opacity-60 hover:opacity-100">
                      <X size={10} />
                    </button>
                  </span>
                )}
                <button
                  onClick={clearFilters}
                  className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-slate-100 text-slate-500 text-xs hover:bg-red-50 hover:text-red-500 transition-colors"
                >
                  <X size={9} /> Limpar
                </button>
              </div>
            )}
          </div>

          {/* ── Estado de erro ── */}
          {isError && (
            <div className="flex flex-col items-center justify-center py-20 text-center text-slate-400">
              <span className="text-3xl mb-3">⚠️</span>
              <p className="text-sm font-semibold text-slate-600">Erro ao carregar dados</p>
              <p className="text-xs mt-1">Tente novamente em alguns instantes.</p>
            </div>
          )}

          {/* ── Skeleton ── */}
          {showLoading && (
            <div className="grid gap-px sm:grid-cols-2 lg:grid-cols-3">
              {Array.from({ length: POLITICOS_PAGE_SIZE }).map((_, i) => (
                <div
                  key={i}
                  className="px-5 py-4 flex items-center gap-4 animate-pulse border-b border-slate-100 last:border-0"
                >
                  <div className="w-[60px] h-[60px] rounded-xl bg-slate-200 flex-shrink-0" />
                  <div className="flex-1 space-y-2">
                    <div className="h-3 bg-slate-200 rounded w-3/4" />
                    <div className="h-2.5 bg-slate-200 rounded w-1/2" />
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* ── Grid de parlamentares ── */}
          {!showLoading && !isError && (
            <>
              {allPoliticos.length === 0 ? (
                <div className="flex flex-col items-center justify-center py-20 text-center text-slate-400">
                  <Users size={36} className="mb-3 opacity-30" />
                  <p className="text-sm font-semibold text-slate-600">Nenhum parlamentar encontrado</p>
                  <p className="text-xs mt-1">Tente ajustar os filtros de busca.</p>
                  <button
                    onClick={clearFilters}
                    className="inline-flex items-center gap-1 mt-4 px-3 py-1.5 rounded-full bg-slate-100 text-slate-500 text-xs hover:bg-red-50 hover:text-red-500 transition-colors"
                  >
                    <X size={10} /> Limpar filtros
                  </button>
                </div>
              ) : (
                <div className="divide-y divide-slate-100 sm:grid sm:grid-cols-2 sm:divide-y-0 lg:grid-cols-3">
                  {allPoliticos.map((p) => (
                    <Link
                      key={p.id}
                      to={`/politicos/${p.slug ?? p.id}`}
                      className="group flex items-center gap-4 px-5 py-4 hover:bg-slate-50 transition-colors border-b border-slate-100 sm:border-b sm:border-r last:border-0 no-underline"
                    >
                      {/* Foto */}
                      <div className="w-[56px] h-[56px] rounded-xl overflow-hidden bg-slate-100 border border-slate-200 group-hover:border-blue-200 flex-shrink-0 transition-colors">
                        <img
                          src={`${PATH_FOTOS}${p.id}.jpg`}
                          alt={p.nome}
                          loading="lazy"
                          className="w-full h-full object-cover"
                        />
                      </div>

                      {/* Info */}
                      <div className="flex-1 min-w-0">
                        <p className="font-semibold text-sm text-slate-800 leading-snug truncate mb-1.5">
                          {p.nome}
                        </p>
                        <div className="flex items-center gap-1.5 flex-wrap">
                          <span className="font-mono text-[11px] font-semibold text-blue-600 bg-blue-50 px-1.5 py-0.5 rounded border border-blue-100">
                            {p.partido_sigla}
                          </span>
                          <span className="font-mono inline-flex items-center gap-1 text-[11px] text-slate-500 bg-slate-100 px-1.5 py-0.5 rounded">
                            <MapPin size={9} />
                            {p.uf}
                          </span>
                        </div>
                      </div>

                      <ChevronRight
                        size={14}
                        className="flex-shrink-0 text-slate-300 group-hover:text-blue-400 transition-colors"
                      />
                    </Link>
                  ))}
                </div>
              )}

              {/* ── Sentinel + estados do scroll (apenas sem busca) ── */}
              {shouldInfiniteScroll && (
                <div ref={sentinelRef} className="border-t border-slate-100">
                  {isFetchingNextPage && (
                    <div className="flex items-center justify-center gap-2 py-5 text-sm text-slate-400">
                      <Loader2 size={15} className="animate-spin text-blue-400" />
                      <span>Carregando mais parlamentares...</span>
                    </div>
                  )}
                  {!hasNextPage && allPoliticos.length > 0 && (
                    <p className="text-center text-xs text-slate-300 py-5 font-mono">
                      ✓ Todos os {allPoliticos.length} parlamentares carregados
                    </p>
                  )}
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  )
}