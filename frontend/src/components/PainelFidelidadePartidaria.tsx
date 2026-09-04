/**
 * PainelFidelidadePartidaria.tsx — Alinhamento Factual com a Bancada Partidária.
 *
 * Apresenta o percentual de coincidência entre os votos nominais registrados
 * do parlamentar e as orientações oficiais emitidas pela liderança de sua bancada.
 *
 * Princípio da Neutralidade Factual (AGENTS.md):
 *  - 100% descritivo e objetivo, sem juízos de valor ("fiel", "rebelde", "traidor").
 *  - Rastreabilidade com votações oficiais da Câmara dos Deputados.
 *  - Transparência metodológica documentada via tooltip.
 */

import { useState, useMemo } from "react"
import {
  Scale,
  CheckCircle2,
  AlertCircle,
  Vote,
  Search,
  ChevronDown,
  ChevronUp,
  FileText,
  HelpCircle,
} from "lucide-react"
import { usePoliticoFidelidade } from "../hooks/usePoliticos"
import type { VotoDivergentePartido } from "../api/politicos.api"
import InfoDica from "./InfoDica"

interface PainelFidelidadePartidariaProps {
  politicoId: string | number
}

export default function PainelFidelidadePartidaria({
  politicoId,
}: PainelFidelidadePartidariaProps) {
  const { data, isLoading, isError } = usePoliticoFidelidade(politicoId, {
    limit_divergencias: 50,
  })

  const [mostrarDivergencias, setMostrarDivergencias] = useState(false)
  const [filtroTexto, setFiltroTexto] = useState("")
  const [itensVisiveis, setItensVisiveis] = useState(6)
  const [ementasExpandidas, setEmentasExpandidas] = useState<Record<number, boolean>>({})

  const toggleEmenta = (idVotacao: number) => {
    setEmentasExpandidas((prev) => ({
      ...prev,
      [idVotacao]: !prev[idVotacao],
    }))
  }

  const divergenciasFiltradas = useMemo(() => {
    if (!data?.divergencias) return []
    if (!filtroTexto.trim()) return data.divergencias

    const q = filtroTexto.toLowerCase()
    return data.divergencias.filter(
      (d) =>
        (d.proposicao && d.proposicao.toLowerCase().includes(q)) ||
        (d.ementa && d.ementa.toLowerCase().includes(q)) ||
        (d.voto_politico && d.voto_politico.toLowerCase().includes(q)) ||
        (d.orientacao_partido && d.orientacao_partido.toLowerCase().includes(q))
    )
  }, [data?.divergencias, filtroTexto])

  // Não renderiza em erro 404/400 ou quando não houver votações com orientação registradas
  if (isError || (!isLoading && (!data || data.total_votacoes_orientadas === 0))) {
    return null
  }

  // Skeleton de carregamento sutil
  if (isLoading) {
    return (
      <section className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm animate-pulse mt-8">
        <div className="flex items-center justify-between mb-6">
          <div className="h-6 w-56 bg-slate-200 rounded-md" />
          <div className="h-5 w-28 bg-slate-100 rounded-full" />
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="h-24 bg-slate-100 rounded-xl" />
          <div className="h-24 bg-slate-100 rounded-xl" />
          <div className="h-24 bg-slate-100 rounded-xl" />
          <div className="h-24 bg-slate-100 rounded-xl" />
        </div>
      </section>
    )
  }

  if (!data) return null

  const taxaAlinhamento = Math.min(Math.max(data.taxa_fidelidade, 0), 100)

  return (
    <section
      data-testid="section-fidelidade-partidaria"
      className="bg-white rounded-2xl border border-slate-200/80 p-6 shadow-sm mt-8 transition-all hover:border-slate-300"
    >
      {/* ── CABEÇALHO DA SEÇÃO ── */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-6 border-b border-slate-100 pb-4">
        <div className="flex items-center gap-2.5">
          <div className="p-2 rounded-xl bg-blue-50 text-blue-600">
            <Scale size={20} />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h2 className="display-font text-lg sm:text-xl font-bold text-slate-800">
                Fidelidade Partidária nas Votações
              </h2>
              <InfoDica
                content="Percentual de votações nominais em que o voto individual do parlamentar coincidiu com a orientação formal emitida pela liderança de sua bancada partidária. Votações com bancada liberada ou sem orientação expressa são desconsideradas deste cômputo."
                side="top"
              >
                <button
                  type="button"
                  aria-label="Metodologia da fidelidade partidária"
                  className="text-slate-400 hover:text-slate-600 transition-colors"
                >
                  <HelpCircle size={15} />
                </button>
              </InfoDica>
            </div>
            <p className="text-xs text-slate-500 mt-0.5">
              Cruzamento entre votos nominais e as orientações da bancada do{" "}
              <strong className="text-slate-700 font-semibold">
                {data.sigla_partido || "partido"}
              </strong>
            </p>
          </div>
        </div>

        {data.sigla_partido && (
          <div className="self-start sm:self-center">
            <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-semibold bg-slate-100 text-slate-700 border border-slate-200">
              Bancada {data.sigla_partido}
            </span>
          </div>
        )}
      </div>

      {/* ── GRID DE MÉTRICAS (KPIS) ── */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        {/* KPI 1: Taxa Geral */}
        <div className="bg-slate-50/70 border border-slate-200/70 rounded-xl p-4 flex flex-col justify-between">
          <div className="flex items-center justify-between text-xs text-slate-500 mb-1">
            <span>Taxa de Alinhamento</span>
            <span className="font-medium text-slate-400">Geral</span>
          </div>
          <div className="my-1">
            <div className="flex items-baseline gap-1.5">
              <span className="mono-font text-2xl sm:text-3xl font-bold text-slate-900">
                {taxaAlinhamento.toFixed(1)}%
              </span>
            </div>
            {/* Barra proporcional de alinhamento */}
            <div className="w-full bg-slate-200 h-2 rounded-full mt-2 overflow-hidden flex">
              <div
                className="bg-emerald-500 h-full transition-all duration-500"
                style={{ width: `${taxaAlinhamento}%` }}
                title={`Alinhamento: ${taxaAlinhamento.toFixed(1)}%`}
              />
              <div
                className="bg-amber-400 h-full transition-all duration-500"
                style={{ width: `${100 - taxaAlinhamento}%` }}
                title={`Divergência: ${(100 - taxaAlinhamento).toFixed(1)}%`}
              />
            </div>
          </div>
          <p className="text-[11px] text-slate-500 mt-2">
            Proporção de votos coincidentes com a liderança
          </p>
        </div>

        {/* KPI 2: Votos Alinhados */}
        <div className="bg-emerald-50/40 border border-emerald-100 rounded-xl p-4 flex flex-col justify-between">
          <div className="flex items-center justify-between text-xs text-emerald-800 mb-1">
            <span>Votos com a Bancada</span>
            <CheckCircle2 size={16} className="text-emerald-500" />
          </div>
          <div className="my-1">
            <span className="mono-font text-2xl sm:text-3xl font-bold text-emerald-950">
              {data.votos_com_bancada.toLocaleString("pt-BR")}
            </span>
          </div>
          <p className="text-[11px] text-emerald-700/80 mt-2">
            Votos no mesmo sentido da orientação partidária
          </p>
        </div>

        {/* KPI 3: Votos Divergentes */}
        <div className="bg-amber-50/40 border border-amber-100 rounded-xl p-4 flex flex-col justify-between">
          <div className="flex items-center justify-between text-xs text-amber-800 mb-1">
            <span>Votos Divergentes</span>
            <AlertCircle size={16} className="text-amber-500" />
          </div>
          <div className="my-1">
            <span className="mono-font text-2xl sm:text-3xl font-bold text-amber-950">
              {data.votos_contra_bancada.toLocaleString("pt-BR")}
            </span>
          </div>
          <p className="text-[11px] text-amber-700/80 mt-2">
            Votos em sentido distinto da orientação do partido
          </p>
        </div>

        {/* KPI 4: Total Analisado */}
        <div className="bg-slate-50/70 border border-slate-200/70 rounded-xl p-4 flex flex-col justify-between">
          <div className="flex items-center justify-between text-xs text-slate-500 mb-1">
            <span>Votações Orientadas</span>
            <Vote size={16} className="text-blue-500" />
          </div>
          <div className="my-1">
            <span className="mono-font text-2xl sm:text-3xl font-bold text-slate-800">
              {data.total_votacoes_orientadas.toLocaleString("pt-BR")}
            </span>
          </div>
          <p className="text-[11px] text-slate-500 mt-2">
            Total de matérias com recomendação expressa
          </p>
        </div>
      </div>

      {/* ── BLOCO DE DIVERGÊNCIAS REGISTRADAS ── */}
      {data.divergencias && data.divergencias.length > 0 ? (
        <div className="border border-slate-200/80 rounded-xl overflow-hidden bg-slate-50/30">
          <div className="p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3 bg-slate-50/80 border-b border-slate-200/70">
            <div className="flex items-center gap-2">
              <span className="text-xs font-semibold text-slate-700 uppercase tracking-wide">
                Posicionamentos Divergentes
              </span>
              <span className="text-xs bg-slate-200/80 text-slate-700 px-2 py-0.5 rounded-full font-semibold mono-font">
                {data.divergencias.length}
              </span>
            </div>

            <button
              type="button"
              data-testid="btn-toggle-divergencias"
              onClick={() => setMostrarDivergencias((v) => !v)}
              className="flex items-center gap-1.5 text-xs font-medium text-blue-600 hover:text-blue-700 transition-colors self-start sm:self-center cursor-pointer"
            >
              <span>{mostrarDivergencias ? "Recolher matérias" : "Ver matérias detalhadas"}</span>
              {mostrarDivergencias ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
            </button>
          </div>

          {mostrarDivergencias && (
            <div className="p-4 space-y-4">
              {/* Barra de busca rápida */}
              {data.divergencias.length > 3 && (
                <div className="relative">
                  <Search
                    size={14}
                    className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400"
                  />
                  <input
                    type="text"
                    data-testid="input-busca-divergencias"
                    placeholder="Filtrar por sigla (ex: PEC, PL) ou termo na ementa..."
                    value={filtroTexto}
                    onChange={(e) => {
                      setFiltroTexto(e.target.value)
                      setItensVisiveis(6)
                    }}
                    className="w-full pl-9 pr-4 py-2 text-xs bg-white border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 text-slate-800 placeholder-slate-400 transition-all"
                  />
                </div>
              )}

              {/* Lista de matérias divergentes */}
              {divergenciasFiltradas.length === 0 ? (
                <div className="text-center py-6 text-xs text-slate-400">
                  Nenhuma matéria encontrada com o termo pesquisado.
                </div>
              ) : (
                <div className="space-y-2.5">
                  {divergenciasFiltradas.slice(0, itensVisiveis).map((div: VotoDivergentePartido) => {
                    const expandida = Boolean(ementasExpandidas[div.id_votacao])
                    const temEmentaLonga = (div.ementa || "").length > 180

                    return (
                      <div
                        key={div.id_votacao}
                        data-testid="card-materia-divergente"
                        className="bg-white border border-slate-200/80 rounded-xl p-3.5 hover:shadow-xs transition-shadow space-y-2.5"
                      >
                        {/* Linha superior: proposição, data e badges */}
                        <div className="flex flex-wrap items-center justify-between gap-2">
                          <div className="flex items-center gap-2">
                            <FileText size={15} className="text-slate-400" />
                            <span className="text-xs font-bold text-slate-800">
                              {div.proposicao || `Votação #${div.id_votacao}`}
                            </span>
                            {div.data && (
                              <span className="text-[11px] text-slate-400">
                                •{" "}
                                {new Date(div.data + "T00:00:00").toLocaleDateString("pt-BR", {
                                  day: "2-digit",
                                  month: "2-digit",
                                  year: "numeric",
                                })}
                              </span>
                            )}
                          </div>

                          {/* Comparação dos votos */}
                          <div className="flex items-center gap-2 text-xs">
                            <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-md bg-slate-100 text-slate-800 border border-slate-200 font-medium">
                              <span className="text-[10px] text-slate-500 font-normal">Deputado:</span>
                              <strong>{div.voto_politico || "—"}</strong>
                            </span>
                            <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-md bg-purple-50 text-purple-800 border border-purple-200/80 font-medium">
                              <span className="text-[10px] text-purple-600 font-normal">
                                {data.sigla_partido}:
                              </span>
                              <strong>{div.orientacao_partido || "—"}</strong>
                            </span>
                          </div>
                        </div>

                        {/* Ementa / Descrição */}
                        {div.ementa && (
                          <div className="text-xs text-slate-600 leading-relaxed pl-6">
                            <p className={!expandida && temEmentaLonga ? "line-clamp-2" : ""}>
                              {div.ementa}
                            </p>
                            {temEmentaLonga && (
                              <button
                                type="button"
                                onClick={() => toggleEmenta(div.id_votacao)}
                                className="text-[11px] text-blue-600 hover:text-blue-700 font-medium mt-1 cursor-pointer"
                              >
                                {expandida ? "Ver menos" : "Ler ementa completa"}
                              </button>
                            )}
                          </div>
                        )}
                      </div>
                    )
                  })}
                </div>
              )}

              {/* Botão de carregar mais */}
              {divergenciasFiltradas.length > itensVisiveis && (
                <div className="text-center pt-2">
                  <button
                    type="button"
                    onClick={() => setItensVisiveis((v) => v + 6)}
                    className="text-xs font-semibold text-slate-600 bg-white border border-slate-200 hover:bg-slate-50 px-4 py-2 rounded-lg transition-colors shadow-xs cursor-pointer"
                  >
                    Mostrar mais matérias ({divergenciasFiltradas.length - itensVisiveis} restantes)
                  </button>
                </div>
              )}
            </div>
          )}
        </div>
      ) : (
        <div className="text-center py-4 bg-slate-50/50 rounded-xl border border-slate-100 text-xs text-slate-500">
          Nenhuma divergência registrada nas votações nominais com orientação da bancada.
        </div>
      )}
    </section>
  )
}
