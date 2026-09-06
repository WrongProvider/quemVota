import Header from "../components/Header"
import { Link, useNavigate } from "react-router-dom"
import { useState } from "react"
import { motion } from "framer-motion"
import {
  Search,
  ArrowRight,
  ShieldCheck,
  Scale,
  TrendingUp,
  BarChart3,
  FileText,
  BookOpen,
  Calendar,
  CheckCircle2,
  XCircle,
  Clock,
  Sparkles,
  Users,
} from "lucide-react"
import { useMaisPesquisados } from "../hooks/useBuscaPopular"
import { useVotacoes } from "../hooks/useProposicoes"
import { useSeo } from "../hooks/useSeo"
import { nomeParaSlug } from "../api/politicos.api"
import type { MaisPesquisado } from "../api/buscaPopular.api"
import type { VotacaoResponse } from "../api/proposicoes.api"

// ── Lista de estados prioritários para filtro rápido no Hero ──
const UFS_DESTAQUE = ["SP", "RJ", "MG", "BA", "RS", "PR", "PE", "CE"]

// ─────────────────────────────────────────────────────────────────────────────
// Skeleton de carregamento para as Fichas Rápidas dos Mais Consultados
// ─────────────────────────────────────────────────────────────────────────────
function FichasSkeleton() {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
      {Array.from({ length: 4 }).map((_, i) => (
        <div
          key={i}
          className="bg-white border border-slate-200/80 rounded-2xl p-4 sm:p-5 flex gap-4 animate-pulse shadow-xs"
        >
          <div className="w-20 h-24 sm:w-24 sm:h-28 rounded-xl bg-slate-200 flex-shrink-0" />
          <div className="flex-1 space-y-2.5 py-1">
            <div className="h-4 w-24 bg-slate-200 rounded" />
            <div className="h-5 w-44 bg-slate-200 rounded" />
            <div className="h-3 w-32 bg-slate-100 rounded" />
            <div className="flex gap-2 pt-2">
              <div className="h-7 w-28 bg-slate-200 rounded-lg" />
              <div className="h-7 w-24 bg-slate-100 rounded-lg" />
            </div>
          </div>
        </div>
      ))}
    </div>
  )
}

/** Formata com fidelidade factual a legislatura e condição do parlamentar */
function formatarLegislaturaCard(politico: MaisPesquisado): string {
  const legIni = politico.id_legislatura_inicial
  const legFim = politico.id_legislatura_final
  const anoIni = politico.ano_inicio
  const anoFim = politico.ano_fim
  const isSuplente = politico.condicao_eleitoral?.toLowerCase() === "suplente"
  const suplenteSuffix = isSuplente ? " · Suplente" : ""

  if (!legFim) {
    return `Deputado(a) Federal${suplenteSuffix}`
  }

  const anosStr = anoIni && anoFim ? ` (${anoIni}–${anoFim})` : ""

  // Ativo na 57ª Legislatura (atual)
  if (legFim === 57) {
    if (!legIni || legIni === 57) {
      return `57ª Legislatura${anosStr || " (2023–2027)"}${suplenteSuffix}`
    }
    return `${legIni}ª a 57ª Legislatura${anosStr}${suplenteSuffix}`
  }

  // Mandato histórico / anterior à 57ª
  if (!legIni || legIni === legFim) {
    return `${legFim}ª Legislatura${anosStr} · Mandato Histórico${suplenteSuffix}`
  }
  return `${legIni}ª a ${legFim}ª Legislatura${anosStr} · Mandato Histórico${suplenteSuffix}`
}

// ─────────────────────────────────────────────────────────────────────────────
// Card Individual de Ficha Rápida (Variação 1C)
// ─────────────────────────────────────────────────────────────────────────────
function FichaDeputadoCard({
  politico,
  rank,
}: {
  politico: MaisPesquisado
  rank: number
}) {
  const [fotoComErro, setFotoComErro] = useState(false)
  const slug = politico.slug || nomeParaSlug(politico.nome) || String(politico.politico_id)

  const siglaPartido = politico.partido_sigla?.trim() || null
  const siglaUf = politico.uf?.trim() || null
  const isHistorico = politico.id_legislatura_final != null && politico.id_legislatura_final < 57
  const partidoUfTexto =
    siglaPartido && siglaUf
      ? `${siglaPartido} · ${siglaUf}`
      : siglaPartido || siglaUf || (isHistorico ? "Mandato Histórico" : "Deputado(a) Federal")

  return (
    <motion.article
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, delay: rank * 0.04 }}
      className="group bg-white border border-slate-200/90 hover:border-blue-400 rounded-2xl p-4 sm:p-5 flex gap-4 items-start shadow-xs hover:shadow-md transition-all duration-200"
    >
      {/* Retrato Oficial em Alta Resolução */}
      <Link
        to={`/politicos/${slug}`}
        tabIndex={-1}
        aria-hidden="true"
        className="w-20 h-24 sm:w-24 sm:h-28 rounded-xl bg-slate-100 ring-1 ring-slate-200/80 overflow-hidden flex-shrink-0 group-hover:ring-blue-400 transition-all block relative"
      >
        {politico.url_foto && !fotoComErro ? (
          <img
            src={politico.url_foto}
            alt=""
            onError={() => setFotoComErro(true)}
            className="w-full h-full object-cover object-top"
            loading="lazy"
          />
        ) : (
          <div className="w-full h-full flex flex-col items-center justify-center bg-slate-100 text-slate-500 font-bold text-lg">
            <span>{politico.nome.charAt(0)}</span>
            <span className="text-[9px] font-normal text-slate-400">Oficial</span>
          </div>
        )}
      </Link>

      {/* Dados e Botões de Ação */}
      <div className="flex-1 min-w-0 flex flex-col justify-between self-stretch">
        <div>
          {/* Topo da ficha: Badge de Partido/UF e Rank de consultas */}
          <div className="flex items-center justify-between gap-2 mb-1">
            <span className="inline-flex items-center px-2 py-0.5 rounded-md bg-blue-50/80 border border-blue-200/60 text-[10px] font-bold text-blue-900 tracking-wide truncate">
              {partidoUfTexto}
            </span>
            <span className="text-[10px] font-mono text-slate-400 font-medium whitespace-nowrap flex-shrink-0">
              #{rank} em consultas
            </span>
          </div>

          {/* Nome com link para Perfil */}
          <h3 className="text-base sm:text-lg font-bold text-slate-900 leading-snug truncate">
            <Link
              to={`/politicos/${slug}`}
              className="text-slate-900 group-hover:text-blue-700 transition-colors no-underline"
            >
              {politico.nome}
            </Link>
          </h3>

          <p className="text-xs text-slate-500 mt-0.5 mb-3">
            {formatarLegislaturaCard(politico)}
          </p>
        </div>

        {/* Botões de Ação Imediata (Ficha Rápida) */}
        <div className="flex flex-wrap items-center gap-2 pt-2 border-t border-slate-100">
          <Link
            to={`/politicos/${slug}`}
            className="inline-flex items-center gap-1.5 px-2.5 sm:px-3 py-1.5 bg-slate-900 hover:bg-blue-700 text-white text-xs font-semibold rounded-lg no-underline transition-colors shadow-2xs flex-shrink-0"
          >
            <span className="hidden sm:inline">Auditar Mandato</span>
            <span className="sm:hidden">Auditar</span>
            <ArrowRight className="w-3 h-3 flex-shrink-0" />
          </Link>

          <Link
            to={`/comparar?p1=${slug}`}
            className="inline-flex items-center gap-1 px-2.5 py-1.5 bg-slate-50 hover:bg-slate-100 text-slate-700 hover:text-slate-900 text-xs font-medium rounded-lg border border-slate-200/80 no-underline transition-colors flex-shrink-0"
          >
            <Scale className="w-3 h-3 text-slate-500 flex-shrink-0" />
            <span>Comparar</span>
          </Link>
        </div>
      </div>
    </motion.article>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// Seção dos Parlamentares Mais Consultados (Fichas Rápidas 1C)
// ─────────────────────────────────────────────────────────────────────────────
function SecaoMaisConsultados() {
  const { data, isLoading, isError } = useMaisPesquisados(6)

  if (isError) return null

  return (
    <section className="max-w-6xl mx-auto px-6 py-12 border-b border-slate-200/80">
      <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-3 mb-6">
        <div>
          <div className="flex items-center gap-1.5 mb-1 text-blue-700">
            <TrendingUp className="w-4 h-4" />
            <span className="text-xs font-bold uppercase tracking-wider">
              Monitoramento Cívico dos Eleitores
            </span>
          </div>
          <h2 className="text-xl sm:text-2xl font-bold tracking-tight text-slate-900">
            Parlamentares Mais Consultados
          </h2>
          <p className="text-xs sm:text-sm text-slate-500 mt-0.5">
            Fichas rápidas com retratos oficiais e acesso imediato à auditoria de votos e despesas.
          </p>
        </div>

        <Link
          to="/politicos"
          className="inline-flex items-center gap-1 text-xs font-semibold text-blue-700 hover:text-blue-900 hover:underline transition-all self-start sm:self-auto"
        >
          Explorar todos os 513 deputados
          <ArrowRight className="w-3 h-3" />
        </Link>
      </div>

      {isLoading ? (
        <FichasSkeleton />
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {data?.slice(0, 6).map((politico, index) => (
            <FichaDeputadoCard
              key={politico.politico_id}
              politico={politico}
              rank={index + 1}
            />
          ))}
        </div>
      )}
    </section>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// Seção de Atividade Recente no Plenário (Votações Nominais)
// ─────────────────────────────────────────────────────────────────────────────
function SecaoPlenarioRecente() {
  const { data: votacoes = [], isLoading } = useVotacoes({ limit: 3 })

  return (
    <div className="lg:col-span-2 space-y-4">
      <div className="flex flex-wrap items-end sm:items-center justify-between gap-2 border-b border-slate-200 pb-3">
        <div>
          <div className="flex items-center gap-1.5 text-blue-700 mb-0.5">
            <Calendar className="w-3.5 h-3.5" />
            <span className="text-[11px] font-bold uppercase tracking-wider">
              Plenário em Ação
            </span>
          </div>
          <h3 className="text-base sm:text-lg font-bold text-slate-900">
            Últimas Votações Nominais Mapeadas
          </h3>
        </div>

        <Link
          to="/proposicoes"
          className="text-xs font-semibold text-blue-700 hover:underline flex-shrink-0"
        >
          <span className="hidden sm:inline">Ver histórico completo →</span>
          <span className="sm:hidden">Ver todas →</span>
        </Link>
      </div>

      {isLoading ? (
        <div className="space-y-3">
          {[1, 2, 3].map((i) => (
            <div key={i} className="p-4 bg-white border border-slate-200 rounded-xl animate-pulse h-24" />
          ))}
        </div>
      ) : votacoes.length === 0 ? (
        <div className="p-6 text-center text-xs text-slate-500 bg-white border border-slate-200 rounded-xl">
          Nenhuma votação nominal recente encontrada no momento.
        </div>
      ) : (
        <div className="space-y-3">
          {votacoes.slice(0, 3).map((v: VotacaoResponse) => {
            const siglaNumero =
              v.proposicao_sigla_tipo && v.proposicao_numero
                ? `${v.proposicao_sigla_tipo} ${v.proposicao_numero}/${v.proposicao_ano || ""}`
                : v.id_camara || `Votação #${v.id}`

            const isAprovada = v.aprovacao === 1
            const isRejeitada = v.aprovacao === 0

            return (
              <div
                key={v.id}
                className="p-4 rounded-xl border border-slate-200/90 hover:border-slate-300 bg-white shadow-2xs hover:shadow-xs transition-all"
              >
                <div className="flex items-center justify-between gap-2 mb-1.5">
                  <span className="text-xs font-mono font-bold text-slate-900 bg-slate-100 px-2 py-0.5 rounded border border-slate-200/60">
                    {siglaNumero}
                  </span>

                  {isAprovada ? (
                    <span className="inline-flex items-center gap-1 text-[11px] font-bold text-emerald-700 bg-emerald-50 px-2.5 py-0.5 rounded-full border border-emerald-200">
                      <CheckCircle2 className="w-3 h-3" />
                      Aprovada
                    </span>
                  ) : isRejeitada ? (
                    <span className="inline-flex items-center gap-1 text-[11px] font-bold text-rose-700 bg-rose-50 px-2.5 py-0.5 rounded-full border border-rose-200">
                      <XCircle className="w-3 h-3" />
                      Rejeitada
                    </span>
                  ) : (
                    <span className="text-[11px] font-medium text-slate-600 bg-slate-100 px-2 py-0.5 rounded-full">
                      Apreciação Concluída
                    </span>
                  )}
                </div>

                <p className="text-xs sm:text-sm text-slate-800 font-medium leading-relaxed line-clamp-2">
                  {v.proposicao_ementa || v.descricao || "Votação de matéria legislativa no plenário da Câmara."}
                </p>

                <div className="flex items-center justify-between text-[11px] text-slate-500 mt-2.5 pt-2 border-t border-slate-100">
                  <span className="font-mono">
                    {v.data ? new Date(v.data + "T00:00:00").toLocaleDateString("pt-BR") : "Data oficial"}
                    {v.sigla_orgao ? ` · ${v.sigla_orgao}` : ""}
                  </span>

                  <Link
                    to="/proposicoes"
                    className="text-blue-700 font-semibold hover:underline no-underline"
                  >
                    Ver votos por bancada →
                  </Link>
                </div>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// Componente Principal: Home.tsx
// ─────────────────────────────────────────────────────────────────────────────
export default function Home() {
  const [query, setQuery] = useState("")
  const navigate = useNavigate()

  useSeo({
    title: "quemvota — Transparência Legislativa Brasileira",
    description:
      "Acompanhe o que seus deputados federais fazem no Congresso. Gastos, votações nominais, presença e atuação legislativa de todos os parlamentares — dados oficiais, sem viés.",
    url: "https://www.quemvota.com.br",
    keywords: "deputados federais, câmara dos deputados, votações nominais, transparência, gastos cota parlamentar",
    type: "website",
  })

  function handleSearch(e: React.FormEvent) {
    e.preventDefault()
    if (!query.trim()) return
    navigate(`/politicos?q=${encodeURIComponent(query.trim())}`)
  }

  function handleFiltrarUf(uf: string) {
    navigate(`/politicos?uf=${encodeURIComponent(uf)}`)
  }

  return (
    <>
      <Header />

      <div className="min-h-screen bg-[#f8fafc]">

        {/* ── HERO SECTION CÍVICA EDITORIAL ── */}
        <section className="relative bg-white border-b border-slate-200/80 pt-24 sm:pt-28 pb-12 sm:pb-14">
          <div className="max-w-4xl mx-auto px-4 sm:px-6 text-center">

            {/* Badge Institucional */}
            <motion.div
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.3 }}
              className="flex justify-center mb-4"
            >
              <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-slate-100 border border-slate-200 text-slate-700 text-xs font-semibold">
                <ShieldCheck className="w-3.5 h-3.5 text-blue-700" />
                Transparência Pública e Neutralidade Factual Absoluta
              </span>
            </motion.div>

            {/* Título Principal */}
            <motion.h1
              initial={{ opacity: 0, y: 14 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.4, delay: 0.05 }}
              className="text-2xl sm:text-4xl lg:text-5xl font-bold tracking-tight text-slate-900 mb-3 sm:mb-4 max-w-3xl mx-auto leading-tight"
            >
              Acompanhe votos, gastos e a atuação dos deputados no Congresso Nacional
            </motion.h1>

            {/* Subtítulo */}
            <motion.p
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.4, delay: 0.1 }}
              className="text-sm sm:text-lg text-slate-600 max-w-2xl mx-auto mb-6 sm:mb-8 leading-relaxed"
            >
              Presença oficial em plenário, histórico de votações nominais, notas fiscais da cota e
              autoria de proposições consolidadas diretamente da Câmara dos Deputados. Sem notas ou viés político.
            </motion.p>

            {/* Formulário de Busca Amplo e Acessível */}
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.4, delay: 0.15 }}
            >
              <div className="max-w-xl mx-auto">
                <form
                  onSubmit={handleSearch}
                  className="flex items-center bg-white border border-slate-300 rounded-xl shadow-xs overflow-hidden focus-within:border-blue-600 focus-within:ring-2 focus-within:ring-blue-600/20 transition-all"
                >
                  <div className="flex items-center pl-3.5 sm:pl-4 text-slate-400 flex-shrink-0">
                    <Search className="w-4 h-4" />
                  </div>
                  <input
                    type="text"
                    data-testid="input-busca-home"
                    placeholder="Pesquise por deputado (ex: Tabata, Nikolas)..."
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    className="flex-1 min-w-0 px-2.5 sm:px-3 py-2.5 sm:py-3 text-xs sm:text-sm text-slate-800 bg-transparent outline-none placeholder:text-slate-400"
                  />
                  <button
                    type="submit"
                    data-testid="btn-consultar-home"
                    className="m-1 px-3 sm:px-4 py-2 bg-slate-900 hover:bg-blue-700 text-white text-xs sm:text-sm font-semibold rounded-lg flex items-center gap-1 sm:gap-1.5 transition-colors cursor-pointer flex-shrink-0 min-h-[38px]"
                  >
                    <span className="hidden sm:inline">Consultar</span>
                    <span className="sm:hidden">Buscar</span>
                    <ArrowRight className="w-3.5 h-3.5 flex-shrink-0" />
                  </button>
                </form>

                {/* Filtros Rápidos por UF */}
                <div className="flex items-center justify-center gap-1.5 mt-3 text-xs text-slate-500 flex-wrap">
                  <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
                    Consultar por Estado:
                  </span>
                  {UFS_DESTAQUE.map((uf) => (
                    <button
                      key={uf}
                      type="button"
                      onClick={() => handleFiltrarUf(uf)}
                      className="px-2 py-0.5 rounded bg-slate-50 hover:bg-white border border-slate-200/90 text-slate-700 hover:border-blue-400 hover:text-blue-700 font-semibold cursor-pointer transition-colors"
                    >
                      {uf}
                    </button>
                  ))}
                  <Link
                    to="/politicos"
                    className="text-blue-700 font-semibold hover:underline ml-1 cursor-pointer no-underline"
                  >
                    Todas as 27 UFs →
                  </Link>
                </div>
              </div>
            </motion.div>
          </div>
        </section>

        {/* ── SEÇÃO: FICHAS RÁPIDAS DOS PARLAMENTARES MAIS CONSULTADOS (VARIAÇÃO 1C) ── */}
        <SecaoMaisConsultados />

        {/* ── FAIXA DE INDICADORES CÍVICOS GLOBAIS (TICKER TABULAR) ── */}
        <section className="bg-slate-900 border-y border-slate-800 text-white">
          <div className="max-w-5xl mx-auto px-4 sm:px-6 grid grid-cols-2 sm:grid-cols-4">
            {[
              { num: "513",     suffix: "",    label: "Deputados Federais", sub: "57ª Legislatura" },
              { num: "78.4",    suffix: "%",   label: "Presença Média", sub: "sessões deliberativas" },
              { num: "4.204",   suffix: "",    label: "Votações Nominais", sub: "auditáveis por deputado" },
              { num: "R$ 1,2",  suffix: "B",   label: "Despesas Mapeadas", sub: "CEAP e verbas oficiais" },
            ].map((s, i) => (
              <div
                key={i}
                className={`py-4 sm:py-6 px-2 sm:px-4 text-center ${
                  i % 2 === 0 ? "border-r border-slate-800" : ""
                } ${i < 2 ? "border-b sm:border-b-0 border-slate-800" : ""} sm:border-r sm:border-slate-800 sm:last:border-r-0`}
              >
                <div className="text-xl sm:text-3xl font-mono font-bold text-white tabular-nums mb-1">
                  {s.num}<span className="text-blue-400 text-lg sm:text-xl font-normal ml-0.5">{s.suffix}</span>
                </div>
                <div className="text-xs font-semibold text-slate-200">
                  {s.label}
                </div>
                <div className="text-[10px] sm:text-[11px] text-slate-400 mt-0.5">
                  {s.sub}
                </div>
              </div>
            ))}
          </div>
        </section>

        {/* ── SEÇÃO: PLENÁRIO EM TEMPO REAL + FERRAMENTAS CÍVICAS ── */}
        <section className="max-w-6xl mx-auto px-4 sm:px-6 py-10 sm:py-14">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 items-start">
            {/* 2/3: Feed do Plenário com Votações Recentes */}
            <SecaoPlenarioRecente />

            {/* 1/3: Widgets do Comparador e Rankings */}
            <div className="space-y-4">
              {/* Card Duelo Parlamentar */}
              <div className="p-5 rounded-2xl bg-gradient-to-br from-blue-50/80 to-indigo-50/50 border border-blue-200/80 shadow-xs">
                <span className="text-[10px] font-bold uppercase tracking-wider text-blue-800 bg-white/80 px-2 py-0.5 rounded border border-blue-200/60">
                  Duelo Parlamentar
                </span>
                <h4 className="text-base font-bold text-slate-900 mt-2 mb-1">
                  Comparador Direto de Votos
                </h4>
                <p className="text-xs text-slate-600 leading-relaxed mb-4">
                  Coloque dois deputados lado a lado e descubra o índice de concordância nominal e onde discordaram.
                </p>
                <Link
                  to="/comparar"
                  className="w-full py-2.5 px-3 bg-blue-700 hover:bg-blue-800 text-white text-xs font-semibold rounded-xl flex items-center justify-center gap-1.5 transition-colors no-underline shadow-xs"
                >
                  <Scale className="w-3.5 h-3.5" />
                  <span>Montar Comparação Agora</span>
                </Link>
              </div>

              {/* Card Rankings Factuais */}
              <div className="p-5 rounded-2xl bg-white border border-slate-200/90 shadow-xs">
                <h4 className="text-sm font-bold text-slate-900 mb-1">
                  Rankings e Estatísticas Factuais
                </h4>
                <p className="text-xs text-slate-500 mb-3.5">
                  Métricas sem notas arbitrárias:
                </p>
                <ul className="text-xs space-y-2.5 text-slate-700">
                  <li>
                    <Link
                      to="/rankings?tipo=gastos"
                      className="flex items-center justify-between hover:text-blue-700 transition-colors no-underline text-slate-700"
                    >
                      <span className="flex items-center gap-1.5">
                        <span className="w-1.5 h-1.5 rounded-full bg-blue-600"></span>
                        Menores despesas da cota (CEAP)
                      </span>
                      <span className="text-slate-400">→</span>
                    </Link>
                  </li>
                  <li>
                    <Link
                      to="/rankings?tipo=presenca"
                      className="flex items-center justify-between hover:text-blue-700 transition-colors no-underline text-slate-700"
                    >
                      <span className="flex items-center gap-1.5">
                        <span className="w-1.5 h-1.5 rounded-full bg-emerald-600"></span>
                        Maiores presenças em plenário
                      </span>
                      <span className="text-slate-400">→</span>
                    </Link>
                  </li>
                  <li>
                    <Link
                      to="/rankings?tipo=discursos"
                      className="flex items-center justify-between hover:text-blue-700 transition-colors no-underline text-slate-700"
                    >
                      <span className="flex items-center gap-1.5">
                        <span className="w-1.5 h-1.5 rounded-full bg-indigo-600"></span>
                        Volume de discursos proferidos
                      </span>
                      <span className="text-slate-400">→</span>
                    </Link>
                  </li>
                </ul>
              </div>
            </div>
          </div>
        </section>

        {/* ── SEÇÃO: COMO FUNCIONA / METODOLOGIA CÍVICA ── */}
        <section className="bg-white border-t border-slate-200/80 py-16">
          <div className="max-w-5xl mx-auto px-6 grid grid-cols-1 md:grid-cols-2 gap-12 items-center">

            {/* Texto explicativo */}
            <div>
              <span className="text-xs font-semibold tracking-wider uppercase text-blue-700">
                Auditoria Cidadã
              </span>
              <h2 className="text-2xl sm:text-3xl font-bold tracking-tight text-slate-900 mt-1 mb-3">
                Dados oficiais, apresentados com clareza e neutralidade
              </h2>
              <p className="text-sm text-slate-600 leading-relaxed mb-6">
                Todas as informações do QuemVota são coletadas diariamente de forma automatizada
                a partir das APIs oficiais de dados abertos da Câmara dos Deputados e do Senado Federal.
                A plataforma não emite opiniões políticas, notas morais ou rankings avaliativos.
              </p>
              <Link
                to="/metodologia"
                className="inline-flex items-center gap-1.5 px-4 py-2 bg-slate-900 hover:bg-blue-700 text-white text-sm font-medium rounded-lg no-underline transition-colors shadow-xs"
              >
                Conhecer a metodologia completa
                <ArrowRight className="w-3.5 h-3.5" />
              </Link>
            </div>

            {/* Etapas do processo */}
            <div className="space-y-4">
              {[
                {
                  n: "01",
                  title: "Coleta e Sanitização Diária",
                  text: "Ingestão automatizada de votações nominais, despesas da CEAP e tramitações diretamente da Câmara.",
                },
                {
                  n: "02",
                  title: "Consolidação Desagregada",
                  text: "Cálculo transparente de índices factuais (presença em plenário, gastos discriminados e coautorias).",
                },
                {
                  n: "03",
                  title: "Transparência sem Juízo de Valor",
                  text: "Exibição clara e acessível para que cada cidadão avalie seus representantes com base em fatos.",
                },
              ].map((step, i) => (
                <div key={i} className="flex gap-4 p-4 rounded-xl bg-slate-50 border border-slate-200/60">
                  <div className="w-8 h-8 rounded-lg bg-white border border-slate-200 flex items-center justify-center font-mono text-xs font-bold text-blue-700 flex-shrink-0 shadow-2xs">
                    {step.n}
                  </div>
                  <div>
                    <h3 className="text-sm font-semibold text-slate-900 mb-0.5">{step.title}</h3>
                    <p className="text-xs text-slate-500 leading-relaxed">{step.text}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* ── RODAPÉ DISCRETO ── */}
        <footer className="bg-slate-50 border-t border-slate-200/80 py-6 text-center text-xs text-slate-500">
          <div className="max-w-5xl mx-auto px-6 flex flex-col sm:flex-row items-center justify-between gap-2">
            <p>
              Dados abertos da{" "}
              <a
                href="https://dadosabertos.camara.leg.br"
                target="_blank"
                rel="noreferrer"
                className="text-slate-700 hover:text-blue-700 underline underline-offset-2 transition-colors"
              >
                Câmara dos Deputados
              </a>
              {" "}e do{" "}
              <a
                href="https://www12.senado.leg.br/dadosabertos"
                target="_blank"
                rel="noreferrer"
                className="text-slate-700 hover:text-blue-700 underline underline-offset-2 transition-colors"
              >
                Senado Federal
              </a>
            </p>
            <p className="font-mono text-[11px] text-slate-400">
              quemvota.com.br · Código Aberto
            </p>
          </div>
        </footer>

      </div>
    </>
  )
}