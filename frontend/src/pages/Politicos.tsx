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
  AlertCircle,
  User,
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

function PoliticoAvatar({ id, nome }: { id: number | string; nome: string }) {
  const [hasError, setHasError] = useState(false)

  if (hasError) {
    const initials = nome
      .split(" ")
      .slice(0, 2)
      .map((n) => n[0])
      .join("")
      .toUpperCase()

    return (
      <div className="w-full h-full flex items-center justify-center bg-slate-100 text-slate-500 font-mono text-xs font-bold">
        {initials || <User size={20} />}
      </div>
    )
  }

  return (
    <img
      src={`${PATH_FOTOS}${id}.jpg`}
      alt={nome}
      loading="lazy"
      onError={() => setHasError(true)}
      className="w-full h-full object-cover"
    />
  )
}

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
      "Pesquise e filtre todos os deputados federais em exercício. Veja presença, gastos, votações e indicadores de mandato de cada parlamentar.",
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
    <div className="min-h-screen bg-canvas">
      <Header />

      {/* ── Cabeçalho da página ── */}
      <div className="bg-white border-b border-slate-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 py-6 sm:py-8 pt-20 sm:pt-24">
          <p className="text-xs font-semibold tracking-wider uppercase text-blue-700 mb-1">
            Câmara dos Deputados
          </p>
          <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-slate-900 mb-1">
            Diretório de Parlamentares
          </h1>
          <p className="text-slate-600 text-xs sm:text-sm">
            Consulte o registro factual de atuação, gastos de cota e presenças dos 513 deputados federais.
          </p>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 py-4 sm:py-6 pb-16">
        <div className="bg-white rounded-xl border border-slate-200/90 shadow-xs overflow-hidden">

          {/* ── Barra de busca e filtros ── */}
          <div className="px-3.5 sm:px-5 py-3 sm:py-3.5 border-b border-slate-200/80 bg-slate-50/40">
            <div className="flex flex-wrap sm:flex-nowrap gap-2 sm:gap-3 items-center">
              <div className="relative flex-1 min-w-[180px] sm:min-w-0">
                <Search
                  size={14}
                  className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400"
                />
                <input
                  type="text"
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  placeholder="Buscar por nome do deputado..."
                  className="w-full pl-9 pr-3 py-1.5 text-base sm:text-sm border border-slate-200 rounded-lg bg-white focus:outline-none focus:ring-2 focus:ring-slate-900/10 focus:border-slate-400 transition-all text-slate-800 placeholder-slate-400 min-w-0"
                />
              </div>

              <div className="flex items-center gap-2 flex-shrink-0 ml-auto sm:ml-0">
                <button
                  onClick={() => setShowFilters((v) => !v)}
                  className={`flex items-center gap-1.5 sm:gap-2 px-3 sm:px-3.5 py-1.5 border rounded-lg text-xs sm:text-sm font-medium flex-shrink-0 transition-all cursor-pointer ${
                    showFilters
                      ? "border-slate-900 bg-slate-900 text-white"
                      : "border-slate-200 bg-white text-slate-700 hover:border-slate-300 hover:bg-slate-50"
                  }`}
                >
                  <SlidersHorizontal size={13} />
                  Filtros
                  {(selectedUF || selectedPartido) && (
                    <span className={`flex items-center justify-center w-4 h-4 rounded-full text-[10px] font-bold leading-none ${
                      showFilters ? "bg-white text-slate-900" : "bg-blue-600 text-white"
                    }`}>
                      {[selectedUF, selectedPartido].filter(Boolean).length}
                    </span>
                  )}
                </button>

                {/* Contador */}
                {!showLoading && allPoliticos.length > 0 && (
                  <div className="flex items-center gap-1.5 px-2.5 sm:px-3 py-1.5 bg-white border border-slate-200 rounded-lg flex-shrink-0">
                    <Users size={13} className="text-slate-500" />
                    <span className="font-mono font-semibold text-xs sm:text-sm text-slate-800 tabular-nums">
                      {allPoliticos.length}
                    </span>
                    <span className="text-xs text-slate-500 hidden sm:inline">registros</span>
                  </div>
                )}
              </div>
            </div>

            {/* ── Painel de filtros ── */}
            {showFilters && (
              <div className="mt-4 pt-3.5 border-t border-slate-200/80 space-y-4">
                <div>
                  <div className="flex items-center gap-1.5 mb-2">
                    <MapPin size={12} className="text-slate-400" />
                    <span className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider">
                      Estado (UF)
                    </span>
                  </div>
                  <div className="flex flex-wrap gap-1.5 max-h-28 sm:max-h-none overflow-y-auto sm:overflow-visible pr-1">
                    {UFs.map((uf) => (
                      <button
                        key={uf}
                        onClick={() => setSelectedUF(selectedUF === uf ? "" : uf)}
                        className={`px-2 py-1 rounded border text-xs font-mono transition-all min-h-[32px] sm:min-h-0 ${
                          selectedUF === uf
                            ? "border-slate-900 bg-slate-900 text-white font-bold"
                            : "border-slate-200 bg-white text-slate-600 hover:border-slate-300 hover:bg-slate-50"
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
                    <span className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider">
                      Partido Político
                    </span>
                  </div>
                  <div className="flex flex-wrap gap-1.5 max-h-32 sm:max-h-none overflow-y-auto sm:overflow-visible pr-1">
                    {Partidos.map((partido) => (
                      <button
                        key={partido}
                        onClick={() => setSelectedPartido(selectedPartido === partido ? "" : partido)}
                        className={`px-2 py-1 rounded border text-xs font-mono transition-all min-h-[32px] sm:min-h-0 ${
                          selectedPartido === partido
                            ? "border-slate-900 bg-slate-900 text-white font-bold"
                            : "border-slate-200 bg-white text-slate-600 hover:border-slate-300 hover:bg-slate-50"
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
                <span className="text-[11px] font-medium text-slate-400">Filtros:</span>
                {search && (
                  <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 bg-slate-100 text-slate-800 text-xs font-medium rounded border border-slate-200">
                    "{search}"
                    <button onClick={() => setSearch("")} className="text-slate-400 hover:text-slate-700">
                      <X size={11} />
                    </button>
                  </span>
                )}
                {selectedUF && (
                  <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 bg-slate-100 text-slate-800 text-xs font-mono font-medium rounded border border-slate-200">
                    UF: {selectedUF}
                    <button onClick={() => setSelectedUF("")} className="text-slate-400 hover:text-slate-700">
                      <X size={11} />
                    </button>
                  </span>
                )}
                {selectedPartido && (
                  <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 bg-slate-100 text-slate-800 text-xs font-mono font-medium rounded border border-slate-200">
                    {selectedPartido}
                    <button onClick={() => setSelectedPartido("")} className="text-slate-400 hover:text-slate-700">
                      <X size={11} />
                    </button>
                  </span>
                )}
                <button
                  onClick={clearFilters}
                  className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded bg-slate-100 text-slate-500 text-xs hover:bg-red-50 hover:text-red-600 transition-colors"
                >
                  <X size={10} /> Limpar
                </button>
              </div>
            )}
          </div>

          {/* ── Estado de erro ── */}
          {isError && (
            <div className="flex flex-col items-center justify-center py-20 text-center text-slate-500">
              <AlertCircle size={32} className="text-red-500 mb-2" />
              <p className="text-sm font-semibold text-slate-800">Falha ao carregar lista de parlamentares</p>
              <p className="text-xs text-slate-400 mt-1">Verifique sua conexão ou tente novamente mais tarde.</p>
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
                  <div className="w-[52px] h-[52px] rounded-lg bg-slate-200 flex-shrink-0" />
                  <div className="flex-1 space-y-2">
                    <div className="h-3.5 bg-slate-200 rounded w-3/4" />
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
                  <p className="text-sm font-semibold text-slate-700">Nenhum parlamentar encontrado</p>
                  <p className="text-xs mt-1">Tente ajustar os termos ou filtros selecionados.</p>
                  <button
                    onClick={clearFilters}
                    className="inline-flex items-center gap-1 mt-4 px-3.5 py-1.5 rounded-lg bg-slate-100 text-slate-600 text-xs font-medium hover:bg-slate-200 transition-colors"
                  >
                    <X size={12} /> Limpar filtros
                  </button>
                </div>
              ) : (
                <div className="divide-y divide-slate-100 sm:grid sm:grid-cols-2 sm:divide-y-0 lg:grid-cols-3">
                  {allPoliticos.map((p) => (
                    <Link
                      key={p.id}
                      to={`/politicos/${p.slug ?? p.id}`}
                      className="group flex items-center gap-3 sm:gap-3.5 px-3.5 sm:px-5 py-3 sm:py-3.5 hover:bg-slate-50/80 transition-colors border-b border-slate-100 sm:border-b sm:border-r last:border-0 no-underline"
                    >
                      {/* Foto */}
                      <div className="w-[50px] h-[50px] rounded-lg overflow-hidden bg-slate-100 border border-slate-200 group-hover:border-slate-300 flex-shrink-0 transition-colors">
                        <PoliticoAvatar id={p.id} nome={p.nome} />
                      </div>

                      {/* Info */}
                      <div className="flex-1 min-w-0">
                        <p className="font-medium text-sm text-slate-900 leading-snug truncate mb-1 group-hover:text-blue-700 transition-colors">
                          {p.nome}
                        </p>
                        <div className="flex items-center gap-1.5 flex-wrap">
                          <span className="font-mono text-[11px] font-semibold text-slate-700 bg-slate-100 px-1.5 py-0.5 rounded border border-slate-200/80">
                            {p.sigla_partido}
                          </span>
                          <span className="font-mono inline-flex items-center gap-0.5 text-[11px] font-medium text-slate-500 bg-slate-100 px-1.5 py-0.5 rounded">
                            <MapPin size={9} className="text-slate-400" />
                            {p.sigla_uf}
                          </span>
                        </div>
                      </div>

                      <ChevronRight
                        size={14}
                        className="flex-shrink-0 text-slate-300 group-hover:text-slate-500 transition-colors"
                      />
                    </Link>
                  ))}
                </div>
              )}

              {/* ── Sentinel + estados do scroll (apenas sem busca) ── */}
              {shouldInfiniteScroll && (
                <div ref={sentinelRef} className="border-t border-slate-100">
                  {isFetchingNextPage && (
                    <div className="flex items-center justify-center gap-2 py-5 text-sm text-slate-500">
                      <Loader2 size={15} className="animate-spin text-slate-600" />
                      <span>Carregando mais parlamentares...</span>
                    </div>
                  )}
                  {!hasNextPage && allPoliticos.length > 0 && (
                    <p className="text-center text-xs text-slate-400 py-5 font-mono">
                      Todos os {allPoliticos.length} parlamentares carregados
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