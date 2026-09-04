import {
  PieChart,
  Pie,
  Cell,
  Tooltip,
  ResponsiveContainer,
} from "recharts"
import { CalendarCheck, DollarSign, FileText } from "lucide-react"

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

  const cotaUtilizada = Number(performance.info?.cota_utilizada_pct ?? 0)
  const dadosCota = [
    { name: "Utilizado", value: cotaUtilizada },
    { name: "Restante", value: Math.max(0, 100 - cotaUtilizada) },
  ]

  const COTA_COLORS = ["#2563eb", "#e2e8f0"]

  return (
    <>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,700&family=DM+Mono:wght@400;500&display=swap');
      `}</style>

      <div className="space-y-4">
        {/* ── PAINEL DE INDICADORES FACTUAIS ── */}
        <div className="bg-white rounded-2xl border border-slate-100 p-6 shadow-sm">
          <div className="flex items-center justify-between gap-2 mb-4 border-b border-slate-100 pb-3">
            <div>
              <h3
                className="text-base font-bold text-slate-800"
                style={{ fontFamily: "'Fraunces', serif" }}
              >
                Indicadores de Mandato
              </h3>
              <p className="text-xs text-slate-400 mt-0.5">
                Métricas auditáveis consolidadas diretamente a partir de registros oficiais da Câmara.
              </p>
            </div>
            <ToolDica content="O QuemVota não emite notas, índices avaliativos ou scores ponderados. As métricas exibidas representam dados objetivos registrados na Câmara dos Deputados.">
              <InfoBotao onClick={() => {}} />
            </ToolDica>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div className="flex items-center gap-3.5 p-4 rounded-xl bg-slate-50 border border-slate-100">
              <div className="w-10 h-10 rounded-lg bg-blue-50 text-blue-600 flex items-center justify-center flex-shrink-0">
                <CalendarCheck size={20} />
              </div>
              <div>
                <p className="text-xs text-slate-500 font-medium">Assiduidade Oficial</p>
                <p className="text-xl font-bold text-slate-800 mt-0.5" style={{ fontFamily: "'DM Mono', monospace" }}>
                  {detalhes.nota_assiduidade.toFixed(1)}%
                </p>
                <p className="text-[11px] text-slate-400">em sessões deliberativas</p>
              </div>
            </div>

            <div className="flex items-center gap-3.5 p-4 rounded-xl bg-slate-50 border border-slate-100">
              <div className="w-10 h-10 rounded-lg bg-violet-50 text-violet-600 flex items-center justify-center flex-shrink-0">
                <DollarSign size={20} />
              </div>
              <div>
                <p className="text-xs text-slate-500 font-medium">Uso do Orçamento</p>
                <p className="text-xl font-bold text-slate-800 mt-0.5" style={{ fontFamily: "'DM Mono', monospace" }}>
                  {cotaUtilizada.toFixed(1)}%
                </p>
                <p className="text-[11px] text-slate-400">da cota disponível</p>
              </div>
            </div>

            <div className="flex items-center gap-3.5 p-4 rounded-xl bg-slate-50 border border-slate-100">
              <div className="w-10 h-10 rounded-lg bg-emerald-50 text-emerald-600 flex items-center justify-center flex-shrink-0">
                <FileText size={20} />
              </div>
              <div>
                <p className="text-xs text-slate-500 font-medium">Proposições com Autoria</p>
                <p className="text-xl font-bold text-slate-800 mt-0.5" style={{ fontFamily: "'DM Mono', monospace" }}>
                  {detalhes.nota_producao.toFixed(0)}
                </p>
                <p className="text-[11px] text-slate-400">projetos e emendas</p>
              </div>
            </div>
          </div>
        </div>

        {/* ── GRÁFICOS FACTUAIS ── */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Cota parlamentar */}
          <ChartCard
            title="Execução da Cota Parlamentar (CEAP)"
            subtitle="Percentual da cota parlamentar líquida utilizado"
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
                  <span className="text-[10px] text-slate-400">utilizado</span>
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
                    Disponível{" "}
                    <span className="font-semibold text-slate-700">
                      {Math.max(0, 100 - cotaUtilizada).toFixed(1)}%
                    </span>
                  </span>
                </div>
              </div>
            </div>
          </ChartCard>

          {/* Resumo de Recursos */}
          <ChartCard
            title="Detalhamento Financeiro"
            subtitle="Valores nominais das despesas registradas"
          >
            <div className="space-y-3 pt-2">
              <div className="flex items-center justify-between p-3 rounded-xl bg-slate-50 border border-slate-100">
                <span className="text-xs text-slate-600">Cota Parlamentar (CEAP)</span>
                <span className="text-sm font-bold text-slate-800" style={{ fontFamily: "'DM Mono', monospace" }}>
                  R$ {Number(performance.info?.total_gasto ?? 0).toLocaleString("pt-BR", { minimumFractionDigits: 2 })}
                </span>
              </div>
              <div className="flex items-center justify-between p-3 rounded-xl bg-slate-50 border border-slate-100">
                <span className="text-xs text-slate-600">Verba de Gabinete</span>
                <span className="text-sm font-bold text-slate-800" style={{ fontFamily: "'DM Mono', monospace" }}>
                  R$ {Number(performance.info?.gasto_gabinete ?? 0).toLocaleString("pt-BR", { minimumFractionDigits: 2 })}
                </span>
              </div>
              <div className="flex items-center justify-between p-3 rounded-xl bg-blue-50/60 border border-blue-100">
                <span className="text-xs font-semibold text-blue-900">Total Combinado</span>
                <span className="text-sm font-bold text-blue-700" style={{ fontFamily: "'DM Mono', monospace" }}>
                  R$ {Number(performance.info?.gasto_total ?? performance.info?.total_gasto ?? 0).toLocaleString("pt-BR", { minimumFractionDigits: 2 })}
                </span>
              </div>
            </div>
          </ChartCard>
        </div>
      </div>
    </>
  )
}