/**
 * LinhaDoTempo.tsx — Histórico de gastos parlamentar.
 *
 * Visão "Todos os anos" → gráfico + tabela por ano + dropdowns de empresas/categorias globais.
 * Clica num ano        → gráfico mensal + dropdowns de empresas/categorias daquele ano.
 *
 * Props:
 *   politicoId — ID numérico do parlamentar
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
  ReferenceLine,
} from "recharts"
import {
  ChevronLeft,
  ChevronDown,
  ChevronUp,
  Receipt,
  TrendingDown,
  CalendarDays,
  Loader2,
  Building2,
  Tag,
  Users,
} from "lucide-react"
import { useDespesasResumoCompleto, useVotacoes } from "../hooks/useLinhaDoTempo"
import type { DespesaResumoMensal } from "../api/linhaTempo.api"

// ─────────────────────────────────────────────────────────────────────────────
// Helpers
// ─────────────────────────────────────────────────────────────────────────────

const BRL = (v: number) =>
  v.toLocaleString("pt-BR", { style: "currency", currency: "BRL", maximumFractionDigits: 0 })

const PCT = (v: number, total: number) =>
  total > 0 ? ((v / total) * 100).toFixed(1) + "%" : "0%"

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
    <div className="bg-white/95 backdrop-blur-md border border-slate-200 rounded-lg shadow-md px-3.5 py-2.5 text-xs">
      <p className="font-semibold text-slate-800 mb-0.5">{label}</p>
      <p className="text-blue-700 font-mono font-bold tabular-nums text-sm">{BRL(payload[0]?.value ?? 0)}</p>
      {payload[0]?.payload?.qtd_despesas !== undefined && (
        <p className="text-slate-500 font-mono text-[11px] mt-0.5">
          {payload[0].payload.qtd_despesas} despesas registradas
        </p>
      )}
    </div>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// Barra de progresso reutilizável
// ─────────────────────────────────────────────────────────────────────────────

function ProgressBar({ pct, color = "#3b82f6" }: { pct: number; color?: string }) {
  return (
    <div className="h-1.5 bg-slate-100 rounded-full overflow-hidden mt-1">
      <div
        className="h-full rounded-full transition-all duration-500"
        style={{ width: `${Math.min(pct, 100)}%`, background: color }}
      />
    </div>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// Dropdown reutilizável
// ─────────────────────────────────────────────────────────────────────────────

interface DropdownSectionProps {
  title: string
  subtitle?: string
  icon: React.ReactNode
  defaultOpen?: boolean
  children: React.ReactNode
  badge?: string | number
  testId?: string
}

function DropdownSection({
  title,
  subtitle,
  icon,
  defaultOpen = false,
  children,
  badge,
  testId,
}: DropdownSectionProps) {
  const [open, setOpen] = useState(defaultOpen)
  const baseId = testId ?? title.toLowerCase().replace(/\s+/g, "-")

  return (
    <div
      className="rounded-xl border border-slate-200 overflow-hidden"
      data-testid={`dropdown-section-${baseId}`}
      data-state={open ? "open" : "closed"}
    >
      <button
        onClick={() => setOpen((v) => !v)}
        className="w-full flex items-center justify-between px-4 py-3.5 bg-slate-50 hover:bg-slate-100 transition-colors text-left"
        data-testid={`dropdown-toggle-${baseId}`}
        aria-expanded={open}
      >
        <div className="flex items-center gap-2.5">
          <span className="text-slate-500">{icon}</span>
          <div>
            <span className="text-sm font-semibold text-slate-700">{title}</span>
            {subtitle && (
              <span className="text-xs text-slate-400 ml-2">{subtitle}</span>
            )}
          </div>
          {badge !== undefined && (
            <span
              className="bg-slate-200 text-slate-600 text-[10px] font-semibold px-1.5 py-0.5 rounded-full"
              data-testid={`dropdown-badge-${baseId}`}
            >
              {badge}
            </span>
          )}
        </div>
        {open ? (
          <ChevronUp size={15} className="text-slate-400 flex-shrink-0" />
        ) : (
          <ChevronDown size={15} className="text-slate-400 flex-shrink-0" />
        )}
      </button>

      {open && (
        <div
          className="divide-y divide-slate-100 animate-in fade-in slide-in-from-top-1 duration-150"
          data-testid={`dropdown-content-${baseId}`}
        >
          {children}
        </div>
      )}
    </div>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// Lista de fornecedores
// ─────────────────────────────────────────────────────────────────────────────

interface FornecedorItem {
  nome: string
  total: number
  categoria_principal?: string | null
}

function ListaFornecedores({
  fornecedores,
  total,
}: {
  fornecedores: FornecedorItem[]
  total: number
}) {
  if (!fornecedores.length) {
    return (
      <p className="text-xs text-slate-400 text-center py-5" data-testid="fornecedores-empty">
        Sem dados de fornecedores.
      </p>
    )
  }

  return (
    <>
      {fornecedores.map((f, i) => {
        const pct = total > 0 ? (f.total / total) * 100 : 0
        const slug = (f.nome ?? String(i)).toLowerCase().replace(/\s+/g, "-").replace(/[^a-z0-9-]/g, "")
        return (
          <div
            key={f.nome ?? i}
            className="px-4 py-3"
            data-testid={`fornecedor-item-${i}`}
            data-nome={f.nome}
          >
            <div className="flex items-start gap-3">
              <span className="font-mono text-[10px] text-slate-300 w-5 flex-shrink-0 text-right mt-0.5">
                {i + 1}
              </span>
              <div className="flex-1 min-w-0">
                {/* Nome + valor */}
                <div className="flex justify-between items-baseline gap-2">
                  <span className="text-xs text-slate-700 font-medium truncate" data-testid={`fornecedor-nome-${i}`}>{f.nome}</span>
                  <span className="font-mono text-xs text-slate-500 flex-shrink-0" data-testid={`fornecedor-valor-${i}`}>
                    {BRL(f.total)}
                  </span>
                </div>

                {/* Categoria principal */}
                {f.categoria_principal && (
                  <span className="inline-block mt-0.5 text-[10px] text-slate-400 bg-slate-100 px-1.5 py-0.5 rounded-md leading-tight truncate max-w-full">
                    {f.categoria_principal}
                  </span>
                )}

                {/* Barra de progresso + percentual */}
                <div className="flex items-center gap-2 mt-1.5">
                  <div className="flex-1 h-1.5 bg-slate-100 rounded-full overflow-hidden">
                    <div
                      className="h-full rounded-full bg-blue-400 transition-all duration-500"
                      style={{ width: `${pct}%` }}
                    />
                  </div>
                  <span className="text-[10px] text-slate-400 w-9 text-right flex-shrink-0">
                    {pct.toFixed(1)}%
                  </span>
                </div>
              </div>
            </div>
          </div>
        )
      })}
    </>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// Lista de categorias
// ─────────────────────────────────────────────────────────────────────────────

interface CategoriaItem {
  nome: string
  total: number
}

const CATEGORIA_COLORS = [
  "#3b82f6", "#8b5cf6", "#10b981", "#f59e0b",
  "#ef4444", "#06b6d4", "#ec4899", "#84cc16",
  "#f97316", "#6366f1",
]

function ListaCategorias({
  categorias,
  total,
}: {
  categorias: CategoriaItem[]
  total: number
}) {
  if (!categorias.length) {
    return (
      <p className="text-xs text-slate-400 text-center py-5" data-testid="categorias-empty">
        Sem dados de categorias.
      </p>
    )
  }

  return (
    <>
      {categorias.map((cat, i) => {
        const pct = total > 0 ? (cat.total / total) * 100 : 0
        const color = CATEGORIA_COLORS[i % CATEGORIA_COLORS.length]
        return (
          <div
            key={cat.nome ?? i}
            className="px-4 py-3"
            data-testid={`categoria-item-${i}`}
            data-nome={cat.nome}
          >
            <div className="flex items-center gap-3">
              <span
                className="w-2.5 h-2.5 rounded-sm flex-shrink-0"
                style={{ background: color }}
              />
              <div className="flex-1 min-w-0">
                <div className="flex justify-between items-baseline gap-2">
                  <span className="text-xs text-slate-700 font-medium truncate" data-testid={`categoria-nome-${i}`}>{cat.nome}</span>
                  <span className="font-mono text-xs text-slate-500 flex-shrink-0" data-testid={`categoria-valor-${i}`}>{BRL(cat.total)}</span>
                </div>
                <div className="flex items-center gap-2 mt-1">
                  <div className="flex-1 h-1.5 bg-slate-100 rounded-full overflow-hidden">
                    <div
                      className="h-full rounded-full transition-all duration-500"
                      style={{ width: `${pct}%`, background: color }}
                    />
                  </div>
                  <span className="text-[10px] text-slate-400 w-9 text-right flex-shrink-0">
                    {pct.toFixed(1)}%
                  </span>
                </div>
              </div>
            </div>
          </div>
        )
      })}
    </>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// Navegação da linha do tempo (pílulas de ano)
// ─────────────────────────────────────────────────────────────────────────────

interface AnoPilula {
  ano: number | null
  label: string
  total_gasto: number
}

function LinhaTempoNav({
  anos,
  anoSelecionado,
  onSelect,
}: {
  anos: AnoPilula[]
  anoSelecionado: number | null
  onSelect: (ano: number | null) => void
}) {
  return (
    <div
      className="relative flex items-center gap-0 overflow-x-auto pb-2 select-none"
      data-testid="linha-tempo-nav"
    >
      <div className="absolute left-0 right-0 top-[22px] h-px bg-slate-200 z-0 pointer-events-none" />
      {anos.map((item, idx) => {
        const isActive = item.ano === anoSelecionado
        return (
          <div
            key={item.ano ?? "todos"}
            className="relative flex flex-col items-center z-10 flex-shrink-0"
          >
            <button
              onClick={() => onSelect(item.ano)}
              data-testid={`ano-pilula-${item.ano ?? "todos"}`}
              data-active={isActive}
              aria-pressed={isActive}
              className={`
                px-2.5 h-8 rounded-lg border flex items-center justify-center
                transition-all duration-150 cursor-pointer font-bold text-xs
                ${isActive
                  ? "bg-slate-900 border-slate-900 text-white shadow-xs"
                  : "bg-white border-slate-300 text-slate-600 hover:border-slate-400 hover:text-slate-900"
                }
              `}
            >
              {item.label}
            </button>
            <span
              className={`mt-1 text-[10px] font-medium whitespace-nowrap transition-colors
                ${isActive ? "text-slate-900 font-semibold" : "text-slate-400"}
              `}
            >
              {item.ano ? `${BRL(item.total_gasto).slice(0, 7)}...` : "geral"}
            </span>
            {idx < anos.length - 1 && (
              <div className="absolute top-[16px] left-[52px] w-4 h-px bg-slate-200" />
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
  fornecedores,
  categorias,
}: {
  anosData: { ano: number; total_gasto: number; qtd_despesas: number }[]
  totalGeral: number
  totalDespesas: number
  onSelectAno: (ano: number) => void
  fornecedores: FornecedorItem[]
  categorias: CategoriaItem[]
}) {
  const chartData = [...anosData]
    .sort((a, b) => a.ano - b.ano)
    .map((d) => ({ ...d, label: String(d.ano) }))

  const mediaAnual =
    chartData.length > 0
      ? chartData.reduce((acc, d) => acc + d.total_gasto, 0) / chartData.length
      : 0

  return (
    <div className="space-y-5">
      {/* Cards de totais cívicos */}
      <div className="grid grid-cols-2 md:grid-cols-3 gap-3" data-testid="resumo-cards">
        <div className="bg-slate-50 border border-slate-200/90 rounded-xl p-4" data-testid="card-total-gasto">
          <p className="text-[11px] text-slate-600 font-semibold uppercase tracking-wider mb-1 flex items-center gap-1.5">
            <Receipt size={13} className="text-blue-700" /> Total Desembolsado
          </p>
          <p className="font-mono text-xl font-bold text-slate-900 tabular-nums" data-testid="card-total-gasto-valor">
            {BRL(totalGeral)}
          </p>
        </div>
        <div className="bg-slate-50 border border-slate-200/90 rounded-xl p-4" data-testid="card-num-despesas">
          <p className="text-[11px] text-slate-600 font-semibold uppercase tracking-wider mb-1 flex items-center gap-1.5">
            <CalendarDays size={13} className="text-indigo-700" /> Notas e Recibos
          </p>
          <p className="font-mono text-xl font-bold text-slate-900 tabular-nums" data-testid="card-num-despesas-valor">
            {totalDespesas.toLocaleString("pt-BR")}
          </p>
        </div>
        <div className="bg-slate-50 border border-slate-200/90 rounded-xl p-4 col-span-2 md:col-span-1" data-testid="card-anos-registrados">
          <p className="text-[11px] text-slate-600 font-semibold uppercase tracking-wider mb-1 flex items-center gap-1.5">
            <TrendingDown size={13} className="text-emerald-700" /> Anos Mapeados
          </p>
          <p className="font-mono text-xl font-bold text-slate-900 tabular-nums" data-testid="card-anos-registrados-valor">
            {anosData.length} anos
          </p>
        </div>
      </div>

      {/* Gráfico por ano com linha de média */}
      <div data-testid="grafico-anos">
        <div className="flex items-center justify-between mb-3">
          <p className="text-xs text-slate-500 font-semibold uppercase tracking-wider">
            Gastos por ano · clique na coluna para detalhar os meses
          </p>
          {mediaAnual > 0 && (
            <span className="text-[11px] font-mono text-slate-500 tabular-nums">
              Média: {BRL(mediaAnual)}/ano
            </span>
          )}
        </div>
        <ResponsiveContainer width="100%" height={210}>
          <BarChart
            data={chartData}
            margin={{ top: 8, right: 8, left: 0, bottom: 0 }}
            barCategoryGap="30%"
          >
            <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" vertical={false} />
            <XAxis
              dataKey="label"
              tick={{ fontSize: 11, fill: "#64748b" }}
              axisLine={{ stroke: "#e2e8f0" }}
              tickLine={false}
            />
            <YAxis
              tickFormatter={(v) => `R$${(v / 1000).toFixed(0)}k`}
              tick={{ fontSize: 10, fill: "#94a3b8" }}
              axisLine={false}
              tickLine={false}
              width={56}
            />
            <Tooltip content={<CustomTooltip />} cursor={{ fill: "#f8fafc", radius: 4 }} />
            {mediaAnual > 0 && (
              <ReferenceLine
                y={mediaAnual}
                stroke="#94a3b8"
                strokeDasharray="4 4"
              />
            )}
            <Bar
              dataKey="total_gasto"
              radius={[4, 4, 0, 0]}
              onClick={(d) => onSelectAno(d.ano)}
            >
              {chartData.map((entry) => (
                <Cell
                  key={entry.ano}
                  fill="#1d4ed8"
                  className="cursor-pointer hover:opacity-80 transition-opacity"
                />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Tabela resumida por ano */}
      <div className="rounded-xl border border-slate-200 overflow-hidden" data-testid="tabela-anos">
        <table className="w-full text-sm">
          <thead>
            <tr className="bg-slate-50 border-b border-slate-200">
              <th className="text-left text-[11px] text-slate-400 font-medium uppercase tracking-wide px-4 py-2.5">
                Ano
              </th>
              <th className="text-right text-[11px] text-slate-400 font-medium uppercase tracking-wide px-4 py-2.5">
                Total Gasto
              </th>
              <th className="text-right text-[11px] text-slate-400 font-medium uppercase tracking-wide px-4 py-2.5 hidden sm:table-cell">
                Despesas
              </th>
              <th className="px-4 py-2.5 w-10" />
            </tr>
          </thead>
          <tbody>
            {[...anosData].sort((a, b) => b.ano - a.ano).map((row) => (
              <tr
                key={row.ano}
                className="border-b border-slate-100 last:border-0 hover:bg-blue-50 transition-colors cursor-pointer group"
                onClick={() => onSelectAno(row.ano)}
                data-testid={`tabela-ano-row-${row.ano}`}
                data-ano={row.ano}
              >
                <td className="px-4 py-3 font-semibold text-slate-700 font-mono" data-testid={`tabela-ano-label-${row.ano}`}>{row.ano}</td>
                <td className="px-4 py-3 text-right font-mono text-slate-600" data-testid={`tabela-ano-total-${row.ano}`}>
                  {BRL(row.total_gasto)}
                </td>
                <td className="px-4 py-3 text-right text-slate-400 hidden sm:table-cell" data-testid={`tabela-ano-despesas-${row.ano}`}>
                  {row.qtd_despesas}
                </td>
                <td className="px-4 py-3 text-right">
                  <ChevronLeft
                    size={14}
                    className="text-slate-300 group-hover:text-blue-500 rotate-180 transition-colors ml-auto"
                  />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* ── Dropdowns globais ── */}
      <div className="space-y-3 pt-1">
        <DropdownSection
          title="Maiores Empresas"
          subtitle="todo o período"
          icon={<Building2 size={15} />}
          badge={fornecedores.length}
          defaultOpen={false}
          testId="fornecedores-geral"
        >
          <ListaFornecedores fornecedores={fornecedores} total={totalGeral} />
        </DropdownSection>

        <DropdownSection
          title="Categorias de Gastos"
          subtitle="todo o período"
          icon={<Tag size={15} />}
          badge={categorias.length}
          defaultOpen={false}
          testId="categorias-geral"
        >
          <ListaCategorias categorias={categorias} total={totalGeral} />
        </DropdownSection>
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
  fornecedores: FornecedorItem[]
  categorias: CategoriaItem[]
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
    <div className="space-y-5">
      {/* Header do ano */}
      <div className="flex items-center justify-between" data-testid={`painel-ano-header-${ano}`}>
        <div>
          <p className="text-xs text-slate-400 uppercase tracking-wide mb-0.5">
            Total em {ano}
          </p>
          <p className="font-mono text-2xl font-bold text-blue-700" data-testid="painel-ano-total">{BRL(totalAno)}</p>
        </div>
        <div className="text-right">
          <p className="text-xs text-slate-400" data-testid="painel-ano-meses-count">{mesesDoAno.length} meses</p>
          <p className="text-sm text-slate-500 font-medium" data-testid="painel-ano-media-mensal">
            {BRL(totalAno / (mesesDoAno.length || 1))}/mês
          </p>
        </div>
      </div>

      {/* Gráfico mensal */}
      {mesesDoAno.length > 0 ? (
        <div data-testid="grafico-mensal">
          <div className="flex items-center justify-between mb-3">
            <p className="text-xs text-slate-500 font-semibold uppercase tracking-wider">
              Evolução mês a mês em {ano}
            </p>
            <span className="text-[11px] font-mono text-slate-500 tabular-nums">
              Média mensal: {BRL(totalAno / mesesDoAno.length)}
            </span>
          </div>
          <ResponsiveContainer width="100%" height={190}>
            <BarChart
              data={mesesDoAno}
              margin={{ top: 8, right: 8, left: 0, bottom: 0 }}
              barCategoryGap="25%"
            >
              <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" vertical={false} />
              <XAxis
                dataKey="label"
                tick={{ fontSize: 11, fill: "#64748b" }}
                axisLine={{ stroke: "#e2e8f0" }}
                tickLine={false}
              />
              <YAxis
                tickFormatter={(v) => `R$${(v / 1000).toFixed(0)}k`}
                tick={{ fontSize: 10, fill: "#94a3b8" }}
                axisLine={false}
                tickLine={false}
                width={56}
              />
              <Tooltip content={<CustomTooltip />} cursor={{ fill: "#f8fafc", radius: 4 }} />
              <ReferenceLine
                y={totalAno / mesesDoAno.length}
                stroke="#94a3b8"
                strokeDasharray="4 4"
              />
              <Bar dataKey="total_gasto" radius={[4, 4, 0, 0]}>
                {mesesDoAno.map((entry) => (
                  <Cell
                    key={entry.mes}
                    fill={entry.total_gasto === maxMes ? "#1d4ed8" : "#60a5fa"}
                  />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      ) : (
        <p className="text-sm text-slate-400 text-center py-6">
          Sem dados mensais para {ano}.
        </p>
      )}

      {/* ── Dropdowns do ano ── */}
      <div className="space-y-3">
        <DropdownSection
          title="Maiores Empresas"
          subtitle={String(ano)}
          icon={<Building2 size={15} />}
          badge={fornecedores.length}
          defaultOpen={true}
          testId={`fornecedores-${ano}`}
        >
          <ListaFornecedores fornecedores={fornecedores} total={totalAno} />
        </DropdownSection>

        <DropdownSection
          title="Categorias de Gastos"
          subtitle={String(ano)}
          icon={<Tag size={15} />}
          badge={categorias.length}
          defaultOpen={true}
          testId={`categorias-${ano}`}
        >
          <ListaCategorias categorias={categorias} total={totalAno} />
        </DropdownSection>
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

  const { data: resumoGeral, isLoading: loadingGeral } = useDespesasResumoCompleto(politicoId)
  const { data: resumoAno, isLoading: loadingAno } = useDespesasResumoCompleto(
    politicoId,
    anoSelecionado ?? undefined,
  )

  const resumo = anoSelecionado ? resumoAno : resumoGeral
  const isLoading = anoSelecionado ? loadingAno : loadingGeral

  const anosAgrupados = useMemo(
    () => (resumoGeral ? agruparPorAno(resumoGeral.historico_mensal) : []),
    [resumoGeral],
  )

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

  // Normaliza fornecedores e categorias independente da forma que o backend retorna
  const fornecedores: FornecedorItem[] = useMemo(() => {
    if (!resumo) return []
    return (resumo.top_fornecedores ?? []).map((f: any) => ({
      nome: f.nome ?? f.nome_fornecedor ?? "—",
      total: f.total ?? f.total_recebido ?? 0,
      categoria_principal: f.categoria_principal ?? null,
    }))
  }, [resumo])

  const categorias: CategoriaItem[] = useMemo(() => {
    if (!resumo) return []
    // O backend pode retornar tanto `por_categoria` quanto `top_categorias`
    const lista = resumo.por_categoria ?? resumo.top_categorias ?? []
    return lista.map((c: any) => ({
      nome: c.nome ?? c.tipo_despesa ?? "—",
      total: c.total ?? 0,
    }))
  }, [resumo])

  return (
    <div
      style={{ fontFamily: "'DM Sans', sans-serif" }}
      className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden"
      data-testid="linha-do-tempo"
      data-politico-id={politicoId}
    >
      {/* ── Header ── */}
      <div className="px-6 py-5 border-b border-slate-100 flex items-center justify-between" data-testid="linha-tempo-header">
        <div className="flex items-center gap-2">
          <CalendarDays size={18} className="text-blue-500" />
          <h3 className="text-lg font-bold tracking-tight text-slate-900">
            Histórico de Gastos
          </h3>
          {anoSelecionado && (
            <span
              className="bg-blue-50 border border-blue-100 text-blue-700 text-xs font-semibold px-2 py-0.5 rounded-full"
              data-testid="header-ano-badge"
            >
              {anoSelecionado}
            </span>
          )}
        </div>

        {anoSelecionado && (
          <button
            onClick={() => setAnoSelecionado(null)}
            className="inline-flex items-center gap-1 text-xs text-slate-400 hover:text-blue-600 transition-colors font-medium"
            data-testid="btn-voltar-todos-anos"
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
      <div className="px-6 py-6" data-testid="linha-tempo-content">
        {isLoading ? (
          <div className="flex items-center justify-center py-16 gap-3 text-slate-400" data-testid="loading-state">
            <Loader2 size={20} className="animate-spin" />
            <span className="text-sm">Carregando dados...</span>
          </div>
        ) : !resumo ? (
          <p className="text-sm text-slate-400 text-center py-10" data-testid="empty-state">
            Nenhum dado encontrado.
          </p>
        ) : anoSelecionado ? (
          <PainelAno
            ano={anoSelecionado}
            historico={resumo.historico_mensal}
            fornecedores={fornecedores}
            categorias={categorias}
          />
        ) : (
          <PainelTodos
            anosData={anosAgrupados}
            totalGeral={totalGeral}
            totalDespesas={totalDespesas}
            onSelectAno={setAnoSelecionado}
            fornecedores={fornecedores}
            categorias={categorias}
          />
        )}
      </div>
    </div>
  )
}