/**
 * PainelRadarAfinidades.tsx — Radar de Afinidades e Divergências de Voto.
 *
 * Apresenta o cruzamento estatístico entre o histórico de votos nominais do
 * parlamentar e os demais deputados federais com quem participou de votações conjuntas.
 *
 * Princípio da Neutralidade Factual (AGENTS.md):
 *  - Linguagem estritamente descritiva e quantitativa ("convergência", "divergência").
 *  - Proibido o uso de adjetivos de teor moral ou afetivo ("aliados", "inimigos", "traidores").
 *  - Rastreabilidade total: dados oficiais da Câmara dos Deputados e metodologia pública.
 */

import { useState } from "react"
import { Link } from "react-router-dom"
import {
  Users,
  TrendingUp,
  TrendingDown,
  HelpCircle,
  ArrowRight,
  Filter,
} from "lucide-react"
import { usePoliticoAfinidades } from "../hooks/usePoliticos"
import type { PoliticoAfinidadeItem } from "../api/politicos.api"
import InfoDica from "./InfoDica"

interface PainelRadarAfinidadesProps {
  politicoId: string | number
}

const OPCOES_MIN_VOTACOES = [10, 25, 50]

export default function PainelRadarAfinidades({
  politicoId,
}: PainelRadarAfinidadesProps) {
  const [minVotacoes, setMinVotacoes] = useState(10)
  const [apenasOutrosPartidos, setApenasOutrosPartidos] = useState(false)
  const [fotoErros, setFotoErros] = useState<Record<number, boolean>>({})

  const { data, isLoading, isError } = usePoliticoAfinidades(politicoId, {
    min_votacoes_comuns: minVotacoes,
    apenas_outros_partidos: apenasOutrosPartidos,
    limit: 10,
  })

  const marcarFotoErro = (id: number) => {
    setFotoErros((prev) => ({ ...prev, [id]: true }))
  }

  // Não renderiza em erro ou quando não há dados suficientes para exibir
  if (
    isError ||
    (!isLoading &&
      (!data ||
        (data.mais_alinhados.length === 0 && data.mais_divergentes.length === 0)))
  ) {
    return null
  }

  // Skeleton de carregamento
  if (isLoading) {
    return (
      <section className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm animate-pulse mt-8">
        <div className="flex items-center justify-between mb-6">
          <div className="h-6 w-64 bg-slate-200 rounded-md" />
          <div className="h-5 w-32 bg-slate-100 rounded-full" />
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="space-y-3">
            <div className="h-20 bg-slate-100 rounded-xl" />
            <div className="h-20 bg-slate-100 rounded-xl" />
            <div className="h-20 bg-slate-100 rounded-xl" />
          </div>
          <div className="space-y-3">
            <div className="h-20 bg-slate-100 rounded-xl" />
            <div className="h-20 bg-slate-100 rounded-xl" />
            <div className="h-20 bg-slate-100 rounded-xl" />
          </div>
        </div>
      </section>
    )
  }

  if (!data) return null

  const idPoliticoBase = data.politico_base.slug || data.politico_base.id

  return (
    <section
      data-testid="section-radar-afinidades"
      className="bg-white rounded-2xl border border-slate-200/80 p-6 shadow-sm mt-8 transition-all hover:border-slate-300"
    >
      {/* ── CABEÇALHO DA SEÇÃO ── */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-6 border-b border-slate-100 pb-4">
        <div className="flex items-center gap-2.5">
          <div className="p-2 rounded-xl bg-indigo-50 text-indigo-600">
            <Users size={20} />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h2 className="display-font text-lg sm:text-xl font-bold text-slate-800">
                Radar de Afinidades e Divergências de Voto
              </h2>
              <InfoDica
                content="A taxa de alinhamento é o percentual de votações nominais em que ambos os parlamentares registraram exatamente o mesmo voto (Sim, Não ou Abstenção) em relação ao total de matérias em que ambos votaram conjuntamente. Excluem-se ausências e licenças."
                side="top"
              >
                <button
                  type="button"
                  aria-label="Metodologia do radar de afinidades"
                  className="text-slate-400 hover:text-slate-600 transition-colors cursor-pointer"
                >
                  <HelpCircle size={15} />
                </button>
              </InfoDica>
            </div>
            <p className="text-xs text-slate-500 mt-0.5">
              Cruzamento factual de posicionamentos nominais com os demais deputados federais
            </p>
          </div>
        </div>

        {/* ── CONTROLES DE FILTRO ESTATÍSTICO ── */}
        <div className="flex flex-wrap items-center gap-3 self-start md:self-center">
          {/* Seletor de threshold de votações */}
          <div className="flex items-center gap-1.5 bg-slate-100/80 p-1 rounded-xl border border-slate-200/60 text-xs">
            <span className="text-[11px] font-medium text-slate-500 pl-1.5 pr-0.5 flex items-center gap-1">
              <Filter size={11} />
              Mínimo:
            </span>
            {OPCOES_MIN_VOTACOES.map((valor) => (
              <button
                key={valor}
                type="button"
                data-testid={`btn-min-votacoes-${valor}`}
                onClick={() => setMinVotacoes(valor)}
                className={`px-2 py-1 rounded-lg font-medium transition-all cursor-pointer ${
                  minVotacoes === valor
                    ? "bg-white text-slate-800 shadow-xs font-semibold"
                    : "text-slate-600 hover:text-slate-900"
                }`}
              >
                {valor}+ votos
              </button>
            ))}
          </div>

          {/* Toggle outros partidos */}
          <label className="flex items-center gap-2 text-xs text-slate-600 cursor-pointer bg-slate-50 border border-slate-200/70 px-3 py-1.5 rounded-xl hover:bg-slate-100/70 transition-colors select-none">
            <input
              type="checkbox"
              data-testid="checkbox-outros-partidos"
              checked={apenasOutrosPartidos}
              onChange={(e) => setApenasOutrosPartidos(e.target.checked)}
              className="rounded border-slate-300 text-indigo-600 focus:ring-indigo-500 h-3.5 w-3.5"
            />
            <span>Apenas outros partidos</span>
          </label>
        </div>
      </div>

      {/* ── GRID DE DUAS COLUNAS: CONVERGÊNCIA VS DIVERGÊNCIA ── */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* ════ COLUNA 1: MAIOR CONVERGÊNCIA ════ */}
        <div
          data-testid="coluna-maior-convergencia"
          className="border border-emerald-100 rounded-2xl p-4 bg-emerald-50/20"
        >
          <div className="flex items-center justify-between gap-2 mb-4 pb-3 border-b border-emerald-100/80">
            <div className="flex items-center gap-2">
              <div className="p-1.5 rounded-lg bg-emerald-100 text-emerald-700">
                <TrendingUp size={16} />
              </div>
              <div>
                <h3 className="text-sm font-bold text-emerald-950">
                  Maior Convergência de Votos
                </h3>
                <p className="text-[11px] text-emerald-700">
                  Deputados com maior taxa de votos idênticos
                </p>
              </div>
            </div>
            <span className="text-xs font-semibold mono-font px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-800">
              {data.mais_alinhados.length}
            </span>
          </div>

          {data.mais_alinhados.length === 0 ? (
            <div className="text-center py-8 text-xs text-slate-400">
              Nenhum parlamentar atende aos critérios com este filtro.
            </div>
          ) : (
            <div className="space-y-3">
              {data.mais_alinhados.map((item: PoliticoAfinidadeItem) => {
                const taxa = Math.min(Math.max(item.taxa_alinhamento, 0), 100)
                const slugOrId = item.politico.slug || item.politico.id
                const semFoto = Boolean(fotoErros[item.politico.id]) || !item.politico.url_foto

                return (
                  <div
                    key={item.politico.id}
                    data-testid="card-afinidade-item"
                    className="bg-white border border-slate-200/80 rounded-xl p-3.5 hover:shadow-xs transition-all space-y-2.5"
                  >
                    <div className="flex items-center justify-between gap-3">
                      {/* Avatar e Nome */}
                      <div className="flex items-center gap-3 min-w-0">
                        <div className="w-10 h-10 rounded-full overflow-hidden flex-shrink-0 bg-slate-100 border border-slate-200 flex items-center justify-center text-xs font-bold text-slate-500">
                          {!semFoto ? (
                            <img
                              src={item.politico.url_foto!}
                              alt={item.politico.nome}
                              onError={() => marcarFotoErro(item.politico.id)}
                              className="w-full h-full object-cover"
                              loading="lazy"
                            />
                          ) : (
                            item.politico.nome.slice(0, 2).toUpperCase()
                          )}
                        </div>

                        <div className="min-w-0">
                          <Link
                            to={`/politicos/${slugOrId}`}
                            className="text-xs font-bold text-slate-900 hover:text-blue-600 transition-colors truncate block"
                          >
                            {item.politico.nome}
                          </Link>
                          <div className="flex items-center gap-1.5 text-[11px] text-slate-500 mt-0.5">
                            {item.politico.sigla_partido && (
                              <span className="font-semibold text-slate-700">
                                {item.politico.sigla_partido}
                              </span>
                            )}
                            {item.politico.sigla_uf && (
                              <span>• {item.politico.sigla_uf}</span>
                            )}
                            {item.mesmo_partido && (
                              <span className="bg-slate-100 text-slate-600 text-[10px] px-1.5 py-0.2 rounded font-medium">
                                Mesmo partido
                              </span>
                            )}
                          </div>
                        </div>
                      </div>

                      {/* Taxa percentual em destaque */}
                      <div className="text-right flex-shrink-0">
                        <span className="mono-font text-base sm:text-lg font-bold text-emerald-600">
                          {taxa.toFixed(1)}%
                        </span>
                        <span className="block text-[10px] text-slate-400">alinhamento</span>
                      </div>
                    </div>

                    {/* Barra de progresso visual */}
                    <div>
                      <div className="w-full bg-slate-100 h-1.5 rounded-full overflow-hidden">
                        <div
                          className="bg-emerald-500 h-full rounded-full transition-all duration-300"
                          style={{ width: `${taxa}%` }}
                        />
                      </div>
                      <div className="flex items-center justify-between text-[11px] text-slate-500 mt-1">
                        <span>
                          <strong className="text-slate-700 font-semibold">
                            {item.votos_alinhados}
                          </strong>{" "}
                          votos em comum ({item.total_votacoes_comuns} total)
                        </span>
                        <Link
                          to={`/comparar/${politicoId}/${slugOrId}`}
                          className="text-emerald-700 hover:text-emerald-900 font-semibold inline-flex items-center gap-1 hover:underline"
                        >
                          Comparar <ArrowRight size={11} />
                        </Link>
                      </div>
                    </div>
                  </div>
                )
              })}
            </div>
          )}
        </div>

        {/* ════ COLUNA 2: MAIOR DIVERGÊNCIA ════ */}
        <div
          data-testid="coluna-maior-divergencia"
          className="border border-amber-100 rounded-2xl p-4 bg-amber-50/20"
        >
          <div className="flex items-center justify-between gap-2 mb-4 pb-3 border-b border-amber-100/80">
            <div className="flex items-center gap-2">
              <div className="p-1.5 rounded-lg bg-amber-100 text-amber-700">
                <TrendingDown size={16} />
              </div>
              <div>
                <h3 className="text-sm font-bold text-amber-950">
                  Maior Divergência de Votos
                </h3>
                <p className="text-[11px] text-amber-700">
                  Deputados com maior taxa de votos em sentido oposto
                </p>
              </div>
            </div>
            <span className="text-xs font-semibold mono-font px-2 py-0.5 rounded-full bg-amber-100 text-amber-800">
              {data.mais_divergentes.length}
            </span>
          </div>

          {data.mais_divergentes.length === 0 ? (
            <div className="text-center py-8 text-xs text-slate-400">
              Nenhum parlamentar atende aos critérios com este filtro.
            </div>
          ) : (
            <div className="space-y-3">
              {data.mais_divergentes.map((item: PoliticoAfinidadeItem) => {
                const taxa = Math.min(Math.max(item.taxa_alinhamento, 0), 100)
                const slugOrId = item.politico.slug || item.politico.id
                const semFoto = Boolean(fotoErros[item.politico.id]) || !item.politico.url_foto

                return (
                  <div
                    key={item.politico.id}
                    data-testid="card-divergencia-item"
                    className="bg-white border border-slate-200/80 rounded-xl p-3.5 hover:shadow-xs transition-all space-y-2.5"
                  >
                    <div className="flex items-center justify-between gap-3">
                      {/* Avatar e Nome */}
                      <div className="flex items-center gap-3 min-w-0">
                        <div className="w-10 h-10 rounded-full overflow-hidden flex-shrink-0 bg-slate-100 border border-slate-200 flex items-center justify-center text-xs font-bold text-slate-500">
                          {!semFoto ? (
                            <img
                              src={item.politico.url_foto!}
                              alt={item.politico.nome}
                              onError={() => marcarFotoErro(item.politico.id)}
                              className="w-full h-full object-cover"
                              loading="lazy"
                            />
                          ) : (
                            item.politico.nome.slice(0, 2).toUpperCase()
                          )}
                        </div>

                        <div className="min-w-0">
                          <Link
                            to={`/politicos/${slugOrId}`}
                            className="text-xs font-bold text-slate-900 hover:text-blue-600 transition-colors truncate block"
                          >
                            {item.politico.nome}
                          </Link>
                          <div className="flex items-center gap-1.5 text-[11px] text-slate-500 mt-0.5">
                            {item.politico.sigla_partido && (
                              <span className="font-semibold text-slate-700">
                                {item.politico.sigla_partido}
                              </span>
                            )}
                            {item.politico.sigla_uf && (
                              <span>• {item.politico.sigla_uf}</span>
                            )}
                          </div>
                        </div>
                      </div>

                      {/* Taxa percentual em destaque */}
                      <div className="text-right flex-shrink-0">
                        <span className="mono-font text-base sm:text-lg font-bold text-amber-600">
                          {taxa.toFixed(1)}%
                        </span>
                        <span className="block text-[10px] text-slate-400">alinhamento</span>
                      </div>
                    </div>

                    {/* Barra de progresso visual */}
                    <div>
                      <div className="w-full bg-slate-100 h-1.5 rounded-full overflow-hidden">
                        <div
                          className="bg-amber-500 h-full rounded-full transition-all duration-300"
                          style={{ width: `${taxa}%` }}
                        />
                      </div>
                      <div className="flex items-center justify-between text-[11px] text-slate-500 mt-1">
                        <span>
                          <strong className="text-slate-700 font-semibold">
                            {item.votos_divergentes}
                          </strong>{" "}
                          votos divergentes ({item.total_votacoes_comuns} total)
                        </span>
                        <Link
                          to={`/comparar/${politicoId}/${slugOrId}`}
                          className="text-amber-700 hover:text-amber-900 font-semibold inline-flex items-center gap-1 hover:underline"
                        >
                          Comparar <ArrowRight size={11} />
                        </Link>
                      </div>
                    </div>
                  </div>
                )
              })}
            </div>
          )}
        </div>
      </div>
    </section>
  )
}
