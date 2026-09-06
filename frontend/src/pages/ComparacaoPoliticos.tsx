import { useEffect, useState } from "react"
import { useParams, Link, useNavigate } from "react-router-dom"
import ModalSelecionarPolitico from "../components/ModalSelecionarPolitico"
import {
  usePoliticoDetalheBySlug,
  usePoliticoEstatisticas,
  usePoliticoPerformance,
  useComparacaoPoliticos,
} from "../hooks/usePoliticos"
import { useDebounce } from "../hooks/useDebounce"
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
  Share2,
  Copy,
  Check,
  Scale,
  CheckCircle2,
  XCircle,
  Tag,
  AlertCircle,
  Search,
  X,
  Flame,
} from "lucide-react"
import {
  nomeParaSlug,
} from "../api/politicos.api"
import type {
  PoliticoDetalhe,
  PoliticoEstatisticas,
  PoliticoPerformance,
  ComparacaoPoliticosGrafoResponse,
} from "../api/politicos.api"

const PATH_FOTOS = "/fotos_politicos/"

const PRINCIPAIS_VOTACOES_DESTAQUE = [
  { label: "Escala 6x1 (PEC 221)", query: "6x1" },
  { label: "Previdência", query: "previdencia" },
  { label: "Reforma Tributária", query: "reforma tributaria" },
  { label: "Marco Temporal", query: "marco temporal" },
  { label: "Apostas & Bets", query: "bets" },
  { label: "Porte de Armas", query: "porte de armas" },
  { label: "Desoneração da Folha", query: "desoneracao" },
  { label: "Saúde", query: "saude" },
  { label: "Educação", query: "educacao" },
  { label: "Segurança Pública", query: "seguranca" },
]

// ── Helpers ────────────────────────────────────────────────────────────────


function getOrcamentoColor(_pct: number) {
  return "text-slate-800"
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
    description: `Compare a atuação de ${nomeA} e ${nomeB}. Gastos, votações e atividade parlamentar lado a lado.`,
    url: typeof window !== "undefined" ? window.location.href : "",
    keywords: `${nomeA}, ${nomeB}, comparação parlamentar, deputados, votações, gastos`,
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
}: {
  icon: React.ReactNode
  titulo: string
  valor: React.ReactNode
  accent?: string
}) {
  return (
    <div
      className={`stat-card rounded-xl border p-4 transition-colors duration-200 cursor-default
        ${accentMap[accent] ?? accentMap.slate}
      `}
    >
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
      <div className="min-h-screen bg-canvas flex items-center justify-center pt-16">
        <div className="text-center">
          <div className="w-10 h-10 border-[3px] border-slate-200 border-t-slate-800 rounded-full animate-spin mx-auto mb-4" />
          <p className="text-sm text-slate-500 font-medium">Carregando comparação...</p>
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
      <div className="min-h-screen bg-canvas flex items-center justify-center pt-16">
        <div className="text-center">
          <div className="w-14 h-14 rounded-2xl bg-red-50 flex items-center justify-center mx-auto mb-4">
            <AlertCircle size={28} className="text-red-500" />
          </div>
          <h2 className="text-lg font-semibold text-slate-800 mb-1">Erro ao carregar</h2>
          <p className="text-sm text-slate-500">Não foi possível carregar os dados dos parlamentares.</p>
          <div className="flex flex-wrap items-center justify-center gap-3 mt-5">
            <Link
              to="/comparar"
              className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl bg-slate-900 text-white text-xs font-semibold hover:bg-slate-800 transition-colors shadow-xs"
            >
              <ArrowLeft size={13} />
              Escolher outros deputados
            </Link>
            <Link
              to="/politicos"
              className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl bg-white border border-slate-200 text-slate-700 hover:text-slate-900 text-xs font-semibold transition-colors shadow-xs"
            >
              Ver todos parlamentares
            </Link>
          </div>
        </div>
      </div>
    </>
  )
}

// ── COLUNA DE PERFIL (hero) ─────────────────────────────────────────────────

function ColunaPerfil({
  data,
  performance,
  onTrocar,
}: {
  data: PoliticoDetalhe
  performance: PoliticoPerformance | undefined
  onTrocar?: () => void
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

      {/* Indicador de presença */}
      {performance && (
        <div className="text-center">
          <div className="bg-slate-50 border border-slate-200/80 rounded-xl px-3.5 py-1.5 text-center inline-block">
            <p className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider">Presença</p>
            <p className="mono-font text-base md:text-lg font-bold text-slate-800">
              {performance.detalhes?.nota_assiduidade != null ? `${performance.detalhes.nota_assiduidade.toFixed(0)}%` : "—"}
            </p>
          </div>
        </div>
      )}

      {/* Links e Troca */}
      <div className="flex flex-col items-center gap-1.5 mt-0.5">
        <Link
          to={`/politicos/${data.slug}`}
          className="inline-flex items-center gap-1 text-xs text-blue-600 hover:text-blue-800 font-medium transition-colors"
        >
          <span className="hidden sm:inline">Ver perfil completo</span>
          <span className="sm:hidden">Ver perfil</span>
          <ChevronRight size={11} />
        </Link>
        {onTrocar && (
          <button
            type="button"
            onClick={onTrocar}
            data-testid={`btn-trocar-politico-${data.id}`}
            className="inline-flex items-center gap-1.5 px-3 py-1 rounded-lg text-xs font-semibold text-slate-600 hover:text-blue-700 bg-slate-100 hover:bg-blue-50 border border-slate-200 hover:border-blue-200 transition-all mt-0.5"
          >
            <ArrowLeftRight size={11} />
            <span>Trocar</span>
          </button>
        )}
        {data.id_camara && (
          <a
            href={`https://www.camara.leg.br/deputados/${data.id_camara}`}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-1 text-[11px] text-slate-400 hover:text-blue-600 transition-colors"
          >
            <ExternalLink size={10} />
            <span className="hidden sm:inline">Câmara dos Deputados</span>
          </a>
        )}
      </div>
    </div>
  )
}

// ── LINHA DE COMPARAÇÃO COM BARRAS DIVERGENTES HEAD-TO-HEAD ────────────────

function LinhaComparacao({
  titulo,
  valA,
  valB,
  numA,
  numB,
}: {
  titulo: string
  valA: React.ReactNode
  valB: React.ReactNode
  numA?: number | null
  numB?: number | null
  lowerIsBetter?: boolean
}) {
  const safeA = Number(numA) || 0
  const safeB = Number(numB) || 0
  const maxVal = Math.max(safeA, safeB, 1)
  const pctA = Math.min(100, Math.max(0, (safeA / maxVal) * 100))
  const pctB = Math.min(100, Math.max(0, (safeB / maxVal) * 100))

  return (
    <div className="py-4 border-b border-slate-100 last:border-0">
      {/* Rótulo central com valores */}
      <div className="flex items-center justify-between text-xs mb-2">
        <span className="font-mono font-bold text-sm text-slate-900 tabular-nums">
          {valA}
        </span>
        <span className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider text-center">
          {titulo}
        </span>
        <span className="font-mono font-bold text-sm text-slate-900 tabular-nums">
          {valB}
        </span>
      </div>

      {/* Barra bilateral divergente ancorada ao centro */}
      <div className="grid grid-cols-2 gap-2 items-center">
        {/* Lado A: barra cresce para a esquerda */}
        <div className="h-2 bg-slate-100 rounded-full flex justify-end overflow-hidden">
          <div
            className="h-full bg-slate-900 rounded-full transition-all duration-500"
            style={{ width: `${pctA}%` }}
          />
        </div>
        {/* Lado B: barra cresce para a direita */}
        <div className="h-2 bg-slate-100 rounded-full flex justify-start overflow-hidden">
          <div
            className="h-full bg-slate-600 rounded-full transition-all duration-500"
            style={{ width: `${pctB}%` }}
          />
        </div>
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
  }[] = [
    {
      titulo: "Total de Votações",
      icon: <BadgeCheck size={16} className="text-slate-600" />,
      accent: "slate",
      valA: statsA.total_votacoes,
      valB: statsB.total_votacoes,
      fmt: (v) => v.toString(),
    },
    {
      titulo: "Total de Despesas",
      icon: <Receipt size={16} className="text-slate-600" />,
      accent: "slate",
      valA: statsA.total_despesas,
      valB: statsB.total_despesas,
      fmt: (v) => v.toString(),
    },
    {
      titulo: "Cota Parlamentar",
      icon: <TrendingUp size={16} className="text-slate-600" />,
      accent: "slate",
      valA: statsA.total_gasto,
      valB: statsB.total_gasto,
      fmt: (v) => `R$ ${v.toLocaleString("pt-BR")}`,
    },
    {
      titulo: "Verba de Gabinete",
      icon: <Wallet size={16} className="text-slate-600" />,
      accent: "slate",
      valA: statsA.total_gasto_gabinete ?? 0,
      valB: statsB.total_gasto_gabinete ?? 0,
      fmt: (v) => `R$ ${v.toLocaleString("pt-BR")}`,
    },
    {
      titulo: "Gasto Total",
      icon: <Receipt size={16} className="text-slate-600" />,
      accent: "slate",
      valA: statsA.total_gasto_combinado ?? statsA.total_gasto,
      valB: statsB.total_gasto_combinado ?? statsB.total_gasto,
      fmt: (v) => `R$ ${v.toLocaleString("pt-BR")}`,
    },
    {
      titulo: "Média Mensal",
      icon: <Receipt size={16} className="text-slate-600" />,
      accent: "slate",
      valA: statsA.media_mensal,
      valB: statsB.media_mensal,
      fmt: (v) => `R$ ${v.toLocaleString("pt-BR")}`,
    },
  ]

  return (
    <section className="section-fade">
      <div className="flex items-center gap-2 mb-4">
        <BarChart2 size={18} className="text-slate-700" />
        <h2 className="text-xl font-bold tracking-tight text-slate-900">Estatísticas Fatuais</h2>
      </div>

      {/* Legenda de colunas */}
      <div className="grid grid-cols-2 gap-3 mb-3">
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-white border border-slate-200">
          <div className="w-2.5 h-2.5 rounded-full bg-slate-900 flex-shrink-0" />
          <p className="text-xs font-semibold text-slate-800 truncate">{nomeA}</p>
        </div>
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-white border border-slate-200">
          <div className="w-2.5 h-2.5 rounded-full bg-slate-500 flex-shrink-0" />
          <p className="text-xs font-semibold text-slate-800 truncate">{nomeB}</p>
        </div>
      </div>

      {/* Cards espelhados lado a lado */}
      <div className="grid grid-cols-2 gap-x-3 gap-y-3">
        {metricas.map((m) => (
          <div key={m.titulo} className="contents">
            <StatCard
              icon={m.icon}
              titulo={m.titulo}
              valor={m.fmt(m.valA)}
              accent={m.accent}
            />
            <StatCard
              icon={m.icon}
              titulo={m.titulo}
              valor={m.fmt(m.valB)}
              accent={m.accent}
            />
          </div>
        ))}

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
        <p className="text-[11px] text-slate-500 mt-2 leading-relaxed">
          <strong>Cota Parlamentar (CEAP)</strong> cobre deslocamentos, materiais e serviços de terceiros.{" "}
          <strong>Verba de Gabinete</strong> cobre salários e encargos dos secretários parlamentares.
        </p>
      )}
    </section>
  )
}

// ── BLOCO PERFORMANCE (INDICADORES DE MANDATO) ───────────────────────────────

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
  return (
    <section className="section-fade">
      <div className="flex items-center gap-2 mb-4">
        <TrendingUp size={18} className="text-slate-700" />
        <h2 className="text-xl font-bold tracking-tight text-slate-900">Indicadores de Mandato (Head-to-Head)</h2>
      </div>

      {/* Indicadores linha a linha com barras bilaterais */}
      <div className="bg-white border border-slate-200/90 rounded-xl overflow-hidden shadow-xs">
        <div className="px-5 py-3 border-b border-slate-100 bg-slate-50/50">
          <div className="grid grid-cols-[1fr_auto_1fr] gap-3 items-center">
            <p className="text-left text-xs font-semibold text-slate-900 truncate">{nomeA}</p>
            <div className="min-w-[120px] text-center text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
              Confronto Direto
            </div>
            <p className="text-right text-xs font-semibold text-slate-700 truncate">{nomeB}</p>
          </div>
        </div>
        <div className="px-5 py-1">
          <LinhaComparacao
            titulo="Assiduidade Oficial"
            valA={`${perfA.detalhes?.nota_assiduidade?.toFixed(1) ?? 0}%`}
            valB={`${perfB.detalhes?.nota_assiduidade?.toFixed(1) ?? 0}%`}
            numA={perfA.detalhes?.nota_assiduidade ?? 0}
            numB={perfB.detalhes?.nota_assiduidade ?? 0}
          />
          <LinhaComparacao
            titulo="Uso da Cota (CEAP)"
            valA={`${Number(perfA.info?.cota_utilizada_pct ?? 0).toFixed(1)}%`}
            valB={`${Number(perfB.info?.cota_utilizada_pct ?? 0).toFixed(1)}%`}
            numA={Number(perfA.info?.cota_utilizada_pct ?? 0)}
            numB={Number(perfB.info?.cota_utilizada_pct ?? 0)}
          />
          <LinhaComparacao
            titulo="Proposições com Autoria"
            valA={`${perfA.detalhes?.nota_producao?.toFixed(0) ?? 0}`}
            valB={`${perfB.detalhes?.nota_producao?.toFixed(0) ?? 0}`}
            numA={perfA.detalhes?.nota_producao ?? 0}
            numB={perfB.detalhes?.nota_producao ?? 0}
          />
        </div>
      </div>

      {/* Composição do orçamento */}
      {((perfA.info?.gasto_gabinete ?? 0) > 0 || (perfB.info?.gasto_gabinete ?? 0) > 0) && (
        <div className="mt-4 bg-white border border-slate-200/90 rounded-xl overflow-hidden shadow-xs">
          <div className="px-5 py-3 border-b border-slate-100 bg-slate-50/50">
            <p className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider">
              Composição Orçamentária
            </p>
          </div>

          {[
            { info: perfA.info, nome: nomeA },
            { info: perfB.info, nome: nomeB },
          ].map(({ info, nome }, i) => {
            const pct = info?.orcamento_utilizado_pct ?? info?.cota_utilizada_pct ?? 0
            return (
              <div key={i} className={i === 1 ? "border-t border-slate-200/70" : ""}>
                <div className="px-5 py-2.5 bg-slate-50/30 border-b border-slate-100">
                  <p className="text-xs font-semibold text-slate-700 truncate">{nome}</p>
                </div>
                <div className="grid grid-cols-2 md:grid-cols-4 divide-x divide-slate-100">
                  {[
                    {
                      label: "Cota Parlamentar",
                      value: `R$ ${(info?.total_gasto ?? 0).toLocaleString("pt-BR")}`,
                      sub: "gastos CEAP",
                      color: "text-slate-900",
                    },
                    {
                      label: "Verba de Gabinete",
                      value: `R$ ${(info?.gasto_gabinete ?? 0).toLocaleString("pt-BR")}`,
                      sub: "pessoal / funcionários",
                      color: "text-slate-900",
                    },
                    {
                      label: "Gasto Total",
                      value: `R$ ${(info?.gasto_total ?? 0).toLocaleString("pt-BR")}`,
                      sub: "CEAP + gabinete",
                      color: "text-slate-900",
                    },
                    {
                      label: "Orçamento Utilizado",
                      value: `${pct.toFixed(1)}%`,
                      sub: "do total disponível",
                      color: getOrcamentoColor(pct),
                    },
                  ].map((item) => (
                    <div key={item.label} className="px-5 py-4 text-center">
                      <p className={`font-mono tabular-nums font-bold text-base ${item.color}`}>{item.value}</p>
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

// ── BLOCO ALINHAMENTO EM VOTAÇÕES (APACHE AGE GRAPH) ───────────────────────

function getVoteBadge(voto: string) {
  const v = (voto || "").toLowerCase().trim()
  if (v === "sim") {
    return (
      <span className="inline-flex items-center px-2 py-0.5 rounded-md text-xs font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
        Sim
      </span>
    )
  }
  if (v === "não" || v === "nao") {
    return (
      <span className="inline-flex items-center px-2 py-0.5 rounded-md text-xs font-semibold bg-red-50 text-red-700 border border-red-200">
        Não
      </span>
    )
  }
  if (v.includes("obstrução") || v.includes("obstrucao")) {
    return (
      <span className="inline-flex items-center px-2 py-0.5 rounded-md text-xs font-semibold bg-amber-50 text-amber-700 border border-amber-200">
        Obstrução
      </span>
    )
  }
  if (v.includes("abstenção") || v.includes("abstencao")) {
    return (
      <span className="inline-flex items-center px-2 py-0.5 rounded-md text-xs font-semibold bg-slate-100 text-slate-700 border border-slate-200">
        Abstenção
      </span>
    )
  }
  return (
    <span className="inline-flex items-center px-2 py-0.5 rounded-md text-xs font-semibold bg-slate-100 text-slate-600 border border-slate-200">
      {voto || "—"}
    </span>
  )
}

function BlocoAlinhamentoVotos({
  comparacao,
  loading,
  nomeA,
  nomeB,
  temaFiltro,
  onSelectTema,
  busca,
  onBuscaChange,
}: {
  comparacao?: ComparacaoPoliticosGrafoResponse
  loading: boolean
  nomeA: string
  nomeB: string
  temaFiltro: string | null
  onSelectTema: (tema: string | null) => void
  busca: string
  onBuscaChange: (val: string) => void
}) {
  const [abaAtiva, setAbaAtiva] = useState<"divergencias" | "alinhamentos">("divergencias")

  if (loading && !comparacao) {
    return (
      <section className="section-fade bg-white rounded-2xl border border-slate-200 p-8 text-center shadow-sm">
        <div className="w-8 h-8 border-[3px] border-slate-200 border-t-blue-500 rounded-full animate-spin mx-auto mb-3" />
        <p className="text-xs text-slate-500 font-medium">Cruzando histórico de votações no grafo...</p>
      </section>
    )
  }

  const temFiltroAtivo = Boolean(temaFiltro || busca.trim())

  if (!comparacao || (comparacao.total_votacoes_comuns === 0 && !temFiltroAtivo)) {
    return (
      <section className="section-fade bg-white rounded-2xl border border-slate-200 p-8 text-center shadow-sm">
        <Scale size={28} className="text-slate-300 mx-auto mb-2" />
        <h3 className="text-sm font-semibold text-slate-700">Sem votações nominais comuns registradas</h3>
        <p className="text-xs text-slate-400 mt-1 max-w-md mx-auto">
          Não foram identificadas matérias votadas nominalmente por ambos os parlamentares no período analisado.
        </p>
      </section>
    )
  }

  const lista = abaAtiva === "divergencias" ? comparacao.divergencias : comparacao.alinhamentos
  const temasDisponiveis = comparacao.temas_disponiveis || []

  return (
    <section className="section-fade space-y-4">
      {/* Cabeçalho da seção */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-xl bg-blue-50 flex items-center justify-center text-blue-600">
            <Scale size={18} />
          </div>
          <div>
            <h2 className="display-font text-xl font-bold text-slate-800">
              Alinhamento em Votações
            </h2>
            <p className="text-xs text-slate-400">
              Cruzamento factual de posicionamentos em matérias comuns no plenário
            </p>
          </div>
        </div>

        {/* Badge da fonte dos dados */}
        <div className="flex items-center gap-2">
          {comparacao.fonte_dados === "apache_age_graph" ? (
            <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium bg-indigo-50 text-indigo-700 border border-indigo-100 shadow-sm">
              <span className="w-1.5 h-1.5 rounded-full bg-indigo-500 animate-pulse" />
              Grafo Apache AGE
            </span>
          ) : (
            <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium bg-slate-100 text-slate-600 border border-slate-200">
              Reconciliação Relacional
            </span>
          )}
        </div>
      </div>

      {/* Caixa de Busca e Filtros de Matérias de Grande Repercussão */}
      <div className="bg-white rounded-2xl border border-slate-200 p-4 sm:p-5 shadow-sm space-y-3.5">
        {/* Topo do bloco de filtros: Título e botão limpar */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
          <div className="flex items-center gap-2">
            <Flame size={16} className="text-amber-500 flex-shrink-0" />
            <h3 className="text-xs sm:text-sm font-bold text-slate-800">
              Principais Votações & Temas em Destaque
            </h3>
          </div>
          {temFiltroAtivo && (
            <button
              type="button"
              onClick={() => {
                onSelectTema(null)
                onBuscaChange("")
              }}
              className="text-[11px] font-semibold text-blue-600 hover:text-blue-800 transition-colors flex items-center gap-1 self-start sm:self-auto"
            >
              <X size={13} />
              Limpar todos os filtros
            </button>
          )}
        </div>

        {/* Input de Busca Textual Inteligente */}
        <div className="relative flex items-center">
          <Search size={15} className="absolute left-3.5 text-slate-400 pointer-events-none" />
          <input
            type="text"
            value={busca}
            onChange={(e) => onBuscaChange(e.target.value)}
            placeholder="Buscar por tema ou proposição (ex: escala 6x1, previdência, PEC 221, armas, reforma)..."
            className="w-full pl-9 pr-9 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-xs sm:text-sm text-slate-800 placeholder-slate-400 focus:outline-none focus:bg-white focus:border-blue-500 focus:ring-2 focus:ring-blue-100 transition-all min-h-[42px]"
          />
          {busca && (
            <button
              type="button"
              onClick={() => onBuscaChange("")}
              className="absolute right-3 text-slate-400 hover:text-slate-600 p-1"
              aria-label="Limpar busca"
            >
              <X size={14} />
            </button>
          )}
        </div>

        {/* Pílulas de Temas Populares com Rolagem Horizontal Touch no Mobile */}
        <div>
          <p className="text-[11px] font-medium text-slate-400 mb-1.5">
            Matérias de alta repercussão:
          </p>
          <div className="flex items-center gap-1.5 overflow-x-auto pb-1.5 scrollbar-none -mx-1 px-1 touch-pan-x flex-nowrap sm:flex-wrap">
            {PRINCIPAIS_VOTACOES_DESTAQUE.map((item) => {
              const isSelected = busca.toLowerCase().trim() === item.query.toLowerCase().trim()
              return (
                <button
                  key={item.query}
                  type="button"
                  onClick={() => onBuscaChange(isSelected ? "" : item.query)}
                  className={`flex-shrink-0 inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-medium transition-all border min-h-[38px] ${
                    isSelected
                      ? "bg-blue-600 text-white border-blue-600 shadow-sm"
                      : "bg-slate-50 text-slate-700 border-slate-200 hover:bg-slate-100 hover:border-slate-300"
                  }`}
                >
                  <span>{item.label}</span>
                  {isSelected && <Check size={12} className="text-white ml-0.5" />}
                </button>
              )
            })}
          </div>
        </div>

        {/* Filtros de Tema Legislativo Formal da Câmara */}
        {temasDisponiveis.length > 0 && (
          <div className="pt-2.5 border-t border-slate-100">
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center gap-1.5 text-slate-500 text-[11px] font-medium">
                <Tag size={13} className="text-slate-400" />
                <span>Temas formais da Câmara:</span>
              </div>
              {temaFiltro && (
                <button
                  type="button"
                  onClick={() => onSelectTema(null)}
                  className="text-[10px] text-slate-400 hover:text-slate-600 underline"
                >
                  remover tema
                </button>
              )}
            </div>
            <div className="flex items-center gap-1.5 overflow-x-auto pb-1.5 scrollbar-none -mx-1 px-1 touch-pan-x flex-nowrap sm:flex-wrap">
              <button
                type="button"
                onClick={() => onSelectTema(null)}
                className={`flex-shrink-0 px-2.5 py-1 rounded-lg text-[11px] font-medium transition-all ${
                  !temaFiltro
                    ? "bg-slate-800 text-white"
                    : "bg-slate-100 text-slate-600 hover:bg-slate-200"
                }`}
              >
                Todos
              </button>
              {temasDisponiveis.map((t) => {
                const isSelected = temaFiltro?.toLowerCase() === t.tema.toLowerCase()
                return (
                  <button
                    key={t.tema}
                    type="button"
                    onClick={() => onSelectTema(isSelected ? null : t.tema)}
                    className={`flex-shrink-0 inline-flex items-center gap-1 px-2.5 py-1 rounded-lg text-[11px] font-medium transition-all border ${
                      isSelected
                        ? "bg-indigo-600 text-white border-indigo-600 shadow-sm"
                        : "bg-white text-slate-600 border-slate-200 hover:bg-slate-50"
                    }`}
                  >
                    <span>{t.tema}</span>
                    <span
                      className={`px-1 py-0.1 rounded text-[9px] font-semibold ${
                        isSelected
                          ? "bg-indigo-500/50 text-white"
                          : "bg-slate-100 text-slate-500"
                      }`}
                    >
                      {t.total_votacoes}
                    </span>
                  </button>
                )
              })}
            </div>
          </div>
        )}
      </div>

      {/* Cards de Métricas de Alinhamento */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
        {/* Taxa de Alinhamento */}
        <div className="bg-white rounded-2xl border border-slate-200 p-5 shadow-sm">
          <p className="text-[11px] font-semibold text-slate-400 uppercase tracking-wide mb-1 truncate">
            Taxa de Alinhamento {busca ? `("${busca}")` : temaFiltro ? `(${temaFiltro})` : ""}
          </p>
          <div className="flex items-baseline gap-2">
            <span className="mono-font text-3xl font-bold text-slate-800">
              {comparacao.taxa_alinhamento.toFixed(1)}%
            </span>
            <span className="text-xs text-slate-400">de concordância</span>
          </div>
          <div className="w-full bg-slate-100 h-2 rounded-full mt-3 overflow-hidden">
            <div
              className="h-full transition-all duration-500 bg-blue-600 rounded-full"
              style={{ width: `${comparacao.taxa_alinhamento}%` }}
            />
          </div>
        </div>

        {/* Votações Comuns */}
        <div className="bg-white rounded-2xl border border-slate-200 p-5 shadow-sm">
          <p className="text-[11px] font-semibold text-slate-400 uppercase tracking-wide mb-1">
            Votações em Comum
          </p>
          <div className="flex items-baseline gap-2">
            <span className="mono-font text-3xl font-bold text-slate-800">
              {comparacao.total_votacoes_comuns}
            </span>
            <span className="text-xs text-slate-400">matérias avaliadas</span>
          </div>
          <p className="text-xs text-slate-500 mt-3 flex items-center gap-1.5">
            <CheckCircle2 size={13} className="text-emerald-500" />
            {comparacao.votos_alinhados} votos em conjunto
          </p>
        </div>

        {/* Votos Divergentes */}
        <div className="bg-white rounded-2xl border border-slate-200 p-5 shadow-sm">
          <p className="text-[11px] font-semibold text-slate-400 uppercase tracking-wide mb-1">
            Divergências Nominais
          </p>
          <div className="flex items-baseline gap-2">
            <span className="mono-font text-3xl font-bold text-slate-800">
              {comparacao.votos_divergentes}
            </span>
            <span className="text-xs text-slate-400">votos opostos</span>
          </div>
          <p className="text-xs text-slate-500 mt-3 flex items-center gap-1.5">
            <XCircle size={13} className="text-red-500" />
            {comparacao.total_votacoes_comuns > 0
              ? `${((comparacao.votos_divergentes / comparacao.total_votacoes_comuns) * 100).toFixed(1)}% de discordância`
              : "0% de discordância"}
          </p>
        </div>
      </div>

      {/* Tabs / Alternador Divergências vs Alinhamentos */}
      <div className="bg-white rounded-2xl border border-slate-200 overflow-hidden shadow-sm">
        <div className="flex border-b border-slate-100 bg-slate-50/70 p-1.5 gap-1.5">
          <button
            type="button"
            onClick={() => setAbaAtiva("divergencias")}
            className={`flex-1 flex items-center justify-center gap-2 py-2 px-4 rounded-xl text-xs font-semibold transition-all ${
              abaAtiva === "divergencias"
                ? "bg-white text-slate-800 shadow-sm border border-slate-200/80"
                : "text-slate-500 hover:text-slate-700 hover:bg-slate-100/50"
            }`}
          >
            <XCircle size={14} className={abaAtiva === "divergencias" ? "text-red-500" : "text-slate-400"} />
            Principais Divergências ({comparacao.votos_divergentes})
          </button>
          <button
            type="button"
            onClick={() => setAbaAtiva("alinhamentos")}
            className={`flex-1 flex items-center justify-center gap-2 py-2 px-4 rounded-xl text-xs font-semibold transition-all ${
              abaAtiva === "alinhamentos"
                ? "bg-white text-slate-800 shadow-sm border border-slate-200/80"
                : "text-slate-500 hover:text-slate-700 hover:bg-slate-100/50"
            }`}
          >
            <CheckCircle2 size={14} className={abaAtiva === "alinhamentos" ? "text-emerald-500" : "text-slate-400"} />
            Votos Alinhados ({comparacao.votos_alinhados})
          </button>
        </div>

        {/* Lista de Votações */}
        <div className="divide-y divide-slate-100 max-h-[520px] overflow-y-auto">
          {lista.length === 0 ? (
            <div className="p-8 text-center text-xs text-slate-500 space-y-3">
              <p>
                {temFiltroAtivo
                  ? `Nenhuma votação encontrada para os filtros selecionados ${
                      busca ? `(busca: "${busca}")` : ""
                    } ${temaFiltro ? `(tema: "${temaFiltro}")` : ""} nesta categoria.`
                  : "Nenhuma votação nesta categoria."}
              </p>
              {temFiltroAtivo && (
                <button
                  type="button"
                  onClick={() => {
                    onSelectTema(null)
                    onBuscaChange("")
                  }}
                  className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-blue-50 text-blue-600 hover:bg-blue-100 font-medium transition-colors"
                >
                  <X size={13} />
                  Limpar filtros de busca
                </button>
              )}
            </div>
          ) : (
            lista.map((item) => (
              <div key={item.id_votacao} className="p-4 hover:bg-slate-50/50 transition-colors">
                <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-3">
                  <div className="flex-1 min-w-0">
                    <div className="flex flex-wrap items-center gap-1.5 mb-1.5">
                      {item.proposicao ? (
                        <a
                          href={`https://www.camara.leg.br/busca-portal?contextoBusca=BuscaProposicoes&termo=${encodeURIComponent(
                            item.proposicao
                          )}`}
                          target="_blank"
                          rel="noreferrer"
                          title="Consultar proposição na Câmara dos Deputados"
                          className="mono-font text-[11px] font-semibold px-2 py-0.5 rounded-md bg-blue-50 text-blue-700 border border-blue-100 hover:bg-blue-100 inline-flex items-center gap-1 transition-colors"
                        >
                          <span>{item.proposicao}</span>
                          <ExternalLink size={10} className="text-blue-500" />
                        </a>
                      ) : (
                        <span className="mono-font text-[11px] font-semibold px-2 py-0.5 rounded-md bg-slate-100 text-slate-600">
                          Votação #{item.id_votacao}
                        </span>
                      )}
                      {item.temas && item.temas.length > 0 && item.temas.slice(0, 3).map((tm) => (
                        <span
                          key={tm}
                          className="text-[10px] font-medium px-2 py-0.5 rounded-md bg-slate-100 text-slate-600 border border-slate-200/60"
                        >
                          {tm}
                        </span>
                      ))}
                      {item.data && (
                        <span className="text-[11px] text-slate-400 ml-auto sm:ml-0">{item.data}</span>
                      )}
                    </div>
                    <p className="text-xs text-slate-700 font-medium line-clamp-2 leading-relaxed">
                      {item.ementa || item.descricao || "Sem descrição disponível"}
                    </p>
                  </div>

                  {/* Comparativo lado a lado dos votos */}
                  <div className="flex items-center gap-3 sm:gap-6 flex-shrink-0 pt-2 sm:pt-0">
                    <div className="text-right">
                      <p className="text-[10px] text-slate-400 font-medium truncate max-w-[90px]">{nomeA}</p>
                      {getVoteBadge(item.voto_politico1)}
                    </div>
                    <div className="text-slate-300 text-xs">vs</div>
                    <div className="text-left">
                      <p className="text-[10px] text-slate-400 font-medium truncate max-w-[90px]">{nomeB}</p>
                      {getVoteBadge(item.voto_politico2)}
                    </div>
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </section>
  )
}

// ── PAGE ────────────────────────────────────────────────────────────────────

export default function ComparacaoPoliticos() {
  const navigate = useNavigate()
  const { slug1: slugA, slug2: slugB } = useParams<{ slug1: string; slug2: string }>()
  const [temaFiltro, setTemaFiltro] = useState<string | null>(null)
  const [buscaVotacao, setBuscaVotacao] = useState<string>("")
  const buscaDebounced = useDebounce(buscaVotacao.trim(), 400)
  const [trocandoLado, setTrocandoLado] = useState<"A" | "B" | null>(null)

  const isSlugAInvalido = !slugA || slugA === "null" || slugA === "undefined"
  const isSlugBInvalido = !slugB || slugB === "null" || slugB === "undefined"

  const { data: dataA, isLoading: loadA, error: errA } = usePoliticoDetalheBySlug(
    isSlugAInvalido ? undefined : slugA
  )
  const { data: dataB, isLoading: loadB, error: errB } = usePoliticoDetalheBySlug(
    isSlugBInvalido ? undefined : slugB
  )

  const { data: statsA } = usePoliticoEstatisticas(dataA?.id ?? 0, null)
  const { data: statsB } = usePoliticoEstatisticas(dataB?.id ?? 0, null)
  const { data: perfA  } = usePoliticoPerformance(dataA?.id ?? 0, null)
  const { data: perfB  } = usePoliticoPerformance(dataB?.id ?? 0, null)

  const idOrSlug1 = dataA?.slug || (dataA?.id ? String(dataA.id) : slugA)
  const idOrSlug2 = dataB?.slug || (dataB?.id ? String(dataB.id) : slugB)

  const { data: compData, isLoading: loadComp } = useComparacaoPoliticos(
    dataA && dataB ? idOrSlug1 : undefined,
    dataA && dataB ? idOrSlug2 : undefined,
    {
      tema: temaFiltro || undefined,
      q: buscaDebounced || undefined,
    }
  )

  if (loadA || loadB) return <LoadingScreen />
  if (isSlugAInvalido || isSlugBInvalido || errA || errB || !dataA || !dataB) return <ErrorScreen />

  const primeiroNomeA = dataA.nome.split(" ")[0]
  const primeiroNomeB = dataB.nome.split(" ")[0]

  return (
    <>
      <SeoHead nomeA={dataA.nome} nomeB={dataB.nome} />

      <style>{`
        .detail-root  { font-family: 'DM Sans', sans-serif; }
        .display-font { font-family: 'DM Sans', sans-serif; }
        .mono-font    { font-family: 'DM Mono', monospace; font-variant-numeric: tabular-nums; }

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
          background: #f1f5f9;
        }

        .section-fade { animation: sectionFade 0.3s ease both; }
        @keyframes sectionFade {
          from { opacity: 0.4; transform: translateY(4px); }
          to   { opacity: 1; transform: translateY(0); }
        }
      `}</style>

      <div className="detail-root min-h-screen bg-canvas">
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
                  <div className="flex items-center gap-1.5 text-sm text-slate-400 group min-w-0">
                    <Link
                      to="/comparar"
                      className="inline-flex items-center gap-1 text-slate-400 hover:text-blue-600 transition-colors flex-shrink-0"
                    >
                      <ArrowLeft size={14} className="group-hover:-translate-x-0.5 transition-transform" />
                      <span>Comparador</span>
                    </Link>
                    <ChevronRight size={12} className="opacity-50 flex-shrink-0" />
                    <Link
                      to={`/politicos/${dataA.slug}`}
                      className="truncate text-slate-500 hover:text-slate-800 transition-colors hidden sm:inline"
                    >
                      {dataA.nome}
                    </Link>
                    <ChevronRight size={12} className="opacity-50 flex-shrink-0 hidden sm:inline" />
                    <span className="text-slate-700 font-medium flex-shrink-0">Confronto</span>
                  </div>

                  <div className="flex items-center gap-2 flex-shrink-0">
                    {compData && compData.total_votacoes_comuns > 0 && (
                      <span className="hidden md:inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-indigo-50 border border-indigo-100 text-indigo-700 text-xs font-semibold">
                        <Scale size={13} />
                        {compData.taxa_alinhamento.toFixed(0)}% de alinhamento
                      </span>
                    )}
                    <button
                      type="button"
                      onClick={() => {
                        const sA = dataA.slug || slugA
                        const sB = dataB.slug || slugB
                        navigate(`/comparar/${sB}/${sA}`)
                      }}
                      data-testid="btn-inverter-lados"
                      title="Inverter ordem dos parlamentares"
                      className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-slate-100 hover:bg-blue-50 text-slate-700 hover:text-blue-700 text-xs font-semibold border border-slate-200 hover:border-blue-200 transition-all shadow-xs"
                    >
                      <ArrowLeftRight size={13} />
                      <span className="hidden sm:inline">Inverter lados</span>
                      <span className="sm:hidden">Inverter</span>
                    </button>
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
                <ColunaPerfil
                  data={dataA}
                  performance={perfA}
                  onTrocar={() => setTrocandoLado("A")}
                />
                {/* Divisor vertical — só desktop */}
                <div className="hidden md:block absolute left-1/2 top-0 bottom-0 w-px bg-slate-100 -translate-x-1/2 pointer-events-none" />
                <ColunaPerfil
                  data={dataB}
                  performance={perfB}
                  onTrocar={() => setTrocandoLado("B")}
                />
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

          {/* ── ALINHAMENTO EM VOTAÇÕES (APACHE AGE GRAPH) ── */}
          <BlocoAlinhamentoVotos
            comparacao={compData}
            loading={loadComp}
            nomeA={primeiroNomeA}
            nomeB={primeiroNomeB}
            temaFiltro={temaFiltro}
            onSelectTema={setTemaFiltro}
            busca={buscaVotacao}
            onBuscaChange={setBuscaVotacao}
          />

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

      {/* ── MODAL TROCAR PARLAMENTAR ── */}
      {trocandoLado && (
        <ModalSelecionarPolitico
          politicoAtualId={trocandoLado === "A" ? dataB.id : dataA.id}
          politicoAtualSlug={trocandoLado === "A" ? (dataB.slug || slugB!) : (dataA.slug || slugA!)}
          titulo={trocandoLado === "A" ? "Substituir 1º Parlamentar" : "Substituir 2º Parlamentar"}
          onClose={() => setTrocandoLado(null)}
          onSelect={(novoPolitico) => {
            const novoSlug =
              novoPolitico.slug || nomeParaSlug(novoPolitico.nome) || String(novoPolitico.id)
            if (trocandoLado === "A") {
              navigate(`/comparar/${novoSlug}/${dataB.slug || slugB}`)
            } else {
              navigate(`/comparar/${dataA.slug || slugA}/${novoSlug}`)
            }
          }}
        />
      )}
    </>
  )
}