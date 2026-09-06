/**
 * PainelRedeCoautoria.tsx — Rede de Coautoria e Parcerias Legislativas.
 *
 * Apresenta o mapeamento de coautoria em proposições (PLs, PECs, Requerimentos),
 * taxa de cooperação multipartidária e temas mais frequentes em parceria.
 *
 * Princípio da Neutralidade Factual (AGENTS.md):
 *  - 100% descritivo e factual, sem conotações morais ou valorativas.
 *  - Baseado em dados abertos oficiais da Câmara dos Deputados.
 *  - Rastreabilidade de proposições com sigla, número, ano e autoria.
 */

import { useState, useMemo, useEffect } from "react"
import { Link } from "react-router-dom"
import {
  GitFork,
  Users,
  FileText,
  HelpCircle,
  ChevronDown,
  ChevronUp,
  Search,
  Layers,
  Sparkles,
} from "lucide-react"
import { usePoliticoCoautoria } from "../hooks/usePoliticos"
import { useIsMobile } from "../hooks/useIsMobile"
import type { ParceiroCoautoria, ProposicaoParceriaResumo } from "../api/politicos.api"
import InfoDica from "./InfoDica"

const PATH_FOTOS = "/fotos_politicos/"

interface FotoPoliticoProps {
  id: number
  nome: string
  urlFoto?: string | null
}

function FotoPolitico({ id, nome, urlFoto }: FotoPoliticoProps) {
  const [tentativa, setTentativa] = useState(0)

  const candidatas = [
    `${PATH_FOTOS}${id}.jpg`,
    ...(urlFoto ? [urlFoto] : []),
  ]

  if (tentativa >= candidatas.length) {
    return (
      <span className="font-bold select-none text-slate-500">
        {nome.slice(0, 2).toUpperCase()}
      </span>
    )
  }

  return (
    <img
      src={candidatas[tentativa]}
      alt={nome}
      onError={() => setTentativa((prev) => prev + 1)}
      className="w-full h-full object-cover"
      loading="lazy"
    />
  )
}

interface PainelRedeCoautoriaProps {
  politicoId: number | string
}

export default function PainelRedeCoautoria({
  politicoId,
}: PainelRedeCoautoriaProps) {
  const isMobile = useIsMobile()
  const { data, isLoading, isError } = usePoliticoCoautoria(politicoId, {
    limit: 20,
  })

  const [itensVisiveis, setItensVisiveis] = useState(isMobile ? 2 : 6)
  const [parceiroExpandido, setParceiroExpandido] = useState<number | null>(null)
  const [filtroTexto, setFiltroTexto] = useState("")

  useEffect(() => {
    setItensVisiveis(isMobile ? 2 : 6)
  }, [isMobile])

  const toggleExpandirParceiro = (id: number) => {
    setParceiroExpandido((prev) => (prev === id ? null : id))
  }

  const parceirosFiltrados = useMemo(() => {
    if (!data?.top_parceiros) return []
    if (!filtroTexto.trim()) return data.top_parceiros

    const q = filtroTexto.toLowerCase()
    return data.top_parceiros.filter(
      (p) =>
        p.politico.nome.toLowerCase().includes(q) ||
        (p.politico.sigla_partido && p.politico.sigla_partido.toLowerCase().includes(q)) ||
        p.temas_comuns.some((t) => t.toLowerCase().includes(q))
    )
  }, [data?.top_parceiros, filtroTexto])

  // Não renderiza em caso de erro ou sem dados de parceria
  if (
    isError ||
    (!isLoading &&
      (!data ||
        data.total_proposicoes_em_parceria === 0 ||
        data.top_parceiros.length === 0))
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
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-6">
          <div className="h-20 bg-slate-100 rounded-xl" />
          <div className="h-20 bg-slate-100 rounded-xl" />
          <div className="h-20 bg-slate-100 rounded-xl" />
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="h-44 bg-slate-100 rounded-xl" />
          <div className="h-44 bg-slate-100 rounded-xl" />
        </div>
      </section>
    )
  }

  if (!data) return null

  const taxaMultipart = Math.min(
    Math.max(data.taxa_coautoria_multipartidaria, 0),
    100
  )

  return (
    <section
      data-testid="section-rede-coautoria"
      className="bg-white rounded-2xl border border-slate-200/80 p-6 shadow-sm mt-8 transition-all hover:border-slate-300"
    >
      {/* ── CABEÇALHO DA SEÇÃO ── */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-6 border-b border-slate-100 pb-4">
        <div className="flex items-center gap-2.5">
          <div className="p-2 rounded-xl bg-purple-50 text-purple-600">
            <GitFork size={20} />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h2 className="display-font text-lg sm:text-xl font-bold text-slate-800">
                Rede de Coautoria e Parcerias Legislativas
              </h2>
              <InfoDica
                content="Mapeamento de projetos de lei, emendas à constituição e requerimentos apresentados conjuntamente na Câmara dos Deputados. A taxa multipartidária reflete a proporção de parcerias com parlamentares de outras legendas."
                side="top"
              >
                <button
                  type="button"
                  aria-label="Metodologia da rede de coautoria"
                  className="text-slate-400 hover:text-slate-600 transition-colors cursor-pointer"
                >
                  <HelpCircle size={15} />
                </button>
              </InfoDica>
            </div>
            <p className="text-xs text-slate-500 mt-0.5">
              Cooperação formal em projetos de lei, propostas de emenda e requerimentos
            </p>
          </div>
        </div>

        <div className="self-start sm:self-center">
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-purple-50 text-purple-700 border border-purple-200/70">
            <Sparkles size={13} />
            {data.total_parceiros_distintos} parceiros registrados
          </span>
        </div>
      </div>

      {/* ── GRID DE KPIS ── */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-6">
        {/* KPI 1: Taxa Multipartidária */}
        <div className="bg-purple-50/30 border border-purple-100/80 rounded-xl p-4 flex flex-col justify-between">
          <div className="flex items-center justify-between text-xs text-purple-900 mb-1">
            <span>Coautoria Multipartidária</span>
            <Users size={16} className="text-purple-500" />
          </div>
          <div className="my-1">
            <span className="mono-font text-2xl sm:text-3xl font-bold text-purple-950">
              {taxaMultipart.toFixed(1)}%
            </span>
            <div className="w-full bg-purple-100 h-1.5 rounded-full mt-2 overflow-hidden">
              <div
                className="bg-purple-600 h-full rounded-full transition-all duration-500"
                style={{ width: `${taxaMultipart}%` }}
              />
            </div>
          </div>
          <p className="text-[11px] text-purple-800/80 mt-1">
            Parcerias firmadas com deputados de outros partidos
          </p>
        </div>

        {/* KPI 2: Total de Parceiros */}
        <div className="bg-slate-50/70 border border-slate-200/70 rounded-xl p-4 flex flex-col justify-between">
          <div className="flex items-center justify-between text-xs text-slate-600 mb-1">
            <span>Parceiros Distintos</span>
            <GitFork size={16} className="text-indigo-500" />
          </div>
          <div className="my-1">
            <span className="mono-font text-2xl sm:text-3xl font-bold text-slate-800">
              {data.total_parceiros_distintos.toLocaleString("pt-BR")}
            </span>
          </div>
          <p className="text-[11px] text-slate-500 mt-1">
            Deputados que coassinaram proposições
          </p>
        </div>

        {/* KPI 3: Total de Proposições em Parceria */}
        <div className="bg-slate-50/70 border border-slate-200/70 rounded-xl p-4 flex flex-col justify-between">
          <div className="flex items-center justify-between text-xs text-slate-600 mb-1">
            <span>Proposições em Parceria</span>
            <FileText size={16} className="text-blue-500" />
          </div>
          <div className="my-1">
            <span className="mono-font text-2xl sm:text-3xl font-bold text-slate-800">
              {data.total_proposicoes_em_parceria.toLocaleString("pt-BR")}
            </span>
          </div>
          <p className="text-[11px] text-slate-500 mt-1">
            Total de matérias legislativas com autoria compartilhada
          </p>
        </div>
      </div>

      {/* ── BARRA DE BUSCA RÁPIDA ── */}
      {data.top_parceiros.length > 3 && (
        <div className="relative mb-5">
          <Search
            size={14}
            className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400"
          />
          <input
            type="text"
            data-testid="input-busca-parceiros"
            placeholder="Filtrar parceiros por nome, partido ou área temática..."
            value={filtroTexto}
            onChange={(e) => {
              setFiltroTexto(e.target.value)
              setItensVisiveis(isMobile ? 2 : 6)
            }}
            className="w-full pl-9 pr-4 py-2 text-xs bg-slate-50/70 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-purple-500/20 focus:border-purple-500 text-slate-800 placeholder-slate-400 transition-all"
          />
        </div>
      )}

      {/* ── GRID DE CARDS DOS PARCEIROS ── */}
      {parceirosFiltrados.length === 0 ? (
        <div className="text-center py-8 text-xs text-slate-400">
          Nenhum parceiro legislativo encontrado com o termo pesquisado.
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {parceirosFiltrados.slice(0, itensVisiveis).map((item: ParceiroCoautoria) => {
            const slugOrId = item.politico.slug || item.politico.id
            const aberto = parceiroExpandido === item.politico.id

            return (
              <div
                key={item.politico.id}
                data-testid="card-parceiro-coautoria"
                className="bg-white border border-slate-200/80 rounded-xl p-4 hover:border-slate-300 hover:shadow-xs transition-all flex flex-col justify-between"
              >
                <div>
                  {/* Topo: Avatar, Nome e Total */}
                  <div className="flex items-start justify-between gap-3 mb-3">
                    <div className="flex items-center gap-3 min-w-0">
                      <div className="w-11 h-11 rounded-full overflow-hidden flex-shrink-0 bg-slate-100 border border-slate-200 flex items-center justify-center text-xs font-bold text-slate-500">
                        <FotoPolitico
                          id={item.politico.id}
                          nome={item.politico.nome}
                          urlFoto={item.politico.url_foto}
                        />
                      </div>

                      <div className="min-w-0">
                        <Link
                          to={`/politicos/${slugOrId}`}
                          className="text-xs font-bold text-slate-900 hover:text-purple-600 transition-colors truncate block"
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

                    <div className="text-right flex-shrink-0">
                      <span className="mono-font text-base font-bold text-purple-700">
                        {item.total_proposicoes_juntos.toLocaleString("pt-BR")}
                      </span>
                      <span className="block text-[10px] text-slate-400">projetos juntos</span>
                    </div>
                  </div>

                  {/* Subdivisão Autor Principal vs Coautor */}
                  <div className="grid grid-cols-2 gap-2 bg-slate-50/80 rounded-lg p-2 text-center text-[11px] text-slate-600 mb-3 border border-slate-100">
                    <div>
                      <span className="text-slate-400 block text-[10px]">Autor Principal</span>
                      <strong className="mono-font text-slate-800">
                        {item.proposicoes_como_autor_principal}
                      </strong>
                    </div>
                    <div>
                      <span className="text-slate-400 block text-[10px]">Coautor</span>
                      <strong className="mono-font text-slate-800">
                        {item.proposicoes_como_coautor}
                      </strong>
                    </div>
                  </div>

                  {/* Temas em Comum */}
                  {item.temas_comuns && item.temas_comuns.length > 0 && (
                    <div className="mb-3">
                      <span className="text-[10px] uppercase tracking-wide text-slate-400 font-semibold block mb-1.5">
                        Temas em comum:
                      </span>
                      <div className="flex flex-wrap gap-1">
                        {item.temas_comuns.slice(0, 4).map((tema, i) => (
                          <span
                            key={i}
                            className="inline-flex items-center text-[10px] bg-slate-100 text-slate-600 px-2 py-0.5 rounded-md font-medium"
                          >
                            {tema}
                          </span>
                        ))}
                        {item.temas_comuns.length > 4 && (
                          <span className="text-[10px] text-slate-400 self-center">
                            +{item.temas_comuns.length - 4}
                          </span>
                        )}
                      </div>
                    </div>
                  )}
                </div>

                {/* Acordeão: Amostra de Proposições Conjuntas */}
                {item.amostra_proposicoes && item.amostra_proposicoes.length > 0 && (
                  <div className="mt-2 border-t border-slate-100 pt-2">
                    <button
                      type="button"
                      data-testid={`btn-toggle-proposicoes-${item.politico.id}`}
                      onClick={() => toggleExpandirParceiro(item.politico.id)}
                      className="w-full flex items-center justify-between text-[11px] font-medium text-purple-600 hover:text-purple-700 transition-colors py-1 cursor-pointer"
                    >
                      <span>
                        {aberto
                          ? "Recolher projetos"
                          : `Ver amostra de matérias (${item.amostra_proposicoes.length})`}
                      </span>
                      {aberto ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
                    </button>

                    {aberto && (
                      <div className="mt-2 space-y-2 pt-1 border-t border-slate-100">
                        {item.amostra_proposicoes.map((prop: ProposicaoParceriaResumo) => (
                          <div
                            key={prop.id}
                            data-testid="item-proposicao-parceria"
                            className="p-2 rounded-lg bg-slate-50/80 border border-slate-200/60 text-xs space-y-1"
                          >
                            <div className="flex items-center justify-between gap-1">
                              <span className="font-bold text-slate-800">
                                {prop.sigla_tipo} {prop.numero}/{prop.ano}
                              </span>
                              {prop.proponente_principal_id === data.politico_base.id && (
                                <span className="text-[9px] bg-emerald-50 text-emerald-700 border border-emerald-200/60 px-1.5 py-0.2 rounded font-medium">
                                  Iniciativa do deputado
                                </span>
                              )}
                            </div>
                            {prop.ementa && (
                              <p className="text-[11px] text-slate-600 line-clamp-2 leading-relaxed">
                                {prop.ementa}
                              </p>
                            )}
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                )}
              </div>
            )
          })}
        </div>
      )}

      {/* Botão de carregar mais parceiros */}
      {parceirosFiltrados.length > itensVisiveis && (
        <div className="text-center pt-5">
          <button
            type="button"
            onClick={() => setItensVisiveis((v) => v + (isMobile ? 2 : 6))}
            className="w-full sm:w-auto text-xs font-semibold text-slate-600 bg-slate-50 border border-slate-200 hover:bg-slate-100 px-4 py-2.5 rounded-xl transition-colors shadow-xs cursor-pointer min-h-[44px]"
          >
            Mostrar mais parceiros ({parceirosFiltrados.length - itensVisiveis} restantes)
          </button>
        </div>
      )}
    </section>
  )
}
