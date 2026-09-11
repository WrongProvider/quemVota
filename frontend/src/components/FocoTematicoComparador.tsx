/**
 * FocoTematicoComparador.tsx — Resumo de Foco Temático e Presença no Comparador de Parlamentares.
 *
 * Apresenta de forma compacta e equilibrada os principais temas da atuação do parlamentar
 * ao lado da métrica de presença em cada coluna de perfil do comparador.
 *
 * Princípio da Neutralidade Factual (AGENTS.md):
 *  - Linguagem puramente descritiva.
 *  - Percentuais factuais calculados sobre proposições oficiais da 57ª Legislatura.
 *  - Mobile-first: adaptação ergonômica sem overflow horizontal.
 */

import { Target } from "lucide-react"
import { Link } from "react-router-dom"
import { usePoliticoTemas } from "../hooks/usePoliticos"

interface FocoTematicoComparadorProps {
  politicoId: string | number
  politicoSlug?: string | null
  notaAssiduidade?: number | null
  corTema?: "blue" | "violet"
  lado?: "A" | "B"
}

const CORES_BARRAS_AZUL = ["#1d4ed8", "#2563eb", "#3b82f6"]
const CORES_BARRAS_VIOLETA = ["#6d28d9", "#7c3aed", "#8b5cf6"]

export function FocoTematicoComparador({
  politicoId,
  politicoSlug,
  notaAssiduidade,
  corTema = "blue",
  lado = "A",
}: FocoTematicoComparadorProps) {
  const { data: temasData, isLoading } = usePoliticoTemas(politicoId, {
    id_legislatura: 57,
    limit: 10,
  })

  const coresBarras = corTema === "violet" ? CORES_BARRAS_VIOLETA : CORES_BARRAS_AZUL
  const corIcone = corTema === "violet" ? "text-violet-600" : "text-blue-600"
  const corLink =
    corTema === "violet"
      ? "text-violet-600 hover:text-violet-800"
      : "text-blue-600 hover:text-blue-800"

  // ── SKELETON DE CARREGAMENTO ──
  if (isLoading) {
    return (
      <div
        data-testid={`foco-tematico-skeleton-${lado}`}
        className="w-full max-w-[340px] lg:max-w-[360px] mx-auto animate-pulse"
      >
        {/* Desktop Skeleton */}
        <div className="hidden md:flex bg-slate-50/80 border border-slate-200/80 rounded-2xl p-3.5 h-[152px] items-center gap-3.5">
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

        {/* Mobile Skeleton */}
        <div className="flex md:hidden flex-col bg-slate-50/80 border border-slate-200/80 rounded-xl p-2.5 space-y-2">
          <div className="h-8 bg-slate-200/70 rounded w-full" />
          <div className="h-3 bg-slate-200/70 rounded w-2/3" />
          <div className="h-3 bg-slate-200/70 rounded w-5/6" />
          <div className="h-3 bg-slate-200/70 rounded w-4/6" />
        </div>
      </div>
    )
  }

  const temas = temasData?.temas || []
  const temTemas = temas.length > 0
  const topTemas = temas.slice(0, 3)
  const maxPercentual = topTemas[0]?.percentual || 1
  const temasRestantes = Math.max(
    0,
    (temasData?.total_temas_identificados || temas.length) - topTemas.length
  )

  // ── FALLBACK QUANDO NÃO HÁ TEMAS CADASTRADOS ──
  if (!temTemas) {
    return (
      <div
        data-testid={`foco-tematico-comparador-${lado}`}
        className="text-center"
      >
        <div
          data-testid="performance-container"
          className="bg-slate-50 border border-slate-200/80 rounded-xl px-3.5 py-1.5 text-center inline-block"
        >
          <p className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider">
            Presença
          </p>
          <p
            data-testid="performance-score"
            className="mono-font text-base md:text-lg font-bold text-slate-800"
          >
            {notaAssiduidade != null ? `${notaAssiduidade.toFixed(0)}%` : "—"}
          </p>
        </div>
      </div>
    )
  }

  const linkPerfil = politicoSlug ? `/politicos/${politicoSlug}#section-atuacao` : undefined

  return (
    <div
      data-testid={`foco-tematico-comparador-${lado}`}
      className="w-full max-w-[340px] lg:max-w-[360px] mx-auto text-left"
    >
      {/* ── VERSÃO DESKTOP (MD+): CARD UNIFICADO HORIZONTAL COM DIVISOR ── */}
      <div className="hidden md:flex bg-slate-50/90 border border-slate-200/90 rounded-2xl p-3.5 h-[152px] shadow-2xs items-center gap-3.5 transition-all hover:border-slate-300">
        {/* Lado Esquerdo: Top 3 Temas */}
        <div className="flex-1 min-w-0 flex flex-col justify-between h-full py-0.5">
          <div className="flex items-center justify-between gap-1 mb-1">
            <div className="flex items-center gap-1.5 min-w-0">
              <Target size={13} className={`${corIcone} shrink-0`} />
              <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider truncate">
                Foco Temático
              </span>
            </div>
            {linkPerfil && temasRestantes > 0 && (
              <Link
                to={linkPerfil}
                data-testid={`btn-ver-mais-temas-comparador-${lado}`}
                className={`text-[10px] font-semibold ${corLink} hover:underline cursor-pointer shrink-0 transition-colors`}
                title="Ver painel analítico completo de temas no perfil do parlamentar"
              >
                +{temasRestantes} temas →
              </Link>
            )}
          </div>

          {/* Mini Barras de Progresso dos Top 3 Temas */}
          <div className="space-y-2">
            {topTemas.map((tema, idx) => {
              const larguraRelativa = Math.max(
                15,
                Math.min(100, Math.round((tema.percentual / maxPercentual) * 100))
              )

              return (
                <div key={tema.id_tema} className="space-y-0.5">
                  <div className="flex items-center justify-between text-[11px] leading-tight">
                    <span
                      className="font-medium text-slate-700 truncate pr-1"
                      title={tema.nome}
                    >
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
                        backgroundColor:
                          coresBarras[idx] || (corTema === "violet" ? "#7c3aed" : "#2563eb"),
                      }}
                    />
                  </div>
                </div>
              )
            })}
          </div>
        </div>

        {/* Divisor Vertical */}
        <div className="w-px h-[120px] bg-slate-200/80 shrink-0" />

        {/* Lado Direito: Métrica de Presença */}
        <div
          data-testid="performance-container"
          className="w-[84px] shrink-0 text-center flex flex-col items-center justify-center"
        >
          <p className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider">
            Presença
          </p>
          <p
            data-testid="performance-score"
            className="mono-font text-2xl font-bold text-slate-800 mt-0.5"
          >
            {notaAssiduidade != null ? `${notaAssiduidade.toFixed(0)}%` : "—"}
          </p>
          <p className="text-[9px] text-slate-400 mt-0.5 truncate max-w-full">
            assiduidade
          </p>
        </div>
      </div>

      {/* ── VERSÃO MOBILE (< MD): CARD VERTICAL COMPACTO SEM OVERFLOW ── */}
      <div className="flex md:hidden flex-col bg-slate-50/90 border border-slate-200/90 rounded-xl p-2.5 space-y-2 shadow-2xs">
        {/* Presença em Destaque */}
        <div
          data-testid="performance-container-mobile"
          className="text-center pb-1.5 border-b border-slate-200/70"
        >
          <p className="text-[9px] font-semibold text-slate-400 uppercase tracking-wider">
            Presença
          </p>
          <p
            data-testid="performance-score-mobile"
            className="mono-font text-lg font-bold text-slate-800 leading-tight"
          >
            {notaAssiduidade != null ? `${notaAssiduidade.toFixed(0)}%` : "—"}
          </p>
          <p className="text-[8px] text-slate-400">assiduidade</p>
        </div>

        {/* Top Temas Compactos */}
        <div className="space-y-1.5">
          <div className="flex items-center justify-between gap-1">
            <div className="flex items-center gap-1 min-w-0">
              <Target size={11} className={`${corIcone} shrink-0`} />
              <span className="text-[9px] font-bold text-slate-500 uppercase tracking-wider truncate">
                Foco Temático
              </span>
            </div>
            {linkPerfil && temasRestantes > 0 && (
              <Link
                to={linkPerfil}
                className={`text-[9px] font-semibold ${corLink} hover:underline shrink-0`}
              >
                +{temasRestantes} →
              </Link>
            )}
          </div>

          <div className="space-y-1.5">
            {topTemas.map((tema, idx) => {
              const larguraRelativa = Math.max(
                15,
                Math.min(100, Math.round((tema.percentual / maxPercentual) * 100))
              )

              return (
                <div key={tema.id_tema} className="space-y-0.5">
                  <div className="flex items-center justify-between text-[10px] leading-tight">
                    <span
                      className="font-medium text-slate-700 truncate pr-1"
                      title={tema.nome}
                    >
                      {tema.nome}
                    </span>
                    <span className="mono-font text-[9px] font-bold text-slate-800 shrink-0 tabular-nums">
                      {tema.percentual.toFixed(1)}%
                    </span>
                  </div>
                  <div className="h-1 w-full bg-slate-200/80 rounded-full overflow-hidden">
                    <div
                      className="h-full rounded-full transition-all duration-700 ease-out"
                      style={{
                        width: `${larguraRelativa}%`,
                        backgroundColor:
                          coresBarras[idx] || (corTema === "violet" ? "#7c3aed" : "#2563eb"),
                      }}
                    />
                  </div>
                </div>
              )
            })}
          </div>
        </div>
      </div>
    </div>
  )
}
