/**
 * PainelTemasAtuacao.tsx — Visualização dos Temas de Atuação Parlamentar (SPEC-001).
 *
 * Apresenta a concentração temática do trabalho legislativo do parlamentar,
 * calculada por similaridade semântica com pgvector (modelo BAAI/bge-m3) sobre
 * proposições apresentadas e relatadas.
 *
 * Princípio da Neutralidade Factual (AGENTS.md):
 *  - Linguagem 100% descritiva e factual.
 *  - Sem juízos de valor sobre temas prioritários.
 *  - Rastreabilidade com a 57ª Legislatura e pesos documentados.
 */

import { useState } from "react"
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from "recharts"
import { Target, Layers, HelpCircle } from "lucide-react"
import { usePoliticoTemas } from "../hooks/usePoliticos"
import ToolDica from "./InfoDica"

interface PainelTemasAtuacaoProps {
  politicoId: string | number
  legislatura?: number
}

// ── Cores da paleta cívica com gradientes graduais por relevância ──
const CORES_RANK = [
  "#1d4ed8", // Rank 1: Azul cívico profundo
  "#2563eb", // Rank 2
  "#3b82f6", // Rank 3
  "#60a5fa", // Rank 4
  "#93c5fd", // Rank 5
  "#cbd5e1", // Rank 6+: Neutro slate
]

// ── Tooltip customizado do Recharts ──
function CustomTooltip({
  active,
  payload,
}: {
  active?: boolean
  payload?: Array<{ payload: { nome: string; percentual: number; peso_total: number; rank: number } }>
}) {
  if (!active || !payload?.length) return null
  const item = payload[0].payload

  return (
    <div className="bg-white/95 backdrop-blur-md border border-slate-200 rounded-xl p-3 shadow-xl text-xs space-y-1 min-w-[190px]">
      <div className="flex items-center justify-between gap-2 border-b border-slate-100 pb-1.5">
        <span className="font-bold text-slate-800">{item.nome}</span>
        <span className="text-[10px] font-semibold text-blue-600 bg-blue-50 px-1.5 py-0.5 rounded">
          #{item.rank}
        </span>
      </div>
      <div className="flex justify-between text-slate-600 pt-0.5">
        <span>Concentração:</span>
        <strong className="mono-font text-slate-900">{item.percentual.toFixed(1)}%</strong>
      </div>
      <div className="flex justify-between text-slate-400 text-[11px]">
        <span>Peso ponderado:</span>
        <span className="mono-font">{item.peso_total.toFixed(0)} pts</span>
      </div>
    </div>
  )
}

export default function PainelTemasAtuacao({
  politicoId,
  legislatura = 57,
}: PainelTemasAtuacaoProps) {
  const { data, isLoading, isError } = usePoliticoTemas(politicoId, {
    id_legislatura: legislatura,
    limit: 10,
  })

  const [temaSelecionado, setTemaSelecionado] = useState<number | null>(null)

  // Se não houver dados calculados (404) ou erro, não polui a página
  if (isError || (!isLoading && (!data || !data.temas || data.temas.length === 0))) {
    return null
  }

  // Skeleton shimmer durante carregamento
  if (isLoading) {
    return (
      <section className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm animate-pulse">
        <div className="flex items-center justify-between mb-4">
          <div className="h-6 w-48 bg-slate-200 rounded-md" />
          <div className="h-5 w-24 bg-slate-100 rounded-full" />
        </div>
        <div className="space-y-3 mt-6">
          <div className="h-8 bg-slate-100 rounded-lg w-full" />
          <div className="h-8 bg-slate-100 rounded-lg w-5/6" />
          <div className="h-8 bg-slate-100 rounded-lg w-4/6" />
        </div>
      </section>
    )
  }

  const temas = data!.temas
  const topTemas = temas.slice(0, 7) // Top 7 para visualização limpa no gráfico
  const temaEmDestaque = temaSelecionado != null
    ? temas.find((t) => t.id_tema === temaSelecionado) ?? temas[0]
    : temas[0]

  return (
    <section
      data-testid="section-temas-atuacao"
      className="bg-white rounded-2xl border border-slate-200 p-6 md:p-7 shadow-sm transition-all section-fade"
    >
      {/* ── Cabeçalho do Painel ── */}
      <div className="flex items-start justify-between gap-4 mb-3 flex-wrap">
        <div>
          <div className="flex items-center gap-2">
            <Target size={18} className="text-blue-600 flex-shrink-0" />
            <h2 className="display-font text-xl font-bold text-slate-800">
              Foco Temático da Atuação
            </h2>
            <ToolDica
              side="bottom"
              content="Distribuição factual calculada por similaridade semântica (IA / pgvector BAAI/bge-m3) sobre as ementas de proposições apresentadas e relatadas na 57ª Legislatura. Ponderação: autoria principal peso 10, coautoria peso 5."
            >
              <button
                type="button"
                aria-label="Metodologia de cálculo dos temas"
                className="text-slate-400 hover:text-slate-600 transition-colors p-0.5 rounded-full"
              >
                <HelpCircle size={15} />
              </button>
            </ToolDica>
          </div>
          <p className="text-xs text-slate-500 mt-1 max-w-2xl leading-relaxed">
            Áreas de maior concentração da atividade legislativa na {legislatura}ª Legislatura, calculadas por inteligência semântica sobre proposições e relatorias.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-blue-50 text-blue-700 border border-blue-100">
            <Layers size={13} />
            {data!.total_temas_identificados} temas identificados
          </span>
        </div>
      </div>

      {/* ── Visualização Principal: Gráfico de Barras + Destaque ── */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 mt-6 items-center">
        {/* Gráfico Horizontal Recharts */}
        <div className="lg:col-span-8 h-[270px] w-full min-w-0">
          <ResponsiveContainer width="100%" height="100%" minWidth={0}>
            <BarChart
              data={topTemas}
              layout="vertical"
              margin={{ top: 5, right: 30, left: 10, bottom: 5 }}
            >
              <XAxis
                type="number"
                domain={[0, (dataMax: number) => Math.min(100, Math.ceil(dataMax * 1.15))]}
                tickFormatter={(v: number) => `${v}%`}
                stroke="#94a3b8"
                fontSize={11}
                tickLine={false}
                axisLine={false}
              />
              <YAxis
                type="category"
                dataKey="nome"
                stroke="#475569"
                fontSize={12}
                width={120}
                tickLine={false}
                axisLine={false}
              />
              <Tooltip
                content={<CustomTooltip />}
                cursor={{ fill: "rgba(241, 245, 249, 0.6)" }}
              />
              <Bar
                dataKey="percentual"
                radius={[0, 6, 6, 0]}
                barSize={16}
                onClick={(entry: { id_tema: number }) => setTemaSelecionado(entry.id_tema)}
                className="cursor-pointer"
              >
                {topTemas.map((entry, index) => {
                  const isSelected = temaSelecionado === entry.id_tema
                  const corBase = CORES_RANK[index] ?? CORES_RANK[CORES_RANK.length - 1]
                  return (
                    <Cell
                      key={`cell-${entry.id_tema}`}
                      fill={isSelected ? "#1d4ed8" : corBase}
                      opacity={temaSelecionado != null && !isSelected ? 0.45 : 1}
                    />
                  )
                })}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Card Lateral de Destaque do Tema Selecionado */}
        {temaEmDestaque && (
          <div className="lg:col-span-4 bg-slate-50 border border-slate-100 rounded-2xl p-5 flex flex-col justify-between h-full min-h-[220px]">
            <div>
              <div className="flex items-center justify-between mb-2">
                <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400">
                  Tema em Destaque
                </span>
                <span className="text-xs font-bold text-blue-600 bg-white border border-blue-200 px-2 py-0.5 rounded-md">
                  #{temaEmDestaque.rank} no ranking
                </span>
              </div>
              <h3 className="display-font text-lg font-bold text-slate-800 leading-snug">
                {temaEmDestaque.nome}
              </h3>
              <p className="text-xs text-slate-500 mt-2 leading-relaxed">
                Corresponde a <strong className="text-slate-700 font-semibold">{temaEmDestaque.percentual.toFixed(1)}%</strong> da pontuação semântica ponderada do parlamentar nesta legislatura.
              </p>
            </div>

            <div className="pt-4 border-t border-slate-200/70 mt-4 flex items-center justify-between">
              <div>
                <p className="text-[10px] font-medium text-slate-400 uppercase">Peso Total Acumulado</p>
                <p className="mono-font text-base font-bold text-slate-700">
                  {temaEmDestaque.peso_total.toFixed(0)} <span className="text-xs text-slate-400 font-normal">pts</span>
                </p>
              </div>
              <div className="text-right">
                <p className="text-[10px] font-medium text-slate-400 uppercase">Score Relativo</p>
                <p className="mono-font text-base font-bold text-blue-600">
                  {(temaEmDestaque.score * 100).toFixed(1)}%
                </p>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* ── Chips / Pílulas no Rodapé ── */}
      <div className="mt-6 pt-5 border-t border-slate-100">
        <p className="text-[11px] font-semibold text-slate-400 uppercase tracking-wide mb-2.5">
          Todos os temas classificados (clique para inspecionar):
        </p>
        <div className="flex flex-wrap gap-2">
          {temas.map((t) => {
            const ativo = temaSelecionado === t.id_tema
            return (
              <button
                key={t.id_tema}
                type="button"
                onClick={() => setTemaSelecionado(ativo ? null : t.id_tema)}
                className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-medium border transition-all cursor-pointer ${
                  ativo
                    ? "bg-blue-600 border-blue-600 text-white shadow-sm"
                    : "bg-white border-slate-200 text-slate-600 hover:border-blue-300 hover:bg-blue-50/50"
                }`}
              >
                <span>{t.nome}</span>
                <span
                  className={`mono-font text-[11px] font-semibold px-1.5 py-0.2 rounded-md ${
                    ativo ? "bg-blue-700 text-white" : "bg-slate-100 text-slate-500"
                  }`}
                >
                  {t.percentual.toFixed(1)}%
                </span>
              </button>
            )
          })}
        </div>
      </div>
    </section>
  )
}
