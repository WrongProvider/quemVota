/**
 * ComparadorLanding.tsx — Pouso e Seletor do Comparador de Parlamentares.
 *
 * Permite ao cidadão pesquisar e selecionar dois deputados federais simultaneamente
 * para confrontar seus históricos de votos nominais, despesas de gabinete e scores.
 *
 * Princípio da Neutralidade Factual (AGENTS.md):
 *  - Apresentação estritamente quantitativa e neutra.
 *  - Explicação transparente da fórmula de cálculo de alinhamento.
 */

import { useState, useRef } from "react"
import { useNavigate, Link } from "react-router-dom"
import Header from "../components/Header"
import { useSeo } from "../hooks/useSeo"
import { usePoliticos } from "../hooks/usePoliticos"
import { useDebounce } from "../hooks/useDebounce"
import { nomeParaSlug } from "../api/politicos.api"
import type { Politico } from "../api/politicos.api"
import {
  ArrowLeftRight,
  Search,
  Scale,
  MapPin,
  X,
  Loader2,
  Sparkles,
  ChevronRight,
  CheckCircle2,
  ShieldCheck,
} from "lucide-react"

const PATH_FOTOS = "/fotos_politicos/"

interface SugestaoPar {
  p1Nome: string
  p1Slug: string
  p1Partido: string
  p1Uf: string
  p2Nome: string
  p2Slug: string
  p2Partido: string
  p2Uf: string
  rotulo: string
}

const SUGESTOES_COMPARACAO: SugestaoPar[] = [
  {
    p1Nome: "Arthur Lira",
    p1Slug: "arthur-lira",
    p1Partido: "PP",
    p1Uf: "AL",
    p2Nome: "Erika Hilton",
    p2Slug: "erika-hilton",
    p2Partido: "PSOL",
    p2Uf: "SP",
    rotulo: "Espectros políticos distintos",
  },
  {
    p1Nome: "Tabata Amaral",
    p1Slug: "tabata-amaral",
    p1Partido: "PSB",
    p1Uf: "SP",
    p2Nome: "Kim Kataguiri",
    p2Slug: "kim-kataguiri",
    p2Partido: "UNIÃO",
    p2Uf: "SP",
    rotulo: "Bancada de São Paulo",
  },
  {
    p1Nome: "Guilherme Boulos",
    p1Slug: "guilherme-boulos",
    p1Partido: "PSOL",
    p1Uf: "SP",
    p2Nome: "Eduardo Bolsonaro",
    p2Slug: "eduardo-bolsonaro",
    p2Partido: "PL",
    p2Uf: "SP",
    rotulo: "Mesma UF, atuações contrastantes",
  },
  {
    p1Nome: "Baleia Rossi",
    p1Slug: "baleia-rossi",
    p1Partido: "MDB",
    p1Uf: "SP",
    p2Nome: "Gleisi Hoffmann",
    p2Slug: "gleisi-hoffmann",
    p2Partido: "PT",
    p2Uf: "PR",
    rotulo: "Lideranças partidárias nacionais",
  },
]

export default function ComparadorLanding() {
  const navigate = useNavigate()
  useSeo({
    title: "Comparador de Parlamentares — Confronto de Votos e Desempenho | quemvota",
    description:
      "Compare lado a lado o histórico de votações nominais, fidelidade partidária, uso de verbas e scores de desempenho de dois deputados federais.",
    url: typeof window !== "undefined" ? window.location.href : "",
    keywords: "comparador de politicos, confronto de votos, deputados federais, comparacao parlamentar, camara dos deputados",
    type: "website",
  })

  const [politico1, setPolitico1] = useState<Politico | null>(null)
  const [politico2, setPolitico2] = useState<Politico | null>(null)

  const [query1, setQuery1] = useState("")
  const [query2, setQuery2] = useState("")

  const debouncedQuery1 = useDebounce(query1, 350)
  const debouncedQuery2 = useDebounce(query2, 350)

  const { data: resultados1, isFetching: buscando1 } = usePoliticos(
    debouncedQuery1.trim().length >= 2 ? { q: debouncedQuery1.trim(), limit: 6 } : undefined,
  )

  const { data: resultados2, isFetching: buscando2 } = usePoliticos(
    debouncedQuery2.trim().length >= 2 ? { q: debouncedQuery2.trim(), limit: 6 } : undefined,
  )

  const input1Ref = useRef<HTMLInputElement>(null)
  const input2Ref = useRef<HTMLInputElement>(null)

  const listaFiltrada1 = (resultados1 ?? []).filter((p) => p.id !== politico2?.id)
  const listaFiltrada2 = (resultados2 ?? []).filter((p) => p.id !== politico1?.id)

  const inverterOrdem = () => {
    setPolitico1(politico2)
    setPolitico2(politico1)
  }

  const executarComparacao = () => {
    if (!politico1 || !politico2) return
    const slug1 = politico1.slug || nomeParaSlug(politico1.nome) || String(politico1.id)
    const slug2 = politico2.slug || nomeParaSlug(politico2.nome) || String(politico2.id)
    navigate(`/comparar/${slug1}/${slug2}`)
  }

  return (
    <div className="min-h-screen bg-[#f8f9fb] flex flex-col">
      <Header />

      <main className="flex-1 pt-24 pb-16 px-4 md:px-6">
        <div className="max-w-5xl mx-auto space-y-10">
          {/* ── HERO HEADER ── */}
          <div className="text-center space-y-4 max-w-3xl mx-auto">
            <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-blue-50 border border-blue-100 text-blue-700 text-xs font-semibold shadow-xs">
              <Scale size={14} className="text-blue-600" />
              <span>Grafo de Votações Nominais</span>
            </div>

            <h1 className="text-3xl sm:text-4xl md:text-5xl font-bold text-slate-900 tracking-tight font-serif">
              Comparador de Parlamentares
            </h1>

            <p className="text-sm sm:text-base text-slate-600 leading-relaxed">
              Cruze o histórico oficial de votações nominais, desempenho parlamentar,
              assiduidade e gastos públicos entre dois deputados federais da 57ª Legislatura.
            </p>
          </div>

          {/* ── CARD SELETOR DUPLO ── */}
          <div
            data-testid="seletor-duplo-comparacao"
            className="bg-white rounded-3xl border border-slate-200/90 shadow-xl p-6 sm:p-8 space-y-8 relative overflow-hidden"
          >
            <div className="grid grid-cols-1 lg:grid-cols-[1fr_auto_1fr] gap-6 items-center">
              {/* ════ SLOT 1: 1º PARLAMENTAR ════ */}
              <div
                data-testid="slot-politico-1"
                className="bg-slate-50/70 rounded-2xl border border-slate-200/70 p-5 space-y-3 relative"
              >
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold uppercase tracking-wider text-slate-500">
                    1º Parlamentar
                  </span>
                  {politico1 && (
                    <button
                      onClick={() => {
                        setPolitico1(null)
                        setQuery1("")
                        setTimeout(() => input1Ref.current?.focus(), 80)
                      }}
                      className="text-xs font-medium text-slate-400 hover:text-red-500 transition-colors flex items-center gap-1"
                      title="Remover seleção"
                    >
                      <X size={13} />
                      Trocar
                    </button>
                  )}
                </div>

                {politico1 ? (
                  /* Parlamentar 1 Selecionado */
                  <div className="flex items-center gap-4 bg-white rounded-xl border border-slate-200 p-3.5 shadow-xs">
                    <div className="w-14 h-14 rounded-xl overflow-hidden flex-shrink-0 bg-slate-100 ring-2 ring-blue-500/20">
                      <img
                        src={`${PATH_FOTOS}${politico1.id}.jpg`}
                        alt={politico1.nome}
                        onError={(e) => {
                          ;(e.target as HTMLImageElement).src = `https://ui-avatars.com/api/?name=${encodeURIComponent(
                            politico1.nome,
                          )}&background=e2e8f0&color=64748b&size=100`
                        }}
                        className="w-full h-full object-cover"
                      />
                    </div>
                    <div className="min-w-0 flex-1">
                      <p className="font-bold text-slate-900 text-sm sm:text-base truncate">
                        {politico1.nome}
                      </p>
                      <div className="flex items-center gap-2 text-xs text-slate-500 mt-1">
                        {politico1.sigla_partido && (
                          <span className="font-semibold text-slate-700 bg-slate-100 px-2 py-0.5 rounded-md">
                            {politico1.sigla_partido}
                          </span>
                        )}
                        {politico1.sigla_uf && (
                          <span className="flex items-center gap-0.5 text-slate-500">
                            <MapPin size={12} />
                            {politico1.sigla_uf}
                          </span>
                        )}
                      </div>
                    </div>
                  </div>
                ) : (
                  /* Busca do Parlamentar 1 */
                  <div className="space-y-2">
                    <div className="relative">
                      <Search
                        size={15}
                        className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400 pointer-events-none"
                      />
                      <input
                        ref={input1Ref}
                        type="text"
                        data-testid="input-busca-politico-1"
                        value={query1}
                        onChange={(e) => setQuery1(e.target.value)}
                        placeholder="Busque o 1º parlamentar (ex: Arthur Lira)..."
                        className="w-full pl-10 pr-9 py-2.5 text-sm bg-white border border-slate-200 rounded-xl text-slate-800 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500/30 focus:border-blue-500 transition shadow-xs"
                      />
                      {buscando1 && (
                        <Loader2
                          size={15}
                          className="absolute right-3.5 top-1/2 -translate-y-1/2 text-blue-500 animate-spin"
                        />
                      )}
                    </div>

                    {/* Lista suspensa de resultados 1 */}
                    {debouncedQuery1.trim().length >= 2 && !buscando1 && (
                      <div className="bg-white border border-slate-200 rounded-xl shadow-lg max-h-56 overflow-y-auto divide-y divide-slate-100">
                        {listaFiltrada1.length === 0 ? (
                          <div className="p-3 text-center text-xs text-slate-400">
                            Nenhum parlamentar encontrado.
                          </div>
                        ) : (
                          listaFiltrada1.map((p) => (
                            <button
                              key={p.id}
                              type="button"
                              onClick={() => {
                                setPolitico1(p)
                                setQuery1("")
                              }}
                              className="w-full flex items-center gap-3 px-3 py-2 text-left hover:bg-blue-50/70 transition-colors"
                            >
                              <div className="w-8 h-8 rounded-lg overflow-hidden bg-slate-100 flex-shrink-0">
                                <img
                                  src={`${PATH_FOTOS}${p.id}.jpg`}
                                  alt={p.nome}
                                  onError={(e) => {
                                    ;(e.target as HTMLImageElement).src = `https://ui-avatars.com/api/?name=${encodeURIComponent(
                                      p.nome,
                                    )}&background=e2e8f0&color=64748b&size=64`
                                  }}
                                  className="w-full h-full object-cover"
                                />
                              </div>
                              <div className="min-w-0 flex-1">
                                <p className="text-xs font-semibold text-slate-800 truncate">
                                  {p.nome}
                                </p>
                                <p className="text-[11px] text-slate-400">
                                  {p.sigla_partido || "—"} • {p.sigla_uf || "—"}
                                </p>
                              </div>
                            </button>
                          ))
                        )}
                      </div>
                    )}
                  </div>
                )}
              </div>

              {/* ════ BOTÃO INVERTER / DIVISOR CENTRAL ════ */}
              <div className="flex flex-col items-center justify-center">
                <button
                  type="button"
                  data-testid="btn-inverter-politicos"
                  onClick={inverterOrdem}
                  disabled={!politico1 && !politico2}
                  className="w-11 h-11 rounded-2xl bg-white border border-slate-200 shadow-sm flex items-center justify-center text-slate-600 hover:text-blue-600 hover:border-blue-200 hover:bg-blue-50 transition-all disabled:opacity-40 disabled:pointer-events-none"
                  title="Inverter ordem dos parlamentares"
                >
                  <ArrowLeftRight size={18} />
                </button>
                <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 mt-1">
                  vs
                </span>
              </div>

              {/* ════ SLOT 2: 2º PARLAMENTAR ════ */}
              <div
                data-testid="slot-politico-2"
                className="bg-slate-50/70 rounded-2xl border border-slate-200/70 p-5 space-y-3 relative"
              >
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold uppercase tracking-wider text-slate-500">
                    2º Parlamentar
                  </span>
                  {politico2 && (
                    <button
                      onClick={() => {
                        setPolitico2(null)
                        setQuery2("")
                        setTimeout(() => input2Ref.current?.focus(), 80)
                      }}
                      className="text-xs font-medium text-slate-400 hover:text-red-500 transition-colors flex items-center gap-1"
                      title="Remover seleção"
                    >
                      <X size={13} />
                      Trocar
                    </button>
                  )}
                </div>

                {politico2 ? (
                  /* Parlamentar 2 Selecionado */
                  <div className="flex items-center gap-4 bg-white rounded-xl border border-slate-200 p-3.5 shadow-xs">
                    <div className="w-14 h-14 rounded-xl overflow-hidden flex-shrink-0 bg-slate-100 ring-2 ring-violet-500/20">
                      <img
                        src={`${PATH_FOTOS}${politico2.id}.jpg`}
                        alt={politico2.nome}
                        onError={(e) => {
                          ;(e.target as HTMLImageElement).src = `https://ui-avatars.com/api/?name=${encodeURIComponent(
                            politico2.nome,
                          )}&background=e2e8f0&color=64748b&size=100`
                        }}
                        className="w-full h-full object-cover"
                      />
                    </div>
                    <div className="min-w-0 flex-1">
                      <p className="font-bold text-slate-900 text-sm sm:text-base truncate">
                        {politico2.nome}
                      </p>
                      <div className="flex items-center gap-2 text-xs text-slate-500 mt-1">
                        {politico2.sigla_partido && (
                          <span className="font-semibold text-slate-700 bg-slate-100 px-2 py-0.5 rounded-md">
                            {politico2.sigla_partido}
                          </span>
                        )}
                        {politico2.sigla_uf && (
                          <span className="flex items-center gap-0.5 text-slate-500">
                            <MapPin size={12} />
                            {politico2.sigla_uf}
                          </span>
                        )}
                      </div>
                    </div>
                  </div>
                ) : (
                  /* Busca do Parlamentar 2 */
                  <div className="space-y-2">
                    <div className="relative">
                      <Search
                        size={15}
                        className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400 pointer-events-none"
                      />
                      <input
                        ref={input2Ref}
                        type="text"
                        data-testid="input-busca-politico-2"
                        value={query2}
                        onChange={(e) => setQuery2(e.target.value)}
                        placeholder="Busque o 2º parlamentar (ex: Erika Hilton)..."
                        className="w-full pl-10 pr-9 py-2.5 text-sm bg-white border border-slate-200 rounded-xl text-slate-800 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-violet-500/30 focus:border-violet-500 transition shadow-xs"
                      />
                      {buscando2 && (
                        <Loader2
                          size={15}
                          className="absolute right-3.5 top-1/2 -translate-y-1/2 text-violet-500 animate-spin"
                        />
                      )}
                    </div>

                    {/* Lista suspensa de resultados 2 */}
                    {debouncedQuery2.trim().length >= 2 && !buscando2 && (
                      <div className="bg-white border border-slate-200 rounded-xl shadow-lg max-h-56 overflow-y-auto divide-y divide-slate-100">
                        {listaFiltrada2.length === 0 ? (
                          <div className="p-3 text-center text-xs text-slate-400">
                            Nenhum parlamentar encontrado.
                          </div>
                        ) : (
                          listaFiltrada2.map((p) => (
                            <button
                              key={p.id}
                              type="button"
                              onClick={() => {
                                setPolitico2(p)
                                setQuery2("")
                              }}
                              className="w-full flex items-center gap-3 px-3 py-2 text-left hover:bg-violet-50/70 transition-colors"
                            >
                              <div className="w-8 h-8 rounded-lg overflow-hidden bg-slate-100 flex-shrink-0">
                                <img
                                  src={`${PATH_FOTOS}${p.id}.jpg`}
                                  alt={p.nome}
                                  onError={(e) => {
                                    ;(e.target as HTMLImageElement).src = `https://ui-avatars.com/api/?name=${encodeURIComponent(
                                      p.nome,
                                    )}&background=e2e8f0&color=64748b&size=64`
                                  }}
                                  className="w-full h-full object-cover"
                                />
                              </div>
                              <div className="min-w-0 flex-1">
                                <p className="text-xs font-semibold text-slate-800 truncate">
                                  {p.nome}
                                </p>
                                <p className="text-[11px] text-slate-400">
                                  {p.sigla_partido || "—"} • {p.sigla_uf || "—"}
                                </p>
                              </div>
                            </button>
                          ))
                        )}
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>

            {/* ════ CTA BOTÃO DE COMPARAÇÃO ════ */}
            <div className="pt-2 flex flex-col sm:flex-row items-center justify-between gap-4 border-t border-slate-100">
              <p className="text-xs text-slate-400 text-center sm:text-left">
                {politico1 && politico2 ? (
                  <span className="text-emerald-600 font-medium flex items-center gap-1.5 justify-center sm:justify-start">
                    <CheckCircle2 size={14} />
                    Pronto para confrontar o histórico oficial de votações
                  </span>
                ) : (
                  "Selecione ambos os deputados para liberar a análise comparativa detalhada."
                )}
              </p>

              <button
                type="button"
                data-testid="btn-executar-comparacao"
                disabled={!politico1 || !politico2}
                onClick={executarComparacao}
                className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-6 py-3.5 rounded-xl bg-blue-600 hover:bg-blue-700 text-white font-semibold text-sm shadow-md hover:shadow-lg transition-all disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:bg-blue-600"
              >
                <span>Comparar Votações e Desempenho</span>
                <ChevronRight size={16} />
              </button>
            </div>
          </div>

          {/* ── SUGESTÕES RÁPIDAS DE COMPARAÇÃO ── */}
          <div className="space-y-4">
            <div className="flex items-center gap-2">
              <Sparkles size={16} className="text-amber-500" />
              <h2 className="text-base font-bold text-slate-800">
                Sugestões de Comparações Frequentes
              </h2>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {SUGESTOES_COMPARACAO.map((par, i) => (
                <Link
                  key={i}
                  to={`/comparar/${par.p1Slug}/${par.p2Slug}`}
                  className="group bg-white rounded-2xl border border-slate-200/80 p-4 hover:border-blue-300 hover:shadow-md transition-all flex items-center justify-between gap-3"
                >
                  <div className="min-w-0 space-y-1.5">
                    <span className="text-[10px] font-semibold text-blue-600 bg-blue-50 px-2 py-0.5 rounded-full inline-block">
                      {par.rotulo}
                    </span>
                    <p className="text-sm font-bold text-slate-800 group-hover:text-blue-600 transition-colors truncate">
                      {par.p1Nome} ({par.p1Partido}-{par.p1Uf}){" "}
                      <span className="text-slate-300 font-normal">vs</span>{" "}
                      {par.p2Nome} ({par.p2Partido}-{par.p2Uf})
                    </p>
                  </div>
                  <ChevronRight
                    size={16}
                    className="text-slate-400 group-hover:text-blue-600 group-hover:translate-x-0.5 transition-all flex-shrink-0"
                  />
                </Link>
              ))}
            </div>
          </div>

          {/* ── CARD METODOLOGIA FACTUAL E TRANSPARÊNCIA ── */}
          <div className="bg-white rounded-2xl border border-slate-200/80 p-6 space-y-4 shadow-xs">
            <div className="flex items-center gap-2.5">
              <div className="p-2 rounded-xl bg-blue-50 text-blue-600">
                <ShieldCheck size={18} />
              </div>
              <h3 className="text-sm font-bold text-slate-800">
                Metodologia Factual e Critérios Estatísticos
              </h3>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs text-slate-600 leading-relaxed">
              <div className="space-y-1.5 p-3 rounded-xl bg-slate-50 border border-slate-100">
                <p className="font-semibold text-slate-800">Fórmula de Alinhamento</p>
                <p>
                  Percentual calculado como{" "}
                  <code className="bg-slate-200/60 px-1 py-0.5 rounded text-[11px] font-mono">
                    (Votos Sim/Sim + Não/Não + Obs/Obs) / Total Comum
                  </code>
                  . Avalia estritamente votações em que ambos votaram no plenário.
                </p>
              </div>

              <div className="space-y-1.5 p-3 rounded-xl bg-slate-50 border border-slate-100">
                <p className="font-semibold text-slate-800">Neutralidade Descritiva</p>
                <p>
                  A plataforma não atribui juízos de valor nem classifica votos como positivos
                  ou negativos. Apresenta-se unicamente o cruzamento objetivo das atas oficiais.
                </p>
              </div>

              <div className="space-y-1.5 p-3 rounded-xl bg-slate-50 border border-slate-100">
                <p className="font-semibold text-slate-800">Fontes Oficiais</p>
                <p>
                  Todas as proposições, ementas e votos nominais são indexados a partir dos
                  Dados Abertos da Câmara dos Deputados e rastreáveis pelo identificador oficial da votação.
                </p>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  )
}
