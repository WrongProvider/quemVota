import { useState } from "react"
import { Link } from "react-router-dom"
import Header from "../components/Header"
import { Github, Database, Shield, Users, Target, Heart, ArrowRight, ExternalLink, Code2, BarChart3, FileSearch } from "lucide-react"

// ─────────────────────────────────────────────────────────────────────────────
// Dados
// ─────────────────────────────────────────────────────────────────────────────

const PILARES = [
  {
    icon: <Database size={20} className="text-blue-600" />,
    bg: "bg-blue-50 border-blue-100",
    title: "Dados abertos",
    text: "Todas as informações são extraídas diretamente das APIs públicas da Câmara dos Deputados. Nada é inventado ou estimado — se está aqui, tem fonte oficial.",
  },
  {
    icon: <Shield size={20} className="text-emerald-600" />,
    bg: "bg-emerald-50 border-emerald-100",
    title: "Sem viés editorial",
    text: "Não comentamos, não opinamos e não classificamos políticos por ideologia. Apresentamos os números como são e deixamos que você tire suas próprias conclusões.",
  },
  {
    icon: <Code2 size={20} className="text-purple-600" />,
    bg: "bg-purple-50 border-purple-100",
    title: "Código aberto",
    text: "O projeto é open source. Qualquer pessoa pode auditar a metodologia, propor melhorias ou identificar erros. Transparência começa em casa.",
  },
  {
    icon: <Heart size={20} className="text-rose-600" />,
    bg: "bg-rose-50 border-rose-100",
    title: "Feito por cidadãos",
    text: "Somos um projeto independente, sem financiamento público ou político. Desenvolvido por pessoas comuns que acreditam que informação transforma democracia.",
  },
]

const FUNCIONALIDADES = [
  {
    icon: <Users size={18} className="text-slate-600" />,
    name: "Parlamentares",
    desc: "Perfil completo de cada deputado federal: presença, gastos, votações e histórico.",
  },
  {
    icon: <BarChart3 size={18} className="text-slate-600" />,
    name: "Rankings",
    desc: "Compare parlamentares por performance, economia da cota e volume de discursos.",
  },
  {
    icon: <FileSearch size={18} className="text-slate-600" />,
    name: "Projetos e Votações",
    desc: "Pesquise proposições legislativas e veja como cada partido orientou seus votos.",
  },
]

const TIMELINE = [
  { ano: "2024", marco: "Início do projeto", desc: "Primeiras coletas de dados da API da Câmara." },
  { ano: "2024", marco: "Score de performance", desc: "Desenvolvimento da metodologia de avaliação parlamentar." },
  { ano: "2025", marco: "Lançamento público", desc: "Abertura da plataforma para qualquer cidadão acessar." },
  { ano: "2025", marco: "Projetos e Votações", desc: "Módulo de busca de proposições e votações em plenário." },
]

// ─────────────────────────────────────────────────────────────────────────────
// Componentes auxiliares
// ─────────────────────────────────────────────────────────────────────────────

function PageHeader() {
  return (
    <div className="bg-white border-b border-slate-200">
      <div className="max-w-4xl mx-auto px-6 py-12">
        <p className="text-xs font-semibold tracking-widest uppercase text-blue-600 mb-3">
          Institucional
        </p>
        <h1
          style={{ fontFamily: "'Fraunces', serif" }}
          className="text-4xl font-bold text-slate-900 mb-4 leading-tight"
        >
          Sobre o quemvota
        </h1>
        <p className="text-lg text-slate-500 leading-relaxed max-w-2xl">
          Uma plataforma independente de transparência legislativa — para que qualquer
          cidadão possa acompanhar o que acontece no Congresso Nacional.
        </p>
      </div>
    </div>
  )
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section className="mb-14">
      <h2
        style={{ fontFamily: "'Fraunces', serif" }}
        className="text-2xl font-bold text-slate-800 mb-6"
      >
        {title}
      </h2>
      {children}
    </section>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// Página principal
// ─────────────────────────────────────────────────────────────────────────────

export default function Sobre() {
  return (
    <>
      <Header />
      <div className="min-h-screen bg-gray-50 pt-16">
        <PageHeader />

        <div className="max-w-4xl mx-auto px-6 py-14">

          {/* ── MISSÃO ── */}
          <Section title="Nossa missão">
            <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-8">
              <p className="text-slate-600 leading-relaxed text-base mb-5">
                O <strong className="text-slate-800">quemvota</strong> nasceu de uma pergunta simples:{" "}
                <em>"Será que tem alguma forma fácil de saber o que meu deputado fez nos últimos meses?"</em>
              </p>
              <p className="text-slate-600 leading-relaxed text-base mb-5">
                Os dados existem — a Câmara dos Deputados disponibiliza uma API pública com votações,
                presenças, despesas e proposições. O problema é que eles estão espalhados, em formatos
                difíceis de consumir e sem nenhuma visualização amigável.
              </p>
              <p className="text-slate-600 leading-relaxed text-base">
                O quemvota coleta, organiza e apresenta esses dados de forma clara. Sem propaganda.
                Sem opinião. Só informação.
              </p>
            </div>
          </Section>

          {/* ── PILARES ── */}
          <Section title="Nossos princípios">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              {PILARES.map((p) => (
                <div
                  key={p.title}
                  className={`rounded-2xl border p-6 ${p.bg}`}
                >
                  <div className="flex items-center gap-3 mb-3">
                    <div className="w-9 h-9 rounded-xl bg-white/70 flex items-center justify-center flex-shrink-0 border border-white/50">
                      {p.icon}
                    </div>
                    <h3 className="text-sm font-semibold text-slate-800">{p.title}</h3>
                  </div>
                  <p className="text-sm text-slate-600 leading-relaxed">{p.text}</p>
                </div>
              ))}
            </div>
          </Section>

          {/* ── FUNCIONALIDADES ── */}
          <Section title="O que você encontra aqui">
            <div className="bg-white rounded-2xl border border-slate-200 shadow-sm divide-y divide-slate-100">
              {FUNCIONALIDADES.map((f) => (
                <div key={f.name} className="flex items-start gap-4 px-6 py-5">
                  <div className="w-9 h-9 rounded-xl bg-slate-50 border border-slate-100 flex items-center justify-center flex-shrink-0 mt-0.5">
                    {f.icon}
                  </div>
                  <div>
                    <p className="text-sm font-semibold text-slate-800 mb-1">{f.name}</p>
                    <p className="text-sm text-slate-500 leading-relaxed">{f.desc}</p>
                  </div>
                </div>
              ))}
            </div>
          </Section>

          {/* ── TIMELINE ── */}
          <Section title="História do projeto">
            <div className="relative">
              <div className="absolute left-[19px] top-2 bottom-2 w-px bg-slate-200" />
              <div className="space-y-6">
                {TIMELINE.map((item, i) => (
                  <div key={i} className="flex gap-5 relative">
                    <div className={`w-10 h-10 rounded-full border-2 flex items-center justify-center flex-shrink-0 z-10 ${
                      i === TIMELINE.length - 1
                        ? "bg-blue-600 border-blue-600"
                        : "bg-white border-slate-300"
                    }`}>
                      <span className={`text-[10px] font-mono font-bold ${
                        i === TIMELINE.length - 1 ? "text-white" : "text-slate-400"
                      }`}>
                        {item.ano.slice(2)}
                      </span>
                    </div>
                    <div className="flex-1 pt-1.5">
                      <p className="text-sm font-semibold text-slate-800">{item.marco}</p>
                      <p className="text-sm text-slate-500 mt-0.5">{item.desc}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </Section>

          {/* ── FONTES ── */}
          <Section title="Fontes de dados">
            <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6">
              <p className="text-sm text-slate-600 leading-relaxed mb-5">
                Todo o conteúdo da plataforma é derivado exclusivamente de fontes públicas e oficiais:
              </p>
              <div className="space-y-3">
                {[
                  {
                    name: "API de Dados Abertos — Câmara dos Deputados",
                    url: "https://dadosabertos.camara.leg.br",
                    desc: "Votações, presenças, despesas, proposições e deputados",
                  },
                  {
                    name: "Portal de Dados Abertos — Senado Federal",
                    url: "https://www12.senado.leg.br/dadosabertos",
                    desc: "Dados complementares do processo legislativo",
                  },
                ].map((fonte) => (
                  <a
                    key={fonte.url}
                    href={fonte.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-start justify-between gap-4 p-4 rounded-xl border border-slate-100 bg-slate-50 hover:bg-blue-50 hover:border-blue-100 transition-all group no-underline"
                  >
                    <div>
                      <p className="text-sm font-medium text-slate-800 group-hover:text-blue-700 transition-colors">
                        {fonte.name}
                      </p>
                      <p className="text-xs text-slate-400 mt-0.5">{fonte.desc}</p>
                    </div>
                    <ExternalLink size={14} className="text-slate-300 group-hover:text-blue-500 flex-shrink-0 mt-0.5 transition-colors" />
                  </a>
                ))}
              </div>
            </div>
          </Section>

          {/* ── CTA FINAL ── */}
          <div className="bg-[#1a1a1a] rounded-2xl p-8 text-center">
            <h3
              style={{ fontFamily: "'Fraunces', serif" }}
              className="text-2xl font-bold text-white mb-3"
            >
              Comece a explorar
            </h3>
            <p className="text-slate-400 text-sm mb-6 max-w-md mx-auto leading-relaxed">
              Veja o que seus representantes têm feito — dados atualizados, organizados e de graça.
            </p>
            <div className="flex items-center justify-center gap-3 flex-wrap">
              <Link
                to="/politicos"
                className="inline-flex items-center gap-2 px-5 py-2.5 bg-blue-600 hover:bg-blue-500 text-white text-sm font-medium rounded-xl no-underline transition-colors"
              >
                Ver parlamentares <ArrowRight size={14} />
              </Link>
              <a
                href="https://github.com/WrongProvider/quemVota"
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-2 px-5 py-2.5 bg-white/10 hover:bg-white/20 text-white text-sm font-medium rounded-xl no-underline transition-colors"
              >
                <Github size={14} /> Ver no GitHub
              </a>
            </div>
          </div>

        </div>

        {/* Rodapé */}
        <div className="border-t border-slate-200 bg-white py-6 text-center">
          <p className="text-xs text-slate-400">
            Dados públicos da{" "}
            <a href="https://dadosabertos.camara.leg.br" target="_blank" rel="noreferrer" className="text-slate-500 hover:text-blue-600 transition-colors">
              Câmara dos Deputados
            </a>
            {" "}· quemvota.com.br
          </p>
        </div>
      </div>
    </>
  )
}