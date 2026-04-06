import { useEffect, useState } from "react"
import { useParams, Link } from "react-router-dom"
import {
  usePoliticoDetalheBySlug,
  usePoliticoEstatisticas,
  usePoliticoPerformance,
} from "../hooks/usePoliticos"
import Header from "../components/Header"
import { useSeo } from "../hooks/useSeo"
import {
  ArrowLeft,
  MapPin,
  Users,
  GraduationCap,
  BadgeCheck,
  BarChart2,
  TrendingUp,
  Receipt,
  Wallet,
  Calendar,
  ChevronRight,
  ExternalLink,
  ArrowLeftRight,
  Trophy,
  Share2,
  Copy,
  Check,
} from "lucide-react"
import type {
  PoliticoDetalhe,
  PoliticoEstatisticas,
  PoliticoPerformance,
} from "../api/politicos.api"

const PATH_FOTOS = "/fotos_politicos/"

// ── Helpers ────────────────────────────────────────────────────────────────

function getScoreColor(score: number) {
  if (score >= 70) return "text-emerald-500"
  if (score >= 40) return "text-amber-500"
  return "text-red-500"
}

function getOrcamentoColor(pct: number) {
  if (pct > 85) return "text-red-500"
  if (pct > 60) return "text-amber-500"
  return "text-emerald-600"
}

/**
 * Compara dois valores numéricos e retorna qual é "melhor".
 * lowerIsBetter=true para métricas de gasto.
 */
function comparar(
  a: number | null | undefined,
  b: number | null | undefined,
  lowerIsBetter = false,
): "a" | "b" | "tie" | null {
  if (a == null || b == null) return null
  if (a === b) return "tie"
  if (lowerIsBetter) return a < b ? "a" : "b"
  return a > b ? "a" : "b"
}

// ── COMPARTILHAMENTO ── idêntico ao PoliticosDetalhe ───────────────────────

function BotoesCompartilhamento({ texto, url }: { texto: string; url: string }) {
  const [copiado, setCopiado] = useState(false)
  const [aberto, setAberto]   = useState(false)

  const redes = [
    {
      label: "WhatsApp",
      icon: (
        <svg viewBox="0 0 24 24" className="w-4 h-4 fill-current" xmlns="http://www.w3.org/2000/svg">
          <path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z"/>
        </svg>
      ),
      href: `https://wa.me/?text=${encodeURIComponent(`${texto}\n${url}`)}`,
      color: "hover:bg-green-50 hover:text-green-600 hover:border-green-200",
    },
    {
      label: "X / Twitter",
      icon: (
        <svg viewBox="0 0 24 24" className="w-4 h-4 fill-current" xmlns="http://www.w3.org/2000/svg">
          <path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-4.714-6.231-5.401 6.231H2.744l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"/>
        </svg>
      ),
      href: `https://twitter.com/intent/tweet?text=${encodeURIComponent(texto)}&url=${encodeURIComponent(url)}`,
      color: "hover:bg-slate-50 hover:text-slate-900 hover:border-slate-300",
    },
    {
      label: "LinkedIn",
      icon: (
        <svg viewBox="0 0 24 24" className="w-4 h-4 fill-current" xmlns="http://www.w3.org/2000/svg">
          <path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433a2.062 2.062 0 01-2.063-2.065 2.064 2.064 0 112.063 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z"/>
        </svg>
      ),
      href: `https://www.linkedin.com/sharing/share-offsite/?url=${encodeURIComponent(url)}`,
      color: "hover:bg-blue-50 hover:text-blue-700 hover:border-blue-200",
    },
  ]

  const copiarLink = async () => {
    await navigator.clipboard.writeText(url)
    setCopiado(true)
    setTimeout(() => setCopiado(false), 2000)
  }

  return (
    <div className="relative">
      <button
        onClick={() => setAberto(!aberto)}
        className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-slate-100 hover:bg-blue-50 hover:text-blue-700 text-slate-600 text-sm font-medium transition-colors border border-transparent hover:border-blue-100"
      >
        <Share2 size={15} />
        Compartilhar
      </button>

      {aberto && (
        <>
          <div className="fixed inset-0 z-10" onClick={() => setAberto(false)} />
          <div className="absolute right-0 mt-2 z-20 bg-white rounded-2xl shadow-xl border border-slate-100 p-3 min-w-[200px]">
            <p className="text-[11px] text-slate-400 font-medium uppercase tracking-wide px-2 mb-2">
              Compartilhar comparação
            </p>
            <div className="space-y-1">
              {redes.map((rede) => (
                <a
                  key={rede.label}
                  href={rede.href}
                  target="_blank"
                  rel="noopener noreferrer"
                  onClick={() => setAberto(false)}
                  className={`flex items-center gap-3 px-3 py-2 rounded-xl text-sm text-slate-600 border border-transparent transition-all ${rede.color}`}
                >
                  {rede.icon}
                  {rede.label}
                </a>
              ))}
              <button
                onClick={copiarLink}
                className="w-full flex items-center gap-3 px-3 py-2 rounded-xl text-sm text-slate-600 border border-transparent hover:bg-slate-50 hover:border-slate-200 transition-all"
              >
                {copiado ? (
                  <>
                    <Check size={16} className="text-emerald-500" />
                    <span className="text-emerald-600 font-medium">Link copiado!</span>
                  </>
                ) : (
                  <>
                    <Copy size={16} />
                    Copiar link
                  </>
                )}
              </button>
            </div>
          </div>
        </>
      )}
    </div>
  )
}

// ── SEO HEAD ────────────────────────────────────────────────────────────────

function SeoHead({ nomeA, nomeB }: { nomeA: string; nomeB: string }) {
  useSeo({
    title: `${nomeA} vs ${nomeB} — Comparação Parlamentar | quemvota`,
    description: `Compare o desempenho de ${nomeA} e ${nomeB}. Gastos, votações, score e performance lado a lado.`,
    url: typeof window !== "undefined" ? window.location.href : "",
    keywords: `${nomeA}, ${nomeB}, comparação parlamentar, deputados, performance`,
    type: "website",
  })
  return null
}

// ── STAT CARD ── idêntico ao PoliticosDetalhe, com prop destaque opcional ──

const accentMap: Record<string, string> = {
  blue:    "bg-blue-50 border-blue-100 hover:border-blue-300",
  violet:  "bg-violet-50 border-violet-100 hover:border-violet-300",
  emerald: "bg-emerald-50 border-emerald-100 hover:border-emerald-300",
  amber:   "bg-amber-50 border-amber-100 hover:border-amber-300",
  slate:   "bg-white border-slate-200 hover:border-slate-300",
}

function StatCard({
  icon,
  titulo,
  valor,
  accent = "slate",
  destaque = false,
}: {
  icon: React.ReactNode
  titulo: string
  valor: React.ReactNode
  accent?: string
  destaque?: boolean
}) {
  return (
    <div
      className={`stat-card rounded-xl border p-4 transition-colors duration-200 cursor-default relative
        ${accentMap[accent] ?? accentMap.slate}
        ${destaque ? "ring-2 ring-amber-400 ring-offset-1" : ""}
      `}
    >
      {destaque && (
        <span className="absolute -top-2 -right-2 w-5 h-5 rounded-full bg-amber-400 flex items-center justify-center shadow-sm">
          <Trophy size={10} className="text-white" />
        </span>
      )}
      <div className="flex items-center gap-2 mb-2">
        {icon}
        <p className="text-[11px] font-medium text-slate-500 uppercase tracking-wide leading-tight">{titulo}</p>
      </div>
      <p className="mono-font text-lg font-semibold text-slate-800 leading-tight truncate">{valor}</p>
    </div>
  )
}

// ── LOADING ── idêntico ao PoliticosDetalhe ─────────────────────────────────

function LoadingScreen() {
  return (
    <>
      <Header />
      <div className="min-h-screen bg-[#f8f9fb] flex items-center justify-center pt-16">
        <div className="text-center">
          <div className="w-10 h-10 border-[3px] border-slate-200 border-t-blue-500 rounded-full animate-spin mx-auto mb-4" />
          <p className="text-sm text-slate-400 font-medium">Carregando comparação...</p>
        </div>
      </div>
    </>
  )
}

// ── ERROR ── idêntico ao PoliticosDetalhe ───────────────────────────────────

function ErrorScreen() {
  return (
    <>
      <Header />
      <div className="min-h-screen bg-[#f8f9fb] flex items-center justify-center pt-16">
        <div className="text-center">
          <div className="w-14 h-14 rounded-2xl bg-red-50 flex items-center justify-center mx-auto mb-4">
            <span className="text-2xl">⚠️</span>
          </div>
          <h2 className="text-lg font-semibold text-slate-700 mb-1">Erro ao carregar</h2>
          <p className="text-sm text-slate-400">Não foi possível carregar os parlamentares.</p>
          <Link
            to="/politicos"
            className="inline-flex items-center gap-1.5 mt-5 text-sm text-blue-600 hover:text-blue-800 font-medium"
          >
            <ArrowLeft size={14} />
            Voltar aos Parlamentares
          </Link>
        </div>
      </div>
    </>
  )
}

// ── COLUNA DE PERFIL (hero) ─────────────────────────────────────────────────

function ColunaPerfil({
  data,
  performance,
}: {
  data: PoliticoDetalhe
  performance: PoliticoPerformance | undefined
}) {
  return (
    <div className="flex flex-col items-center text-center gap-2 md:gap-3">
      {/* Foto */}
      <div className="profile-photo relative">
        <div className="w-20 h-20 md:w-36 md:h-36 rounded-2xl overflow-hidden ring-2 md:ring-4 ring-white shadow-lg md:shadow-xl">
          <img
            src={`${PATH_FOTOS}${data.id}.jpg`}
            alt={`Foto de ${data.nome}`}
            className="w-full h-full object-cover"
          />
        </div>
        {data.situacao && (
          <div className="absolute -bottom-2 left-1/2 -translate-x-1/2 whitespace-nowrap">
            <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] md:text-[11px] font-medium bg-emerald-500 text-white shadow-sm">
              <span className="w-1 h-1 md:w-1.5 md:h-1.5 rounded-full bg-white inline-block" />
              <span className="hidden sm:inline">{data.situacao}</span>
            </span>
          </div>
        )}
      </div>

      {/* Nome */}
      <div className="mt-2">
        {data.condicao_eleitoral && (
          <span className="pill-badge text-blue-700 text-[10px] md:text-[11px] font-medium px-2 py-0.5 rounded-full border border-blue-100 inline-block mb-1.5">
            {data.condicao_eleitoral}
          </span>
        )}
        <h2 className="display-font text-base md:text-2xl font-bold text-slate-900 leading-tight">
          {data.nome}
        </h2>
      </div>

      {/* Metadados — ocultos no mobile mais apertado */}
      <div className="flex flex-wrap justify-center gap-x-2 md:gap-x-4 gap-y-1 text-xs md:text-sm text-slate-500">
        {data.sigla_uf && (
          <span className="flex items-center gap-1">
            <MapPin size={11} className="text-slate-400" />
            {data.sigla_uf}
          </span>
        )}
        {data.sigla_partido && (
          <span className="flex items-center gap-1">
            <Users size={11} className="text-slate-400" />
            {data.sigla_partido}
          </span>
        )}
        {data.escolaridade && (
          <span className="hidden md:flex items-center gap-1">
            <GraduationCap size={11} className="text-slate-400" />
            {data.escolaridade}
          </span>
        )}
      </div>

      {/* Score ring — menor no mobile */}
      {performance && (
        <div className="text-center">
          <div
            className="score-ring w-20 h-20 md:w-28 md:h-28"
            style={{ "--score": performance.score_final } as React.CSSProperties}
          >
            <div className="score-ring-inner flex-col">
              <span className={`mono-font text-xl md:text-2xl font-bold ${getScoreColor(performance.score_final)}`}>
                {performance.score_final.toFixed(0)}
              </span>
              <span className="text-[9px] md:text-[10px] text-slate-400 leading-tight mt-0.5">score</span>
            </div>
          </div>
          <p className="text-xs text-slate-400 mt-1.5 font-medium">Performance</p>
        </div>
      )}

      {/* Links */}
      <div className="flex flex-col items-center gap-1">
        <Link
          to={`/politicos/${data.slug}`}
          className="inline-flex items-center gap-1 text-xs text-blue-600 hover:text-blue-800 font-medium transition-colors"
        >
          <span className="hidden sm:inline">Ver perfil completo</span>
          <span className="sm:hidden">Ver perfil</span>
          <ChevronRight size={11} />
        </Link>
        {data.id_camara && (
          <a
            href={`https://www.camara.leg.br/deputados/${data.id_camara}`}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-1 text-xs text-slate-400 hover:text-blue-600 transition-colors"
          >
            <ExternalLink size={10} />
            <span className="hidden sm:inline">Câmara dos Deputados</span>
          </a>
        )}
      </div>
    </div>
  )
}

// ── LINHA DE COMPARAÇÃO ─────────────────────────────────────────────────────

function LinhaComparacao({
  titulo,
  valA,
  valB,
  numA,
  numB,
  lowerIsBetter = false,
}: {
  titulo: string
  valA: React.ReactNode
  valB: React.ReactNode
  numA?: number | null
  numB?: number | null
  lowerIsBetter?: boolean
}) {
  const melhor = comparar(numA, numB, lowerIsBetter)

  return (
    <div className="grid grid-cols-[1fr_auto_1fr] items-center gap-3 py-3.5 border-b border-slate-100 last:border-0">
      <div className={`text-right ${melhor === "a" ? "font-bold text-slate-900" : "text-slate-500"}`}>
        <span className="mono-font text-sm">{valA}</span>
        {melhor === "a" && (
          <Trophy size={11} className="inline ml-1.5 text-amber-400 mb-0.5" />
        )}
      </div>

      <div className="min-w-[100px] px-1 text-center">
        <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wide whitespace-nowrap">
          {titulo}
        </span>
      </div>

      <div className={`text-left ${melhor === "b" ? "font-bold text-slate-900" : "text-slate-500"}`}>
        {melhor === "b" && (
          <Trophy size={11} className="inline mr-1.5 text-amber-400 mb-0.5" />
        )}
        <span className="mono-font text-sm">{valB}</span>
      </div>
    </div>
  )
}

// ── BLOCO ESTATÍSTICAS ──────────────────────────────────────────────────────

function BlocoEstatisticas({
  statsA,
  statsB,
  nomeA,
  nomeB,
}: {
  statsA: PoliticoEstatisticas
  statsB: PoliticoEstatisticas
  nomeA: string
  nomeB: string
}) {
  const metricas: {
    titulo: string
    icon: React.ReactNode
    accent: string
    valA: number
    valB: number
    fmt: (v: number) => string
    lowerIsBetter: boolean
  }[] = [
    {
      titulo: "Total de Votações",
      icon: <BadgeCheck size={16} className="text-blue-500" />,
      accent: "blue",
      valA: statsA.total_votacoes,
      valB: statsB.total_votacoes,
      fmt: (v) => v.toString(),
      lowerIsBetter: false,
    },
    {
      titulo: "Total de Despesas",
      icon: <Receipt size={16} className="text-violet-500" />,
      accent: "violet",
      valA: statsA.total_despesas,
      valB: statsB.total_despesas,
      fmt: (v) => v.toString(),
      lowerIsBetter: true,
    },
    {
      titulo: "Cota Parlamentar",
      icon: <TrendingUp size={16} className="text-emerald-500" />,
      accent: "emerald",
      valA: statsA.total_gasto,
      valB: statsB.total_gasto,
      fmt: (v) => `R$ ${v.toLocaleString("pt-BR")}`,
      lowerIsBetter: true,
    },
    {
      titulo: "Verba de Gabinete",
      icon: <Wallet size={16} className="text-orange-500" />,
      accent: "amber",
      valA: statsA.total_gasto_gabinete ?? 0,
      valB: statsB.total_gasto_gabinete ?? 0,
      fmt: (v) => `R$ ${v.toLocaleString("pt-BR")}`,
      lowerIsBetter: true,
    },
    {
      titulo: "Gasto Total",
      icon: <Receipt size={16} className="text-red-500" />,
      accent: "slate",
      valA: statsA.total_gasto_combinado ?? statsA.total_gasto,
      valB: statsB.total_gasto_combinado ?? statsB.total_gasto,
      fmt: (v) => `R$ ${v.toLocaleString("pt-BR")}`,
      lowerIsBetter: true,
    },
    {
      titulo: "Média Mensal",
      icon: <Receipt size={16} className="text-amber-500" />,
      accent: "amber",
      valA: statsA.media_mensal,
      valB: statsB.media_mensal,
      fmt: (v) => `R$ ${v.toLocaleString("pt-BR")}`,
      lowerIsBetter: true,
    },
  ]

  return (
    <section className="section-fade">
      <div className="flex items-center gap-2 mb-5">
        <BarChart2 size={18} className="text-blue-500" />
        <h2 className="display-font text-xl font-bold text-slate-800">Estatísticas</h2>
      </div>

      {/* Legenda de colunas */}
      <div className="grid grid-cols-2 gap-3 mb-3">
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-white border border-slate-100">
          <div className="w-2 h-2 rounded-full bg-blue-500 flex-shrink-0" />
          <p className="text-xs font-semibold text-slate-600 truncate">{nomeA}</p>
        </div>
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-white border border-slate-100">
          <div className="w-2 h-2 rounded-full bg-violet-500 flex-shrink-0" />
          <p className="text-xs font-semibold text-slate-600 truncate">{nomeB}</p>
        </div>
      </div>

      {/* Cards espelhados lado a lado */}
      <div className="grid grid-cols-2 gap-x-3 gap-y-3">
        {metricas.map((m) => {
          const melhor = comparar(m.valA, m.valB, m.lowerIsBetter)
          return (
            <div key={m.titulo} className="contents">
              <StatCard
                icon={m.icon}
                titulo={m.titulo}
                valor={m.fmt(m.valA)}
                accent={m.accent}
                destaque={melhor === "a"}
              />
              <StatCard
                icon={m.icon}
                titulo={m.titulo}
                valor={m.fmt(m.valB)}
                accent={m.accent}
                destaque={melhor === "b"}
              />
            </div>
          )
        })}

        {statsA.primeiro_ano != null && statsB.primeiro_ano != null && (
          <>
            <StatCard icon={<Calendar size={16} className="text-slate-400" />} titulo="Primeiro Ano" valor={statsA.primeiro_ano ?? "—"} accent="slate" />
            <StatCard icon={<Calendar size={16} className="text-slate-400" />} titulo="Primeiro Ano" valor={statsB.primeiro_ano ?? "—"} accent="slate" />
            <StatCard icon={<Calendar size={16} className="text-slate-400" />} titulo="Último Ano"   valor={statsA.ultimo_ano   ?? "—"} accent="slate" />
            <StatCard icon={<Calendar size={16} className="text-slate-400" />} titulo="Último Ano"   valor={statsB.ultimo_ano   ?? "—"} accent="slate" />
          </>
        )}
      </div>

      {/* Aviso de gabinete */}
      {((statsA.total_gasto_gabinete ?? 0) > 0 || (statsB.total_gasto_gabinete ?? 0) > 0) && (
        <p className="text-[11px] text-slate-400 mt-2 leading-relaxed">
          ℹ️ <strong>Cota Parlamentar</strong> cobre deslocamentos, materiais e serviços de terceiros.{" "}
          <strong>Verba de Gabinete</strong> cobre salários e encargos dos funcionários do escritório.{" "}
          <Trophy size={10} className="inline text-amber-400 mb-0.5" /> indica o melhor desempenho na métrica.
        </p>
      )}
    </section>
  )
}

// ── BLOCO PERFORMANCE ───────────────────────────────────────────────────────

function BlocoPerformance({
  perfA,
  perfB,
  nomeA,
  nomeB,
}: {
  perfA: PoliticoPerformance
  perfB: PoliticoPerformance
  nomeA: string
  nomeB: string
}) {
  const melhorScore = comparar(perfA.score_final, perfB.score_final)

  return (
    <section className="section-fade">
      <div className="flex items-center gap-2 mb-5">
        <TrendingUp size={18} className="text-blue-500" />
        <h2 className="display-font text-xl font-bold text-slate-800">Performance Parlamentar</h2>
      </div>

      {/* Score geral lado a lado */}
      <div className="bg-white border border-slate-200 rounded-2xl overflow-hidden mb-4">
        <div className="px-5 py-3 border-b border-slate-100 bg-slate-50/60">
          <p className="text-[11px] font-semibold text-slate-500 uppercase tracking-wide">
            Score Geral
          </p>
        </div>
        <div className="grid grid-cols-2 divide-x divide-slate-100">
          {([
            { nome: nomeA, perf: perfA, melhor: melhorScore === "a" },
            { nome: nomeB, perf: perfB, melhor: melhorScore === "b" },
          ] as const).map(({ nome, perf, melhor }, i) => (
            <div key={i} className={`px-5 py-6 text-center ${melhor ? "bg-amber-50/30" : ""}`}>
              <p className="text-xs font-semibold text-slate-500 mb-4 truncate">{nome}</p>
              <div
                className="score-ring w-28 h-28 mx-auto"
                style={{ "--score": perf.score_final } as React.CSSProperties}
              >
                <div className="score-ring-inner flex-col">
                  <span className={`mono-font text-2xl font-bold ${getScoreColor(perf.score_final)}`}>
                    {perf.score_final.toFixed(0)}
                  </span>
                  <span className="text-[10px] text-slate-400 leading-tight mt-0.5">score</span>
                </div>
              </div>
              <p className="text-xs text-slate-400 mt-2 font-medium">Performance</p>
              {melhor && (
                <p className="text-[11px] font-semibold text-amber-600 mt-2 flex items-center justify-center gap-1">
                  <Trophy size={11} className="text-amber-400" />
                  Melhor score
                </p>
              )}
              {melhorScore === "tie" && (
                <p className="text-[11px] text-slate-400 mt-2">Empate</p>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Sub-scores linha a linha */}
      <div className="bg-white border border-slate-200 rounded-2xl overflow-hidden">
        <div className="px-5 py-3 border-b border-slate-100 bg-slate-50/60">
          <div className="grid grid-cols-[1fr_auto_1fr] gap-3">
            <p className="text-right text-xs font-semibold text-blue-600 truncate">{nomeA}</p>
            <div className="min-w-[100px]" />
            <p className="text-left text-xs font-semibold text-violet-600 truncate">{nomeB}</p>
          </div>
        </div>
        <div className="px-5">
          <LinhaComparacao
            titulo="Assiduidade"
            valA={perfA.detalhes.nota_assiduidade.toFixed(1)}
            valB={perfB.detalhes.nota_assiduidade.toFixed(1)}
            numA={perfA.detalhes.nota_assiduidade}
            numB={perfB.detalhes.nota_assiduidade}
          />
          <LinhaComparacao
            titulo="Economia"
            valA={perfA.detalhes.nota_economia.toFixed(1)}
            valB={perfB.detalhes.nota_economia.toFixed(1)}
            numA={perfA.detalhes.nota_economia}
            numB={perfB.detalhes.nota_economia}
          />
          <LinhaComparacao
            titulo="Produção"
            valA={perfA.detalhes.nota_producao.toFixed(1)}
            valB={perfB.detalhes.nota_producao.toFixed(1)}
            numA={perfA.detalhes.nota_producao}
            numB={perfB.detalhes.nota_producao}
          />
          <LinhaComparacao
            titulo="Score Final"
            valA={perfA.score_final.toFixed(1)}
            valB={perfB.score_final.toFixed(1)}
            numA={perfA.score_final}
            numB={perfB.score_final}
          />
          <LinhaComparacao
            titulo="Média Global"
            valA={perfA.media_global.toFixed(1)}
            valB={perfB.media_global.toFixed(1)}
            numA={perfA.media_global}
            numB={perfB.media_global}
          />
        </div>
      </div>

      {/* Composição do orçamento — mesmo card do PoliticosDetalhe, duplicado para cada político */}
      {((perfA.info?.gasto_gabinete ?? 0) > 0 || (perfB.info?.gasto_gabinete ?? 0) > 0) && (
        <div className="mt-4 bg-white border border-slate-200 rounded-2xl overflow-hidden">
          <div className="px-5 py-3 border-b border-slate-100 bg-slate-50/60">
            <p className="text-[11px] font-semibold text-slate-500 uppercase tracking-wide">
              💰 Composição do Orçamento
            </p>
          </div>

          {[
            { info: perfA.info, nome: nomeA },
            { info: perfB.info, nome: nomeB },
          ].map(({ info, nome }, i) => {
            const pct = info?.orcamento_utilizado_pct ?? info?.cota_utilizada_pct ?? 0
            return (
              <div key={i} className={i === 1 ? "border-t border-slate-100" : ""}>
                <div className="px-5 py-2.5 bg-slate-50/50 border-b border-slate-50">
                  <p className="text-[11px] font-semibold text-slate-500 truncate">{nome}</p>
                </div>
                <div className="grid grid-cols-2 md:grid-cols-4 divide-x divide-slate-100">
                  {[
                    {
                      label: "Cota Parlamentar",
                      value: `R$ ${(info?.total_gasto ?? 0).toLocaleString("pt-BR")}`,
                      sub: "gastos CEAP",
                      color: "text-violet-600",
                    },
                    {
                      label: "Verba de Gabinete",
                      value: `R$ ${(info?.gasto_gabinete ?? 0).toLocaleString("pt-BR")}`,
                      sub: "pessoal / funcionários",
                      color: "text-orange-500",
                    },
                    {
                      label: "Gasto Total",
                      value: `R$ ${(info?.gasto_total ?? 0).toLocaleString("pt-BR")}`,
                      sub: "CEAP + gabinete",
                      color: "text-red-500",
                    },
                    {
                      label: "Orçamento Utilizado",
                      value: `${pct.toFixed(1)}%`,
                      sub: "do total disponível",
                      color: getOrcamentoColor(pct),
                    },
                  ].map((item) => (
                    <div key={item.label} className="px-5 py-4 text-center">
                      <p className={`mono-font font-bold text-base ${item.color}`}>{item.value}</p>
                      <p className="text-[11px] font-semibold text-slate-600 mt-1">{item.label}</p>
                      <p className="text-[10px] text-slate-400 mt-0.5">{item.sub}</p>
                    </div>
                  ))}
                </div>
              </div>
            )
          })}
        </div>
      )}
    </section>
  )
}

// ── PAGE ────────────────────────────────────────────────────────────────────

export default function ComparacaoPoliticos() {
  const { slug1: slugA, slug2: slugB } = useParams<{ slug1: string; slug2: string }>()

  const { data: dataA, isLoading: loadA, error: errA } = usePoliticoDetalheBySlug(slugA)
  const { data: dataB, isLoading: loadB, error: errB } = usePoliticoDetalheBySlug(slugB)

  const { data: statsA } = usePoliticoEstatisticas(dataA?.id ?? 0, null)
  const { data: statsB } = usePoliticoEstatisticas(dataB?.id ?? 0, null)
  const { data: perfA  } = usePoliticoPerformance(dataA?.id ?? 0, null)
  const { data: perfB  } = usePoliticoPerformance(dataB?.id ?? 0, null)

  if (loadA || loadB) return <LoadingScreen />
  if (errA || errB || !dataA || !dataB) return <ErrorScreen />

  const primeiroNomeA = dataA.nome.split(" ")[0]
  const primeiroNomeB = dataB.nome.split(" ")[0]

  return (
    <>
      <SeoHead nomeA={dataA.nome} nomeB={dataB.nome} />

      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=DM+Sans:ital,opsz,wght@0,9..40,300;0,9..40,400;0,9..40,500;0,9..40,600;1,9..40,400&family=DM+Mono:wght@400;500&family=Fraunces:ital,opsz,wght@0,9..144,300;0,9..144,700;1,9..144,400&display=swap');

        .detail-root  { font-family: 'DM Sans', sans-serif; }
        .display-font { font-family: 'Fraunces', serif; }
        .mono-font    { font-family: 'DM Mono', monospace; }

        .profile-photo { animation: photoReveal 0.7s cubic-bezier(0.22, 1, 0.36, 1) both; }
        @keyframes photoReveal {
          from { opacity: 0; transform: scale(0.92) translateY(12px); }
          to   { opacity: 1; transform: scale(1) translateY(0); }
        }

        .stat-card { animation: cardSlide 0.5s cubic-bezier(0.22, 1, 0.36, 1) both; }
        .stat-card:nth-child(1)  { animation-delay: 0.05s; }
        .stat-card:nth-child(2)  { animation-delay: 0.08s; }
        .stat-card:nth-child(3)  { animation-delay: 0.11s; }
        .stat-card:nth-child(4)  { animation-delay: 0.14s; }
        .stat-card:nth-child(5)  { animation-delay: 0.17s; }
        .stat-card:nth-child(6)  { animation-delay: 0.20s; }
        .stat-card:nth-child(7)  { animation-delay: 0.23s; }
        .stat-card:nth-child(8)  { animation-delay: 0.26s; }
        .stat-card:nth-child(9)  { animation-delay: 0.29s; }
        .stat-card:nth-child(10) { animation-delay: 0.32s; }
        .stat-card:nth-child(11) { animation-delay: 0.35s; }
        .stat-card:nth-child(12) { animation-delay: 0.38s; }
        @keyframes cardSlide {
          from { opacity: 0; transform: translateY(16px); }
          to   { opacity: 1; transform: translateY(0); }
        }

        .hero-fade { animation: heroFade 0.6s ease both; }
        @keyframes heroFade {
          from { opacity: 0; transform: translateY(-8px); }
          to   { opacity: 1; transform: translateY(0); }
        }

        .pill-badge {
          background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%);
        }

        .score-ring {
          position: relative;
          display: inline-flex;
          align-items: center;
          justify-content: center;
        }
        .score-ring::before {
          content: '';
          position: absolute;
          inset: -4px;
          border-radius: 50%;
          background: conic-gradient(
            #2563eb calc(var(--score, 0) * 3.6deg),
            #e2e8f0 0deg
          );
          z-index: 0;
        }
        .score-ring-inner {
          position: relative;
          z-index: 1;
          background: white;
          border-radius: 50%;
          width: 100%;
          height: 100%;
          display: flex;
          align-items: center;
          justify-content: center;
        }

        .section-fade { animation: sectionFade 0.3s ease both; }
        @keyframes sectionFade {
          from { opacity: 0.4; transform: translateY(4px); }
          to   { opacity: 1; transform: translateY(0); }
        }
      `}</style>

      <div className="detail-root min-h-screen bg-[#f8f9fb]">
        <Header />

        {/* ── HERO ── */}
        <div className="pt-16">
          <div className="relative overflow-hidden bg-white border-b border-slate-100">
            {/* Gradiente decorativo — idêntico ao PoliticosDetalhe */}
            <div
              className="absolute inset-0 opacity-[0.03]"
              style={{
                backgroundImage:
                  "radial-gradient(circle at 80% 50%, #2563eb 0%, transparent 60%), radial-gradient(circle at 20% 80%, #7c3aed 0%, transparent 50%)",
              }}
            />

            <div className="relative max-w-5xl mx-auto px-4 md:px-6 py-8 md:py-12 hero-fade">

              {/* Breadcrumb + ações */}
              <div className="mb-8">
                {/* Linha 1: breadcrumb + badge */}
                <div className="flex items-center justify-between gap-2">
                  <Link
                    to={`/politicos/${dataA.slug}`}
                    className="inline-flex items-center gap-1.5 text-sm text-slate-400 hover:text-slate-700 transition-colors group min-w-0"
                  >
                    <ArrowLeft size={14} className="group-hover:-translate-x-0.5 transition-transform flex-shrink-0" />
                    <span className="truncate hidden sm:inline">{dataA.nome}</span>
                    <span className="truncate sm:hidden">{dataA.nome.split(" ")[0]}</span>
                    <ChevronRight size={12} className="opacity-50 flex-shrink-0" />
                    <span className="text-slate-600 font-medium flex-shrink-0">Comparação</span>
                  </Link>

                  <div className="flex items-center gap-2 flex-shrink-0">
                    <span className="hidden sm:inline-flex items-center gap-2 px-3 py-1.5 rounded-xl bg-blue-50 border border-blue-100 text-blue-600 text-sm font-medium">
                      <ArrowLeftRight size={14} />
                      Comparando
                    </span>
                    <BotoesCompartilhamento
                      texto={`Compare ${dataA.nome} e ${dataB.nome} no QuemVota`}
                      url={`${window.location.origin}/comparar/${slugA}/${slugB}`}
                    />
                  </div>
                </div>
              </div>

              {/* Título central */}
              <div className="text-center mb-10">
                <span className="mono-font text-xs text-slate-400 uppercase tracking-widest block mb-2">
                  Comparação Parlamentar
                </span>
                <h1 className="display-font text-2xl md:text-3xl font-bold text-slate-900 leading-tight">
                  {primeiroNomeA}{" "}
                  <span className="text-slate-300 font-light mx-1">vs</span>{" "}
                  {primeiroNomeB}
                </h1>
              </div>

              {/* Perfis lado a lado */}
              <div className="grid grid-cols-2 gap-3 md:gap-16 items-start">
                <ColunaPerfil data={dataA} performance={perfA} />
                {/* Divisor vertical — só desktop */}
                <div className="hidden md:block absolute left-1/2 top-0 bottom-0 w-px bg-slate-100 -translate-x-1/2 pointer-events-none" />
                <ColunaPerfil data={dataB} performance={perfB} />
              </div>
            </div>
          </div>
        </div>

        {/* ── CONTEÚDO PRINCIPAL ── */}
        <div className="max-w-5xl mx-auto px-6 py-10 space-y-10">

          {/* Âncora visual de legenda de colunas */}
          <div className="grid grid-cols-2 gap-3">
            <div className="flex items-center gap-2 px-4 py-2.5 bg-white rounded-xl border border-slate-200 shadow-sm">
              <div className="w-2 h-2 rounded-full bg-blue-500 flex-shrink-0" />
              <p className="text-xs font-semibold text-slate-700 truncate">{dataA.nome}</p>
            </div>
            <div className="flex items-center gap-2 px-4 py-2.5 bg-white rounded-xl border border-slate-200 shadow-sm">
              <div className="w-2 h-2 rounded-full bg-violet-500 flex-shrink-0" />
              <p className="text-xs font-semibold text-slate-700 truncate">{dataB.nome}</p>
            </div>
          </div>

          {/* ── ESTATÍSTICAS ── */}
          {statsA && statsB && (
            <BlocoEstatisticas
              statsA={statsA}
              statsB={statsB}
              nomeA={primeiroNomeA}
              nomeB={primeiroNomeB}
            />
          )}

          {/* ── PERFORMANCE PARLAMENTAR ── */}
          {perfA && perfB && (
            <BlocoPerformance
              perfA={perfA}
              perfB={perfB}
              nomeA={primeiroNomeA}
              nomeB={primeiroNomeB}
            />
          )}

          {/* ── CTAs finais ── */}
          <div className="grid grid-cols-2 gap-4 pb-4">
            <Link
              to={`/politicos/${dataA.slug}`}
              className="flex items-center justify-center gap-2 px-5 py-3.5 rounded-xl bg-white hover:bg-blue-50 text-slate-700 hover:text-blue-700 text-sm font-medium border border-slate-200 hover:border-blue-200 transition-colors shadow-sm"
            >
              <ArrowLeft size={14} />
              Perfil de {primeiroNomeA}
            </Link>
            <Link
              to={`/politicos/${dataB.slug}`}
              className="flex items-center justify-center gap-2 px-5 py-3.5 rounded-xl bg-white hover:bg-blue-50 text-slate-700 hover:text-blue-700 text-sm font-medium border border-slate-200 hover:border-blue-200 transition-colors shadow-sm"
            >
              Perfil de {primeiroNomeB}
              <ChevronRight size={14} />
            </Link>
          </div>

        </div>
      </div>
    </>
  )
}