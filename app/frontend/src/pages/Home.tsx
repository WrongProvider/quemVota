import Header from "../components/Header"
import { Link, useNavigate } from "react-router-dom"
import { useState } from "react"
import { motion } from "framer-motion"
import { MagnifyingGlassIcon, ArrowRightIcon } from "@heroicons/react/24/outline"

export default function Home() {
  const [query, setQuery] = useState("")
  const navigate = useNavigate()

  function handleSearch(e: React.FormEvent) {
    e.preventDefault()
    if (!query.trim()) return
    navigate(`/politicos?q=${encodeURIComponent(query)}`)
  }

  return (
    <>
      <Header />

      <div className="font-sans bg-gray-50 min-h-screen">

        {/* ── HERO ── */}
        <section className="relative overflow-hidden bg-white border-b border-gray-100">
          {/* Glow de fundo */}
          <div className="absolute -top-48 left-1/2 -translate-x-1/2 w-[900px] h-[560px] rounded-full bg-blue-100 opacity-40 blur-3xl pointer-events-none" />

          <div className="relative max-w-4xl mx-auto px-6 pt-32 pb-24 text-center">

            {/* Badge */}
            <motion.div
              initial={{ opacity: 0, y: 14 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.45 }}
              className="flex justify-center mb-7"
            >
              <span className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-blue-50 border border-blue-200 text-blue-600 text-xs font-semibold tracking-wide">
                <span className="w-1.5 h-1.5 rounded-full bg-blue-500 animate-pulse" />
                Dados atualizados diariamente
              </span>
            </motion.div>

            {/* Título */}
            <motion.h1
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.55, delay: 0.08 }}
              className="text-4xl sm:text-5xl lg:text-6xl font-bold leading-[1.1] tracking-tight text-slate-900 mb-5"
            >
              Transparência sobre<br />
              <span className="text-blue-600">quem decide</span> o seu futuro
            </motion.h1>

            {/* Subtítulo */}
            <motion.p
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.55, delay: 0.16 }}
              className="text-base sm:text-lg text-slate-500 max-w-xl mx-auto mb-11 leading-relaxed"
            >
              Acompanhe votações, presenças, discursos e gastos do Congresso Nacional
              com dados oficiais, organizados de forma clara e acessível.
            </motion.p>

            {/* Search */}
            <motion.div
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.55, delay: 0.24 }}
            >
              <div className="max-w-xl mx-auto mb-5">
                <form
                  onSubmit={handleSearch}
                  className="flex items-center bg-white border-2 border-slate-200 rounded-2xl shadow-sm overflow-hidden focus-within:border-blue-500 focus-within:ring-4 focus-within:ring-blue-500/10 transition-all"
                >
                  <div className="flex items-center pl-4 text-slate-400">
                    <MagnifyingGlassIcon className="w-5 h-5" />
                  </div>
                  <input
                    type="text"
                    placeholder="Pesquisar por parlamentar..."
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    className="flex-1 px-3 py-4 text-sm text-slate-800 bg-transparent outline-none placeholder:text-slate-400"
                  />
                  <button
                    type="submit"
                    className="m-1.5 px-5 py-2.5 bg-slate-900 hover:bg-blue-600 text-white text-sm font-medium rounded-xl flex items-center gap-1.5 transition-colors"
                  >
                    Buscar
                    <ArrowRightIcon className="w-3.5 h-3.5" />
                  </button>
                </form>
              </div>

              {/* Quick links */}
              <div className="flex justify-center flex-wrap items-center gap-2 text-sm text-slate-400">
                <span>Sugestões:</span>
                {[
                  { label: "São Paulo", href: "/politicos?uf=SP" },
                  { label: "Rio de Janeiro", href: "/politicos?uf=RJ" },
                  { label: "Rankings", href: "/rankings" },
                  { label: "Metodologia", href: "/metodologia" },
                ].map((l) => (
                  <a
                    key={l.label}
                    href={l.href}
                    className="px-3 py-1 rounded-full bg-slate-50 border border-slate-200 text-slate-500 text-xs font-medium hover:bg-blue-50 hover:border-blue-200 hover:text-blue-600 transition-all"
                  >
                    {l.label}
                  </a>
                ))}
              </div>
            </motion.div>
          </div>
        </section>

        {/* ── STATS STRIP ── */}
        <motion.div
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6 }}
          className="bg-slate-900"
        >
          <div className="max-w-5xl mx-auto px-6 grid grid-cols-2 sm:grid-cols-4">
            {[
              { num: "513",    suffix: "",    label: "Deputados Federais" },
              { num: "81",     suffix: "",    label: "Senadores" },
              { num: "+2",     suffix: "M",   label: "Votações registradas" },
              { num: "R$1,2",  suffix: "B",   label: "Gastos mapeados" },
            ].map((s, i) => (
              <div
                key={i}
                className="py-7 text-center border-r border-white/[0.07] last:border-r-0"
              >
                <div className="text-2xl sm:text-3xl font-mono font-medium text-white leading-none mb-1.5">
                  {s.num}
                  <span className="text-blue-400">{s.suffix}</span>
                </div>
                <div className="text-[11px] uppercase tracking-widest text-slate-500 font-medium">
                  {s.label}
                </div>
              </div>
            ))}
          </div>
        </motion.div>

        {/* ── FEATURE CARDS ── */}
        <section className="max-w-5xl mx-auto px-6 py-20">
          <motion.div
            initial={{ opacity: 0, y: 16 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.5 }}
          >
            <p className="text-xs font-semibold tracking-widest uppercase text-blue-600 mb-3">
              Explore
            </p>
            <h2 className="text-2xl sm:text-3xl font-bold tracking-tight text-slate-900 mb-12">
              O que você pode acompanhar
            </h2>
          </motion.div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {[
              {
                icon: "👥",
                title: "Parlamentares",
                desc: "Veja o perfil completo, presença em votações, gastos e histórico de cada parlamentar.",
                link: "/politicos",
                cta: "Explorar parlamentares",
              },
              {
                icon: "📊",
                title: "Rankings",
                desc: "Compare parlamentares por performance, gastos, economia e quantidade de discursos.",
                link: "/rankings",
                cta: "Ver rankings",
              },
              {
                icon: "🧩",
                title: "Projetos e Votações",
                desc: "Pesquise por votações e proposições legislativas em tramitação ou encerradas.",
                link: null,
                cta: null,
              },
              {
                icon: "⚖️",
                title: "Metodologia",
                desc: "Entenda como coletamos, processamos e apresentamos os dados oficiais.",
                link: "/metodologia",
                cta: "Saiba mais",
              },
            ].map((card, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.45, delay: i * 0.07 }}
              >
                {card.link ? (
                  <Link
                    to={card.link}
                    className="group flex flex-col bg-white border-2 border-slate-200 rounded-2xl p-6 h-full no-underline hover:border-blue-300 hover:shadow-lg hover:shadow-blue-500/10 hover:-translate-y-0.5 transition-all duration-200"
                  >
                    <div className="w-11 h-11 bg-blue-50 rounded-xl flex items-center justify-center text-xl mb-5">
                      {card.icon}
                    </div>
                    <h3 className="text-sm font-semibold text-slate-900 mb-2">{card.title}</h3>
                    <p className="text-sm text-slate-500 leading-relaxed flex-1 mb-5">{card.desc}</p>
                    <span className="inline-flex items-center gap-1 text-xs font-semibold text-blue-600 group-hover:gap-2 transition-all">
                      {card.cta}
                      <ArrowRightIcon className="w-3 h-3" />
                    </span>
                  </Link>
                ) : (
                  <div className="flex flex-col bg-white border-2 border-slate-200 rounded-2xl p-6 h-full opacity-60">
                    <div className="w-11 h-11 bg-slate-100 rounded-xl flex items-center justify-center text-xl mb-5">
                      {card.icon}
                    </div>
                    <h3 className="text-sm font-semibold text-slate-900 mb-2">{card.title}</h3>
                    <p className="text-sm text-slate-500 leading-relaxed flex-1 mb-5">{card.desc}</p>
                    <span className="inline-flex items-center text-[11px] font-semibold uppercase tracking-wide text-slate-400 bg-slate-100 border border-slate-200 px-2.5 py-1 rounded-full w-fit">
                      Em breve
                    </span>
                  </div>
                )}
              </motion.div>
            ))}
          </div>
        </section>

        {/* ── HOW IT WORKS ── */}
        <section className="bg-slate-50 border-y border-slate-100">
          <div className="max-w-5xl mx-auto px-6 py-20 grid grid-cols-1 md:grid-cols-2 gap-16 lg:gap-24 items-center">

            {/* Texto */}
            <motion.div
              initial={{ opacity: 0, x: -20 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.55 }}
            >
              <p className="text-xs font-semibold tracking-widest uppercase text-blue-600 mb-3">
                Transparência
              </p>
              <h2 className="text-2xl sm:text-3xl font-bold tracking-tight text-slate-900 mb-4">
                Dados públicos,<br />apresentados com clareza
              </h2>
              <p className="text-[15px] text-slate-500 leading-relaxed mb-8">
                Coletamos dados diretamente das APIs oficiais da Câmara dos Deputados e do Senado Federal,
                processamos e organizamos para que qualquer cidadão possa acompanhar o trabalho dos seus representantes.
              </p>
              <Link
                to="/metodologia"
                className="inline-flex items-center gap-2 px-5 py-3 bg-slate-900 hover:bg-blue-600 text-white text-sm font-medium rounded-xl no-underline transition-colors"
              >
                Conhecer a metodologia
                <ArrowRightIcon className="w-3.5 h-3.5" />
              </Link>
            </motion.div>

            {/* Steps */}
            <motion.div
              initial={{ opacity: 0, x: 20 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.55, delay: 0.1 }}
              className="flex flex-col"
            >
              {[
                { n: "01", title: "Coleta automática",       text: "Dados coletados diariamente das APIs oficiais do Congresso Nacional." },
                { n: "02", title: "Processamento e cálculo", text: "Calculamos scores de performance com base em assiduidade, produção e economia." },
                { n: "03", title: "Visualização acessível",  text: "Apresentamos tudo de forma clara para que qualquer cidadão possa acompanhar." },
              ].map((step, i, arr) => (
                <div key={i} className="flex gap-5 relative">
                  {/* Linha conectora */}
                  {i < arr.length - 1 && (
                    <div className="absolute left-5 top-10 bottom-0 w-px bg-slate-200" />
                  )}
                  <div className="w-10 h-10 rounded-full bg-white border-2 border-slate-200 flex items-center justify-center font-mono text-xs font-medium text-blue-600 flex-shrink-0 relative z-10">
                    {step.n}
                  </div>
                  <div className={i < arr.length - 1 ? "pb-8" : ""}>
                    <p className="text-sm font-semibold text-slate-900 mt-2 mb-1">{step.title}</p>
                    <p className="text-sm text-slate-500 leading-relaxed">{step.text}</p>
                  </div>
                </div>
              ))}
            </motion.div>
          </div>
        </section>

        {/* ── FOOTER STRIP ── */}
        <div className="bg-white border-t border-slate-100 py-7 text-center">
          <p className="text-xs text-slate-400">
            Dados públicos da{" "}
            <a href="https://dadosabertos.camara.leg.br" target="_blank" rel="noreferrer" className="text-slate-500 hover:text-blue-600 transition-colors">
              Câmara dos Deputados
            </a>
            {" "}e do{" "}
            <a href="https://www12.senado.leg.br/dadosabertos" target="_blank" rel="noreferrer" className="text-slate-500 hover:text-blue-600 transition-colors">
              Senado Federal
            </a>
            {" "}· quemvota.com.br
          </p>
        </div>

      </div>
    </>
  )
}