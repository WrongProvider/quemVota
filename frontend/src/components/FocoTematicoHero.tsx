/**
 * FocoTematicoHero.tsx — Resumo de Foco Temático e Presença para o Hero do Parlamentar.
 *
 * Apresenta de forma compacta e equilibrada os principais temas da atuação do parlamentar
 * ao lado da métrica de presença, ocupando o espaço livre do cabeçalho sem ultrapassar
 * a altura da foto do parlamentar (160px).
 *
 * Princípio da Neutralidade Factual (AGENTS.md):
 *  - Linguagem puramente descritiva.
 *  - Percentuais factuais calculados sobre proposições oficiais da 57ª Legislatura.
 */

import { Target } from "lucide-react"
import { usePoliticoTemas } from "../hooks/usePoliticos"

interface FocoTematicoHeroProps {
  politicoId: string | number
  notaAssiduidade?: number | null
  anoSelecionado?: number | null
  onVerTodosTemas?: () => void
}

// Cores para as 3 barras de progresso (gradiente semântico harmonioso)
const CORES_BARRAS = ["#1d4ed8", "#2563eb", "#3b82f6"]

export default function FocoTematicoHero({
  politicoId,
  notaAssiduidade,
  anoSelecionado,
  onVerTodosTemas,
}: FocoTematicoHeroProps) {
  const { data: temasData, isLoading } = usePoliticoTemas(politicoId, {
    id_legislatura: 57,
    limit: 10,
  })

  // Skeleton de carregamento com tamanho fixo idêntico para evitar CLS
  if (isLoading) {
    return (
      <div
        data-testid="foco-tematico-hero-skeleton"
        className="hidden md:flex flex-shrink-0 bg-slate-50/80 border border-slate-200/80 rounded-2xl p-3.5 h-[152px] w-[360px] animate-pulse items-center gap-3.5"
      >
        <div className="flex-1 space-y-2.5">
          <div className="h-3.5 w-24 bg-slate-200 rounded" />
          <div className="space-y-2">
            <div className="h-4 bg-slate-200/70 rounded w-full" />
            <div className="h-4 bg-slate-200/70 rounded w-5/6" />
            <div className="h-4 bg-slate-200/70 rounded w-4/6" />
          </div>
        </div>
        <div className="w-px h-24 bg-slate-200" />
        <div className="w-20 space-y-2 text-center flex flex-col items-center justify-center">
          <div className="h-3 w-12 bg-slate-200 rounded" />
          <div className="h-7 w-14 bg-slate-200 rounded" />
          <div className="h-2.5 w-16 bg-slate-200 rounded" />
        </div>
      </div>
    )
  }

  const temas = temasData?.temas || []
  const temTemas = temas.length > 0
  const topTemas = temas.slice(0, 3)
  const maxPercentual = topTemas[0]?.percentual || 1
  const temasRestantes = Math.max(0, (temasData?.total_temas_identificados || temas.length) - topTemas.length)

  // Se não houver temas disponíveis, renderiza apenas o card de presença clássico
  if (!temTemas) {
    return (
      <div className="hidden md:flex flex-shrink-0 text-center" data-testid="performance-container">
        <div className="bg-slate-50 border border-slate-200/80 rounded-2xl p-4 text-center min-w-[120px] h-[152px] flex flex-col items-center justify-center">
          <p className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">Presença</p>
          <p data-testid="performance-score" className="mono-font text-2xl font-bold text-slate-800 mt-1">
            {notaAssiduidade != null ? `${notaAssiduidade.toFixed(0)}%` : "—"}
          </p>
          <p className="text-[10px] text-slate-400 mt-0.5">
            {anoSelecionado ? `em ${anoSelecionado}` : "assiduidade"}
          </p>
        </div>
      </div>
    )
  }

  return (
    <div
      data-testid="foco-tematico-hero"
      className="hidden md:flex flex-shrink-0 bg-slate-50/80 border border-slate-200/80 rounded-2xl p-3.5 h-[152px] w-[360px] lg:w-[380px] shadow-2xs items-center gap-3.5 transition-all hover:border-slate-300"
    >
      {/* ── LADO ESQUERDO: TOP 3 TEMAS ── */}
      <div className="flex-1 min-w-0 flex flex-col justify-between h-full py-0.5">
        {/* Cabeçalho do Foco Temático */}
        <div className="flex items-center justify-between gap-1 mb-1">
          <div className="flex items-center gap-1.5 min-w-0">
            <Target size={13} className="text-blue-600 shrink-0" />
            <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider truncate">
              Foco Temático
            </span>
          </div>
          {onVerTodosTemas && temasRestantes > 0 && (
            <button
              type="button"
              onClick={onVerTodosTemas}
              data-testid="btn-ver-mais-temas-hero"
              className="text-[10px] font-semibold text-blue-600 hover:text-blue-800 hover:underline cursor-pointer shrink-0 transition-colors"
              title="Ver painel analítico completo de temas"
            >
              +{temasRestantes} temas →
            </button>
          )}
        </div>

        {/* Mini barras dos top 3 temas */}
        <div className="space-y-2">
          {topTemas.map((tema, idx) => {
            // Largura proporcional normalizada em relação ao tema líder
            const larguraRelativa = Math.max(15, Math.min(100, Math.round((tema.percentual / maxPercentual) * 100)))

            return (
              <div key={tema.id_tema} className="space-y-0.5">
                <div className="flex items-center justify-between text-[11px] leading-tight">
                  <span className="font-medium text-slate-700 truncate pr-1" title={tema.nome}>
                    {tema.nome}
                  </span>
                  <span className="mono-font text-[10px] font-bold text-slate-800 shrink-0 tabular-nums">
                    {tema.percentual.toFixed(1)}%
                  </span>
                </div>
                <div className="h-1.5 w-full bg-slate-200/80 rounded-full overflow-hidden">
                  <div
                    className="h-full rounded-full transition-all duration-700 ease-out"
                    style={{
                      width: `${larguraRelativa}%`,
                      backgroundColor: CORES_BARRAS[idx] || "#2563eb",
                    }}
                  />
                </div>
              </div>
            )
          })}
        </div>
      </div>

      {/* ── DIVISOR VERTICAL ── */}
      <div className="w-px h-[120px] bg-slate-200/80 shrink-0" />

      {/* ── LADO DIREITO: MÉTRICA DE PRESENÇA ── */}
      <div
        data-testid="performance-container"
        className="w-[84px] shrink-0 text-center flex flex-col items-center justify-center"
      >
        <p className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider">Presença</p>
        <p data-testid="performance-score" className="mono-font text-2xl font-bold text-slate-800 mt-0.5">
          {notaAssiduidade != null ? `${notaAssiduidade.toFixed(0)}%` : "—"}
        </p>
        <p className="text-[9px] text-slate-400 mt-0.5 truncate max-w-full">
          {anoSelecionado ? `em ${anoSelecionado}` : "assiduidade"}
        </p>
      </div>
    </div>
  )
}
