import { useParams, Link } from "react-router-dom"
import { usePoliticoEstatisticas, usePoliticoDetalhe, usePoliticoPerformance } from "../hooks/usePoliticos"
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
  Calendar,
  ChevronRight,
  ArrowLeft,
} from "lucide-react"

const PATH_FOTOS = "/politicos/" // As fotos devem estar disponíveis neste caminho público

export default function PoliticoDetalhe() {
  const { id } = useParams()
  const politicoId = Number(id)
  const { data, isLoading, error } = usePoliticoDetalhe(politicoId)
  const { data: stats } = usePoliticoEstatisticas(politicoId)
  const { data: performance } = usePoliticoPerformance(politicoId)

  if (isLoading) return <LoadingScreen />
  if (error) return <ErrorScreen />
  if (!data) return null

  const scoreColor =
    performance?.score_final >= 70
      ? "text-emerald-500"
      : performance?.score_final >= 40
      ? "text-amber-500"
      : "text-red-500"

  const scoreBg =
    performance?.score_final >= 70
      ? "bg-emerald-50 border-emerald-200"
      : performance?.score_final >= 40
      ? "bg-amber-50 border-amber-200"
      : "bg-red-50 border-red-200"

  return (
    <>
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
      `}</style>

      <div className="detail-root min-h-screen bg-[#f8f9fb]">
        <Header />

        {/* ── HERO SECTION ── */}
        <div className="pt-16">
          <div className="relative overflow-hidden bg-white border-b border-slate-100">
            {/* Decorative background */}
            <div
              className="absolute inset-0 opacity-[0.03]"
              style={{
                backgroundImage:
                  "radial-gradient(circle at 80% 50%, #2563eb 0%, transparent 60%), radial-gradient(circle at 20% 80%, #7c3aed 0%, transparent 50%)",
              }}
            />

            <div className="relative max-w-5xl mx-auto px-6 py-12 hero-fade">
              {/* Back breadcrumb */}
              <Link
                to="/politicos"
                className="inline-flex items-center gap-1.5 text-sm text-slate-400 hover:text-slate-700 transition-colors mb-8 group"
              >
                <ArrowLeft size={14} className="group-hover:-translate-x-0.5 transition-transform" />
                Parlamentares
                <ChevronRight size={12} className="opacity-50" />
                <span className="text-slate-600 font-medium">{data.nome}</span>
              </Link>

              <div className="flex flex-col md:flex-row gap-8 items-start md:items-center">
                {/* PHOTO */}
                <div className="profile-photo relative flex-shrink-0">
                  <div className="w-32 h-32 md:w-40 md:h-40 rounded-2xl overflow-hidden ring-4 ring-white shadow-xl">
                    <img
                      src={`${PATH_FOTOS}${data.id}.jpg`}
                      alt={data.nome}
                      className="w-full h-full object-cover"
                    />
                  </div>
                  {/* Status badge */}
                  {data.situacao && (
                    <div className="absolute -bottom-2 left-1/2 -translate-x-1/2 whitespace-nowrap">
                      <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-medium bg-emerald-500 text-white shadow-sm">
                        <span className="w-1.5 h-1.5 rounded-full bg-white inline-block" />
                        {data.situacao}
                      </span>
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

                {/* SCORE RING (if available) */}
                {performance && (
                  <div className="flex-shrink-0 text-center">
                    <div
                      className="score-ring w-28 h-28"
                      style={{ "--score": performance.score_final } as React.CSSProperties}
                    >
                      <div className="score-ring-inner flex-col">
                        <span className={`mono-font text-2xl font-bold ${scoreColor}`}>
                          {performance.score_final.toFixed(0)}
                        </span>
                        <span className="text-[10px] text-slate-400 leading-tight mt-0.5">
                          score
                        </span>
                      </div>
                    </div>
                    <p className="text-xs text-slate-400 mt-2 font-medium">Performance</p>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* ── MAIN CONTENT ── */}
        <div className="max-w-5xl mx-auto px-6 py-10">

          {/* ── ESTATÍSTICAS ── */}
          {stats && (
            <section className="mb-10">
              <div className="flex items-center gap-2 mb-5">
                <BarChart2 size={18} className="text-blue-500" />
                <h2 className="display-font text-xl font-bold text-slate-800">Estatísticas</h2>
                <ToolDica
                  side="right"
                  content="O score é calculado com base em assiduidade, economia e produção parlamentar."
                >
                  <InfoBotao />
                </ToolDica>
              </div>

              <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                <StatCard
                  icon={<BadgeCheck size={16} className="text-blue-500" />}
                  titulo="Total de Votações"
                  valor={stats.total_votacoes}
                  accent="blue"
                />
                <StatCard
                  icon={<Receipt size={16} className="text-violet-500" />}
                  titulo="Total de Despesas"
                  valor={stats.total_despesas}
                  accent="violet"
                />
                <StatCard
                  icon={<TrendingUp size={16} className="text-emerald-500" />}
                  titulo="Cota Utilizada"
                  valor={`R$ ${stats.total_gasto.toLocaleString("pt-BR")}`}
                  accent="emerald"
                />
                <StatCard
                  icon={<Receipt size={16} className="text-amber-500" />}
                  titulo="Média Mensal"
                  valor={`R$ ${stats.media_mensal.toLocaleString("pt-BR")}`}
                  accent="amber"
                />
                <StatCard
                  icon={<Calendar size={16} className="text-slate-400" />}
                  titulo="Primeiro Ano"
                  valor={stats.primeiro_ano ?? "—"}
                  accent="slate"
                />
                <StatCard
                  icon={<Calendar size={16} className="text-slate-400" />}
                  titulo="Último Ano"
                  valor={stats.ultimo_ano ?? "—"}
                  accent="slate"
                />
              </div>
            </section>
          )}

          {/* ── GRÁFICOS ── */}
          {performance && (
            <section>
              <div className="flex items-center gap-2 mb-5">
                <TrendingUp size={18} className="text-blue-500" />
                <h2 className="display-font text-xl font-bold text-slate-800">Performance Parlamentar</h2>
              </div>
              <PoliticoGraficos performance={performance} />
            </section>
          )}

          {/* ── LINHA DO TEMPO ── */}
          <section className="mt-10">
            <div className="flex items-center gap-2 mb-5">
              <Receipt size={18} className="text-blue-500" />
              <h2 className="display-font text-xl font-bold text-slate-800">Histórico de Gastos</h2>
            </div>
            <LinhaDoTempo politicoId={politicoId} />
          </section>
        </div>
      </div>
    </>
  )
}

// ── STAT CARD ──
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
  valor: any
  accent?: string
}) {
  return (
    <div
      className={`stat-card rounded-xl border p-4 transition-colors duration-200 cursor-default ${accentMap[accent] ?? accentMap.slate}`}
    >
      <div className="flex items-center gap-2 mb-2">
        {icon}
        <p className="text-[11px] font-medium text-slate-500 uppercase tracking-wide leading-tight">
          {titulo}
        </p>
      </div>
      <p className="mono-font text-lg font-semibold text-slate-800 leading-tight truncate">{valor}</p>
    </div>
  )
}

// ── LOADING ──
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

// ── ERROR ──
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