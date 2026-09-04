import { CalendarCheck, DollarSign, FileText, Wallet, Layers, ShieldCheck } from "lucide-react"
import InfoBotao from "./InfoDicaBotao"
import ToolDica from "./InfoDica"

// Formatação BRL
const BRL = (v) =>
  Number(v || 0).toLocaleString("pt-BR", { style: "currency", currency: "BRL" })

export default function PoliticoGraficos({ performance }) {
  if (!performance) return null

  const detalhes = performance.detalhes ?? {
    nota_assiduidade: 0,
    nota_economia: 0,
    nota_producao: 0,
  }

  const cotaUtilizada = Number(performance.info?.cota_utilizada_pct ?? 0)
  const saldoRestante = Math.max(0, 100 - cotaUtilizada)

  const totalCEAP = Number(performance.info?.total_gasto ?? 0)
  const totalGabinete = Number(performance.info?.gasto_gabinete ?? 0)
  const totalCombinado = Number(
    performance.info?.gasto_total ?? (totalCEAP + totalGabinete)
  )

  const pctCEAP = totalCombinado > 0 ? (totalCEAP / totalCombinado) * 100 : 0
  const pctGabinete = totalCombinado > 0 ? (totalGabinete / totalCombinado) * 100 : 0

  return (
    <div className="space-y-4">
      {/* ── PAINEL DE INDICADORES FACTUAIS DE MANDATO ── */}
      <div className="bg-white rounded-xl border border-slate-200/90 p-5 md:p-6 shadow-xs">
        <div className="flex items-center justify-between gap-3 mb-5 border-b border-slate-100 pb-3">
          <div>
            <h3 className="text-base font-bold text-slate-900 tracking-tight">
              Indicadores Oficiais de Mandato
            </h3>
            <p className="text-xs text-slate-500 mt-0.5">
              Métricas auditáveis consolidadas diretamente a partir dos registros oficiais da Câmara dos Deputados.
            </p>
          </div>
          <ToolDica content="O QuemVota não emite notas, índices avaliativos ou scores ponderados. As métricas exibidas representam dados objetivos registrados na Câmara dos Deputados.">
            <InfoBotao onClick={() => {}} />
          </ToolDica>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3.5">
          {/* Assiduidade */}
          <div className="p-4 rounded-lg bg-slate-50 border border-slate-200/70">
            <div className="flex items-center gap-2 text-slate-600 mb-1.5">
              <CalendarCheck size={16} className="text-blue-700" />
              <span className="text-xs font-semibold">Assiduidade Oficial</span>
            </div>
            <p className="text-2xl font-bold text-slate-900 font-mono tabular-nums">
              {detalhes.nota_assiduidade.toFixed(1)}%
            </p>
            <p className="text-[11px] text-slate-500 mt-0.5">presença em sessões deliberativas</p>
          </div>

          {/* Uso do Orçamento CEAP */}
          <div className="p-4 rounded-lg bg-slate-50 border border-slate-200/70">
            <div className="flex items-center gap-2 text-slate-600 mb-1.5">
              <Wallet size={16} className="text-indigo-700" />
              <span className="text-xs font-semibold">Uso da Cota (CEAP)</span>
            </div>
            <p className="text-2xl font-bold text-slate-900 font-mono tabular-nums">
              {cotaUtilizada.toFixed(1)}%
            </p>
            <p className="text-[11px] text-slate-500 mt-0.5">da cota de atividade consumida</p>
          </div>

          {/* Proposições */}
          <div className="p-4 rounded-lg bg-slate-50 border border-slate-200/70">
            <div className="flex items-center gap-2 text-slate-600 mb-1.5">
              <FileText size={16} className="text-emerald-700" />
              <span className="text-xs font-semibold">Proposições com Autoria</span>
            </div>
            <p className="text-2xl font-bold text-slate-900 font-mono tabular-nums">
              {detalhes.nota_producao.toFixed(0)}
            </p>
            <p className="text-[11px] text-slate-500 mt-0.5">projetos de lei e emendas</p>
          </div>
        </div>
      </div>

      {/* ── PAINEL FINANCEIRO CÍVICO COM GRÁFICOS ESPECIALIZADOS ── */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Gráfico 1: Barra Linear de Capacidade da Cota (Substitui o Donut ineficiente) */}
        <div className="bg-white rounded-xl border border-slate-200/90 p-5 md:p-6 shadow-xs flex flex-col justify-between">
          <div>
            <div className="flex items-start justify-between gap-2 mb-3">
              <div>
                <h4 className="text-sm font-bold text-slate-900 tracking-tight">
                  Execução da Cota Parlamentar (CEAP)
                </h4>
                <p className="text-xs text-slate-500 mt-0.5">
                  Capacidade orçamentária líquida consumida vs. saldo disponível
                </p>
              </div>
              <span className="font-mono text-sm font-bold text-blue-700 bg-blue-50 px-2 py-0.5 rounded border border-blue-100 tabular-nums">
                {cotaUtilizada.toFixed(1)}%
              </span>
            </div>

            {/* Medidor Linear com Escala (Bullet/Capacity Bar) */}
            <div className="mt-4 mb-2">
              <div className="h-4 bg-slate-100 rounded-full overflow-hidden p-0.5 border border-slate-200/80">
                <div
                  className="h-full rounded-full transition-all duration-500 bg-blue-700"
                  style={{ width: `${Math.min(Math.max(cotaUtilizada, 0), 100)}%` }}
                />
              </div>

              {/* Escala de Ticks */}
              <div className="flex justify-between text-[10px] font-mono text-slate-400 mt-1.5 px-0.5">
                <span>0%</span>
                <span>25%</span>
                <span>50%</span>
                <span>75%</span>
                <span>100%</span>
              </div>
            </div>
          </div>

          {/* Legenda discriminada com valores reais */}
          <div className="grid grid-cols-2 gap-3 pt-4 border-t border-slate-100 mt-4">
            <div className="p-2.5 rounded-lg bg-slate-50 border border-slate-200/60">
              <div className="flex items-center gap-1.5 mb-1">
                <span className="w-2 h-2 rounded-full bg-blue-700" />
                <span className="text-[11px] font-medium text-slate-600">Total Utilizado</span>
              </div>
              <p className="text-xs sm:text-sm font-bold text-slate-900 font-mono tabular-nums">
                {BRL(totalCEAP)}
              </p>
              <p className="text-[10px] text-slate-500 font-mono mt-0.5">
                {cotaUtilizada.toFixed(1)}% da cota
              </p>
            </div>

            <div className="p-2.5 rounded-lg bg-slate-50 border border-slate-200/60">
              <div className="flex items-center gap-1.5 mb-1">
                <span className="w-2 h-2 rounded-full bg-slate-300" />
                <span className="text-[11px] font-medium text-slate-600">Saldo Disponível</span>
              </div>
              <p className="text-xs sm:text-sm font-bold text-slate-700 font-mono tabular-nums">
                {saldoRestante.toFixed(1)}%
              </p>
              <p className="text-[10px] text-slate-500 mt-0.5">
                não gasto no período
              </p>
            </div>
          </div>
        </div>

        {/* Gráfico 2: Composição Proporcional do Orçamento (Stacked Bar) */}
        <div className="bg-white rounded-xl border border-slate-200/90 p-5 md:p-6 shadow-xs flex flex-col justify-between">
          <div>
            <div className="flex items-start justify-between gap-2 mb-3">
              <div>
                <h4 className="text-sm font-bold text-slate-900 tracking-tight">
                  Divisão de Recursos Públicos
                </h4>
                <p className="text-xs text-slate-500 mt-0.5">
                  Proporção entre despesas operacionais (CEAP) e equipe (Gabinete)
                </p>
              </div>
              <div className="text-right">
                <span className="text-[10px] text-slate-400 uppercase font-semibold block">Total</span>
                <span className="font-mono text-sm font-bold text-slate-900 tabular-nums">
                  {BRL(totalCombinado)}
                </span>
              </div>
            </div>

            {/* Barra Empilhada Proporcional */}
            {totalCombinado > 0 ? (
              <div className="mt-4 mb-2">
                <div className="h-4 bg-slate-100 rounded-full overflow-hidden flex border border-slate-200/80">
                  <div
                    className="h-full bg-blue-700 transition-all duration-500"
                    style={{ width: `${pctCEAP}%` }}
                    title={`Cota CEAP: ${pctCEAP.toFixed(1)}%`}
                  />
                  <div
                    className="h-full bg-slate-500 transition-all duration-500"
                    style={{ width: `${pctGabinete}%` }}
                    title={`Verba de Gabinete: ${pctGabinete.toFixed(1)}%`}
                  />
                </div>

                <div className="flex justify-between text-[11px] font-mono text-slate-500 mt-1.5 px-0.5">
                  <span>CEAP: {pctCEAP.toFixed(0)}%</span>
                  <span>Gabinete: {pctGabinete.toFixed(0)}%</span>
                </div>
              </div>
            ) : (
              <div className="h-4 bg-slate-100 rounded-full my-4" />
            )}
          </div>

          {/* Cards descritivos de rubricas */}
          <div className="grid grid-cols-2 gap-3 pt-4 border-t border-slate-100 mt-4">
            <div className="p-2.5 rounded-lg bg-blue-50/50 border border-blue-100">
              <div className="flex items-center gap-1.5 mb-1">
                <span className="w-2 h-2 rounded-full bg-blue-700" />
                <span className="text-[11px] font-medium text-blue-900">Cota Parlamentar (CEAP)</span>
              </div>
              <p className="text-xs sm:text-sm font-bold text-slate-900 font-mono tabular-nums">
                {BRL(totalCEAP)}
              </p>
              <p className="text-[10px] text-slate-500 mt-0.5">viagens, materiais, serviços</p>
            </div>

            <div className="p-2.5 rounded-lg bg-slate-50 border border-slate-200/60">
              <div className="flex items-center gap-1.5 mb-1">
                <span className="w-2 h-2 rounded-full bg-slate-500" />
                <span className="text-[11px] font-medium text-slate-700">Verba de Gabinete</span>
              </div>
              <p className="text-xs sm:text-sm font-bold text-slate-900 font-mono tabular-nums">
                {BRL(totalGabinete)}
              </p>
              <p className="text-[10px] text-slate-500 mt-0.5">remuneração de secretários</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}