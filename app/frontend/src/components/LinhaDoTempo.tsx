/**
 * LinhaDoTempo.tsx — Linha do tempo interativa do parlamentar.
 *
 * Estado "Todos os anos" → visão geral de todos os gastos (por ano agregado).
 * Clica num ano         → detalha mensalmente aquele ano (categorias + fornecedores).
 *
 * Props:
 *   politicoId   — ID numérico do parlamentar
 *
 * Dependências (instale se ainda não tiver):
 *   npm install recharts
 */

import { useState, useMemo } from "react"
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
  Cell,
} from "recharts"
import { ChevronLeft, Receipt, TrendingDown, Users, CalendarDays, Loader2 } from "lucide-react"
import { useDespesasResumoCompleto, useVotacoes } from "../hooks/useLinhaDoTempo"
import type { DespesaResumoMensal } from "../api/linhaTempo.api"

// ─────────────────────────────────────────────────────────────────────────────
// Helpers
// ─────────────────────────────────────────────────────────────────────────────

const BRL = (v: number) =>
  v.toLocaleString("pt-BR", { style: "currency", currency: "BRL", maximumFractionDigits: 0 })

const MESES = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"]

function agruparPorAno(
  historico: DespesaResumoMensal[],
): { ano: number; total_gasto: number; qtd_despesas: number }[] {
  const mapa: Record<number, { total_gasto: number; qtd_despesas: number }> = {}
  for (const item of historico) {
    if (!mapa[item.ano]) mapa[item.ano] = { total_gasto: 0, qtd_despesas: 0 }
    mapa[item.ano].total_gasto += item.total_gasto
    mapa[item.ano].qtd_despesas += item.qtd_despesas
  }
  return Object.entries(mapa)
    .map(([ano, v]) => ({ ano: Number(ano), ...v }))
    .sort((a, b) => b.ano - a.ano)
}

// ─────────────────────────────────────────────────────────────────────────────
// Tooltip customizado
// ─────────────────────────────────────────────────────────────────────────────

function CustomTooltip({ active, payload, label }: any) {
  if (!active || !payload?.length) return null
  return (
    <div className="bg-white border border-slate-200 rounded-xl shadow-lg px-4 py-3 text-sm">
      <p className="font-semibold text-slate-700 mb-1">{label}</p>
      <p className="text-blue-600 font-mono">{BRL(payload[0]?.value ?? 0)}</p>
      {payload[0]?.payload?.qtd_despesas !== undefined && (
        <p className="text-slate-400 text-xs mt-0.5">
          {payload[0].payload.qtd_despesas} despesas
        </p>
      )}
    </div>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// Barra de "anos" — linha do tempo navegável
// ─────────────────────────────────────────────────────────────────────────────

interface AnoPilula {
  ano: number | null   // null = "todos"
  label: string
  total_gasto: number
}

interface LinhaTempoNavProps {
  anos: AnoPilula[]
  anoSelecionado: number | null
  onSelect: (ano: number | null) => void
}

function LinhaTempoNav({ anos, anoSelecionado, onSelect }: LinhaTempoNavProps) {
  return (
    <div className="relative flex items-center gap-0 overflow-x-auto pb-2 select-none">
      {/* Linha horizontal conectora */}
      <div className="absolute left-0 right-0 top-[22px] h-px bg-slate-200 z-0 pointer-events-none" />

      {anos.map((item, idx) => {
        const isActive = item.ano === anoSelecionado
        return (
          <div key={item.ano ?? "todos"} className="relative flex flex-col items-center z-10 flex-shrink-0">
            {/* Marcador */}
            <button
              onClick={() => onSelect(item.ano)}
              className={`
                w-10 h-10 rounded-full border-2 flex items-center justify-center
                transition-all duration-200 cursor-pointer font-semibold text-[11px]
                ${isActive
                  ? "bg-blue-600 border-blue-600 text-white shadow-lg scale-110"
                  : "bg-white border-slate-300 text-slate-500 hover:border-blue-400 hover:text-blue-600"
                }
              `}
            >
              {item.label === "Todos" ? "★" : item.label.slice(2)}
            </button>

            {/* Label abaixo */}
            <span
              className={`mt-1.5 text-[10px] font-medium whitespace-nowrap transition-colors
                ${isActive ? "text-blue-600" : "text-slate-400"}
              `}
            >
              {item.label}
            </span>

            {/* Conector entre nós */}
            {idx < anos.length - 1 && (
              <div className="absolute top-[19px] left-[40px] w-8 h-px bg-slate-200" />
            )}
          </div>
        )
      })}
    </div>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// Painel: visão geral de todos os anos
// ─────────────────────────────────────────────────────────────────────────────

function PainelTodos({
  anosData,
  totalGeral,
  totalDespesas,
  onSelectAno,
}: {
  anosData: { ano: number; total_gasto: number; qtd_despesas: number }[]
  totalGeral: number
  totalDespesas: number
  onSelectAno: (ano: number) => void
}) {
  const chartData = [...anosData].sort((a, b) => a.ano - b.ano).map((d) => ({
    ...d,
    label: String(d.ano),
  }))

  return (
    <div className="space-y-6">
      {/* Cards de totais */}
      <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
        <div className="bg-blue-50 border border-blue-100 rounded-xl p-4">
          <p className="text-[11px] text-blue-500 font-medium uppercase tracking-wide mb-1 flex items-center gap-1">
            <Receipt size={12} /> Total Gasto
          </p>
          <p className="font-mono text-lg font-bold text-blue-700">{BRL(totalGeral)}</p>
        </div>
        <div className="bg-slate-50 border border-slate-200 rounded-xl p-4">
          <p className="text-[11px] text-slate-500 font-medium uppercase tracking-wide mb-1 flex items-center gap-1">
            <CalendarDays size={12} /> Nº de Despesas
          </p>
          <p className="font-mono text-lg font-bold text-slate-700">{totalDespesas.toLocaleString("pt-BR")}</p>
        </div>
        <div className="bg-slate-50 border border-slate-200 rounded-xl p-4 col-span-2 md:col-span-1">
          <p className="text-[11px] text-slate-500 font-medium uppercase tracking-wide mb-1 flex items-center gap-1">
            <TrendingDown size={12} /> Anos Registrados
          </p>
          <p className="font-mono text-lg font-bold text-slate-700">{anosData.length}</p>
        </div>
      </div>

      {/* Gráfico de barras por ano */}
      <div>
        <p className="text-xs text-slate-400 font-medium mb-3 uppercase tracking-wide">
          Gastos por ano · clique para detalhar
        </p>
        <ResponsiveContainer width="100%" height={200}>
          <BarChart
            data={chartData}
            margin={{ top: 4, right: 4, left: 0, bottom: 0 }}
            barCategoryGap="30%"
          >
            <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" vertical={false} />
            <XAxis dataKey="label" tick={{ fontSize: 11, fill: "#94a3b8" }} axisLine={false} tickLine={false} />
            <YAxis
              tickFormatter={(v) => `R$${(v / 1000).toFixed(0)}k`}
              tick={{ fontSize: 10, fill: "#cbd5e1" }}
              axisLine={false}
              tickLine={false}
              width={52}
            />
            <Tooltip content={<CustomTooltip />} cursor={{ fill: "#f1f5f9", radius: 6 }} />
            <Bar dataKey="total_gasto" radius={[6, 6, 0, 0]} onClick={(d) => onSelectAno(d.ano)}>
              {chartData.map((entry) => (
                <Cell
                  key={entry.ano}
                  fill="#2563eb"
                  className="cursor-pointer hover:opacity-75 transition-opacity"
                />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Tabela resumida por ano */}
      <div className="rounded-xl border border-slate-200 overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="bg-slate-50 border-b border-slate-200">
              <th className="text-left text-[11px] text-slate-400 font-medium uppercase tracking-wide px-4 py-2.5">Ano</th>
              <th className="text-right text-[11px] text-slate-400 font-medium uppercase tracking-wide px-4 py-2.5">Total Gasto</th>
              <th className="text-right text-[11px] text-slate-400 font-medium uppercase tracking-wide px-4 py-2.5 hidden sm:table-cell">Despesas</th>
              <th className="px-4 py-2.5 w-10" />
            </tr>
          </thead>
          <tbody>
            {[...anosData].sort((a, b) => b.ano - a.ano).map((row) => (
              <tr
                key={row.ano}
                className="border-b border-slate-100 last:border-0 hover:bg-blue-50 transition-colors cursor-pointer group"
                onClick={() => onSelectAno(row.ano)}
              >
                <td className="px-4 py-3 font-semibold text-slate-700 font-mono">{row.ano}</td>
                <td className="px-4 py-3 text-right font-mono text-slate-600">{BRL(row.total_gasto)}</td>
                <td className="px-4 py-3 text-right text-slate-400 hidden sm:table-cell">{row.qtd_despesas}</td>
                <td className="px-4 py-3 text-right">
                  <ChevronLeft size={14} className="text-slate-300 group-hover:text-blue-500 rotate-180 transition-colors ml-auto" />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// Painel: detalhe de um ano específico
// ─────────────────────────────────────────────────────────────────────────────

function PainelAno({
  ano,
  historico,
  fornecedores,
  categorias,
}: {
  ano: number
  historico: DespesaResumoMensal[]
  fornecedores: { nome_fornecedor: string; total_recebido: number; qtd_notas: number }[]
  categorias: { tipo_despesa: string; total: number; qtd: number }[]
}) {
  const mesesDoAno = useMemo(
    () =>
      historico
        .filter((h) => h.ano === ano)
        .sort((a, b) => a.mes - b.mes)
        .map((h) => ({ ...h, label: MESES[h.mes - 1] })),
    [historico, ano],
  )

  const totalAno = mesesDoAno.reduce((s, m) => s + m.total_gasto, 0)
  const maxMes = mesesDoAno.length > 0 ? Math.max(...mesesDoAno.map((m) => m.total_gasto)) : 0

  return (
    <div className="space-y-6">
      {/* Header do ano */}
      <div className="flex items-center justify-between">
        <div>
          <p className="text-xs text-slate-400 uppercase tracking-wide mb-0.5">Total em {ano}</p>
          <p className="font-mono text-2xl font-bold text-blue-700">{BRL(totalAno)}</p>
        </div>
        <div className="text-right">
          <p className="text-xs text-slate-400">{mesesDoAno.length} meses</p>
          <p className="text-sm text-slate-500 font-medium">
            {BRL(totalAno / (mesesDoAno.length || 1))}/mês
          </p>
        </div>
      </div>

      {/* Gráfico mensal */}
      {mesesDoAno.length > 0 ? (
        <div>
          <p className="text-xs text-slate-400 font-medium mb-3 uppercase tracking-wide">Mês a mês</p>
          <ResponsiveContainer width="100%" height={180}>
            <BarChart data={mesesDoAno} margin={{ top: 4, right: 4, left: 0, bottom: 0 }} barCategoryGap="25%">
              <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" vertical={false} />
              <XAxis dataKey="label" tick={{ fontSize: 11, fill: "#94a3b8" }} axisLine={false} tickLine={false} />
              <YAxis
                tickFormatter={(v) => `R$${(v / 1000).toFixed(0)}k`}
                tick={{ fontSize: 10, fill: "#cbd5e1" }}
                axisLine={false}
                tickLine={false}
                width={52}
              />
              <Tooltip content={<CustomTooltip />} cursor={{ fill: "#f1f5f9", radius: 6 }} />
              <Bar dataKey="total_gasto" radius={[5, 5, 0, 0]}>
                {mesesDoAno.map((entry) => (
                  <Cell
                    key={entry.mes}
                    fill={entry.total_gasto === maxMes ? "#2563eb" : "#93c5fd"}
                  />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      ) : (
        <p className="text-sm text-slate-400 text-center py-6">Sem dados mensais para {ano}.</p>
      )}

      {/* Categorias + Fornecedores em grid */}
      <div className="grid md:grid-cols-2 gap-4">
        {/* Categorias */}
        {categorias.length > 0 && (
          <div className="rounded-xl border border-slate-200 overflow-hidden">
            <div className="bg-slate-50 px-4 py-2.5 border-b border-slate-200">
              <p className="text-[11px] text-slate-400 font-medium uppercase tracking-wide">Por Categoria</p>
            </div>
            <div className="divide-y divide-slate-100">
              {categorias.slice(0, 6).map((cat) => {
                const pct = totalAno > 0 ? (cat.total / totalAno) * 100 : 0
                return (
                  <div key={cat.tipo_despesa} className="px-4 py-2.5">
                    <div className="flex justify-between items-center mb-1">
                      <span className="text-xs text-slate-600 truncate pr-2 max-w-[65%]">{cat.tipo_despesa}</span>
                      <span className="font-mono text-xs text-slate-500 flex-shrink-0">{BRL(cat.total)}</span>
                    </div>
                    <div className="h-1.5 bg-slate-100 rounded-full overflow-hidden">
                      <div
                        className="h-full bg-blue-400 rounded-full transition-all duration-500"
                        style={{ width: `${pct}%` }}
                      />
                    </div>
                  </div>
                )
              })}
            </div>
          </div>
        )}

        {/* Top fornecedores */}
        {fornecedores.length > 0 && (
          <div className="rounded-xl border border-slate-200 overflow-hidden">
            <div className="bg-slate-50 px-4 py-2.5 border-b border-slate-200">
              <p className="text-[11px] text-slate-400 font-medium uppercase tracking-wide flex items-center gap-1">
                <Users size={11} /> Top Fornecedores
              </p>
            </div>
            <div className="divide-y divide-slate-100">
              {fornecedores.slice(0, 6).map((f, i) => (
                <div key={f.nome_fornecedor} className="px-4 py-2.5 flex items-center gap-3">
                  <span className="font-mono text-[10px] text-slate-300 w-4 flex-shrink-0">{i + 1}</span>
                  <span className="text-xs text-slate-600 flex-1 truncate">{f.nome_fornecedor}</span>
                  <span className="font-mono text-xs text-slate-500 flex-shrink-0">{BRL(f.total_recebido)}</span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// Componente principal
// ─────────────────────────────────────────────────────────────────────────────

interface LinhaDoTempoProps {
  politicoId: number
}

export default function LinhaDoTempo({ politicoId }: LinhaDoTempoProps) {
  const [anoSelecionado, setAnoSelecionado] = useState<number | null>(null)

  // Busca "todos os dados" quando não há ano selecionado, ou o ano específico
  const { data: resumoGeral, isLoading: loadingGeral } = useDespesasResumoCompleto(politicoId)
  const { data: resumoAno, isLoading: loadingAno } = useDespesasResumoCompleto(
    politicoId,
    anoSelecionado ?? undefined,
  )

  const resumo = anoSelecionado ? resumoAno : resumoGeral
  const isLoading = anoSelecionado ? loadingAno : loadingGeral

  // Agrega por ano para a navegação e o painel "todos"
  const anosAgrupados = useMemo(
    () => (resumoGeral ? agruparPorAno(resumoGeral.historico_mensal) : []),
    [resumoGeral],
  )

  // Monta a lista de nós da linha do tempo
  const nosTimeline: AnoPilula[] = useMemo(() => {
    const todosOsAnos = anosAgrupados.map((a) => ({
      ano: a.ano,
      label: String(a.ano),
      total_gasto: a.total_gasto,
    }))
    return [
      { ano: null, label: "Todos", total_gasto: 0 },
      ...todosOsAnos.sort((a, b) => (a.ano ?? 0) - (b.ano ?? 0)),
    ]
  }, [anosAgrupados])

  const totalGeral = anosAgrupados.reduce((s, a) => s + a.total_gasto, 0)
  const totalDespesas = anosAgrupados.reduce((s, a) => s + a.qtd_despesas, 0)

  return (
    <div
      style={{ fontFamily: "'DM Sans', sans-serif" }}
      className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden"
    >
      {/* ── Header ── */}
      <div className="px-6 py-5 border-b border-slate-100 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <CalendarDays size={18} className="text-blue-500" />
          <h3
            style={{ fontFamily: "'Fraunces', serif" }}
            className="text-lg font-bold text-slate-800"
          >
            Linha do Tempo
          </h3>
          {anoSelecionado && (
            <span className="bg-blue-50 border border-blue-100 text-blue-700 text-xs font-semibold px-2 py-0.5 rounded-full">
              {anoSelecionado}
            </span>
          )}
        </div>

        {anoSelecionado && (
          <button
            onClick={() => setAnoSelecionado(null)}
            className="inline-flex items-center gap-1 text-xs text-slate-400 hover:text-blue-600 transition-colors font-medium"
          >
            <ChevronLeft size={13} />
            Todos os anos
          </button>
        )}
      </div>

      {/* ── Navegação da linha do tempo ── */}
      {nosTimeline.length > 1 && (
        <div className="px-6 pt-5 pb-2">
          <LinhaTempoNav
            anos={nosTimeline}
            anoSelecionado={anoSelecionado}
            onSelect={setAnoSelecionado}
          />
        </div>
      )}

      {/* ── Conteúdo ── */}
      <div className="px-6 py-6">
        {isLoading ? (
          <div className="flex items-center justify-center py-16 gap-3 text-slate-400">
            <Loader2 size={20} className="animate-spin" />
            <span className="text-sm">Carregando dados...</span>
          </div>
        ) : !resumo ? (
          <p className="text-sm text-slate-400 text-center py-10">
            Nenhum dado encontrado.
          </p>
        ) : anoSelecionado ? (
          <PainelAno
            ano={anoSelecionado}
            historico={resumo.historico_mensal}
            fornecedores={resumo.top_fornecedores}
            categorias={resumo.por_categoria}
          />
        ) : (
          <PainelTodos
            anosData={anosAgrupados}
            totalGeral={totalGeral}
            totalDespesas={totalDespesas}
            onSelectAno={setAnoSelecionado}
          />
        )}
      </div>
    </div>
  )
}
