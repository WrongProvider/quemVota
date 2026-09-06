import { useState, useMemo, useEffect } from "react"
import { useParams, Link, useNavigate } from "react-router-dom"
import {
  usePoliticoEstatisticas,
  usePoliticoDetalhe,
  usePoliticoDetalheBySlug,
  usePoliticoPerformance,
  usePoliticoTimeline,
  usePoliticoAtividade,
} from "../hooks/usePoliticos"
import PoliticoGraficos from "../components/PoliticoGraficos"
import LinhaDoTempo from "../components/LinhaDoTempo"
import PainelTemasAtuacao from "../components/PainelTemasAtuacao"
import PainelFidelidadePartidaria from "../components/PainelFidelidadePartidaria"
import PainelRadarAfinidades from "../components/PainelRadarAfinidades"
import PainelRedeCoautoria from "../components/PainelRedeCoautoria"
import HistoricoProjetos from "../components/HistoricoProjetos"
import InfoBotao from "../components/InfoDicaBotao"
import ToolDica from "../components/InfoDica"
import Header from "../components/Header"
import useIsMobile from "../hooks/useIsMobile"
import {
  MapPin,
  Users,
  GraduationCap,
  BadgeCheck,
  Mail,
  Phone,
  BarChart2,
  Layers,
  TrendingUp,
  Receipt,
  Wallet,
  Calendar,
  ChevronRight,
  ArrowLeft,
  ChevronLeft,
  ExternalLink,
  Share2,
  Copy,
  Check,
  Vote,
  CheckCircle2,
  XCircle,
  MinusCircle,
  ChevronDown,
  Loader2,
  ArrowLeftRight,
  AlertCircle,
  Clock,
  FileText,
  Search,
  X,
  Building2,
  Tag,
  Flame,
  ArrowUp,
  Compass,
  GitFork,
  Scale,
  SlidersHorizontal,
} from "lucide-react"
import { useRegistrarBusca } from "../hooks/useBuscaPopular"
import { useVotacao } from "../hooks/useProposicoes"
import { useDebounce } from "../hooks/useDebounce"
import { type VotacaoResumida, nomeParaSlug } from "../api/politicos.api"
import ModalSelecionarPolitico from "../components/ModalSelecionarPolitico"
import { formatarMoedaBRL, formatarNumero } from "../utils/formatters"
import PerfilHistorico from "../components/PerfilHistorico"

const PATH_FOTOS = "/fotos_politicos/"

// ── SEO HEAD ────────────────────────────────────────────────────────────────

import { useSeo, BASE_URL } from "../hooks/useSeo"

/**
 * Injeta meta tags SEO, Open Graph, Twitter Card, canonical e
 * JSON-LD Person (rich snippet) dinamicamente no <head>.
 */
function SeoHead({
  nome,
  partido,
  uf,
  fotoUrl,
  pageUrl,
}: {
  nome: string
  partido?: string
  uf?: string
  fotoUrl: string
  pageUrl: string
}) {
  const localTexto = [partido, uf].filter(Boolean).join(" • ")

  useSeo({
    title: `${nome} — Perfil Parlamentar${localTexto ? ` | ${localTexto}` : ""}`,
    description:
      `Veja o perfil completo de ${nome}${localTexto ? ` (${localTexto})` : ""}` +
      `. Gastos, votações e atividade parlamentar.`,
    url: pageUrl,
    image: fotoUrl,
    type: "profile",
    keywords: `${nome}, deputado federal, ${partido ?? ""}, ${uf ?? ""}, perfil parlamentar`,
    jsonLd: {
      "@context": "https://schema.org",
      "@type": "Person",
      name: nome,
      jobTitle: "Deputado Federal",
      ...(partido && {
        memberOf: {
          "@type": "Organization",
          name: partido,
        },
      }),
      ...(uf && {
        address: {
          "@type": "PostalAddress",
          addressRegion: uf,
          addressCountry: "BR",
        },
      }),
      ...(fotoUrl && { image: fotoUrl }),
      url: pageUrl,
      sameAs: [
        `https://www.camara.leg.br`,
      ],
      worksFor: {
        "@type": "GovernmentOrganization",
        name: "Câmara dos Deputados",
        url: "https://www.camara.leg.br",
      },
    },
  })

  return null
}

// ── SHARE BUTTON ────────────────────────────────────────────────────────────

function BotoesCompartilhamento({ nome, url }: { nome: string; url: string }) {
  const [copiado, setCopiado] = useState(false)
  const [aberto, setAberto] = useState(false)

  const texto = `Veja o perfil parlamentar de ${nome}`

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
        className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-white hover:bg-slate-50 text-slate-700 text-sm font-medium transition-colors border border-slate-300 hover:border-slate-400 shadow-sm"
      >
        <Share2 size={15} />
        <span className="hidden sm:inline">Compartilhar</span>
        <span className="sm:hidden">Share</span>
      </button>

      {aberto && (
        <>
          {/* overlay para fechar ao clicar fora */}
          <div className="fixed inset-0 z-10" onClick={() => setAberto(false)} />

          <div className="absolute right-0 mt-2 z-20 bg-white rounded-2xl shadow-xl border border-slate-100 p-3 min-w-[200px]">
            <p className="text-[11px] text-slate-400 font-medium uppercase tracking-wide px-2 mb-2">
              Compartilhar perfil
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

// ── TIMELINE YEAR SELECTOR ──────────────────────────────────────────────────
function TimelineSelector({
  anos,
  anoSelecionado,
  onChange,
}: {
  anos: number[]
  anoSelecionado: number | null
  onChange: (ano: number | null) => void
}) {
  if (!anos.length) return null

  return (
    <div
      className="bg-white border border-slate-200/90 rounded-2xl shadow-2xs overflow-hidden"
      data-testid="year-selector-container"
    >
      <div className="bg-slate-50 border-b border-slate-100 px-4 sm:px-6 py-2.5 flex flex-col sm:flex-row sm:items-center justify-between gap-2 text-center sm:text-left">
        <p className="text-xs sm:text-sm font-medium text-slate-600 flex items-center justify-center sm:justify-start gap-1.5">
          <Calendar size={14} className="text-slate-400 flex-shrink-0" />
          {anoSelecionado ? (
            <>
              Exibindo dados de <strong className="text-slate-900 font-bold">{anoSelecionado}</strong>
            </>
          ) : (
            "Selecione um ano abaixo ou veja o mandato completo"
          )}
        </p>
        <span className="text-[11px] text-slate-400 hidden sm:inline">
          Informações disponíveis desde {anos[0]}
        </span>
      </div>

      <div className="p-3 sm:p-4">
        {/* Mobile & Desktop: botões responsivos com scroll horizontal suave */}
        <div className="flex flex-wrap items-center justify-center gap-2">
          {/* Botão "Tudo" */}
          <button
            onClick={() => onChange(null)}
            data-testid="year-button-all"
            className={`flex items-center justify-center min-w-[3.5rem] px-3.5 h-9 rounded-xl border text-xs font-bold transition-all ${
              anoSelecionado === null
                ? "bg-slate-700 border-slate-700 text-white shadow-xs"
                : "bg-white border-slate-200 text-slate-600 hover:border-slate-300 hover:bg-slate-50"
            }`}
            title="Mandato completo"
          >
            ∑ Todos
          </button>

          {anos.map((ano) => {
            const ativo = ano === anoSelecionado
            return (
              <button
                key={ano}
                onClick={() => onChange(ativo ? null : ano)}
                data-testid={`year-button-${ano}`}
                className={`flex items-center justify-center px-3.5 h-9 rounded-xl border text-xs font-semibold transition-all ${
                  ativo
                    ? "bg-yellow-400 border-yellow-400 text-white shadow-xs scale-105"
                    : "bg-white border-slate-200 text-slate-600 hover:border-blue-400 hover:text-blue-600 hover:bg-blue-50/50"
                }`}
              >
                {ano}
              </button>
            )
          })}
        </div>
      </div>
    </div>
  )
}

// ── PAGE ────────────────────────────────────────────────────────────────────
export default function PoliticoDetalhe() {
  const { id: idOuSlug } = useParams<{ id: string }>()
  const navigate = useNavigate()

  const isNumerico = /^\d+$/.test(idOuSlug ?? "")

  const [anoSelecionado, setAnoSelecionado] = useState<number | null>(null)
  const [abaAtiva, setAbaAtiva] = useState<"visao-geral" | "votacoes" | "projetos" | "conexoes" | "gastos" | "atuacao">("visao-geral")
  const [subAbaLegislativa, setSubAbaLegislativa] = useState<"votacoes" | "projetos">("votacoes")
  const [subAbaConexoes, setSubAbaConexoes] = useState<"afinidades" | "coautoria" | "fidelidade">(() => {
    if (typeof window !== "undefined") {
      const hash = window.location.hash.toLowerCase()
      if (hash.includes("coautoria")) return "coautoria"
      if (hash.includes("fidelidade")) return "fidelidade"
    }
    return "afinidades"
  })
  const [mostrarVoltarAoTopo, setMostrarVoltarAoTopo] = useState(false)
  const [avisoSaidaAberto, setAvisoSaidaAberto] = useState(false)
  const [modalCompararAberto, setModalCompararAberto] = useState(false)

  const scrollParaSecao = (id: string, aba: "visao-geral" | "votacoes" | "projetos" | "conexoes" | "gastos" | "atuacao") => {
    setAbaAtiva(aba)
    if (aba === "votacoes") {
      setSubAbaLegislativa("votacoes")
    } else if (aba === "projetos") {
      setSubAbaLegislativa("projetos")
    }

    let targetId = id
    if (aba === "votacoes" || aba === "projetos") targetId = "section-atividade-legislativa"
    if (aba === "conexoes") targetId = "section-conexoes"

    const el =
      document.querySelector(`[data-testid="${targetId}"]`) ||
      document.getElementById(targetId) ||
      document.querySelector(`[data-testid="${id}"]`) ||
      document.getElementById(id)
    if (el) {
      const topOffset = 130
      const elementPosition = el.getBoundingClientRect().top + window.pageYOffset
      window.scrollTo({
        top: Math.max(elementPosition - topOffset, 0),
        behavior: "smooth",
      })
    }
  }

  useEffect(() => {
    const secoes = [
      { id: "section-stats", aba: "visao-geral" as const },
      { id: "section-atividade-legislativa", aba: (subAbaLegislativa === "projetos" ? "projetos" : "votacoes") as const },
      { id: "section-conexoes", aba: "conexoes" as const },
      { id: "section-historico-de-gastos", aba: "gastos" as const },
      { id: "section-atuacao", aba: "atuacao" as const },
    ]

    const handleScroll = () => {
      setMostrarVoltarAoTopo(window.scrollY > 400)
      const scrollPos = window.scrollY + 200
      for (const sec of secoes.slice().reverse()) {
        const el = document.querySelector(`[data-testid="${sec.id}"]`) || document.getElementById(sec.id)
        if (el && el.getBoundingClientRect().top + window.scrollY <= scrollPos) {
          setAbaAtiva(sec.aba)
          break
        }
      }
    }

    window.addEventListener("scroll", handleScroll, { passive: true })
    return () => window.removeEventListener("scroll", handleScroll)
  }, [subAbaLegislativa])

  // Busca por ID numérico (legado) ou por slug (canônico)
  const porId   = usePoliticoDetalhe(isNumerico ? Number(idOuSlug) : 0)
  const porSlug = usePoliticoDetalheBySlug(isNumerico ? undefined : idOuSlug)

  const { data, isLoading, error } = isNumerico ? porId : porSlug

  const { data: timeline, isLoading: timelineLoading } = usePoliticoTimeline(data?.id ?? 0)
  const { data: stats } = usePoliticoEstatisticas(data?.id ?? 0, anoSelecionado)
  const { data: performance } = usePoliticoPerformance(data?.id ?? 0, anoSelecionado)

  const anosDisponiveis = useMemo(
    () => (timeline ?? []).map((t: { ano: number }) => t.ano).sort((a: number, b: number) => a - b),
    [timeline]
  )

  const { mutate: registrarBusca } = useRegistrarBusca()

  // Registra busca e redireciona ID numérico para o slug canônico do banco
  useEffect(() => {
    if (!data) return
    registrarBusca(data.id)

    if (isNumerico && data.slug) {
      navigate(`/politicos/${data.slug}`, { replace: true })
    }
  }, [data?.id])

  if (isLoading) return <LoadingScreen />
  if (error) return <ErrorScreen />
  if (!data) return null

  // ── Detecção de Perfil Histórico ──────────────────────────────────────────
  // Ativa quando não há absolutamente nenhum dado digitalizado: nenhuma
  // votação, nenhuma despesa e nenhum ano disponível na timeline.
  // Ocorre com parlamentares de mandatos anteriores à 52ª Legislatura (2003),
  // quando a Câmara não disponibilizava registros eletrônicos.
  const isPerfilHistorico =
    !timelineLoading &&
    stats != null &&
    stats.total_votacoes === 0 &&
    stats.total_despesas === 0 &&
    stats.total_gasto === 0 &&
    anosDisponiveis.length === 0

  if (isPerfilHistorico) return <PerfilHistorico data={data} />

  const pageUrl = `${BASE_URL}/politicos/${data.slug}`
  const fotoAbsoluta = `${BASE_URL}${PATH_FOTOS}${data.id}.jpg`

  return (
    <>
      {/* ── SEO META TAGS ── */}
      <SeoHead
        nome={data.nome}
        partido={data.sigla_partido}
        uf={data.sigla_uf}
        fotoUrl={fotoAbsoluta}
        pageUrl={pageUrl}
      />

      <style>{`
        .detail-root { font-family: 'DM Sans', sans-serif; }
        .display-font { font-family: 'DM Sans', sans-serif; font-weight: 700; letter-spacing: -0.02em; }
        .mono-font { font-family: 'DM Mono', monospace; font-variant-numeric: tabular-nums; }

        .profile-photo {
          animation: photoReveal 0.7s cubic-bezier(0.22, 1, 0.36, 1) both;
        }
        @keyframes photoReveal {
          from { opacity: 0; transform: scale(0.92) translateY(12px); }
          to   { opacity: 1; transform: scale(1) translateY(0); }
        }

        .stat-card {
          animation: cardSlide 0.5s cubic-bezier(0.22, 1, 0.36, 1) both;
        }
        .stat-card:nth-child(1) { animation-delay: 0.05s; }
        .stat-card:nth-child(2) { animation-delay: 0.10s; }
        .stat-card:nth-child(3) { animation-delay: 0.15s; }
        .stat-card:nth-child(4) { animation-delay: 0.20s; }
        .stat-card:nth-child(5) { animation-delay: 0.25s; }
        .stat-card:nth-child(6) { animation-delay: 0.30s; }
        @keyframes cardSlide {
          from { opacity: 0; transform: translateY(16px); }
          to   { opacity: 1; transform: translateY(0); }
        }

        .hero-fade {
          animation: heroFade 0.6s ease both;
        }
        @keyframes heroFade {
          from { opacity: 0; transform: translateY(-8px); }
          to   { opacity: 1; transform: translateY(0); }
        }

        .pill-badge {
          background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%);
        }

        .section-fade {
          animation: sectionFade 0.3s ease both;
        }
        @keyframes sectionFade {
          from { opacity: 0.4; transform: translateY(4px); }
          to   { opacity: 1; transform: translateY(0); }
        }
      `}</style>

      <div className="detail-root min-h-screen bg-[#f8f9fb]">
        <Header />

        {/* ── HERO SECTION ── */}
        <div className="pt-16">
          <div className="relative overflow-hidden bg-white border-b border-slate-100">
            <div
              className="absolute inset-0 opacity-[0.03]"
              style={{
                backgroundImage:
                  "radial-gradient(circle at 80% 50%, #2563eb 0%, transparent 60%), radial-gradient(circle at 20% 80%, #7c3aed 0%, transparent 50%)",
              }}
            />

            <div className="relative max-w-5xl mx-auto px-6 py-12 hero-fade">
              {/* Back breadcrumb + Botões */}
              <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 mb-8">
                <Link
                  to="/politicos"
                  className="inline-flex items-center gap-1.5 text-sm text-slate-400 hover:text-slate-700 transition-colors group"
                >
                  <ArrowLeft size={14} className="group-hover:-translate-x-0.5 transition-transform" />
                  Parlamentares
                  <ChevronRight size={12} className="opacity-50" />
                  <span className="text-slate-600 font-medium">{data.nome}</span>
                </Link>

                {/* ── BOTÕES DE AÇÃO ── */}
                <div className="flex items-center gap-2">
                  {/* ── LINK OFICIAL DA CÂMARA ── */}
                  <a
                    href={`https://www.camara.leg.br/deputados/${data.id_camara}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-xl border border-slate-200 bg-white hover:bg-slate-50 text-slate-700 text-xs font-medium transition-colors shadow-2xs"
                  >
                    <ExternalLink size={13} className="text-slate-400" />
                    <span className="hidden sm:inline">Ficha na Câmara</span>
                    <span className="sm:hidden">Câmara</span>
                  </a>

                  {/* ── BOTÃO COMPARAR ── */}
                  <button
                    onClick={() => setModalCompararAberto(true)}
                    data-testid="btn-comparar"
                    className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-blue-600 hover:bg-blue-700 active:bg-blue-800 text-white text-sm font-medium transition-colors shadow-sm shadow-blue-200"
                  >
                    <ArrowLeftRight size={15} />
                    <span className="hidden sm:inline">Comparar</span>
                    <span className="sm:hidden">Comp.</span>
                  </button>

                  {/* ── BOTÃO COMPARTILHAR ── */}
                  <BotoesCompartilhamento nome={data.nome} url={pageUrl} />
                </div>
              </div>

              <div className="flex flex-col md:flex-row gap-6 md:gap-8 items-center md:items-start text-center md:text-left">
                {/* PHOTO + SCORE (mobile: centered) */}
                <div className="flex flex-row md:flex-col md:items-start gap-4 sm:gap-5 items-center justify-center w-full md:w-auto">
                  <div className="profile-photo relative flex-shrink-0">
                    <div className="w-28 h-28 md:w-40 md:h-40 rounded-2xl overflow-hidden ring-4 ring-white shadow-xl">
                      <img
                        src={`${PATH_FOTOS}${data.id}.jpg`}
                        alt={`Foto de ${data.nome}`}
                        className="w-full h-full object-cover"
                      />
                    </div>
                    {data.situacao && (
                      <div className="absolute -bottom-2 left-1/2 -translate-x-1/2 whitespace-nowrap">
                        <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-medium bg-emerald-500 text-white shadow-sm">
                          <span className="w-1.5 h-1.5 rounded-full bg-white inline-block" />
                          {data.situacao}
                        </span>
                      </div>
                    )}
                  </div>

                  {/* Indicador de presença no mobile */}
                  {performance && (
                    <div className="flex md:hidden flex-shrink-0 text-center">
                      <div className="bg-slate-50 border border-slate-200/80 rounded-xl px-3 py-2 text-center">
                        <p className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider">Presença</p>
                        <p className="mono-font text-lg font-bold text-slate-800">
                          {performance.detalhes?.nota_assiduidade != null ? `${performance.detalhes.nota_assiduidade.toFixed(0)}%` : "—"}
                        </p>
                        <p className="text-[9px] text-slate-400">Assiduidade</p>
                      </div>
                    </div>
                  )}
                </div>

                {/* INFO */}
                <div className="flex-1 min-w-0 w-full flex flex-col items-center md:items-start">
                  <div className="flex flex-wrap items-center justify-center md:justify-start gap-2 mb-2">
                    <span className="mono-font text-xs text-slate-400 uppercase tracking-widest">
                      Parlamentar Federal
                    </span>
                    {data.condicao_eleitoral && (
                      <span className="pill-badge text-blue-700 text-[11px] font-medium px-2.5 py-0.5 rounded-full border border-blue-100">
                        {data.condicao_eleitoral}
                      </span>
                    )}
                    <span className="text-[11px] font-medium text-slate-500 bg-slate-100 px-2 py-0.5 rounded-md border border-slate-200/70">
                      57ª Legislatura
                    </span>
                  </div>

                  <h1 data-testid="politician-name" className="display-font text-2xl sm:text-3xl md:text-4xl font-bold text-slate-900 mb-2.5 leading-tight text-center md:text-left">
                    {data.nome}
                  </h1>

                  {/* IDENTIFICAÇÃO CÍVICA: PARTIDO, ESTADO E ESCOLARIDADE */}
                  <div className="flex flex-wrap items-center justify-center md:justify-start gap-2 mb-3">
                    {data.sigla_partido && (
                      <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-amber-50 border border-amber-200/90 text-amber-900 font-bold text-xs shadow-2xs">
                        <span className="w-2 h-2 rounded-full bg-amber-500 inline-block" />
                        {data.sigla_partido}
                      </span>
                    )}
                    {data.sigla_uf && (
                      <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-blue-50 border border-blue-200/90 text-blue-900 font-bold text-xs shadow-2xs">
                        <MapPin size={12} className="text-blue-600" />
                        {data.sigla_uf}
                      </span>
                    )}
                    {data.escolaridade && (
                      <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-slate-50 border border-slate-200 text-slate-600 font-medium text-xs">
                        <GraduationCap size={13} className="text-slate-400" />
                        {data.escolaridade}
                      </span>
                    )}
                  </div>

                  {/* Contacts */}
                  <div className="flex flex-wrap items-center justify-center md:justify-start gap-2 sm:gap-3 mt-3">
                    {data.email_gabinete && (
                      <a
                        href={`mailto:${data.email_gabinete}`}
                        className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-100 hover:bg-blue-50 hover:text-blue-700 text-slate-600 text-xs font-medium transition-colors"
                      >
                        <Mail size={12} />
                        {data.email_gabinete}
                      </a>
                    )}
                    {data.telefone_gabinete && (
                      <a
                        href={`tel:${data.telefone_gabinete}`}
                        className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-100 hover:bg-blue-50 hover:text-blue-700 text-slate-600 text-xs font-medium transition-colors"
                      >
                        <Phone size={12} />
                        {data.telefone_gabinete}
                      </a>
                    )}
                  </div>
                </div>

                {/* INDICADOR RÁPIDO DE MANDATO (DESKTOP) */}
                {performance && (
                  <div className="hidden md:flex flex-shrink-0 text-center" data-testid="performance-container">
                    <div className="bg-slate-50 border border-slate-200/80 rounded-2xl p-4 text-center min-w-[120px]">
                      <p className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">Presença</p>
                      <p data-testid="performance-score" className="mono-font text-2xl font-bold text-slate-800 mt-1">
                        {performance.detalhes?.nota_assiduidade != null ? `${performance.detalhes.nota_assiduidade.toFixed(0)}%` : "—"}
                      </p>
                      <p className="text-[10px] text-slate-400 mt-0.5">
                        {anoSelecionado ? `em ${anoSelecionado}` : "assiduidade"}
                      </p>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* ── BARRA DE ABAS CÍVICAS (STICKY MOBILE & DESKTOP) ── */}
        <div className="sticky top-14 sm:top-16 z-30 bg-white/95 backdrop-blur-md border-b border-slate-200 shadow-2xs">
          <div className="max-w-5xl mx-auto px-4 sm:px-6">
            <nav
              className="flex items-center gap-1.5 sm:gap-2 overflow-x-auto scrollbar-none py-2 text-xs sm:text-sm font-medium"
              aria-label="Navegação de seções"
            >
              <button
                data-testid="tab-visao-geral"
                onClick={() => scrollParaSecao("section-stats", "visao-geral")}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-xl transition-all whitespace-nowrap ${
                  abaAtiva === "visao-geral"
                    ? "bg-slate-900 text-white font-semibold shadow-xs"
                    : "text-slate-600 hover:text-slate-900 hover:bg-slate-100"
                }`}
              >
                <BarChart2 size={14} />
                <span>Visão Geral</span>
              </button>
              <button
                data-testid="tab-votacoes"
                onClick={() => scrollParaSecao("section-votacoes", "votacoes")}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-xl transition-all whitespace-nowrap ${
                  abaAtiva === "votacoes"
                    ? "bg-slate-900 text-white font-semibold shadow-xs"
                    : "text-slate-600 hover:text-slate-900 hover:bg-slate-100"
                }`}
              >
                <Vote size={14} />
                <span>Votações</span>
              </button>
              <button
                data-testid="tab-projetos"
                onClick={() => scrollParaSecao("section-projetos", "projetos")}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-xl transition-all whitespace-nowrap ${
                  abaAtiva === "projetos"
                    ? "bg-slate-900 text-white font-semibold shadow-xs"
                    : "text-slate-600 hover:text-slate-900 hover:bg-slate-100"
                }`}
              >
                <FileText size={14} />
                <span>Projetos</span>
              </button>
              <button
                data-testid="tab-conexoes"
                onClick={() => scrollParaSecao("section-conexoes", "conexoes")}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-xl transition-all whitespace-nowrap ${
                  abaAtiva === "conexoes"
                    ? "bg-slate-900 text-white font-semibold shadow-xs"
                    : "text-slate-600 hover:text-slate-900 hover:bg-slate-100"
                }`}
              >
                <Users size={14} />
                <span>Conexões & Parcerias</span>
              </button>
              <button
                data-testid="tab-gastos"
                onClick={() => scrollParaSecao("section-historico-de-gastos", "gastos")}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-xl transition-all whitespace-nowrap ${
                  abaAtiva === "gastos"
                    ? "bg-slate-900 text-white font-semibold shadow-xs"
                    : "text-slate-600 hover:text-slate-900 hover:bg-slate-100"
                }`}
              >
                <Receipt size={14} />
                <span>Gastos & Recursos</span>
              </button>
              <button
                data-testid="tab-atuacao"
                onClick={() => scrollParaSecao("section-atuacao", "atuacao")}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-xl transition-all whitespace-nowrap ${
                  abaAtiva === "atuacao"
                    ? "bg-slate-900 text-white font-semibold shadow-xs"
                    : "text-slate-600 hover:text-slate-900 hover:bg-slate-100"
                }`}
              >
                <TrendingUp size={14} />
                <span>Atuação & Temas</span>
              </button>
            </nav>
          </div>
        </div>

        {/* ── MAIN CONTENT ── */}
        <div className="max-w-5xl mx-auto px-4 sm:px-6 py-8 space-y-10">
          {/* ── SELETOR DE ANO ── */}
          {!timelineLoading && anosDisponiveis.length > 0 && (
            <section data-testid="section-timeline">
              <TimelineSelector
                anos={anosDisponiveis}
                anoSelecionado={anoSelecionado}
                onChange={setAnoSelecionado}
              />
            </section>
          )}

          {timelineLoading && (
            <div className="bg-white border border-slate-200 rounded-2xl h-20 flex items-center justify-center">
              <div className="w-6 h-6 border-2 border-slate-200 border-t-blue-500 rounded-full animate-spin" />
            </div>
          )}

          {anoSelecionado && (
            <div className="flex items-center justify-between bg-slate-50 border border-slate-200 rounded-xl px-4 py-3">
              <p className="text-sm text-slate-800 font-medium flex items-center gap-2">
                <Calendar size={15} className="text-slate-500" />
                <span>Dados filtrados para o ano <strong>{anoSelecionado}</strong></span>
              </p>
              <button
                onClick={() => setAnoSelecionado(null)}
                className="text-xs text-slate-600 hover:text-slate-900 font-medium underline underline-offset-2 transition-colors"
              >
                Ver mandato completo
              </button>
            </div>
          )}

          {/* ── ESTATÍSTICAS ── */}
          {stats && (
            <section data-testid="section-stats" key={`stats-${anoSelecionado}`} className="section-fade space-y-5">
              <div className="flex items-center gap-2 mb-1">
                <BarChart2 size={18} className="text-blue-500" />
                <h2 className="display-font text-xl font-bold text-slate-800">Estatísticas Consolidadas</h2>
                <ToolDica
                  side="bottom"
                  content="Estatísticas consolidadas a partir de dados oficiais abertos da Câmara dos Deputados."
                >
                  <InfoBotao />
                </ToolDica>
              </div>

              {/* SUB-BLOCO 1: ATIVIDADE EM PLENÁRIO */}
              <div className="bg-white rounded-2xl border border-slate-200/90 p-4 sm:p-5 shadow-2xs">
                <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-3 flex items-center gap-2">
                  <Vote size={14} className="text-blue-500" />
                  Atividade em Plenário & Votações
                </h3>
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
                  <StatCard
                    data-testid="stat-total-votacoes"
                    icon={<BadgeCheck size={16} className="text-blue-500" />}
                    titulo="Total de Votações"
                    valor={formatarNumero(stats.total_votacoes)}
                    subtitulo="Sessões deliberativas convocadas"
                    accent="blue"
                  />
                  <StatCard
                    icon={<CheckCircle2 size={16} className="text-emerald-500" />}
                    titulo="Assiduidade em Plenário"
                    valor={performance?.detalhes?.nota_assiduidade != null ? `${performance.detalhes.nota_assiduidade.toFixed(0)}%` : "—"}
                    subtitulo="Presença e votos registrados"
                    accent="emerald"
                  />
                  {data.sigla_partido && (
                    <StatCard
                      icon={<Users size={16} className="text-indigo-500" />}
                      titulo={`Bancada ${data.sigla_partido}`}
                      valor={data.sigla_partido}
                      subtitulo={data.sigla_uf ? `Representação por ${data.sigla_uf}` : "Filiação partidária oficial"}
                      accent="violet"
                    />
                  )}
                </div>
              </div>

              {/* SUB-BLOCO 2: RECURSOS PÚBLICOS E GESTÃO */}
              <div className="bg-white rounded-2xl border border-slate-200/90 p-4 sm:p-5 shadow-2xs">
                <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-3 flex items-center gap-2">
                  <Receipt size={14} className="text-emerald-500" />
                  Recursos Públicos e Gestão Orçamentária
                </h3>

                {/* Card destaque de Gasto Total */}
                <div className="p-4 sm:p-5 rounded-xl bg-slate-900 text-white shadow-xs mb-4">
                  <div className="flex flex-col sm:flex-row sm:items-baseline justify-between gap-2 mb-3">
                    <div>
                      <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block mb-0.5">
                        Gasto Total ({anoSelecionado ? `Ano ${anoSelecionado}` : "Mandato Completo"})
                      </span>
                      <span className="mono-font text-2xl sm:text-3xl font-extrabold text-white">
                        {formatarMoedaBRL(stats.total_gasto_combinado ?? stats.total_gasto)}
                      </span>
                    </div>
                    <div className="text-left sm:text-right">
                      <span className="text-[11px] text-slate-400 block">Média mensal (CEAP):</span>
                      <span className="mono-font text-sm font-bold text-amber-300">
                        {formatarMoedaBRL(stats.media_mensal)} / mês
                      </span>
                    </div>
                  </div>

                  {/* Proporção CEAP vs Gabinete */}
                  {((stats.total_gasto_gabinete ?? 0) > 0 || stats.total_gasto > 0) && (() => {
                    const ceap = stats.total_gasto || 0
                    const gab = stats.total_gasto_gabinete || 0
                    const total = ceap + gab || 1
                    const pctCeap = Math.round((ceap / total) * 100)
                    const pctGab = 100 - pctCeap
                    return (
                      <div className="space-y-1.5 pt-2 border-t border-slate-800">
                        <div className="flex justify-between text-[11px] text-slate-300 font-medium">
                          <span className="flex items-center gap-1.5">
                            <span className="w-2 h-2 rounded-full bg-emerald-400 inline-block" />
                            Cota Parlamentar ({pctCeap}%)
                          </span>
                          <span className="flex items-center gap-1.5">
                            <span className="w-2 h-2 rounded-full bg-indigo-400 inline-block" />
                            Verba de Gabinete ({pctGab}%)
                          </span>
                        </div>
                        <div className="w-full h-2 rounded-full bg-slate-800 overflow-hidden flex">
                          <div className="bg-emerald-400 h-full transition-all duration-300" style={{ width: `${pctCeap}%` }} />
                          <div className="bg-indigo-400 h-full transition-all duration-300" style={{ width: `${pctGab}%` }} />
                        </div>
                      </div>
                    )
                  })()}
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                  <StatCard
                    icon={<TrendingUp size={16} className="text-emerald-500" />}
                    titulo="Cota Parlamentar (CEAP)"
                    valor={formatarMoedaBRL(stats.total_gasto)}
                    subtitulo="Passagens, combustíveis e serviços"
                    accent="emerald"
                  />
                  <StatCard
                    icon={<Wallet size={16} className="text-indigo-500" />}
                    titulo="Verba de Gabinete"
                    valor={formatarMoedaBRL(stats.total_gasto_gabinete ?? 0)}
                    subtitulo="Salários e encargos da equipe"
                    accent="violet"
                  />
                  <StatCard
                    data-testid="stat-total-despesas"
                    icon={<Receipt size={16} className="text-blue-500" />}
                    titulo="Comprovantes Auditados"
                    valor={`${formatarNumero(stats.total_despesas)} notas`}
                    subtitulo="Notas fiscais e recibos na CEAP"
                    accent="blue"
                  />
                </div>

                {(stats.total_gasto_gabinete ?? 0) > 0 && (
                  <p className="text-[11px] text-slate-400 mt-3 leading-relaxed">
                    ℹ️ <strong>Cota Parlamentar (CEAP)</strong> cobre deslocamentos, passagens, materiais e serviços operacionais.{" "}
                    <strong>Verba de Gabinete</strong> remunera secretários parlamentares e assessores técnicos.
                  </p>
                )}
              </div>
            </section>
          )}

          {/* ── 1. ATIVIDADE LEGISLATIVA (VOTAÇÕES & PROPOSIÇÕES EM ABAS) ── */}
          <section
            id="section-atividade-legislativa"
            data-testid="section-atividade-legislativa"
            className="space-y-6 pt-2"
          >
            {/* Cabeçalho Unificado com Segmented Control */}
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-200">
              <div>
                <div className="flex items-center gap-2">
                  <Layers size={20} className="text-blue-500" />
                  <h2 className="display-font text-xl font-bold text-slate-800">
                    Atividade Legislativa
                  </h2>
                </div>
                <p className="text-xs text-slate-500 mt-1">
                  Posicionamentos nominais em plenário e projetos apresentados pelo parlamentar à Câmara.
                </p>
              </div>

              {/* Seletor de Abas (Segmented Control touch-friendly) */}
              <div
                className="inline-flex p-1 bg-slate-100 rounded-2xl border border-slate-200 self-start sm:self-auto w-full sm:w-auto"
                role="tablist"
                aria-label="Alternar entre votações e proposições"
              >
                <button
                  type="button"
                  role="tab"
                  aria-selected={subAbaLegislativa === "votacoes"}
                  data-testid="tab-sub-votacoes"
                  onClick={() => {
                    setSubAbaLegislativa("votacoes")
                    setAbaAtiva("votacoes")
                  }}
                  className={`flex-1 sm:flex-initial inline-flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl text-xs sm:text-sm font-semibold transition-all min-h-[44px] cursor-pointer ${
                    subAbaLegislativa === "votacoes"
                      ? "bg-white text-slate-900 shadow-2xs border border-slate-200/60"
                      : "text-slate-600 hover:text-slate-900 hover:bg-white/50"
                  }`}
                >
                  <Vote size={15} className={subAbaLegislativa === "votacoes" ? "text-blue-600" : "text-slate-400"} />
                  <span>Votações em Plenário</span>
                </button>

                <button
                  type="button"
                  role="tab"
                  aria-selected={subAbaLegislativa === "projetos"}
                  data-testid="tab-sub-projetos"
                  onClick={() => {
                    setSubAbaLegislativa("projetos")
                    setAbaAtiva("projetos")
                  }}
                  className={`flex-1 sm:flex-initial inline-flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl text-xs sm:text-sm font-semibold transition-all min-h-[44px] cursor-pointer ${
                    subAbaLegislativa === "projetos"
                      ? "bg-white text-slate-900 shadow-2xs border border-slate-200/60"
                      : "text-slate-600 hover:text-slate-900 hover:bg-white/50"
                  }`}
                >
                  <FileText size={15} className={subAbaLegislativa === "projetos" ? "text-blue-600" : "text-slate-400"} />
                  <span>Projetos e Proposições</span>
                </button>
              </div>
            </div>

            {/* Painel da Aba 1: Histórico de Votações */}
            <div
              id="section-votacoes"
              data-testid="section-votacoes"
              className={subAbaLegislativa === "votacoes" ? "block" : "hidden"}
            >
              <HistoricoVotacoes politicoId={data.id} anoSelecionado={anoSelecionado} />
            </div>

            {/* Painel da Aba 2: Projetos e Proposições */}
            <div
              id="section-projetos"
              data-testid="section-projetos"
              className={subAbaLegislativa === "projetos" ? "block" : "hidden"}
            >
              <HistoricoProjetos politicoId={data.id} anoSelecionado={anoSelecionado} />
            </div>
          </section>

          {/* ── 2. CONEXÕES & ALINHAMENTOS POLÍTICOS (EM ABAS) ── */}
          <section
            id="section-conexoes"
            data-testid="section-conexoes"
            className="space-y-6 pt-2"
          >
            {/* Alias de retrocompatibilidade para testes legados */}
            <div id="section-posicionamento-container" data-testid="section-posicionamento-container" className="hidden" />

            {/* Cabeçalho Unificado com Segmented Control */}
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-200">
              <div>
                <div className="flex items-center gap-2">
                  <Users size={20} className="text-blue-500" />
                  <h2 className="display-font text-xl font-bold text-slate-800">
                    Conexões & Alinhamentos Políticos
                  </h2>
                </div>
                <p className="text-xs text-slate-500 mt-1">
                  Mapeamento factual de afinidades nominais em plenário, parcerias na autoria de proposições e fidelidade à bancada.
                </p>
              </div>

              {/* Seletor de Abas de Conexões (Segmented Control touch-friendly) */}
              <div
                className="inline-flex p-1 bg-slate-100 rounded-2xl border border-slate-200 self-start sm:self-auto w-full sm:w-auto overflow-x-auto scrollbar-none"
                role="tablist"
                aria-label="Alternar entre afinidades, coautoria e fidelidade partidária"
              >
                <button
                  type="button"
                  role="tab"
                  aria-selected={subAbaConexoes === "afinidades"}
                  data-testid="tab-sub-afinidades"
                  onClick={() => setSubAbaConexoes("afinidades")}
                  className={`flex-1 sm:flex-initial inline-flex items-center justify-center gap-1.5 px-3.5 py-2.5 rounded-xl text-xs sm:text-sm font-semibold transition-all min-h-[44px] cursor-pointer whitespace-nowrap ${
                    subAbaConexoes === "afinidades"
                      ? "bg-white text-slate-900 shadow-2xs border border-slate-200/60"
                      : "text-slate-600 hover:text-slate-900 hover:bg-white/50"
                  }`}
                >
                  <Compass size={15} className={subAbaConexoes === "afinidades" ? "text-blue-600" : "text-slate-400"} />
                  <span>Afinidades de Voto</span>
                </button>

                <button
                  type="button"
                  role="tab"
                  aria-selected={subAbaConexoes === "coautoria"}
                  data-testid="tab-sub-coautoria"
                  onClick={() => setSubAbaConexoes("coautoria")}
                  className={`flex-1 sm:flex-initial inline-flex items-center justify-center gap-1.5 px-3.5 py-2.5 rounded-xl text-xs sm:text-sm font-semibold transition-all min-h-[44px] cursor-pointer whitespace-nowrap ${
                    subAbaConexoes === "coautoria"
                      ? "bg-white text-slate-900 shadow-2xs border border-slate-200/60"
                      : "text-slate-600 hover:text-slate-900 hover:bg-white/50"
                  }`}
                >
                  <GitFork size={15} className={subAbaConexoes === "coautoria" ? "text-blue-600" : "text-slate-400"} />
                  <span>Coautoria & Parcerias</span>
                </button>

                <button
                  type="button"
                  role="tab"
                  aria-selected={subAbaConexoes === "fidelidade"}
                  data-testid="tab-sub-fidelidade"
                  onClick={() => setSubAbaConexoes("fidelidade")}
                  className={`flex-1 sm:flex-initial inline-flex items-center justify-center gap-1.5 px-3.5 py-2.5 rounded-xl text-xs sm:text-sm font-semibold transition-all min-h-[44px] cursor-pointer whitespace-nowrap ${
                    subAbaConexoes === "fidelidade"
                      ? "bg-white text-slate-900 shadow-2xs border border-slate-200/60"
                      : "text-slate-600 hover:text-slate-900 hover:bg-white/50"
                  }`}
                >
                  <Scale size={15} className={subAbaConexoes === "fidelidade" ? "text-blue-600" : "text-slate-400"} />
                  <span>Fidelidade Partidária</span>
                </button>
              </div>
            </div>

            {/* Painel 1: Radar de Afinidades e Divergências de Voto */}
            <div className={subAbaConexoes === "afinidades" ? "block" : "hidden"}>
              <PainelRadarAfinidades politicoId={data.slug || data.id} />
            </div>

            {/* Painel 2: Rede de Coautoria e Parcerias Legislativas */}
            <div className={subAbaConexoes === "coautoria" ? "block" : "hidden"}>
              <PainelRedeCoautoria politicoId={data.slug || data.id} />
            </div>

            {/* Painel 3: Fidelidade Partidária */}
            <div className={subAbaConexoes === "fidelidade" ? "block" : "hidden"}>
              <PainelFidelidadePartidaria politicoId={data.slug || data.id} />
            </div>
          </section>

          {/* ── 3. HISTÓRICO DE GASTOS ── */}
          <section id="section-historico-de-gastos" className="mt-10" data-testid="section-historico-de-gastos">
            <div className="flex items-center gap-2 mb-5">
              <Receipt size={18} className="text-blue-500" />
              <h2 className="display-font text-xl font-bold text-slate-800">Histórico de Gastos</h2>
            </div>
            <LinhaDoTempo politicoId={data.id} />
          </section>

          {/* ── 4. ATUAÇÃO E TEMAS ── */}
          <div id="section-atuacao" data-testid="section-atuacao" className="space-y-10">
            {/* ── ATUAÇÃO E RECURSOS PARLAMENTARES ── */}
            {performance && (
              <section key={`perf-${anoSelecionado}`} className="section-fade">
                <div className="flex items-center gap-2 mb-5">
                  <TrendingUp size={18} className="text-blue-500" />
                  <h2 className="display-font text-xl font-bold text-slate-800">Atuação e Recursos Parlamentares</h2>
                </div>
                <PoliticoGraficos performance={performance} />
              </section>
            )}

            {/* ── FOCO TEMÁTICO DA ATUAÇÃO (SPEC-001) ── */}
            <PainelTemasAtuacao politicoId={data.slug || data.id} />
          </div>
        </div>
      </div>

      {/* ── BOTÃO FLUTUANTE VOLTAR AO TOPO (ANTI-SCROLL FATIGUE) ── */}
      {mostrarVoltarAoTopo && (
        <button
          type="button"
          data-testid="btn-voltar-ao-topo"
          onClick={() => window.scrollTo({ top: 0, behavior: "smooth" })}
          className="fixed bottom-6 right-6 z-40 p-3 bg-slate-900 text-white rounded-full shadow-lg hover:bg-blue-600 hover:shadow-xl hover:-translate-y-0.5 active:translate-y-0 transition-all duration-200 flex items-center justify-center min-w-[44px] min-h-[44px] focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 cursor-pointer"
          aria-label="Voltar ao topo da página"
          title="Voltar ao topo"
        >
          <ArrowUp size={20} />
        </button>
      )}

      {/* ── MODAL COMPARAR ── */}
      {modalCompararAberto && (
        <ModalSelecionarPolitico
          politicoAtualId={data.id}
          politicoAtualSlug={data.slug || nomeParaSlug(data.nome)}
          onClose={() => setModalCompararAberto(false)}
        />
      )}
    </>
  )
}

// ── HISTÓRICO DE VOTAÇÕES ──────────────────────────────────────────────────

const VOTO_CONFIG: Record<string, { label: string; cls: string; clsLight: string; icon: React.ReactNode }> = {
  "Sim":       { label: "Sim",       cls: "text-emerald-700 bg-emerald-50 border-emerald-200",  clsLight: "bg-emerald-50",  icon: <CheckCircle2 size={11} /> },
  "Não":       { label: "Não",       cls: "text-red-600 bg-red-50 border-red-200",              clsLight: "bg-red-50",      icon: <XCircle size={11} /> },
  "Obstrução": { label: "Obstrução", cls: "text-amber-700 bg-amber-50 border-amber-200",        clsLight: "bg-amber-50",    icon: <MinusCircle size={11} /> },
  "Abstenção": { label: "Abstenção", cls: "text-slate-500 bg-slate-100 border-slate-200",       clsLight: "bg-slate-50",    icon: <MinusCircle size={11} /> },
}

function VotoBadge({ voto }: { voto?: string | null }) {
  const v = voto || "Não registrado"
  const cfg = VOTO_CONFIG[v] ?? { label: v, cls: "text-slate-600 bg-slate-50 border-slate-200", icon: <MinusCircle size={11} /> }
  return (
    <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-md border text-[11px] font-semibold flex-shrink-0 ${cfg.cls}`}>
      {cfg.icon} {cfg.label}
    </span>
  )
}

function ResultadoVotacaoBadge({ aprovacao, resultadoTexto }: { aprovacao: number | null | undefined; resultadoTexto?: string | null }) {
  // Deriva aprovacao da string resultado_da_votacao caso não venha como número
  let resolvedAprovacao = aprovacao
  if ((resolvedAprovacao === null || resolvedAprovacao === undefined) && resultadoTexto) {
    const r = resultadoTexto.toLowerCase()
    if (r.startsWith("aprovad") || r.includes(": aprovad")) resolvedAprovacao = 1
    else if (r.startsWith("rejeitad") || r.includes(": rejeitad")) resolvedAprovacao = 0
  }
  const aprovacaoFinal = resolvedAprovacao
  if (aprovacaoFinal === 1) return (
    <span className="inline-flex items-center gap-1 text-[10px] text-emerald-600 font-semibold bg-emerald-50 border border-emerald-200 px-1.5 py-0.5 rounded">
      <CheckCircle2 size={9} /> Aprovada
    </span>
  )
  if (aprovacaoFinal === 0) return (
    <span className="inline-flex items-center gap-1 text-[10px] text-red-500 font-semibold bg-red-50 border border-red-200 px-1.5 py-0.5 rounded">
      <XCircle size={9} /> Rejeitada
    </span>
  )
  return (
    <span className="inline-flex items-center gap-1 text-[10px] text-slate-400 font-semibold bg-slate-50 border border-slate-200 px-1.5 py-0.5 rounded">
      <MinusCircle size={9} /> Indefinido
    </span>
  )
}

// ── PAINEL LATERAL DE DETALHE DA VOTAÇÃO ──────────────────────────────────

function PainelDetalheVotacao({
  votacaoId,
  votoDeputado,
  onClose,
}: {
  votacaoId: number
  votoDeputado?: string | null
  onClose: () => void
}) {
  const { data: votacao, isLoading } = useVotacao(votacaoId)
  const [abaAtiva, setAbaAtiva] = useState<"orientacoes" | "votos">("orientacoes")

  const formatarData = (iso: string | null | undefined) => {
    if (!iso) return "—"
    return new Date(iso).toLocaleDateString("pt-BR", { day: "2-digit", month: "long", year: "numeric" })
  }

  const vDep = votoDeputado || "Não registrado"
  const cfg = VOTO_CONFIG[vDep] ?? { cls: "text-slate-600 bg-slate-50 border-slate-200", clsLight: "bg-slate-50" }

  return (
    <>
      {/* Overlay para fechar clicando fora */}
      <div
        className="fixed inset-0 z-40 bg-black/20 backdrop-blur-[1px]"
        onClick={onClose}
      />

      {/* Painel deslizante */}
      <div
        data-testid="painel-detalhe-votacao"
        className="fixed right-0 top-0 h-full w-full max-w-[440px] z-50 bg-white shadow-2xl flex flex-col"
        style={{ animation: "slideInRight 0.25s cubic-bezier(0.22, 1, 0.36, 1) both" }}
      >
        {/* ── Cabeçalho ── */}
        <div className="px-6 py-5 border-b border-slate-100 flex-shrink-0">
          <div className="flex items-start justify-between gap-3 mb-3">
            <div className="flex items-center gap-2 flex-wrap">
              {votacao?.proposicao_sigla && (
                <span className={`text-xs font-semibold px-2 py-0.5 rounded border ${
                  VOTO_CONFIG[votoDeputado]?.cls ?? "text-slate-600 bg-slate-50 border-slate-200"
                }`}>
                  {votacao.proposicao_sigla}
                </span>
              )}
              {votacao?.proposicao_numero && (
                <span className="text-sm font-mono text-slate-500 font-medium">
                  {votacao.proposicao_numero}/{votacao.proposicao_ano}
                </span>
              )}
              {votacao && <ResultadoVotacaoBadge aprovacao={votacao.aprovacao} resultadoTexto={(votacao as any).resultado_da_votacao} />}
            </div>
            <button
              onClick={onClose}
              className="p-1.5 rounded-lg hover:bg-slate-100 text-slate-400 hover:text-slate-600 transition-colors flex-shrink-0"
            >
              <XCircle size={18} />
            </button>
          </div>

          {/* Voto do deputado em destaque */}
          <div className={`flex items-center gap-3 px-4 py-3 rounded-xl border ${cfg.clsLight} border-current/10`}>
            <div className="flex-1">
              <p className="text-[10px] font-semibold text-slate-400 uppercase tracking-wide mb-0.5">Voto do parlamentar</p>
              <VotoBadge voto={votoDeputado} />
            </div>
            {votacao && (
              <div className="text-right">
                <p className="text-[10px] font-semibold text-slate-400 uppercase tracking-wide mb-0.5">Data</p>
                <p className="text-xs text-slate-600 font-medium">{formatarData(votacao.data)}</p>
              </div>
            )}
          </div>

          {/* Contexto temporal se a proposição tiver 2+ anos em relação à votação */}
          {(() => {
            const anoV = votacao?.data ? new Date(votacao.data).getFullYear() : null
            if (anoV && votacao?.proposicao_ano && anoV - votacao.proposicao_ano >= 2) {
              const diff = anoV - votacao.proposicao_ano
              return (
                <div className="mt-3 p-2.5 bg-amber-50/90 border border-amber-200/80 rounded-xl text-xs text-amber-900 flex items-start gap-2">
                  <Clock size={14} className="text-amber-700 flex-shrink-0 mt-0.5" />
                  <p className="leading-snug">
                    Votação ocorrida em <strong>{formatarData(votacao.data)}</strong> sobre matéria apresentada em <strong>{votacao.proposicao_ano}</strong> ({diff} anos em tramitação).
                  </p>
                </div>
              )
            }
            return null
          })()}
        </div>

        {/* ── Conteúdo scrollável ── */}
        <div className="flex-1 overflow-y-auto">
          {isLoading ? (
            <div className="flex items-center justify-center py-20 gap-3 text-slate-400">
              <Loader2 size={20} className="animate-spin" />
              <span className="text-sm">Carregando detalhes...</span>
            </div>
          ) : !votacao ? (
            <div className="flex flex-col items-center justify-center py-20 text-slate-400">
              <Vote size={32} className="mb-3 opacity-30" />
              <p className="text-sm">Detalhes não disponíveis.</p>
            </div>
          ) : (
            <div className="px-6 py-5 space-y-5">
              {/* Ementa */}
              {(votacao.proposicao_ementa || (votacao as any).ementa || votacao.descricao) && (
                <div>
                  <p className="text-[10px] font-semibold text-slate-400 uppercase tracking-wide mb-2">Proposição</p>
                  <p className="text-sm text-slate-700 leading-relaxed">
                    {votacao.proposicao_ementa ?? (votacao as any).ementa ?? votacao.descricao}
                  </p>
                </div>
              )}

              {/* Placar */}
              {(votacao.votos_sim != null || votacao.votos_nao != null) && (
                <div>
                  <p className="text-[10px] font-semibold text-slate-400 uppercase tracking-wide mb-2">Placar</p>
                  <div className="grid grid-cols-3 gap-2">
                    <div className="bg-emerald-50 border border-emerald-200 rounded-xl p-3 text-center">
                      <p className="text-xl font-bold text-emerald-700">{votacao.votos_sim ?? "—"}</p>
                      <p className="text-[10px] text-emerald-600 font-medium mt-0.5">Sim</p>
                    </div>
                    <div className="bg-red-50 border border-red-200 rounded-xl p-3 text-center">
                      <p className="text-xl font-bold text-red-600">{votacao.votos_nao ?? "—"}</p>
                      <p className="text-[10px] text-red-500 font-medium mt-0.5">Não</p>
                    </div>
                    <div className="bg-slate-50 border border-slate-200 rounded-xl p-3 text-center">
                      <p className="text-xl font-bold text-slate-600">{votacao.votos_outros ?? "—"}</p>
                      <p className="text-[10px] text-slate-500 font-medium mt-0.5">Outros</p>
                    </div>
                  </div>
                </div>
              )}

              {/* Sub-abas: Orientações / Todos os votos */}
              {(votacao.orientacoes.length > 0 || votacao.votos.length > 0) && (
                <div>
                  <div className="flex border-b border-slate-200 mb-3">
                    <button
                      onClick={() => setAbaAtiva("orientacoes")}
                      className={`px-3 py-2 text-xs font-semibold border-b-2 -mb-px transition-colors ${
                        abaAtiva === "orientacoes"
                          ? "border-blue-500 text-blue-600"
                          : "border-transparent text-slate-400 hover:text-slate-600"
                      }`}
                    >
                      Partidos ({votacao.orientacoes.length})
                    </button>
                    <button
                      onClick={() => setAbaAtiva("votos")}
                      className={`px-3 py-2 text-xs font-semibold border-b-2 -mb-px transition-colors ${
                        abaAtiva === "votos"
                          ? "border-blue-500 text-blue-600"
                          : "border-transparent text-slate-400 hover:text-slate-600"
                      }`}
                    >
                      Deputados ({votacao.votos.length})
                    </button>
                  </div>

                  {/* Orientações */}
                  {abaAtiva === "orientacoes" && (
                    <div className="space-y-1.5">
                      {votacao.orientacoes.length === 0 ? (
                        <p className="text-xs text-slate-400 py-4 text-center">Sem orientações registradas.</p>
                      ) : (
                        votacao.orientacoes.map((o, i) => {
                          const oCfg = VOTO_CONFIG[o.orientacao_voto ?? ""] ?? { cls: "text-slate-600 bg-slate-50 border-slate-200" }
                          return (
                            <div key={i} className="flex items-center justify-between px-3 py-2 rounded-lg bg-slate-50 border border-slate-100">
                              <span className="text-sm font-semibold text-slate-700">{o.sigla_partido_bloco ?? "—"}</span>
                              <span className={`text-[11px] font-semibold px-2 py-0.5 rounded border ${oCfg.cls}`}>
                                {o.orientacao_voto ?? "—"}
                              </span>
                            </div>
                          )
                        })
                      )}
                    </div>
                  )}

                  {/* Todos os votos */}
                  {abaAtiva === "votos" && (
                    <div className="space-y-0.5">
                      {votacao.votos.length === 0 ? (
                        <p className="text-xs text-slate-400 py-4 text-center">Sem votos nominais registrados.</p>
                      ) : (
                        votacao.votos.map((v, i) => {
                          const vCfg = VOTO_CONFIG[v.voto] ?? { cls: "text-slate-600 bg-slate-50 border-slate-200" }
                          return (
                            <div key={i} className="flex items-center justify-between px-3 py-2 rounded-lg hover:bg-slate-50 transition-colors">
                              <div className="flex-1 min-w-0">
                                <p className="text-xs font-medium text-slate-700 truncate">{v.nome}</p>
                                <p className="text-[10px] text-slate-400">
                                  {[v.sigla_partido, v.sigla_uf].filter(Boolean).join(" · ")}
                                </p>
                              </div>
                              <span className={`text-[11px] font-semibold px-2 py-0.5 rounded border ml-2 flex-shrink-0 ${vCfg.cls}`}>
                                {v.voto}
                              </span>
                            </div>
                          )
                        })
                      )}
                    </div>
                  )}
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </>
  )
}

const TIPOS_PROPOSICAO_VOTACAO = [
  { label: "Todos os tipos", value: "" },
  { label: "PL — Projeto de Lei", value: "PL" },
  { label: "PEC — Emenda à Constituição", value: "PEC" },
  { label: "PLP — Projeto de Lei Complementar", value: "PLP" },
  { label: "PDL — Projeto de Decreto Legislativo", value: "PDL" },
  { label: "MPV — Medida Provisória", value: "MPV" },
  { label: "REQ — Requerimento", value: "REQ" },
  { label: "PRC — Projeto de Resolução", value: "PRC" },
]

const TEMAS_LEGISLATIVOS_VOTACAO = [
  { label: "Todos os temas", value: "" },
  { label: "Trabalho e Emprego", value: "Trabalho" },
  { label: "Economia e Finanças", value: "Economia" },
  { label: "Saúde", value: "Saúde" },
  { label: "Educação", value: "Educação" },
  { label: "Segurança Pública", value: "Segurança" },
  { label: "Meio Ambiente", value: "Meio Ambiente" },
  { label: "Direitos Humanos", value: "Direitos Humanos" },
  { label: "Administração Pública", value: "Administração Pública" },
  { label: "Agricultura e Pecuária", value: "Agricultura" },
  { label: "Ciência e Tecnologia", value: "Ciência" },
  { label: "Comunicações", value: "Comunicações" },
]

const TEMAS_DO_MOMENTO = [
  { label: "Escala 6x1 (PEC 221)", query: "escala 6x1" },
  { label: "Reforma Tributária", query: "reforma tributária" },
  { label: "Marco Temporal", query: "marco temporal" },
  { label: "Apostas & Bets", query: "apostas" },
  { label: "Porte de Armas", query: "armas" },
  { label: "Desoneração da Folha", query: "desoneração" },
]

function HistoricoVotacoes({ politicoId, anoSelecionado }: { politicoId: number; anoSelecionado: number | null }) {
  const isMobile = useIsMobile()
  const PAGE_SIZE = isMobile ? 2 : 10
  const [offset, setOffset] = useState(0)
  const [filtroVoto, setFiltroVoto] = useState<string>("")
  const [siglaTipo, setSiglaTipo] = useState<string>("")
  const [tema, setTema] = useState<string>("")
  const [busca, setBusca] = useState<string>("")
  const [dataInicio, setDataInicio] = useState<string>("")
  const [dataFim, setDataFim] = useState<string>("")
  const [votacaoAberta, setVotacaoAberta] = useState<{ id: number; voto: string } | null>(null)
  const [filtrosAvancadosAbertos, setFiltrosAvancadosAbertos] = useState(false)

  const buscaDebounced = useDebounce(busca.trim(), 400)

  // Reseta página ao trocar filtros, ano ou modo de tela
  useEffect(() => {
    setOffset(0)
  }, [anoSelecionado, filtroVoto, siglaTipo, tema, buscaDebounced, dataInicio, dataFim, isMobile])

  // Fecha painel ao trocar de página
  useEffect(() => {
    setVotacaoAberta(null)
  }, [offset])

  const { data: atividade, isLoading } = usePoliticoAtividade(politicoId, {
    ano: anoSelecionado ?? undefined,
    q_votacao: buscaDebounced || undefined,
    voto: filtroVoto || undefined,
    sigla_tipo_votacao: siglaTipo || undefined,
    tema_votacao: tema || undefined,
    data_inicio_votacao: dataInicio || undefined,
    data_fim_votacao: dataFim || undefined,
    limit_votacoes: PAGE_SIZE,
    offset_votacoes: offset,
  })

  // Normaliza campos do JSON do endpoint para o formato esperado pelo componente
  const normalizarVotacao = (v: any): VotacaoResumida => {
    // Deriva aprovacao (0/1) a partir da string resultado_da_votacao
    let aprovacao: number | null = v.aprovacao ?? null
    if (aprovacao === null && v.resultado_da_votacao) {
      const r = (v.resultado_da_votacao as string).toLowerCase()
      if (r.startsWith("aprovad") || r.includes(": aprovad")) aprovacao = 1
      else if (r.startsWith("rejeitad") || r.includes(": rejeitad")) aprovacao = 0
    }
    return {
      ...v,
      proposicao_ementa: v.proposicao_ementa ?? v.ementa ?? null,
      aprovacao,
    }
  }

  const votacoes: VotacaoResumida[] = (atividade?.votacoes ?? []).map(normalizarVotacao)
  const total = atividade?.total_votacoes ?? 0
  const totalSim = atividade?.total_votos_sim ?? 0
  const totalNao = atividade?.total_votos_nao ?? 0
  const totalOutros = atividade?.total_votos_outros ?? 0

  const pagina = Math.floor(offset / PAGE_SIZE) + 1
  const totalPaginas = Math.ceil(total / PAGE_SIZE)
  const temAnterior = offset > 0
  const temProxima = offset + PAGE_SIZE < total

  const temFiltroAtivo = Boolean(busca || filtroVoto || siglaTipo || tema || dataInicio || dataFim)
  const filtrosAvancadosCount = [siglaTipo, tema, dataInicio, dataFim].filter(Boolean).length

  const limparFiltros = () => {
    setBusca("")
    setFiltroVoto("")
    setSiglaTipo("")
    setTema("")
    setDataInicio("")
    setDataFim("")
    setOffset(0)
  }

  const formatarData = (iso: string | null | undefined) => {
    if (!iso) return "—"
    try {
      return new Date(iso).toLocaleDateString("pt-BR", { day: "2-digit", month: "short", year: "numeric" })
    } catch {
      return iso
    }
  }

  return (
    <>
      {/* Keyframe de animação do painel */}
      <style>{`
        @keyframes slideInRight {
          from { transform: translateX(100%); opacity: 0; }
          to   { transform: translateX(0);    opacity: 1; }
        }
      `}</style>

      <section className="section-fade space-y-5">
        {/* ── CABEÇALHO DA SEÇÃO ── */}
        <div className="flex items-center justify-between gap-3 flex-wrap">
          <div className="flex items-center gap-2">
            <Vote size={18} className="text-blue-500" />
            <h2 className="display-font text-xl font-bold text-slate-800">Histórico de Votações</h2>
            {total > 0 && (
              <span data-testid="votacoes-total-badge" className="text-xs font-medium text-slate-400 bg-slate-100 px-2 py-0.5 rounded-full">
                {total.toLocaleString("pt-BR")} registros
              </span>
            )}
          </div>

          <ToolDica
            texto="Histórico factual de deliberações nominais do parlamentar em plenário e comissões da Câmara dos Deputados, com indicação do voto individual registrado oficialmente e link para a proposição."
            posicao="left"
          />
        </div>

        {/* ── KPIS DE VOTAÇÃO FACTUAL ── */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          <div className="bg-white p-4 rounded-2xl border border-slate-200/90 shadow-2xs">
            <div className="flex items-center justify-between mb-1">
              <span className="text-xs font-medium text-slate-500">Total sob Filtro</span>
              <Vote size={16} className="text-blue-500" />
            </div>
            <p
              data-testid="kpi-total-votacoes"
              className="mono-font text-2xl font-bold text-slate-800"
            >
              {total.toLocaleString("pt-BR")}
            </p>
            <p className="text-[11px] text-slate-400 mt-0.5">
              {anoSelecionado ? `votações em ${anoSelecionado}` : "votações nominais registradas"}
            </p>
          </div>

          <div className="bg-white p-4 rounded-2xl border border-slate-200/90 shadow-2xs">
            <div className="flex items-center justify-between mb-1">
              <span className="text-xs font-medium text-emerald-700">Votos a Favor ("Sim")</span>
              <CheckCircle2 size={16} className="text-emerald-600" />
            </div>
            <p
              data-testid="kpi-votos-sim"
              className="mono-font text-2xl font-bold text-emerald-900"
            >
              {totalSim.toLocaleString("pt-BR")}
            </p>
            <p className="text-[11px] text-slate-400 mt-0.5">
              {total > 0 ? `${Math.round((totalSim / total) * 100)}% das deliberações` : "posicionamento favorável"}
            </p>
          </div>

          <div className="bg-white p-4 rounded-2xl border border-slate-200/90 shadow-2xs">
            <div className="flex items-center justify-between mb-1">
              <span className="text-xs font-medium text-slate-600">Votos Contra / Outros</span>
              <XCircle size={16} className="text-rose-600" />
            </div>
            <p
              data-testid="kpi-votos-nao"
              className="mono-font text-2xl font-bold text-slate-700"
            >
              {(totalNao + totalOutros).toLocaleString("pt-BR")}
            </p>
            <p className="text-[11px] text-slate-400 mt-0.5">
              {totalNao.toLocaleString("pt-BR")} "Não" {totalOutros > 0 ? `· ${totalOutros.toLocaleString("pt-BR")} outros` : ""}
            </p>
          </div>
        </div>

        {/* ── BARRA DE FILTROS CÍVICA DE VOTAÇÕES ── */}
        <div className="bg-white p-4 rounded-2xl border border-slate-200 shadow-2xs space-y-3.5">
          {/* Linha Superior: Busca textual e Abas de Voto */}
          <div className="flex flex-col md:flex-row gap-3 items-stretch md:items-center justify-between">
            {/* Campo de Busca Textual */}
            <div className="relative flex-1">
              <Search size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 pointer-events-none" />
              <input
                data-testid="input-busca-votacoes"
                type="text"
                value={busca}
                onChange={(e) => setBusca(e.target.value)}
                placeholder="Buscar por tema, nº, sigla ou ementa (ex: escala 6x1, PL 74, tributário)..."
                className="w-full text-sm pl-9 pr-8 py-2 rounded-xl border border-slate-200 bg-slate-50/50 hover:bg-white focus:bg-white text-slate-700 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-400 transition-all"
              />
              {busca && (
                <button
                  type="button"
                  onClick={() => setBusca("")}
                  className="absolute right-2.5 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 p-1"
                  aria-label="Limpar busca"
                >
                  <X size={13} />
                </button>
              )}
            </div>

            {/* Seletor de Voto (Tabs Rápidas) */}
            <div className="flex items-center bg-slate-100 p-1 rounded-xl text-xs font-medium self-start md:self-auto">
              <button
                data-testid="filter-voto-tab-todos"
                type="button"
                onClick={() => setFiltroVoto("")}
                className={`px-3 py-1.5 rounded-lg transition-all ${
                  filtroVoto === ""
                    ? "bg-white text-slate-900 font-semibold shadow-2xs"
                    : "text-slate-600 hover:text-slate-900"
                }`}
              >
                Todos ({total})
              </button>
              <button
                data-testid="filter-voto-tab-sim"
                type="button"
                onClick={() => setFiltroVoto(filtroVoto === "Sim" ? "" : "Sim")}
                className={`px-3 py-1.5 rounded-lg transition-all flex items-center gap-1 ${
                  filtroVoto === "Sim"
                    ? "bg-emerald-600 text-white font-semibold shadow-2xs"
                    : "text-slate-600 hover:text-slate-900"
                }`}
              >
                <span>⭐ Sim</span>
                <span className="text-[11px] opacity-90">({totalSim})</span>
              </button>
              <button
                data-testid="filter-voto-tab-nao"
                type="button"
                onClick={() => setFiltroVoto(filtroVoto === "Não" ? "" : "Não")}
                className={`px-3 py-1.5 rounded-lg transition-all flex items-center gap-1 ${
                  filtroVoto === "Não"
                    ? "bg-rose-600 text-white font-semibold shadow-2xs"
                    : "text-slate-600 hover:text-slate-900"
                }`}
              >
                <span>👥 Não</span>
                <span className="text-[11px] opacity-90">({totalNao})</span>
              </button>
            </div>
          </div>

          {/* Linha de Temas do Momento (com rolagem horizontal fluida no mobile) */}
          <div className="flex items-center gap-2 pt-1 flex-wrap sm:flex-nowrap overflow-hidden">
            <span className="text-xs font-semibold text-slate-500 flex items-center gap-1 shrink-0">
              <Flame size={13} className="text-amber-500" /> Temas em Alta:
            </span>
            <div className="flex items-center gap-1.5 overflow-x-auto pb-1 scrollbar-none flex-nowrap sm:flex-wrap w-full sm:w-auto">
              {TEMAS_DO_MOMENTO.map((item) => {
                const isSelected = busca.toLowerCase() === item.query.toLowerCase()
                return (
                  <button
                    key={item.query}
                    type="button"
                    onClick={() => setBusca(isSelected ? "" : item.query)}
                    className={`text-xs px-2.5 py-1 rounded-full border transition-all shrink-0 cursor-pointer whitespace-nowrap ${
                      isSelected
                        ? "bg-amber-100 border-amber-300 text-amber-900 font-semibold shadow-2xs"
                        : "bg-slate-50 border-slate-200 text-slate-600 hover:bg-amber-50/60 hover:text-amber-800 hover:border-amber-200"
                    }`}
                  >
                    {item.label}
                  </button>
                )
              })}
            </div>
          </div>

          {/* Botão de Toggle para Filtros Avançados no Mobile */}
          <div className="sm:hidden pt-2 border-t border-slate-100 flex items-center justify-between">
            <button
              type="button"
              data-testid="btn-toggle-filtros-avancados"
              onClick={() => setFiltrosAvancadosAbertos((v) => !v)}
              className="inline-flex items-center gap-1.5 text-xs font-semibold text-blue-600 hover:text-blue-800 py-1 cursor-pointer"
            >
              <SlidersHorizontal size={13} />
              <span>{filtrosAvancadosAbertos ? "Recolher filtros detalhados" : "Mais filtros (Tipo, Tema, Período)"}</span>
              {filtrosAvancadosCount > 0 && (
                <span className="bg-blue-100 text-blue-800 text-[10px] px-1.5 py-0.2 rounded-full font-bold">
                  {filtrosAvancadosCount}
                </span>
              )}
            </button>
            {temFiltroAtivo && (
              <button
                type="button"
                onClick={limparFiltros}
                className="text-xs text-rose-600 hover:text-rose-800 font-medium cursor-pointer"
              >
                Limpar filtros
              </button>
            )}
          </div>

          {/* Linha Inferior: Dropdowns de Tipo, Tema, Voto, Datas e Limpar */}
          <div className={`${filtrosAvancadosAbertos ? "flex" : "hidden"} sm:flex flex-wrap items-center gap-3 pt-2 border-t border-slate-100 text-xs`}>
            {/* Dropdown de Tipo */}
            <div className="flex items-center gap-1.5">
              <span className="text-slate-500 font-medium">Tipo:</span>
              <select
                data-testid="select-tipo-votacao"
                value={siglaTipo}
                onChange={(e) => setSiglaTipo(e.target.value)}
                className="text-xs border border-slate-200 rounded-lg px-2.5 py-1.5 bg-white text-slate-700 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-400 cursor-pointer"
              >
                {TIPOS_PROPOSICAO_VOTACAO.map((t) => (
                  <option key={t.value} value={t.value}>
                    {t.label}
                  </option>
                ))}
              </select>
            </div>

            {/* Dropdown de Tema */}
            <div className="flex items-center gap-1.5">
              <span className="text-slate-500 font-medium">Tema:</span>
              <select
                data-testid="select-tema-votacao"
                value={tema}
                onChange={(e) => setTema(e.target.value)}
                className="text-xs border border-slate-200 rounded-lg px-2.5 py-1.5 bg-white text-slate-700 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-400 cursor-pointer"
              >
                {TEMAS_LEGISLATIVOS_VOTACAO.map((t) => (
                  <option key={t.value} value={t.value}>
                    {t.label}
                  </option>
                ))}
              </select>
            </div>

            {/* Dropdown de Voto */}
            <div className="flex items-center gap-1.5">
              <span className="text-slate-500 font-medium">Voto:</span>
              <select
                data-testid="filter-voto-select"
                value={filtroVoto}
                onChange={(e) => setFiltroVoto(e.target.value)}
                className="text-xs border border-slate-200 rounded-lg px-2.5 py-1.5 bg-white text-slate-700 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-400 cursor-pointer"
              >
                <option value="">Todos os votos</option>
                <option value="Sim">Sim</option>
                <option value="Não">Não</option>
                <option value="Obstrução">Obstrução</option>
                <option value="Abstenção">Abstenção</option>
              </select>
            </div>

            {/* Filtro por Datas */}
            <div className="flex items-center gap-2 flex-wrap">
              <span className="text-slate-500 font-medium flex items-center gap-1">
                <Calendar size={13} className="text-slate-400" /> Período:
              </span>
              <input
                data-testid="input-data-inicio-votacao"
                type="date"
                value={dataInicio}
                onChange={(e) => setDataInicio(e.target.value)}
                className="text-xs border border-slate-200 rounded-lg px-2 py-1 bg-white text-slate-700 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-400"
                aria-label="Data inicial da votação"
              />
              <span className="text-slate-400">até</span>
              <input
                data-testid="input-data-fim-votacao"
                type="date"
                value={dataFim}
                onChange={(e) => setDataFim(e.target.value)}
                className="text-xs border border-slate-200 rounded-lg px-2 py-1 bg-white text-slate-700 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-400"
                aria-label="Data final da votação"
              />
            </div>

            {/* Botão Limpar Filtros */}
            {temFiltroAtivo && (
              <button
                data-testid="btn-limpar-filtros-votacoes"
                type="button"
                onClick={limparFiltros}
                className="ml-auto inline-flex items-center gap-1 text-xs text-blue-600 hover:text-blue-800 hover:underline font-medium py-1 px-2 cursor-pointer"
              >
                <X size={12} /> Limpar filtros
              </button>
            )}
          </div>
        </div>

        {/* ── LISTAGEM DE VOTAÇÕES EM CARDS FORMATADOS ── */}
        <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
          {isLoading ? (
            <div className="flex items-center justify-center py-16 gap-3 text-slate-400">
              <Loader2 size={20} className="animate-spin" />
              <span className="text-sm">Carregando votações...</span>
            </div>
          ) : votacoes.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-16 text-slate-400 px-4 text-center">
              <Vote size={32} className="mb-3 opacity-30" />
              <p className="text-sm font-medium text-slate-600">
                Nenhuma votação encontrada para os critérios selecionados.
              </p>
              {temFiltroAtivo && (
                <button
                  type="button"
                  onClick={limparFiltros}
                  className="mt-3 text-xs text-blue-600 hover:underline font-semibold"
                >
                  Limpar todos os filtros
                </button>
              )}
            </div>
          ) : (
            <>
              <div data-testid="votacoes-list" className="divide-y divide-slate-100">
                {votacoes.map((v, i) => {
                  const ativo = votacaoAberta?.id === v.id_votacao
                  const anoVoto = v.data ? new Date(v.data).getFullYear() : null
                  const gapAnos = anoVoto && v.proposicao_ano ? anoVoto - v.proposicao_ano : 0
                  const urlCamara =
                    v.proposicao_url_inteiro_teor ||
                    (v.proposicao_id_camara
                      ? `https://www.camara.leg.br/proposicoesWeb/fichadetramitacao?idProposicao=${v.proposicao_id_camara}`
                      : v.proposicao_id
                      ? `https://www.camara.leg.br/proposicoesWeb/fichadetramitacao?idProposicao=${v.proposicao_id}`
                      : null)

                  return (
                    <article
                      key={`${v.id_votacao}-${i}`}
                      data-testid={`votacao-item-${v.id_votacao}`}
                      onClick={() => setVotacaoAberta(ativo ? null : { id: v.id_votacao, voto: v.voto })}
                      className={`p-5 transition-colors space-y-2.5 cursor-pointer group ${
                        ativo
                          ? "bg-blue-50/60 border-l-4 border-l-blue-500"
                          : "hover:bg-slate-50/70 border-l-4 border-l-transparent"
                      }`}
                    >
                      {/* Linha 1: Identificação da Matéria, Voto, Tipo, Link Câmara e Data */}
                      <div className="flex items-start justify-between gap-3 flex-wrap">
                        <div className="flex items-center gap-2 flex-wrap">
                          {v.proposicao_sigla || v.proposicao_numero ? (
                            urlCamara ? (
                              <a
                                href={urlCamara}
                                target="_blank"
                                rel="noopener noreferrer"
                                onClick={(e) => e.stopPropagation()}
                                className="mono-font text-base font-bold text-blue-600 hover:text-blue-800 hover:underline inline-flex items-center gap-1"
                                title="Ver ficha de tramitação no portal oficial da Câmara dos Deputados"
                              >
                                <span>
                                  {v.proposicao_sigla} {v.proposicao_numero}/{v.proposicao_ano}
                                </span>
                                <ExternalLink size={13} className="text-blue-500" />
                              </a>
                            ) : (
                              <span className="mono-font text-base font-bold text-slate-900">
                                {v.proposicao_sigla} {v.proposicao_numero}/{v.proposicao_ano}
                              </span>
                            )
                          ) : (
                            <span className="mono-font text-base font-bold text-slate-900">
                              {v.tipo_votacao || `Votação #${v.id_votacao}`}
                            </span>
                          )}

                          {/* Badge de Voto Nominal */}
                          <VotoBadge voto={v.voto} />

                          {/* Descrição do tipo da matéria */}
                          {v.proposicao_descricao_tipo && (
                            <span className="text-[11px] text-slate-500 bg-slate-50 px-2 py-0.5 rounded border border-slate-200/60">
                              {v.proposicao_descricao_tipo}
                            </span>
                          )}

                          {/* Alerta de projeto de anos anteriores */}
                          {gapAnos >= 2 && (
                            <span
                              className="inline-flex items-center gap-0.5 text-[10px] font-medium bg-amber-50 text-amber-800 border border-amber-200/70 px-1.5 py-0.2 rounded"
                              title={`Proposição apresentada em ${v.proposicao_ano}`}
                            >
                              <Clock size={9} className="text-amber-600" />
                              Projeto de {v.proposicao_ano}
                            </span>
                          )}
                        </div>

                        <div className="flex items-center gap-3 text-xs text-slate-400">
                          <span className="flex items-center gap-1">
                            <Calendar size={12} /> {formatarData(v.data)}
                          </span>
                          <span className="hidden sm:inline-flex items-center text-blue-600 text-xs font-medium group-hover:translate-x-0.5 transition-transform">
                            Ver detalhes <ChevronRight size={14} className="ml-0.5" />
                          </span>
                        </div>
                      </div>

                      {/* Linha 2: Ementa descritiva */}
                      <p className="text-sm text-slate-700 leading-relaxed">
                        {v.proposicao_ementa || v.tipo_votacao || "Ementa não informada."}
                      </p>

                      {/* Linha 3: Resultado da deliberação, Órgão e Tags Temáticas */}
                      <div className="flex items-center justify-between gap-3 pt-1 flex-wrap text-xs">
                        <div className="flex items-center gap-2 flex-wrap">
                          <ResultadoVotacaoBadge aprovacao={v.aprovacao} resultadoTexto={(v as any).resultado_da_votacao} />

                          {v.sigla_orgao && (
                            <span className="inline-flex items-center gap-1 text-[11px] font-medium text-slate-600 bg-slate-50 border border-slate-200 px-2 py-0.5 rounded-md">
                              <Building2 size={11} className="text-slate-400" />
                              {v.sigla_orgao}
                            </span>
                          )}
                        </div>

                        {/* Badges Temáticas */}
                        {v.temas && v.temas.length > 0 && (
                          <div className="flex items-center gap-1.5 flex-wrap">
                            {v.temas.slice(0, 3).map((temaItem, idx) => (
                              <span
                                key={idx}
                                className="inline-flex items-center gap-1 text-[10px] font-medium text-slate-600 bg-slate-100 px-2 py-0.5 rounded-full"
                              >
                                <Tag size={9} className="text-slate-400" />
                                {temaItem}
                              </span>
                            ))}
                          </div>
                        )}
                      </div>
                    </article>
                  )
                })}
              </div>

              {/* Paginação */}
              {(temAnterior || temProxima) && (
                <div className="flex items-center justify-between px-5 py-3 border-t border-slate-100 bg-slate-50/60">
                  <button
                    data-testid="btn-votacoes-anterior"
                    disabled={!temAnterior}
                    onClick={() => setOffset(Math.max(0, offset - PAGE_SIZE))}
                    className="text-xs text-slate-500 hover:text-slate-700 disabled:opacity-30 disabled:cursor-not-allowed font-medium flex items-center gap-1 transition-colors"
                  >
                    <ChevronLeft size={14} /> Anterior
                  </button>
                  <span className="text-xs text-slate-500 font-medium">
                    Página {pagina} de {Math.max(1, totalPaginas)} ({total.toLocaleString("pt-BR")} votações)
                  </span>
                  <button
                    data-testid="btn-votacoes-proxima"
                    disabled={!temProxima}
                    onClick={() => setOffset(offset + PAGE_SIZE)}
                    className="text-xs text-slate-500 hover:text-slate-700 disabled:opacity-30 disabled:cursor-not-allowed font-medium flex items-center gap-1 transition-colors"
                  >
                    Próxima <ChevronRight size={14} />
                  </button>
                </div>
              )}
            </>
          )}
        </div>
      </section>

      {/* Painel lateral de detalhe — renderizado fora do section para cobrir a tela toda */}
      {votacaoAberta && (
        <PainelDetalheVotacao
          votacaoId={votacaoAberta.id}
          votoDeputado={votacaoAberta.voto}
          onClose={() => setVotacaoAberta(null)}
        />
      )}
    </>
  )
}

// ── STAT CARD CÍVICO ──────────────────────────────────────────────────────────────
const accentMap: Record<string, string> = {
  blue:    "bg-white border-slate-200/90 hover:border-blue-400 shadow-2xs",
  violet:  "bg-white border-slate-200/90 hover:border-indigo-400 shadow-2xs",
  emerald: "bg-white border-slate-200/90 hover:border-emerald-400 shadow-2xs",
  amber:   "bg-white border-slate-200/90 hover:border-amber-400 shadow-2xs",
  slate:   "bg-white border-slate-200/90 hover:border-slate-400 shadow-2xs",
}

function StatCard({
  icon,
  titulo,
  valor,
  subtitulo,
  accent = "slate",
  "data-testid": testId,
}: {
  icon: React.ReactNode
  titulo: string
  valor: any
  subtitulo?: string
  accent?: string
  "data-testid"?: string
}) {
  return (
    <div
      data-testid={testId}
      className={`stat-card rounded-xl border p-4 transition-all duration-150 cursor-default ${
        accentMap[accent] ?? accentMap.slate
      }`}
    >
      <div className="flex items-center gap-2 mb-1.5">
        {icon}
        <p className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider leading-tight">
          {titulo}
        </p>
      </div>
      <p className="font-mono tabular-nums text-lg font-bold text-slate-900 leading-tight truncate">
        {valor}
      </p>
      {subtitulo && (
        <p className="text-[10px] text-slate-400 mt-1 leading-snug">
          {subtitulo}
        </p>
      )}
    </div>
  )
}

// ── LOADING ────────────────────────────────────────────────────────────────
function LoadingScreen() {
  return (
    <>
      <Header />
      <div className="min-h-screen bg-[#f8f9fb] flex items-center justify-center pt-16">
        <div className="text-center">
          <div className="w-10 h-10 border-[3px] border-slate-200 border-t-blue-500 rounded-full animate-spin mx-auto mb-4" />
          <p className="text-sm text-slate-400 font-medium">Carregando perfil...</p>
        </div>
      </div>
    </>
  )
}

// ── ERROR ──────────────────────────────────────────────────────────────────
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
          <p className="text-sm text-slate-500">Não foi possível carregar o perfil deste parlamentar.</p>
          <Link
            to="/politicos"
            className="inline-flex items-center gap-1.5 mt-5 px-4 py-2 rounded-xl bg-slate-900 text-white text-xs font-semibold hover:bg-slate-800 transition-colors shadow-xs"
          >
            <ArrowLeft size={13} />
            Voltar aos Parlamentares
          </Link>
        </div>
      </div>
    </>
  )
}
