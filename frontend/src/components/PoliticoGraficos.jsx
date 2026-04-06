import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  ResponsiveContainer,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  Radar,
  PieChart,
  Pie,
  Cell,
} from "recharts"

import BadgePerformance from "./BadgePerformance"
import InfoBotao from "./InfoDicaBotao"
import ToolDica from "./InfoDica"

// ── Custom Tooltip ──
function CustomTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null
  return (
    <div
      className="rounded-xl border border-slate-100 shadow-xl px-4 py-3"
      style={{ background: "rgba(255,255,255,0.97)", backdropFilter: "blur(8px)" }}
    >
      {label && <p className="text-xs text-slate-400 mb-1 font-medium">{label}</p>}
      {payload.map((entry, i) => (
        <p key={i} className="text-sm font-semibold" style={{ color: entry.color ?? "#1e293b" }}>
          {typeof entry.value === "number" ? entry.value.toFixed(1) : entry.value}
        </p>
      ))}
    </div>
  )
}

// ── Score bar visual ──
function ScoreBar({ label, value, color }) {
  const pct = Math.min(Math.max(value, 0), 100)
  return (
    <div className="flex items-center gap-3">
      <span className="text-xs font-medium text-slate-500 w-20 flex-shrink-0">{label}</span>
      <div className="flex-1 h-2 rounded-full bg-slate-100 overflow-hidden">
        <div
          className="h-full rounded-full transition-all duration-700"
          style={{ width: `${pct}%`, background: color }}
        />
      </div>
      <span
        className="text-xs font-bold text-slate-700 w-8 text-right"
        style={{ fontFamily: "'DM Mono', monospace" }}
      >
        {pct.toFixed(0)}
      </span>
    </div>
  )
}

// ── Card wrapper ──
function ChartCard({ title, subtitle, children }) {
  return (
    <div className="bg-white rounded-2xl border border-slate-100 p-6 shadow-sm hover:shadow-md transition-shadow">
      <div className="mb-4">
        <h3
          className="text-base font-bold text-slate-800"
          style={{ fontFamily: "'Fraunces', serif" }}
        >
          {title}
        </h3>
        {subtitle && <p className="text-xs text-slate-400 mt-0.5">{subtitle}</p>}
      </div>
      {children}
    </div>
  )
}

export default function PoliticoGraficos({ performance }) {
  if (!performance) return null

  const detalhes = performance.detalhes ?? {
    nota_assiduidade: 0,
    nota_economia: 0,
    nota_producao: 0,
  }

  const dadosScore = [
    { name: "Este parlamentar", valor: performance.score_final },
    { name: "Média geral", valor: performance.media_global },
  ]

  const dadosRadar = [
    { subject: "Assiduidade", A: detalhes.nota_assiduidade },
    { subject: "Economia",    A: detalhes.nota_economia    },
    { subject: "Produção",    A: detalhes.nota_producao    },
  ]

  const cotaUtilizada = performance.info.cota_utilizada_pct
  const dadosCota = [
    { name: "Utilizado", value: cotaUtilizada },
    { name: "Restante",  value: Math.max(0, 100 - cotaUtilizada) },
  ]

  const COTA_COLORS = ["#2563eb", "#e2e8f0"]

  const scoreColor =
    performance.score_final >= 70 ? "#10b981"
    : performance.score_final >= 40 ? "#f59e0b"
    : "#ef4444"

  return (
    <>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,700&family=DM+Mono:wght@400;500&display=swap');
      `}</style>

      <div className="space-y-4">

        {/* ── OVERVIEW: Badge + Barras + Score ── */}
        <div className="bg-white rounded-2xl border border-slate-100 p-6 shadow-sm">
          <div className="flex items-start gap-6 flex-wrap">

            {/* Left: breakdown */}
            <div className="flex-1 min-w-[200px]">
              <div className="flex items-center gap-2 mb-3">
                <h3
                  className="text-base font-bold text-slate-800"
                  style={{ fontFamily: "'Fraunces', serif" }}
                >
                  Score de Performance
                </h3>
                <ToolDica content="O score é calculado com base em assiduidade (15%), economia (40%) e produção (45%) parlamentar.">
                  <InfoBotao onClick={() => {}} />
                </ToolDica>
              </div>

              <BadgePerformance score={performance.score_final} />

              <div className="mt-5 space-y-2.5">
                <ScoreBar label="Assiduidade" value={detalhes.nota_assiduidade} color="#2563eb" />
                <ScoreBar label="Produção"    value={detalhes.nota_producao}    color="#7c3aed" />
                <ScoreBar label="Economia"    value={detalhes.nota_economia}    color="#10b981" />
              </div>
            </div>

            {/* Right: big number */}
            <div className="flex-shrink-0 text-center bg-slate-50 rounded-xl px-8 py-5 border border-slate-100">
              <span
                className="block text-5xl font-bold leading-none"
                style={{ color: scoreColor, fontFamily: "'DM Mono', monospace" }}
              >
                {performance.score_final.toFixed(1)}
              </span>
              <span className="text-xs text-slate-400 font-medium mt-1 block">de 100 pts</span>
              <div className="mt-2 text-[11px] text-slate-400">
                Média geral:{" "}
                <span className="font-semibold text-slate-600">
                  {performance.media_global.toFixed(1)}
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* ── CHARTS GRID ── */}
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">

          {/* Score comparativo */}
          <ChartCard
            title="Score Comparativo"
            subtitle="Parlamentar vs. média nacional"
          >
            <ResponsiveContainer width="100%" height={220}>
              <BarChart data={dadosScore} barCategoryGap="35%">
                <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" vertical={false} />
                <XAxis
                  dataKey="name"
                  tick={{ fontSize: 11, fill: "#94a3b8" }}
                  axisLine={false}
                  tickLine={false}
                />
                <YAxis
                  domain={[0, 100]}
                  tick={{ fontSize: 10, fill: "#94a3b8" }}
                  axisLine={false}
                  tickLine={false}
                  width={28}
                />
                <Tooltip content={<CustomTooltip />} cursor={{ fill: "#f8fafc" }} />
                <Bar dataKey="valor" radius={[6, 6, 0, 0]}>
                  {dadosScore.map((_, index) => (
                    <Cell key={index} fill={index === 0 ? scoreColor : "#cbd5e1"} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </ChartCard>

          {/* Radar - composição */}
          <ChartCard
            title="Composição do Score"
            subtitle="Distribuição por critério avaliado"
          >
            <ResponsiveContainer width="100%" height={220}>
              <RadarChart data={dadosRadar} outerRadius={75}>
                <PolarGrid stroke="#e2e8f0" />
                <PolarAngleAxis
                  dataKey="subject"
                  tick={{ fontSize: 11, fill: "#64748b" }}
                />
                <Radar
                  name="Nota"
                  dataKey="A"
                  stroke="#2563eb"
                  fill="#2563eb"
                  fillOpacity={0.12}
                  strokeWidth={2}
                />
                <Tooltip content={<CustomTooltip />} />
              </RadarChart>
            </ResponsiveContainer>
          </ChartCard>

          {/* Cota parlamentar */}
          <ChartCard
            title="Cota Parlamentar"
            subtitle="Percentual da cota utilizado"
          >
            <div className="flex flex-col items-center">
              <div className="relative w-[200px] h-[180px]">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={dadosCota}
                      dataKey="value"
                      nameKey="name"
                      innerRadius={58}
                      outerRadius={80}
                      strokeWidth={0}
                      startAngle={90}
                      endAngle={-270}
                    >
                      {dadosCota.map((_, index) => (
                        <Cell key={index} fill={COTA_COLORS[index]} />
                      ))}
                    </Pie>
                    <Tooltip
                      formatter={(v) => `${Number(v).toFixed(1)}%`}
                      content={<CustomTooltip />}
                    />
                  </PieChart>
                </ResponsiveContainer>

                {/* Center label */}
                <div
                  className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none"
                  style={{ fontFamily: "'DM Mono', monospace" }}
                >
                  <span className="text-2xl font-bold text-slate-800">
                    {cotaUtilizada.toFixed(0)}%
                  </span>
                  <span className="text-[10px] text-slate-400">usado</span>
                </div>
              </div>

              {/* Legend */}
              <div className="flex items-center gap-5 mt-1">
                <div className="flex items-center gap-1.5">
                  <span className="w-2.5 h-2.5 rounded-sm inline-block bg-blue-600" />
                  <span className="text-xs text-slate-500">
                    Utilizado{" "}
                    <span className="font-semibold text-slate-700">
                      {cotaUtilizada.toFixed(1)}%
                    </span>
                  </span>
                </div>
                <div className="flex items-center gap-1.5">
                  <span className="w-2.5 h-2.5 rounded-sm inline-block bg-slate-200" />
                  <span className="text-xs text-slate-500">
                    Restante{" "}
                    <span className="font-semibold text-slate-700">
                      {Math.max(0, 100 - cotaUtilizada).toFixed(1)}%
                    </span>
                  </span>
                </div>
              </div>
            </div>
          </ChartCard>

        </div>
      </div>
    </>
  )
}