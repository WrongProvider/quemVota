import Header from "../components/Header"
import { Link, useNavigate } from "react-router-dom"
import { useState } from "react"
import { motion } from "framer-motion"
import {
  Users,
  BarChart3,
  FileText,
  BookOpen,
  ArrowRight,
  TrendingUp,
  Search,
  ShieldCheck,
  CheckCircle2,
} from "lucide-react"
import { useMaisPesquisados } from "../hooks/useBuscaPopular"
import { useSeo } from "../hooks/useSeo"
import { nomeParaSlug } from "../api/politicos.api"

function EmAltaSkeleton() {
  return (
    <div className="flex gap-2.5 overflow-x-auto pb-1 justify-center">
      {Array.from({ length: 6 }).map((_, i) => (
        <div
          key={i}
          className="flex-shrink-0 flex items-center gap-2.5 px-3 py-2 rounded-lg bg-slate-100 animate-pulse w-36 h-10 border border-slate-200/60"
        />
      ))}
    </div>
  )
}

function EmAlta() {
  const { data, isLoading, isError } = useMaisPesquisados(8)

  if (isError) return null

  return (
    <div className="max-w-2xl mx-auto mt-6">
      <div className="flex items-center gap-1.5 mb-2.5 justify-center">
        <TrendingUp className="w-3.5 h-3.5 text-blue-600" />
        <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
          Mais consultados recentemente
        </span>
      </div>

      {isLoading ? (
        <EmAltaSkeleton />
      ) : (
        <div className="flex gap-2 overflow-x-auto pb-1 justify-center flex-wrap">
          {data?.map((politico, i) => {
            const slug = politico.slug || nomeParaSlug(politico.nome) || String(politico.politico_id)
            return (
              <motion.div
                key={politico.politico_id}
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ duration: 0.2, delay: i * 0.03 }}
              >
                <Link
                  to={`/politicos/${slug}`}
                  aria-label={politico.nome}
                  className="group flex items-center gap-2 px-2.5 py-1.5 rounded-lg bg-white border border-slate-200/90 hover:border-blue-400 hover:shadow-xs transition-all no-underline"
                >
                  {/* Avatar */}
                  <div className="w-6 h-6 rounded-full bg-slate-100 overflow-hidden flex-shrink-0 ring-1 ring-slate-200 group-hover:ring-blue-400 transition-all">
                    {politico.url_foto ? (
                      <img
                        src={politico.url_foto}
                        alt={politico.nome}
                        className="w-full h-full object-cover"
                        onError={(e) => {
                          (e.currentTarget as HTMLImageElement).style.display = "none"
                        }}
                      />
                    ) : (
                      <div className="w-full h-full flex items-center justify-center text-[9px] font-bold text-slate-500">
                        {politico.nome.charAt(0)}
                      </div>
                    )}
                  </div>

                  {/* Info */}
                  <div className="min-w-0 text-left">
                    <p className="text-xs font-medium text-slate-800 truncate max-w-[120px] leading-tight group-hover:text-blue-700 transition-colors">
                      {politico.nome}
                    </p>
                    <p className="text-[10px] text-slate-500 leading-tight">
                      {politico.partido_sigla} · {politico.uf}
                    </p>
                  </div>
                </Link>
              </motion.div>
            )
          })}
        </div>
      )}
    </div>
  )
}

export default function Home() {
  const [query, setQuery] = useState("")
  const navigate = useNavigate()

  useSeo({
    title: "quemvota — Transparência Legislativa Brasileira",
    description:
      "Acompanhe o que seus deputados federais fazem no Congresso. Gastos, votações, presença e performance de todos os parlamentares — dados oficiais, sem viés.",
    url: "https://www.quemvota.com.br",
    keywords: "deputados federais, câmara dos deputados, votações, transparência, gastos parlamentares",
    type: "website",
  })

  function handleSearch(e: React.FormEvent) {
    e.preventDefault()
    if (!query.trim()) return
    navigate(`/politicos?q=${encodeURIComponent(query)}`)
  }

  return (
    <>
      <Header />

      <div className="min-h-screen bg-[#f8fafc]">

        {/* ── HERO SECTION CÍVICA ── */}
        <section className="relative bg-white border-b border-slate-200/80 pt-28 pb-16">
          <div className="max-w-4xl mx-auto px-6 text-center">

            {/* Badge Institucional */}
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.35 }}
              className="flex justify-center mb-5"
            >
              <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-slate-100 border border-slate-200 text-slate-700 text-xs font-medium">
                <ShieldCheck className="w-3.5 h-3.5 text-blue-700" />
                Transparência Pública e Neutralidade Factual
              </span>
            </motion.div>

            {/* Título Principal */}
            <motion.h1
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.45, delay: 0.05 }}
              className="text-3xl sm:text-4xl lg:text-5xl font-bold tracking-tight text-slate-900 mb-4 max-w-2xl mx-auto leading-tight"
            >
              Acompanhe o que seus representantes fazem no Congresso Nacional
            </motion.h1>

            {/* Subtítulo */}
            <motion.p
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.45, delay: 0.1 }}
              className="text-base sm:text-lg text-slate-600 max-w-xl mx-auto mb-8 leading-relaxed"
            >
              Presença oficial, histórico de votações nominais, despesas de mandato e proposições
              consolidadas diretamente a partir de dados abertos da Câmara dos Deputados.
            </motion.p>

            {/* Formulário de Busca Amplo e Acessível */}
            <motion.div
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.45, delay: 0.15 }}
            >
              <div className="max-w-xl mx-auto">
                <form
                  onSubmit={handleSearch}
                  className="flex items-center bg-white border border-slate-300 rounded-xl shadow-xs overflow-hidden focus-within:border-blue-600 focus-within:ring-2 focus-within:ring-blue-600/20 transition-all"
                >
                  <div className="flex items-center pl-4 text-slate-400">
                    <Search className="w-4 h-4" />
                  </div>
                  <input
                    type="text"
                    placeholder="Pesquise pelo nome do deputado (ex: Tabata, Nikolas, Arthur)..."
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    className="flex-1 px-3 py-3 text-sm text-slate-800 bg-transparent outline-none placeholder:text-slate-400"
                  />
                  <button
                    type="submit"
                    className="m-1 px-4 py-2 bg-slate-900 hover:bg-blue-700 text-white text-sm font-medium rounded-lg flex items-center gap-1.5 transition-colors cursor-pointer"
                  >
                    Consultar
                    <ArrowRight className="w-3.5 h-3.5" />
                  </button>
                </form>
              </div>

              {/* Deputados em Destaque de Busca */}
              <EmAlta />
            </motion.div>
          </div>
        </section>

        {/* ── FAIXA DE INDICADORES CÍVICOS GLOBAIS ── */}
        <section className="bg-slate-900 border-y border-slate-800 text-white">
          <div className="max-w-5xl mx-auto px-6 grid grid-cols-2 sm:grid-cols-4">
            {[
              { num: "513",     suffix: "",    label: "Deputados Federais", sub: "57ª Legislatura" },
              { num: "81",      suffix: "",    label: "Senadores da República", sub: "Congresso Nacional" },
              { num: "+2",      suffix: "M",   label: "Votos Nominais", sub: "auditáveis" },
              { num: "R$ 1,2",  suffix: "B",   label: "Despesas Mapeadas", sub: "CEAP e gabinete" },
            ].map((s, i) => (
              <div
                key={i}
                className="py-6 px-4 text-center border-r border-slate-800 last:border-r-0"
              >
                <div className="text-2xl sm:text-3xl font-mono font-bold text-white tabular-nums mb-1">
                  {s.num}<span className="text-blue-400 text-xl font-normal ml-0.5">{s.suffix}</span>
                </div>
                <div className="text-xs font-semibold text-slate-200">
                  {s.label}
                </div>
                <div className="text-[11px] text-slate-400 mt-0.5">
                  {s.sub}
                </div>
              </div>
            ))}
          </div>
        </section>

        {/* ── SEÇÃO: O QUE VOCÊ PODE ACOMPANHAR ── */}
        <section className="max-w-5xl mx-auto px-6 py-16">
          <div className="mb-10 text-center sm:text-left">
            <p className="text-xs font-semibold tracking-wider uppercase text-blue-700 mb-1">
              Transparência Cidadã
            </p>
            <h2 className="text-2xl sm:text-3xl font-bold tracking-tight text-slate-900">
              O que você pode acompanhar no QuemVota
            </h2>
            <p className="text-sm text-slate-500 mt-1">
              Ferramentas de análise objetiva para fiscalizar a atuação dos parlamentares eleitos.
            </p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {[
              {
                icon: <Users className="w-5 h-5 text-blue-700" />,
                title: "Parlamentares",
                desc: "Perfil completo com assiduidade, cotas parlamentares, histórico de votos e foco temático.",
                link: "/politicos",
                cta: "Explorar deputados",
              },
              {
                icon: <BarChart3 className="w-5 h-5 text-indigo-700" />,
                title: "Rankings Fatuais",
                desc: "Métricas auditáveis de despesas da cota, volume de discursos e principais empresas recebedoras.",
                link: "/rankings",
                cta: "Ver rankings",
              },
              {
                icon: <FileText className="w-5 h-5 text-emerald-700" />,
                title: "Projetos e Votações",
                desc: "Pesquise proposições legislativas em tramitação e o posicionamento de cada partido.",
                link: "/proposicoes",
                cta: "Consultar matérias",
              },
              {
                icon: <BookOpen className="w-5 h-5 text-slate-700" />,
                title: "Metodologia",
                desc: "Princípios de neutralidade factual, cálculo de alinhamento e agregação de dados públicos.",
                link: "/metodologia",
                cta: "Conhecer regras",
              },
            ].map((card, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, y: 14 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.35, delay: i * 0.05 }}
              >
                <Link
                  to={card.link}
                  className="group flex flex-col bg-white border border-slate-200/90 rounded-xl p-5 h-full no-underline hover:border-blue-400 hover:shadow-xs transition-all duration-150"
                >
                  <div className="w-10 h-10 bg-slate-50 border border-slate-200/60 rounded-lg flex items-center justify-center mb-4 group-hover:bg-blue-50 group-hover:border-blue-200 transition-colors">
                    {card.icon}
                  </div>
                  <h3 className="text-sm font-semibold text-slate-900 mb-1.5 group-hover:text-blue-700 transition-colors">
                    {card.title}
                  </h3>
                  <p className="text-xs text-slate-500 leading-relaxed flex-1 mb-4">
                    {card.desc}
                  </p>
                  <span className="inline-flex items-center gap-1 text-xs font-semibold text-blue-700 group-hover:gap-1.5 transition-all">
                    {card.cta}
                    <ArrowRight className="w-3 h-3" />
                  </span>
                </Link>
              </motion.div>
            ))}
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
                A plataforma não emite opiniões políticas, notas morais ou julgamentos de valor.
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