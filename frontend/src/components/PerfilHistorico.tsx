import { Link } from "react-router-dom"
import {
  ArrowLeft,
  ChevronRight,
  ExternalLink,
  MapPin,
  Users,
  GraduationCap,
  Calendar,
  Landmark,
  Share2,
  Copy,
  Check,
} from "lucide-react"
import { useState } from "react"
import Header from "./Header"
import type { PoliticoDetalhe } from "../api/politicos.api"

const PATH_FOTOS = "/fotos_politicos/"

// ── Botão compartilhar (simplificado para o perfil histórico) ────────────────
function BotaoCompartilhar({ nome, url }: { nome: string; url: string }) {
  const [copiado, setCopiado] = useState(false)
  const [aberto, setAberto] = useState(false)

  const texto = `Veja o perfil parlamentar de ${nome}`

  const redes = [
    {
      label: "WhatsApp",
      href: `https://wa.me/?text=${encodeURIComponent(`${texto}\n${url}`)}`,
      color: "hover:bg-green-50 hover:text-green-600 hover:border-green-200",
      icon: (
        <svg viewBox="0 0 24 24" className="w-4 h-4 fill-current" xmlns="http://www.w3.org/2000/svg">
          <path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z" />
        </svg>
      ),
    },
    {
      label: "X / Twitter",
      href: `https://twitter.com/intent/tweet?text=${encodeURIComponent(texto)}&url=${encodeURIComponent(url)}`,
      color: "hover:bg-slate-50 hover:text-slate-900 hover:border-slate-300",
      icon: (
        <svg viewBox="0 0 24 24" className="w-4 h-4 fill-current" xmlns="http://www.w3.org/2000/svg">
          <path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-4.714-6.231-5.401 6.231H2.744l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z" />
        </svg>
      ),
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
      </button>

      {aberto && (
        <>
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

// ── Item de informação biográfica ────────────────────────────────────────────
function InfoItem({
  icon,
  label,
  value,
}: {
  icon: React.ReactNode
  label: string
  value: string | undefined | null
}) {
  if (!value) return null
  return (
    <div className="flex items-start gap-3 py-3 border-b border-slate-100 last:border-0">
      <div className="flex-shrink-0 w-8 h-8 rounded-lg bg-slate-100 flex items-center justify-center text-slate-500 mt-0.5">
        {icon}
      </div>
      <div>
        <p className="text-[11px] text-slate-400 font-medium uppercase tracking-wide">{label}</p>
        <p className="text-sm text-slate-700 font-medium mt-0.5">{value}</p>
      </div>
    </div>
  )
}

// ── Componente principal ─────────────────────────────────────────────────────
export interface PerfilHistoricoProps {
  data: PoliticoDetalhe
}

export default function PerfilHistorico({ data }: PerfilHistoricoProps) {
  const pageUrl = `${window.location.origin}/politicos/${data.slug ?? data.id}`

  return (
    <>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=DM+Sans:ital,opsz,wght@0,9..40,300;0,9..40,400;0,9..40,500;0,9..40,600;1,9..40,400&family=Fraunces:ital,opsz,wght@0,9..144,300;0,9..144,700;1,9..144,400&display=swap');
        .hist-root { font-family: 'DM Sans', sans-serif; }
        .hist-display { font-family: 'Fraunces', serif; }
        .hist-photo-reveal {
          animation: photoReveal 0.7s cubic-bezier(0.22, 1, 0.36, 1) both;
        }
        @keyframes photoReveal {
          from { opacity: 0; transform: scale(0.92) translateY(12px); }
          to   { opacity: 1; transform: scale(1) translateY(0); }
        }
        .hist-fade {
          animation: histFade 0.5s ease both;
        }
        @keyframes histFade {
          from { opacity: 0; transform: translateY(10px); }
          to   { opacity: 1; transform: translateY(0); }
        }
      `}</style>

      <div className="hist-root min-h-screen bg-[#f8f9fb]">
        <Header />

        {/* ── HERO ── */}
        <div className="pt-16">
          <div className="relative overflow-hidden bg-white border-b border-slate-100">
            {/* Fundo decorativo — tom âmbar/sépia para distinguir do perfil ativo */}
            <div
              className="absolute inset-0 opacity-[0.04]"
              style={{
                backgroundImage:
                  "radial-gradient(circle at 80% 50%, #b45309 0%, transparent 60%), radial-gradient(circle at 20% 80%, #92400e 0%, transparent 50%)",
              }}
            />

            <div className="relative max-w-5xl mx-auto px-6 py-12 hist-fade">
              {/* Breadcrumb + ações */}
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

                <BotaoCompartilhar nome={data.nome} url={pageUrl} />
              </div>

              <div className="flex flex-col md:flex-row gap-8 items-start md:items-center">
                {/* Foto */}
                <div className="hist-photo-reveal relative flex-shrink-0">
                  <div className="w-28 h-28 md:w-40 md:h-40 rounded-2xl overflow-hidden ring-4 ring-white shadow-xl">
                    <img
                      src={`${PATH_FOTOS}${data.id}.jpg`}
                      alt={`Foto de ${data.nome}`}
                      className="w-full h-full object-cover grayscale-[20%]"
                    />
                  </div>
                  {/* Badge Perfil Histórico na foto */}
                  <div className="absolute -bottom-3 left-1/2 -translate-x-1/2 whitespace-nowrap">
                    <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-[11px] font-semibold bg-amber-600 text-white shadow-md">
                      <Landmark size={11} />
                      Perfil Histórico
                    </span>
                  </div>
                </div>

                {/* Info textual */}
                <div className="flex-1 min-w-0 mt-2 md:mt-0">
                  <div className="flex flex-wrap items-center gap-2 mb-2">
                    <span className="text-xs text-slate-400 uppercase tracking-widest font-mono">
                      Parlamentar Federal
                    </span>
                    {data.condicao_eleitoral && (
                      <span className="text-amber-700 text-[11px] font-medium px-2.5 py-0.5 rounded-full border border-amber-200 bg-amber-50">
                        {data.condicao_eleitoral}
                      </span>
                    )}
                  </div>

                  <h1 className="hist-display text-3xl md:text-4xl font-bold text-slate-900 mb-3 leading-tight">
                    {data.nome}
                  </h1>

                  <div className="flex flex-wrap gap-x-5 gap-y-2 text-sm text-slate-500">
                    {data.sigla_uf && (
                      <span className="flex items-center gap-1.5">
                        <MapPin size={14} className="text-slate-400" />
                        {data.sigla_uf}
                      </span>
                    )}
                    {data.sigla_partido && (
                      <span className="flex items-center gap-1.5">
                        <Users size={20} className="text-slate-400" />
                        {data.sigla_partido}
                      </span>
                    )}
                    {data.escolaridade && (
                      <span className="flex items-center gap-1.5">
                        <GraduationCap size={14} className="text-slate-400" />
                        {data.escolaridade}
                      </span>
                    )}
                  </div>

                  {/* Link Câmara */}
                  <div className="mt-4">
                    <a
                      href={`https://www.camara.leg.br/deputados/${data.id_camara}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center gap-1.5 text-sm text-slate-500 hover:text-amber-700 transition-colors"
                    >
                      <ExternalLink size={14} />
                      Ficha na Câmara dos Deputados
                    </a>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* ── MAIN CONTENT ── */}
        <div className="max-w-5xl mx-auto px-6 py-10 space-y-8 hist-fade">

          {/* ── AVISO DE DADOS AUSENTES ── */}
          <div className="bg-amber-50 border border-amber-200 rounded-2xl p-6">
            <div className="flex gap-4 items-start">
              <div className="flex-shrink-0 w-10 h-10 rounded-xl bg-amber-100 flex items-center justify-center text-amber-700">
                <Landmark size={20} />
              </div>
              <div>
                <h2 className="text-base font-semibold text-amber-900 mb-1">
                  Dados não disponíveis na fonte oficial
                </h2>
                <p className="text-sm text-amber-800 leading-relaxed">
                  Os registros de votações nominais, despesas com cota parlamentar e presença em sessões
                  deste mandato <strong>não estão disponíveis na API oficial da Câmara dos Deputados</strong>.
                  Isso ocorre com mandatos anteriores à digitalização dos registros legislativos, que se
                  iniciou de forma abrangente a partir da{" "}
                  <strong>52ª Legislatura (2003)</strong>. Os dados que o quemvota exibe para outros parlamentares
                  são extraídos diretamente dos registros oficiais — neste caso, a Câmara não os disponibiliza
                  eletronicamente.
                </p>
                <a
                  href={`https://www.camara.leg.br/deputados/${data.id_camara}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-1.5 mt-4 text-sm font-medium text-amber-700 hover:text-amber-900 underline underline-offset-2 transition-colors"
                >
                  <ExternalLink size={14} />
                  Consultar ficha oficial na Câmara dos Deputados
                </a>
              </div>
            </div>
          </div>

          {/* ── DADOS BIOGRÁFICOS DISPONÍVEIS ── */}
          <div className="bg-white border border-slate-200 rounded-2xl overflow-hidden shadow-sm">
            <div className="px-6 py-4 border-b border-slate-100 bg-slate-50/60">
              <h2 className="text-sm font-semibold text-slate-600 uppercase tracking-wide">
                Informações cadastrais registradas
              </h2>
              <p className="text-[11px] text-slate-400 mt-0.5">
                Dados biográficos disponíveis na base da Câmara dos Deputados.
              </p>
            </div>
            <div className="px-6 divide-y divide-slate-100">
              <InfoItem
                icon={<Users size={15} />}
                label="Nome Civil"
                value={data.nome_civil ?? data.nome}
              />
              <InfoItem
                icon={<Calendar size={15} />}
                label="Data de Nascimento"
                value={
                  data.data_nascimento
                    ? new Date(data.data_nascimento).toLocaleDateString("pt-BR", {
                        day: "2-digit",
                        month: "long",
                        year: "numeric",
                      })
                    : undefined
                }
              />
              <InfoItem
                icon={<GraduationCap size={15} />}
                label="Escolaridade"
                value={data.escolaridade}
              />
              <InfoItem
                icon={<Users size={15} />}
                label="Partido"
                value={data.sigla_partido}
              />
              <InfoItem
                icon={<MapPin size={15} />}
                label="Estado"
                value={data.sigla_uf}
              />
              <InfoItem
                icon={<Landmark size={15} />}
                label="Situação"
                value={data.situacao}
              />
              <InfoItem
                icon={<Landmark size={15} />}
                label="Condição Eleitoral"
                value={data.condicao_eleitoral}
              />
            </div>
          </div>

          {/* ── NOTA DE TRANSPARÊNCIA ── */}
          <p className="text-[11px] text-slate-400 text-center leading-relaxed px-4">
            O quemvota exibe exclusivamente dados disponibilizados oficialmente pela Câmara dos Deputados.
            Não é possível inferir ou estimar informações não registradas na fonte.
            ID na Câmara: <span className="font-mono">{data.id_camara ?? data.id}</span>
          </p>
        </div>
      </div>
    </>
  )
}
