/**
 * HistoricoProjetos.tsx — Listagem e Filtragem de Proposições Legislativas do Parlamentar.
 *
 * Apresenta todas as proposições apresentadas pelo parlamentar à Câmara dos Deputados
 * (PL, PEC, REQ, PDL, etc.), distinguindo a autoria principal (proponente) de coautorias,
 * com filtros textuais, tipológicos e temporais.
 *
 * Princípio da Neutralidade Factual Absoluta (AGENTS.md):
 *  - Apenas fatos observáveis e registros oficiais da Câmara.
 *  - Zero julgamento de valor ou adjetivos avaliativos.
 *  - Rastreabilidade com links para o inteiro teor no portal da Câmara.
 */

import { useState, useEffect } from "react"
import {
  FileText,
  Search,
  X,
  ExternalLink,
  Calendar,
  ChevronLeft,
  ChevronRight,
  Loader2,
  Tag,
  Building2,
  CheckCircle2,
  Users,
  Award,
  SlidersHorizontal,
} from "lucide-react"
import { usePoliticoAtividade } from "../hooks/usePoliticos"
import { useDebounce } from "../hooks/useDebounce"
import useIsMobile from "../hooks/useIsMobile"
import ToolDica from "./InfoDica"
import type { ProposicaoResumida } from "../api/politicos.api"

interface HistoricoProjetosProps {
  politicoId: number
  anoSelecionado: number | null
}

const TIPOS_PROPOSICAO = [
  { label: "Todos os tipos", value: "" },
  { label: "PL — Projeto de Lei", value: "PL" },
  { label: "PEC — Emenda à Constituição", value: "PEC" },
  { label: "PLP — Projeto de Lei Complementar", value: "PLP" },
  { label: "PDL — Projeto de Decreto Legislativo", value: "PDL" },
  { label: "REQ — Requerimento", value: "REQ" },
  { label: "RIC — Requerimento de Informação", value: "RIC" },
  { label: "RPD — Requerimento de CPI/Comissão", value: "RPD" },
  { label: "EMC — Emenda na Comissão", value: "EMC" },
  { label: "ESB — Emenda / Substitutivo", value: "ESB" },
]

export default function HistoricoProjetos({
  politicoId,
  anoSelecionado,
}: HistoricoProjetosProps) {
  const isMobile = useIsMobile()
  const PAGE_SIZE = isMobile ? 2 : 10

  // Estados dos filtros
  const [busca, setBusca] = useState("")
  const [tipoAutoria, setTipoAutoria] = useState<"todos" | "proponente" | "coautor">("todos")
  const [siglaTipo, setSiglaTipo] = useState("")
  const [dataInicio, setDataInicio] = useState("")
  const [dataFim, setDataFim] = useState("")
  const [offset, setOffset] = useState(0)
  const [filtrosAvancadosAbertos, setFiltrosAvancadosAbertos] = useState(false)

  const buscaDebounced = useDebounce(busca.trim(), 400)

  // Reseta offset quando qualquer filtro ou tamanho de tela mudar
  useEffect(() => {
    setOffset(0)
  }, [buscaDebounced, tipoAutoria, siglaTipo, dataInicio, dataFim, anoSelecionado, isMobile])

  const proponenteParam =
    tipoAutoria === "proponente" ? true : tipoAutoria === "coautor" ? false : undefined

  const { data: atividade, isLoading } = usePoliticoAtividade(politicoId, {
    ano: anoSelecionado ?? undefined,
    q_proposicao: buscaDebounced || undefined,
    sigla_tipo_proposicao: siglaTipo || undefined,
    proponente: proponenteParam,
    data_inicio_proposicao: dataInicio || undefined,
    data_fim_proposicao: dataFim || undefined,
    limit_proposicoes: PAGE_SIZE,
    offset_proposicoes: offset,
  })

  const proposicoes: ProposicaoResumida[] = atividade?.proposicoes ?? []
  const total = atividade?.total_proposicoes ?? 0
  const totalProponente = atividade?.total_proponente ?? 0
  const totalCoautor = atividade?.total_coautor ?? 0

  const pagina = Math.floor(offset / PAGE_SIZE) + 1
  const totalPaginas = Math.ceil(total / PAGE_SIZE)
  const temAnterior = offset > 0
  const temProxima = offset + PAGE_SIZE < total

  const temFiltroAtivo = Boolean(
    busca || tipoAutoria !== "todos" || siglaTipo || dataInicio || dataFim
  )

  const limparFiltros = () => {
    setBusca("")
    setTipoAutoria("todos")
    setSiglaTipo("")
    setDataInicio("")
    setDataFim("")
    setOffset(0)
  }

  const formatarData = (iso?: string | null) => {
    if (!iso) return "—"
    try {
      return new Date(iso).toLocaleDateString("pt-BR", {
        day: "2-digit",
        month: "short",
        year: "numeric",
      })
    } catch {
      return iso
    }
  }

  return (
    <section className="section-fade space-y-5">
      {/* ── CABEÇALHO DA SEÇÃO ── */}
      <div className="flex items-center justify-between gap-3 flex-wrap">
        <div className="flex items-center gap-2">
          <FileText size={18} className="text-blue-500" />
          <h2 className="display-font text-xl font-bold text-slate-800">
            Projetos e Proposições
          </h2>
          {total > 0 && (
            <span
              data-testid="projetos-total-badge"
              className="text-xs font-medium text-slate-400 bg-slate-100 px-2 py-0.5 rounded-full"
            >
              {total.toLocaleString("pt-BR")} registros
            </span>
          )}
        </div>

        <ToolDica
          texto="Proposições apresentadas pelo parlamentar à Câmara dos Deputados (Projetos de Lei, PECs, Requerimentos e outras matérias legislativas), na condição de autor principal (proponente) ou coautor."
          posicao="left"
        />
      </div>

      {/* ── KPIS DE AUTORIA FACTUAL ── */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
        <div className="bg-white p-4 rounded-2xl border border-slate-200/90 shadow-2xs">
          <div className="flex items-center justify-between mb-1">
            <span className="text-xs font-medium text-slate-500">Total sob Filtro</span>
            <FileText size={16} className="text-blue-500" />
          </div>
          <p
            data-testid="kpi-total-proposicoes"
            className="mono-font text-2xl font-bold text-slate-800"
          >
            {total.toLocaleString("pt-BR")}
          </p>
          <p className="text-[11px] text-slate-400 mt-0.5">
            {anoSelecionado ? `apresentadas em ${anoSelecionado}` : "matérias registradas"}
          </p>
        </div>

        <div className="bg-white p-4 rounded-2xl border border-slate-200/90 shadow-2xs">
          <div className="flex items-center justify-between mb-1">
            <span className="text-xs font-medium text-blue-700">Autor Principal</span>
            <Award size={16} className="text-blue-600" />
          </div>
          <p
            data-testid="kpi-autor-principal"
            className="mono-font text-2xl font-bold text-blue-900"
          >
            {totalProponente.toLocaleString("pt-BR")}
          </p>
          <p className="text-[11px] text-slate-400 mt-0.5">primeiro signatário (proponente)</p>
        </div>

        <div className="bg-white p-4 rounded-2xl border border-slate-200/90 shadow-2xs">
          <div className="flex items-center justify-between mb-1">
            <span className="text-xs font-medium text-slate-600">Coautor</span>
            <Users size={16} className="text-slate-500" />
          </div>
          <p
            data-testid="kpi-coautor"
            className="mono-font text-2xl font-bold text-slate-700"
          >
            {totalCoautor.toLocaleString("pt-BR")}
          </p>
          <p className="text-[11px] text-slate-400 mt-0.5">apoio / assinatura conjunta</p>
        </div>
      </div>

      {/* ── BARRA DE FILTROS CÍVICA ── */}
      <div className="bg-white p-4 rounded-2xl border border-slate-200 shadow-2xs space-y-3.5">
        {/* Linha Superior: Busca textual e Abas de Autoria */}
        <div className="flex flex-col md:flex-row gap-3 items-stretch md:items-center justify-between">
          {/* Campo de Busca */}
          <div className="relative flex-1">
            <Search
              size={15}
              className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 pointer-events-none"
            />
            <input
              data-testid="input-busca-projetos"
              type="text"
              value={busca}
              onChange={(e) => setBusca(e.target.value)}
              placeholder="Buscar por nº, sigla ou ementa (ex: PL 74, saúde, imposto)..."
              className="w-full text-sm pl-9 pr-8 py-2 rounded-xl border border-slate-200 bg-slate-50/50 hover:bg-white focus:bg-white text-slate-700 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-400 transition-all"
            />
            {busca && (
              <button
                onClick={() => setBusca("")}
                className="absolute right-2.5 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 p-1"
                aria-label="Limpar busca"
              >
                <X size={13} />
              </button>
            )}
          </div>

          {/* Seletor de Autoria (Tabs) */}
          <div className="flex items-center bg-slate-100 p-1 rounded-xl text-xs font-medium self-start md:self-auto">
            <button
              data-testid="filter-autoria-todos"
              onClick={() => setTipoAutoria("todos")}
              className={`px-3 py-1.5 rounded-lg transition-all ${
                tipoAutoria === "todos"
                  ? "bg-white text-slate-900 font-semibold shadow-2xs"
                  : "text-slate-600 hover:text-slate-900"
              }`}
            >
              Todos ({totalProponente + totalCoautor})
            </button>
            <button
              data-testid="filter-autoria-proponente"
              onClick={() => setTipoAutoria("proponente")}
              className={`px-3 py-1.5 rounded-lg transition-all flex items-center gap-1 ${
                tipoAutoria === "proponente"
                  ? "bg-blue-600 text-white font-semibold shadow-2xs"
                  : "text-slate-600 hover:text-slate-900"
              }`}
            >
              <span>⭐ Autor Principal</span>
              <span className="text-[11px] opacity-90">({totalProponente})</span>
            </button>
            <button
              data-testid="filter-autoria-coautor"
              onClick={() => setTipoAutoria("coautor")}
              className={`px-3 py-1.5 rounded-lg transition-all flex items-center gap-1 ${
                tipoAutoria === "coautor"
                  ? "bg-slate-700 text-white font-semibold shadow-2xs"
                  : "text-slate-600 hover:text-slate-900"
              }`}
            >
              <span>👥 Coautor</span>
              <span className="text-[11px] opacity-90">({totalCoautor})</span>
            </button>
          </div>
        </div>

        {/* Botão de Toggle para Filtros Avançados no Mobile */}
        <div className="md:hidden pt-2 border-t border-slate-100 flex items-center justify-between">
          <button
            type="button"
            data-testid="btn-toggle-filtros-projetos"
            onClick={() => setFiltrosAvancadosAbertos((v) => !v)}
            className="inline-flex items-center gap-1.5 text-xs font-semibold text-blue-600 hover:text-blue-800 py-1 cursor-pointer"
          >
            <SlidersHorizontal size={13} />
            <span>{filtrosAvancadosAbertos ? "Recolher filtros detalhados" : "Mais filtros (Tipo, Período)"}</span>
            {[siglaTipo, dataInicio, dataFim].filter(Boolean).length > 0 && (
              <span className="bg-blue-100 text-blue-800 text-[10px] px-1.5 py-0.2 rounded-full font-bold">
                {[siglaTipo, dataInicio, dataFim].filter(Boolean).length}
              </span>
            )}
          </button>
          {temFiltroAtivo && (
            <button
              type="button"
              onClick={limparFiltros}
              className="text-xs text-rose-600 hover:text-rose-800 font-medium cursor-pointer"
            >
              Limpar filtros
            </button>
          )}
        </div>

        {/* Linha Inferior: Tipo de proposição, Intervalo de datas e Limpar */}
        <div className={`${filtrosAvancadosAbertos ? "flex" : "hidden"} md:flex flex-wrap items-center gap-3 pt-1 border-t border-slate-100 text-xs`}>
          {/* Dropdown de Tipo */}
          <div className="flex items-center gap-1.5">
            <span className="text-slate-500 font-medium">Tipo:</span>
            <select
              data-testid="select-tipo-proposicao"
              value={siglaTipo}
              onChange={(e) => setSiglaTipo(e.target.value)}
              className="text-xs border border-slate-200 rounded-lg px-2.5 py-1.5 bg-white text-slate-700 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-400 cursor-pointer"
            >
              {TIPOS_PROPOSICAO.map((t) => (
                <option key={t.value} value={t.value}>
                  {t.label}
                </option>
              ))}
            </select>
          </div>

          {/* Intervalo de datas */}
          <div className="flex items-center gap-2 flex-wrap">
            <span className="text-slate-500 font-medium flex items-center gap-1">
              <Calendar size={13} className="text-slate-400" /> Período:
            </span>
            <input
              data-testid="input-data-inicio-proposicao"
              type="date"
              value={dataInicio}
              onChange={(e) => setDataInicio(e.target.value)}
              className="text-xs border border-slate-200 rounded-lg px-2 py-1 bg-white text-slate-700 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-400"
              aria-label="Data de início"
            />
            <span className="text-slate-400">até</span>
            <input
              data-testid="input-data-fim-proposicao"
              type="date"
              value={dataFim}
              onChange={(e) => setDataFim(e.target.value)}
              className="text-xs border border-slate-200 rounded-lg px-2 py-1 bg-white text-slate-700 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-400"
              aria-label="Data de fim"
            />
          </div>

          {/* Botão Limpar Filtros */}
          {temFiltroAtivo && (
            <button
              data-testid="btn-limpar-filtros-projetos"
              onClick={limparFiltros}
              className="ml-auto inline-flex items-center gap-1 text-xs text-blue-600 hover:text-blue-800 hover:underline font-medium py-1 px-2"
            >
              <X size={12} /> Limpar filtros
            </button>
          )}
        </div>
      </div>

      {/* ── LISTAGEM DE PROPOSIÇÕES ── */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
        {isLoading ? (
          <div className="flex items-center justify-center py-16 gap-3 text-slate-400">
            <Loader2 size={20} className="animate-spin" />
            <span className="text-sm">Carregando projetos e proposições...</span>
          </div>
        ) : proposicoes.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-16 text-slate-400 px-4 text-center">
            <FileText size={32} className="mb-3 opacity-30" />
            <p className="text-sm font-medium text-slate-600">
              Nenhuma proposição encontrada para os critérios selecionados.
            </p>
            {temFiltroAtivo && (
              <button
                onClick={limparFiltros}
                className="mt-3 text-xs text-blue-600 hover:underline font-semibold"
              >
                Limpar todos os filtros
              </button>
            )}
          </div>
        ) : (
          <>
            <div data-testid="projetos-list" className="divide-y divide-slate-100">
              {proposicoes.map((p) => {
                const anoProp = p.ano || (p.data_apresentacao ? new Date(p.data_apresentacao).getFullYear() : null)
                return (
                  <article
                    key={p.id}
                    data-testid={`proposicao-card-${p.id}`}
                    className="p-5 hover:bg-slate-50/70 transition-colors space-y-2.5"
                  >
                    {/* Linha 1: Identificação, Badges de autoria, Data e Link */}
                    <div className="flex items-start justify-between gap-3 flex-wrap">
                      <div className="flex items-center gap-2 flex-wrap">
                        {p.url_inteiro_teor ? (
                          <a
                            href={p.url_inteiro_teor}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="mono-font text-base font-bold text-blue-600 hover:text-blue-800 hover:underline inline-flex items-center gap-1"
                            title="Ver inteiro teor no portal da Câmara dos Deputados"
                          >
                            <span>
                              {p.sigla_tipo} {p.numero}/{anoProp}
                            </span>
                            <ExternalLink size={13} className="text-blue-500" />
                          </a>
                        ) : (
                          <span className="mono-font text-base font-bold text-slate-900">
                            {p.sigla_tipo} {p.numero}/{anoProp}
                          </span>
                        )}

                        {/* Badge de Autoria Principal vs Coautor */}
                        {p.proponente ? (
                          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-blue-50 text-blue-700 border border-blue-200 shadow-2xs">
                            ⭐ Autor Principal
                          </span>
                        ) : (
                          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-slate-100 text-slate-700 border border-slate-200">
                            👥 Coautor
                          </span>
                        )}

                        {p.descricao_tipo && (
                          <span className="text-[11px] text-slate-500 bg-slate-50 px-2 py-0.5 rounded border border-slate-200/60">
                            {p.descricao_tipo}
                          </span>
                        )}
                      </div>

                      <div className="flex items-center gap-2 text-xs text-slate-400">
                        <span className="flex items-center gap-1">
                          <Calendar size={12} /> {formatarData(p.data_apresentacao)}
                        </span>
                      </div>
                    </div>

                    {/* Linha 2: Ementa descritiva */}
                    <p className="text-sm text-slate-700 leading-relaxed">
                      {p.ementa || "Ementa não informada."}
                    </p>

                    {/* Linha 3: Status / Órgão de Tramitação e Temas */}
                    <div className="flex items-center justify-between gap-3 pt-1 flex-wrap text-xs">
                      <div className="flex items-center gap-2 flex-wrap">
                        {p.ultimo_status_situacao && (
                          <span className="inline-flex items-center gap-1 text-[11px] font-medium text-emerald-800 bg-emerald-50 border border-emerald-200 px-2 py-0.5 rounded-md">
                            <CheckCircle2 size={11} className="text-emerald-600" />
                            {p.ultimo_status_situacao}
                          </span>
                        )}

                        {p.ultimo_status_orgao && (
                          <span className="inline-flex items-center gap-1 text-[11px] font-medium text-slate-600 bg-slate-50 border border-slate-200 px-2 py-0.5 rounded-md">
                            <Building2 size={11} className="text-slate-400" />
                            {p.ultimo_status_orgao}
                          </span>
                        )}
                      </div>

                      {/* Badges Temáticas */}
                      {p.temas && p.temas.length > 0 && (
                        <div className="flex items-center gap-1.5 flex-wrap">
                          {p.temas.slice(0, 3).map((tema, idx) => (
                            <span
                              key={idx}
                              className="inline-flex items-center gap-1 text-[10px] font-medium text-slate-600 bg-slate-100 px-2 py-0.5 rounded-full"
                            >
                              <Tag size={9} className="text-slate-400" />
                              {tema}
                            </span>
                          ))}
                        </div>
                      )}
                    </div>
                  </article>
                )
              })}
            </div>

            {/* ── PAGINAÇÃO ── */}
            {(temAnterior || temProxima) && (
              <div className="flex items-center justify-between px-5 py-3 border-t border-slate-100 bg-slate-50/60">
                <button
                  data-testid="btn-projetos-anterior"
                  disabled={!temAnterior}
                  onClick={() => setOffset(Math.max(0, offset - PAGE_SIZE))}
                  className="text-xs text-slate-500 hover:text-slate-700 disabled:opacity-30 disabled:cursor-not-allowed font-medium flex items-center gap-1 transition-colors"
                >
                  <ChevronLeft size={14} /> Anterior
                </button>
                <span className="text-xs text-slate-500 font-medium">
                  Página {pagina} de {Math.max(1, totalPaginas)} ({total.toLocaleString("pt-BR")} proposições)
                </span>
                <button
                  data-testid="btn-projetos-proxima"
                  disabled={!temProxima}
                  onClick={() => setOffset(offset + PAGE_SIZE)}
                  className="text-xs text-slate-500 hover:text-slate-700 disabled:opacity-30 disabled:cursor-not-allowed font-medium flex items-center gap-1 transition-colors"
                >
                  Próxima <ChevronRight size={14} />
                </button>
              </div>
            )}
          </>
        )}
      </div>
    </section>
  )
}
