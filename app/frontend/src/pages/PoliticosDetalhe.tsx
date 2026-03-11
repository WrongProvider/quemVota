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
import InfoBotao from "../components/InfoDicaBotao"
import ToolDica from "../components/InfoDica"
import Header from "../components/Header"
import {
  MapPin,
  Users,
  GraduationCap,
  BadgeCheck,
  Mail,
  Phone,
  BarChart2,
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
} from "lucide-react"
import { useRegistrarBusca } from "../hooks/useBuscaPopular"
import { useVotacao } from "../hooks/useProposicoes"
import type { VotacaoResumida } from "../api/politicos.api"
import ModalSelecionarPolitico from "../components/ModalSelecionarPolitico"

const PATH_FOTOS = "/fotos_politicos/"

// ── SEO HEAD ────────────────────────────────────────────────────────────────

import { useSeo } from "../hooks/useSeo"

/**
 * Injeta meta tags SEO, Open Graph, Twitter Card, canonical e
 * JSON-LD Person (rich snippet) dinamicamente no <head>.
 */
function SeoHead({
  nome,
  partido,
  uf,
  score,
  fotoUrl,
  pageUrl,
}: {
  nome: string
  partido?: string
  uf?: string
  score?: number
  fotoUrl: string
  pageUrl: string
}) {
  const scoreTexto = score != null ? ` | Score: ${score.toFixed(0)}/100` : ""
  const localTexto = [partido, uf].filter(Boolean).join(" • ")

  useSeo({
    title: `${nome} — Perfil Parlamentar${localTexto ? ` | ${localTexto}` : ""}`,
    description:
      `Veja o perfil completo de ${nome}${localTexto ? ` (${localTexto})` : ""}` +
      `${scoreTexto}. Gastos, votações e performance parlamentar.`,
    url: pageUrl,
    image: fotoUrl,
    type: "profile",
    keywords: `${nome}, deputado federal, ${partido ?? ""}, ${uf ?? ""}, perfil parlamentar`,
  })

  // ── JSON-LD Person ──────────────────────────────────────────────────────
  useEffect(() => {
    const script = document.createElement("script")
    script.setAttribute("type", "application/ld+json")
    script.setAttribute("data-seo-dynamic", "true")
    script.textContent = JSON.stringify({
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
    })
    document.head.appendChild(script)

    return () => {
      document.querySelectorAll('[data-seo-dynamic="true"]').forEach((el) => el.remove())
    }
  }, [nome, partido, uf, fotoUrl, pageUrl])

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

  const idx = anoSelecionado ? anos.indexOf(anoSelecionado) : -1

  const handlePrev = () => {
    if (idx > 0) onChange(anos[idx - 1])
    else if (idx === -1) onChange(anos[anos.length - 1])
  }

  const handleNext = () => {
    if (idx === -1) return
    if (idx < anos.length - 1) onChange(anos[idx + 1])
    else onChange(null)
  }

  return (
    <div className="bg-white border border-slate-200 rounded-2xl shadow-sm overflow-hidden">
      <div className="bg-slate-50 border-b border-slate-100 px-6 py-3 text-center">
        <p className="text-sm font-medium text-slate-500">
          {anoSelecionado ? (
            <>Exibindo dados de <strong className="text-slate-800">{anoSelecionado}</strong></>
          ) : (
            "Selecione um ano abaixo ou veja o mandato completo"
          )}
        </p>
      </div>

      <div className="px-4 py-5">
        {/* Mobile: botões individuais em grid */}
        <div className="flex flex-wrap justify-center gap-2">
          {/* Botão "Tudo" */}
          <button
            onClick={() => onChange(null)}
            className={`flex items-center justify-center w-12 h-10 rounded-xl border-2 text-xs font-bold transition-all ${
              anoSelecionado === null
                ? "bg-slate-700 border-slate-700 text-white shadow-md"
                : "bg-white border-slate-200 text-slate-500 hover:border-slate-400"
            }`}
            title="Mandato completo"
          >
            ∑
          </button>

          {anos.map((ano) => {
            const ativo = ano === anoSelecionado
            return (
              <button
                key={ano}
                onClick={() => onChange(ativo ? null : ano)}
                className={`flex items-center justify-center px-3 h-10 rounded-xl border-2 text-xs font-semibold transition-all ${
                  ativo
                    ? "bg-yellow-400 border-yellow-400 text-white shadow-md scale-105"
                    : "bg-white border-slate-200 text-slate-600 hover:border-blue-400 hover:text-blue-600"
                }`}
              >
                {ano}
              </button>
            )
          })}
        </div>

        <p className="text-center text-[11px] text-slate-400 mt-4">
          ⓘ Informações disponíveis desde {anos[0]}
        </p>
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
  const [avisoSaidaAberto, setAvisoSaidaAberto] = useState(false)
  const [modalCompararAberto, setModalCompararAberto] = useState(false)

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

  const scoreColor =
    performance?.score_final >= 70
      ? "text-emerald-500"
      : performance?.score_final >= 40
      ? "text-amber-500"
      : "text-red-500"

  const pageUrl = `${window.location.origin}/politicos/${data.slug}`
  const fotoAbsoluta = `${window.location.origin}${PATH_FOTOS}${data.id}.jpg`

  return (
    <>
      {/* ── SEO META TAGS ── */}
      <SeoHead
        nome={data.nome}
        partido={data.partido_sigla}
        uf={data.uf}
        score={performance?.score_final}
        fotoUrl={fotoAbsoluta}
        pageUrl={pageUrl}
      />

      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=DM+Sans:ital,opsz,wght@0,9..40,300;0,9..40,400;0,9..40,500;0,9..40,600;1,9..40,400&family=DM+Mono:wght@400;500&family=Fraunces:ital,opsz,wght@0,9..144,300;0,9..144,700;1,9..144,400&display=swap');

        .detail-root { font-family: 'DM Sans', sans-serif; }
        .display-font { font-family: 'Fraunces', serif; }
        .mono-font { font-family: 'DM Mono', monospace; }

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
                  {/* ── BOTÃO COMPARAR ── */}
                  <button
                    onClick={() => setModalCompararAberto(true)}
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

              <div className="flex flex-col md:flex-row gap-8 items-start md:items-center">
                {/* PHOTO + SCORE (mobile: side by side) */}
                <div className="flex flex-row md:flex-col md:items-start gap-5 items-center">
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

                  {/* Score ring visível só no mobile, ao lado da foto */}
                  {performance && (
                    <div className="flex md:hidden flex-shrink-0 text-center">
                      <div>
                        <div
                          className="score-ring w-24 h-24"
                          style={{ "--score": performance.score_final } as React.CSSProperties}
                        >
                          <div className="score-ring-inner flex-col">
                            <span className={`mono-font text-xl font-bold ${scoreColor}`}>
                              {performance.score_final.toFixed(0)}
                            </span>
                            <span className="text-[10px] text-slate-400 leading-tight mt-0.5">
                              {anoSelecionado ? anoSelecionado : "score"}
                            </span>
                          </div>
                        </div>
                        <p className="text-xs text-slate-400 mt-2 font-medium">Performance</p>
                      </div>
                    </div>
                  )}
                </div>

                {/* INFO */}
                <div className="flex-1 min-w-0">
                  <div className="flex flex-wrap items-center gap-2 mb-2">
                    <span className="mono-font text-xs text-slate-400 uppercase tracking-widest">
                      Parlamentar Federal
                    </span>
                    {data.condicao_eleitoral && (
                      <span className="pill-badge text-blue-700 text-[11px] font-medium px-2.5 py-0.5 rounded-full border border-blue-100">
                        {data.condicao_eleitoral}
                      </span>
                    )}
                  </div>

                  <h1 className="display-font text-3xl md:text-4xl font-bold text-slate-900 mb-3 leading-tight">
                    {data.nome}
                  </h1>

                  <div className="flex flex-wrap gap-x-5 gap-y-2 text-sm text-slate-500">
                    {data.uf && (
                      <span className="flex items-center gap-1.5">
                        <MapPin size={14} className="text-slate-400" />
                        {data.uf}
                      </span>
                    )}
                    {data.partido_sigla && (
                      <span className="flex items-center gap-1.5">
                        <Users size={20} className="text-slate-400" />
                        {data.partido_sigla}
                      </span>
                    )}
                    {data.escolaridade && (
                      <span className="flex items-center gap-1.5">
                        <GraduationCap size={14} className="text-slate-400" />
                        {data.escolaridade}
                      </span>
                    )}
                  </div>

                  {/* Contacts */}
                  <div className="flex flex-wrap gap-3 mt-4">
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

                {/* SCORE RING — oculto no mobile (aparece ao lado da foto) */}
                {performance && (
                  <div className="hidden md:flex flex-shrink-0 text-center">
                    <div>
                      <div
                        className="score-ring w-28 h-28"
                        style={{ "--score": performance.score_final } as React.CSSProperties}
                      >
                        <div className="score-ring-inner flex-col">
                          <span className={`mono-font text-2xl font-bold ${scoreColor}`}>
                            {performance.score_final.toFixed(0)}
                          </span>
                          <span className="text-[10px] text-slate-400 leading-tight mt-0.5">
                            {anoSelecionado ? anoSelecionado : "score"}
                          </span>
                        </div>
                      </div>
                      <p className="text-xs text-slate-400 mt-2 font-medium">Performance</p>
                    </div>
                  </div>
                )}
              </div>

              {/* ── LINK OFICIAL DA CÂMARA ── */}
              <div className="mt-8 flex justify-center border-t border-slate-100 pt-6">
                <a
                  href={`https://www.camara.leg.br/deputados/${data.id_camara}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-2 text-sm text-slate-500 hover:text-blue-600 transition-colors"
                >
                  <ExternalLink size={16} />
                  Confira os dados oficiais da Câmara:{" "}
                  <span className="font-medium underline underline-offset-2">
                    https://www.camara.leg.br/deputados/{data.id_camara}
                  </span>
                </a>
              </div>
            </div>
          </div>
        </div>

        {/* ── MAIN CONTENT ── */}
        <div className="max-w-5xl mx-auto px-6 py-10 space-y-10">
          {/* ── SELETOR DE ANO ── */}
          {!timelineLoading && anosDisponiveis.length > 0 && (
            <section>
              <TimelineSelector
                anos={anosDisponiveis}
                anoSelecionado={anoSelecionado}
                onChange={setAnoSelecionado}
              />
            </section>
          )}

          {timelineLoading && (
            <div className="bg-white border border-slate-200 rounded-2xl h-28 flex items-center justify-center">
              <div className="w-6 h-6 border-2 border-slate-200 border-t-blue-500 rounded-full animate-spin" />
            </div>
          )}

          {anoSelecionado && (
            <div className="flex items-center justify-between bg-blue-50 border border-blue-100 rounded-xl px-4 py-3">
              <p className="text-sm text-blue-700 font-medium">
                📅 Dados filtrados para o ano <strong>{anoSelecionado}</strong>
              </p>
              <button
                onClick={() => setAnoSelecionado(null)}
                className="text-xs text-blue-500 hover:text-blue-700 font-medium underline underline-offset-2 transition-colors"
              >
                Ver mandato completo
              </button>
            </div>
          )}

          {/* ── ESTATÍSTICAS ── */}
          {stats && (
            <section key={`stats-${anoSelecionado}`} className="section-fade">
              <div className="flex items-center gap-2 mb-5">
                <BarChart2 size={18} className="text-blue-500" />
                <h2 className="display-font text-xl font-bold text-slate-800">Estatísticas</h2>
                <ToolDica
                  side="bottom"
                  content="O score é calculado com base em assiduidade, economia e produção parlamentar."
                >
                  <InfoBotao />
                </ToolDica>
              </div>

              <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                <StatCard icon={<BadgeCheck size={16} className="text-blue-500" />}    titulo="Total de Votações"   valor={stats.total_votacoes}                                                        accent="blue"    />
                <StatCard icon={<Receipt size={16} className="text-violet-500" />}     titulo="Total de Despesas"   valor={stats.total_despesas}                                                        accent="violet"  />
                <StatCard icon={<TrendingUp size={16} className="text-emerald-500" />} titulo="Cota Parlamentar"    valor={`R$ ${stats.total_gasto.toLocaleString("pt-BR")}`}                           accent="emerald" />
                <StatCard icon={<Wallet size={16} className="text-orange-500" />}      titulo="Verba de Gabinete"   valor={`R$ ${(stats.total_gasto_gabinete ?? 0).toLocaleString("pt-BR")}`}           accent="amber"   />
                <StatCard icon={<Receipt size={16} className="text-red-500" />}        titulo="Gasto Total"         valor={`R$ ${(stats.total_gasto_combinado ?? stats.total_gasto).toLocaleString("pt-BR")}`} accent="slate" />
                <StatCard icon={<Receipt size={16} className="text-amber-500" />}      titulo="Média Mensal"        valor={`R$ ${stats.media_mensal.toLocaleString("pt-BR")}`}                          accent="amber"   />
                {!anoSelecionado && (
                  <>
                    <StatCard icon={<Calendar size={16} className="text-slate-400" />} titulo="Primeiro Ano" valor={stats.primeiro_ano ?? "—"} accent="slate" />
                    <StatCard icon={<Calendar size={16} className="text-slate-400" />} titulo="Último Ano"   valor={stats.ultimo_ano ?? "—"}   accent="slate" />
                  </>
                )}
              </div>

              {/* Aviso quando gabinete != 0 */}
              {(stats.total_gasto_gabinete ?? 0) > 0 && (
                <p className="text-[11px] text-slate-400 mt-2 leading-relaxed">
                  ℹ️ <strong>Cota Parlamentar</strong> cobre deslocamentos, materiais e serviços de terceiros.{" "}
                  <strong>Verba de Gabinete</strong> cobre salários e encargos dos funcionários do escritório.
                </p>
              )}
            </section>
          )}

          {/* ── PERFORMANCE PARLAMENTAR ── */}
          {performance && (
            <section key={`perf-${anoSelecionado}`} className="section-fade">
              <div className="flex items-center gap-2 mb-5">
                <TrendingUp size={18} className="text-blue-500" />
                <h2 className="display-font text-xl font-bold text-slate-800">Performance Parlamentar</h2>
              </div>
              <PoliticoGraficos performance={performance} />

              {/* Breakdown do orçamento — exibido quando há dados de gabinete */}
              {(performance.info?.gasto_gabinete ?? 0) > 0 && (
                <div className="mt-4 bg-white border border-slate-200 rounded-2xl overflow-hidden">
                  <div className="px-5 py-3 border-b border-slate-100 bg-slate-50/60">
                    <p className="text-[11px] font-semibold text-slate-500 uppercase tracking-wide">
                      💰 Composição do Orçamento
                    </p>
                  </div>
                  <div className="grid grid-cols-2 md:grid-cols-4 divide-x divide-slate-100">
                    {[
                      {
                        label: "Cota Parlamentar",
                        value: `R$ ${(performance.info.total_gasto ?? 0).toLocaleString("pt-BR")}`,
                        sub: "gastos CEAP",
                        color: "text-violet-600",
                      },
                      {
                        label: "Verba de Gabinete",
                        value: `R$ ${(performance.info.gasto_gabinete ?? 0).toLocaleString("pt-BR")}`,
                        sub: "pessoal / funcionários",
                        color: "text-orange-500",
                      },
                      {
                        label: "Gasto Total",
                        value: `R$ ${(performance.info.gasto_total ?? 0).toLocaleString("pt-BR")}`,
                        sub: "CEAP + gabinete",
                        color: "text-red-500",
                      },
                      {
                        label: "Orçamento Utilizado",
                        value: `${(performance.info.orcamento_utilizado_pct ?? performance.info.cota_utilizada_pct ?? 0).toFixed(1)}%`,
                        sub: "do total disponível",
                        color:
                          (performance.info.orcamento_utilizado_pct ?? 0) > 85
                            ? "text-red-500"
                            : (performance.info.orcamento_utilizado_pct ?? 0) > 60
                            ? "text-amber-500"
                            : "text-emerald-600",
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
              )}
            </section>
          )}

          {/* ── HISTÓRICO DE GASTOS ── */}
          <section className="mt-10">
            <div className="flex items-center gap-2 mb-5">
              <Receipt size={18} className="text-blue-500" />
              <h2 className="display-font text-xl font-bold text-slate-800">Histórico de Gastos</h2>
            </div>
            <LinhaDoTempo politicoId={data.id} />
          </section>

          {/* ── HISTÓRICO DE VOTAÇÕES ── */}
          <HistoricoVotacoes politicoId={data.id} anoSelecionado={anoSelecionado} />
        </div>
      </div>

      {/* ── MODAL COMPARAR ── */}
      {modalCompararAberto && (
        <ModalSelecionarPolitico
          politicoAtualId={data.id}
          politicoAtualSlug={data.slug}
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

function VotoBadge({ voto }: { voto: string }) {
  const cfg = VOTO_CONFIG[voto] ?? { label: voto, cls: "text-slate-600 bg-slate-50 border-slate-200", icon: <MinusCircle size={11} /> }
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
  votoDeputado: string   // voto já conhecido — exibido imediatamente sem aguardar fetch
  onClose: () => void
}) {
  const { data: votacao, isLoading } = useVotacao(votacaoId)
  const [abaAtiva, setAbaAtiva] = useState<"orientacoes" | "votos">("orientacoes")

  const formatarData = (iso: string | null | undefined) => {
    if (!iso) return "—"
    return new Date(iso).toLocaleDateString("pt-BR", { day: "2-digit", month: "long", year: "numeric" })
  }

  const cfg = VOTO_CONFIG[votoDeputado] ?? { cls: "text-slate-600 bg-slate-50 border-slate-200", clsLight: "bg-slate-50" }

  return (
    <>
      {/* Overlay para fechar clicando fora */}
      <div
        className="fixed inset-0 z-40 bg-black/20 backdrop-blur-[1px]"
        onClick={onClose}
      />

      {/* Painel deslizante */}
      <div
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

function HistoricoVotacoes({ politicoId, anoSelecionado }: { politicoId: number; anoSelecionado: number | null }) {
  const PAGE_SIZE = 15
  const [offset, setOffset] = useState(0)
  const [filtroVoto, setFiltroVoto] = useState<string>("")
  const [votacaoAberta, setVotacaoAberta] = useState<{ id: number; voto: string } | null>(null)

  // Reseta página ao trocar filtros ou ano
  useEffect(() => { setOffset(0) }, [anoSelecionado, filtroVoto])

  // Fecha painel ao trocar de página
  useEffect(() => { setVotacaoAberta(null) }, [offset])

  const { data: atividade, isLoading } = usePoliticoAtividade(politicoId, {
    ano: anoSelecionado ?? undefined,
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

  const votacoesFiltradas = filtroVoto
    ? votacoes.filter((v) => v.voto === filtroVoto)
    : votacoes

  const pagina = Math.floor(offset / PAGE_SIZE) + 1
  const temAnterior = offset > 0
  const temProxima = votacoes.length === PAGE_SIZE

  const formatarData = (iso: string | null | undefined) => {
    if (!iso) return "—"
    return new Date(iso).toLocaleDateString("pt-BR", { day: "2-digit", month: "short", year: "numeric" })
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

      <section className="section-fade">
        <div className="flex items-center justify-between gap-3 mb-5 flex-wrap">
          <div className="flex items-center gap-2">
            <Vote size={18} className="text-blue-500" />
            <h2 className="display-font text-xl font-bold text-slate-800">Histórico de Votações</h2>
            {total > 0 && (
              <span className="text-xs font-medium text-slate-400 bg-slate-100 px-2 py-0.5 rounded-full">
                {total.toLocaleString("pt-BR")} registros
              </span>
            )}
          </div>

          <div className="relative">
            <select
              value={filtroVoto}
              onChange={(e) => setFiltroVoto(e.target.value)}
              className="appearance-none text-sm border border-slate-200 rounded-lg pl-3 pr-8 py-1.5 bg-white text-slate-600 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-400 transition-all cursor-pointer"
            >
              <option value="">Todos os votos</option>
              <option value="Sim">Sim</option>
              <option value="Não">Não</option>
              <option value="Obstrução">Obstrução</option>
              <option value="Abstenção">Abstenção</option>
            </select>
            <ChevronDown size={13} className="absolute right-2.5 top-1/2 -translate-y-1/2 text-slate-400 pointer-events-none" />
          </div>
        </div>

        <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
          {isLoading ? (
            <div className="flex items-center justify-center py-16 gap-3 text-slate-400">
              <Loader2 size={20} className="animate-spin" />
              <span className="text-sm">Carregando votações...</span>
            </div>
          ) : votacoesFiltradas.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-16 text-slate-400">
              <Vote size={32} className="mb-3 opacity-30" />
              <p className="text-sm">
                {filtroVoto
                  ? `Nenhum voto "${filtroVoto}" encontrado${anoSelecionado ? ` em ${anoSelecionado}` : ""}.`
                  : `Sem votações registradas${anoSelecionado ? ` em ${anoSelecionado}` : ""}.`}
              </p>
            </div>
          ) : (
            <>
              {/* Cabeçalho da tabela */}
              <div className="hidden md:grid grid-cols-[1fr_auto_auto_auto_auto] gap-4 px-5 py-3 border-b border-slate-100 bg-slate-50">
                <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wide">Proposição / Ementa</span>
                <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wide">Data</span>
                <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wide">Resultado</span>
                <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wide">Voto</span>
                <span /> {/* coluna do chevron */}
              </div>

              <div className="divide-y divide-slate-100">
                {votacoesFiltradas.map((v, i) => {
                  const ativo = votacaoAberta?.id === v.id_votacao
                  return (
                    <button
                      key={`${v.id_votacao}-${i}`}
                      onClick={() => setVotacaoAberta(ativo ? null : { id: v.id_votacao, voto: v.voto })}
                      className={`w-full text-left px-5 py-3.5 transition-colors group ${
                        ativo
                          ? "bg-blue-50 border-l-2 border-l-blue-500"
                          : "hover:bg-slate-50 border-l-2 border-l-transparent"
                      }`}
                    >
                      {/* Layout mobile */}
                      <div className="md:hidden space-y-2">
                        <div className="flex items-start justify-between gap-3">
                          <div className="flex-1 min-w-0">
                            {(v.proposicao_sigla || v.proposicao_numero) && (
                              <span className="text-[11px] font-semibold text-blue-600 font-mono">
                                {v.proposicao_sigla} {v.proposicao_numero}/{v.proposicao_ano}
                              </span>
                            )}
                            <p className="text-sm text-slate-700 leading-snug mt-0.5 line-clamp-2">
                              {v.proposicao_ementa ?? v.tipo_votacao ?? "—"}
                            </p>
                          </div>
                          <VotoBadge voto={v.voto} />
                        </div>
                        <div className="flex items-center gap-3 text-[11px] text-slate-400">
                          <span>{formatarData(v.data)}</span>
                          <ResultadoVotacaoBadge aprovacao={v.aprovacao} resultadoTexto={(v as any).resultado_da_votacao} />
                          {v.sigla_orgao && (
                            <span className="bg-slate-100 px-1.5 py-0.5 rounded text-slate-500">{v.sigla_orgao}</span>
                          )}
                        </div>
                      </div>

                      {/* Layout desktop */}
                      <div className="hidden md:grid grid-cols-[1fr_auto_auto_auto_auto] gap-4 items-center">
                        <div className="min-w-0">
                          {(v.proposicao_sigla || v.proposicao_numero) && (
                            <span className="text-[11px] font-semibold text-blue-600 font-mono mr-2">
                              {v.proposicao_sigla} {v.proposicao_numero}/{v.proposicao_ano}
                            </span>
                          )}
                          <p className="text-sm text-slate-700 leading-snug truncate">
                            {v.proposicao_ementa ?? v.tipo_votacao ?? "—"}
                          </p>
                          {v.sigla_orgao && (
                            <span className="text-[10px] text-slate-400 mt-0.5 inline-block">{v.sigla_orgao}</span>
                          )}
                        </div>
                        <span className="text-sm text-slate-500 whitespace-nowrap">{formatarData(v.data)}</span>
                        <ResultadoVotacaoBadge aprovacao={v.aprovacao} resultadoTexto={(v as any).resultado_da_votacao} />
                        <VotoBadge voto={v.voto} />
                        <ChevronRight
                          size={14}
                          className={`transition-colors flex-shrink-0 ${
                            ativo ? "text-blue-500" : "text-slate-300 group-hover:text-slate-500"
                          }`}
                        />
                      </div>
                    </button>
                  )
                })}
              </div>

              {/* Paginação */}
              {(temAnterior || temProxima) && (
                <div className="flex items-center justify-between px-5 py-3 border-t border-slate-100 bg-slate-50/60">
                  <button
                    disabled={!temAnterior}
                    onClick={() => setOffset(Math.max(0, offset - PAGE_SIZE))}
                    className="text-xs text-slate-500 hover:text-slate-700 disabled:opacity-30 disabled:cursor-not-allowed font-medium flex items-center gap-1 transition-colors"
                  >
                    <ArrowLeft size={12} /> Anterior
                  </button>
                  <span className="text-xs text-slate-400">Página {pagina}</span>
                  <button
                    disabled={!temProxima}
                    onClick={() => setOffset(offset + PAGE_SIZE)}
                    className="text-xs text-slate-500 hover:text-slate-700 disabled:opacity-30 disabled:cursor-not-allowed font-medium flex items-center gap-1 transition-colors"
                  >
                    Próxima <ChevronRight size={12} />
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

// ── STAT CARD ──────────────────────────────────────────────────────────────
const accentMap: Record<string, string> = {
  blue:    "bg-blue-50 border-blue-100 hover:border-blue-300",
  violet:  "bg-violet-50 border-violet-100 hover:border-violet-300",
  emerald: "bg-emerald-50 border-emerald-100 hover:border-emerald-300",
  amber:   "bg-amber-50 border-amber-100 hover:border-amber-300",
  slate:   "bg-white border-slate-200 hover:border-slate-300",
}

function StatCard({
  icon, titulo, valor, accent = "slate",
}: {
  icon: React.ReactNode
  titulo: string
  valor: any
  accent?: string
}) {
  return (
    <div className={`stat-card rounded-xl border p-4 transition-colors duration-200 cursor-default ${accentMap[accent] ?? accentMap.slate}`}>
      <div className="flex items-center gap-2 mb-2">
        {icon}
        <p className="text-[11px] font-medium text-slate-500 uppercase tracking-wide leading-tight">{titulo}</p>
      </div>
      <p className="mono-font text-lg font-semibold text-slate-800 leading-tight truncate">{valor}</p>
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
      <div className="min-h-screen bg-[#f8f9fb] flex items-center justify-center pt-16">
        <div className="text-center">
          <div className="w-14 h-14 rounded-2xl bg-red-50 flex items-center justify-center mx-auto mb-4">
            <span className="text-2xl">⚠️</span>
          </div>
          <h2 className="text-lg font-semibold text-slate-700 mb-1">Erro ao carregar</h2>
          <p className="text-sm text-slate-400">Não foi possível carregar o perfil deste parlamentar.</p>
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