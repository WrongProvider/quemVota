/**
 * PainelDiscursosAtuacao.tsx — Pronunciamentos × Atuação Legislativa (SPEC-007).
 *
 * Apresenta os discursos oficiais do parlamentar na Câmara dos Deputados,
 * correlacionados com proposições de sua autoria e votações nominais em que
 * participou. Cada discurso pode ser expandido para revelar as correlações.
 *
 * Princípio da Neutralidade Factual (AGENTS.md):
 *  - Linguagem 100% descritiva e factual.
 *  - Sem juízos de valor sobre coerência entre discurso e voto.
 *  - Rastreabilidade com links para o Diário da Câmara e ficha de tramitação.
 */

import { useState, useMemo, useEffect } from "react"
import {
  Mic,
  ChevronDown,
  ChevronUp,
  FileText,
  Vote,
  ExternalLink,
  Search,
  Calendar,
  Tag,
  Loader2,
  AlertCircle,
  MessageSquareText,
  X,
} from "lucide-react"
import { usePoliticoDiscursosAtuacao } from "../hooks/usePoliticos"
import { useDebounce } from "../hooks/useDebounce"
import type {
  DiscursoAtuacaoItem,
  ProposicaoCorrelataDiscurso,
  VotacaoCorrelataDiscurso,
  PoliticoDiscursosAtuacaoParams,
} from "../api/politicos.api"

interface PainelDiscursosAtuacaoProps {
  politicoId: string | number
}

// ── Formatador de data ──────────────────────────────────────────────────────
function formatarData(iso: string): string {
  try {
    const d = new Date(iso)
    return d.toLocaleDateString("pt-BR", {
      day: "2-digit",
      month: "short",
      year: "numeric",
    })
  } catch {
    return iso
  }
}

function formatarDataHora(iso: string): string {
  try {
    const d = new Date(iso)
    return d.toLocaleDateString("pt-BR", {
      day: "2-digit",
      month: "short",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    })
  } catch {
    return iso
  }
}

// ── Badge do voto ───────────────────────────────────────────────────────────
function VotoBadge({ voto }: { voto: string }) {
  const lower = voto.toLowerCase()
  let className = "inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md border text-xs font-bold tracking-wide flex-shrink-0 shadow-sm "
  if (lower === "sim") {
    className += "text-white bg-emerald-600 border-emerald-700"
  } else if (lower.includes("não") || lower === "nao") {
    className += "text-white bg-red-600 border-red-700"
  } else if (lower.includes("obstrução") || lower === "obstrucao") {
    className += "text-amber-900 bg-amber-400 border-amber-500"
  } else if (lower.includes("abstenção") || lower === "abstencao") {
    className += "text-slate-700 bg-slate-200 border-slate-300"
  } else {
    className += "text-slate-700 bg-slate-200 border-slate-300"
  }
  return <span className={className}>{voto.toUpperCase()}</span>
}

// ── Card de proposição correlata ────────────────────────────────────────────
function ProposicaoCard({ prop }: { prop: ProposicaoCorrelataDiscurso }) {
  return (
    <div className="flex items-start gap-3 p-3 bg-blue-50/60 rounded-xl border border-blue-100/80">
      <FileText size={16} className="text-blue-500 mt-0.5 shrink-0" />
      <div className="min-w-0 flex-1">
        <div className="flex items-center gap-2 flex-wrap">
          <span className="font-semibold text-sm text-slate-800">
            {prop.sigla_tipo} {prop.numero}/{prop.ano}
          </span>
          <span className="text-[10px] font-medium text-blue-600 bg-blue-100 px-1.5 py-0.5 rounded">
            {prop.tipo_participacao}
          </span>
        </div>
        {prop.ementa && (
          <p className="text-xs text-slate-600 mt-1 line-clamp-2">{prop.ementa}</p>
        )}
        {prop.url_camara && (
          <a
            href={prop.url_camara}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-1 text-[11px] text-blue-600 hover:text-blue-800 mt-1.5 font-medium"
          >
            <ExternalLink size={11} />
            Ver na Câmara
          </a>
        )}
      </div>
    </div>
  )
}

// ── Card de votação correlata ───────────────────────────────────────────────
function VotacaoCard({ vot }: { vot: VotacaoCorrelataDiscurso }) {
  return (
    <div className="flex items-start gap-3 p-3 bg-amber-50/60 rounded-xl border border-amber-100/80">
      <Vote size={16} className="text-amber-600 mt-0.5 shrink-0" />
      <div className="min-w-0 flex-1">
        <div className="flex items-center gap-2 flex-wrap">
          <span className="font-semibold text-sm text-slate-800 line-clamp-1">
            {vot.descricao}
          </span>
          <VotoBadge voto={vot.voto_registrado} />
        </div>
        {vot.data && (
          <p className="text-[11px] text-slate-500 mt-0.5">
            {formatarData(vot.data)}
            {vot.sigla_orgao && ` · ${vot.sigla_orgao}`}
          </p>
        )}
        {vot.proposicao_ementa && (
          <p className="text-xs text-slate-600 mt-1 line-clamp-2">
            {vot.proposicao_ementa}
          </p>
        )}
      </div>
    </div>
  )
}

// ── Item de discurso (colapsável) ───────────────────────────────────────────
function DiscursoItem({ item }: { item: DiscursoAtuacaoItem }) {
  const [aberto, setAberto] = useState(false)
  const temCorrelacoes =
    item.proposicoes_correlatas.length > 0 || item.votacoes_correlatas.length > 0

  return (
    <div className="bg-white rounded-2xl border border-slate-200 shadow-xs overflow-hidden">
      {/* Cabeçalho — sempre visível */}
      <button
        type="button"
        data-testid={`discurso-toggle-${item.id}`}
        onClick={() => setAberto(!aberto)}
        className="w-full text-left p-4 sm:p-5 flex items-start gap-3 hover:bg-slate-50/50 transition-colors cursor-pointer min-h-[44px]"
        aria-expanded={aberto}
      >
        <Mic size={18} className="text-indigo-500 mt-0.5 shrink-0" />
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2 flex-wrap mb-1">
            <span className="text-[11px] font-medium text-slate-500 flex items-center gap-1">
              <Calendar size={11} />
              {formatarDataHora(item.data_hora_inicio)}
            </span>
            {item.tipo_discurso && (
              <span className="text-[10px] font-semibold text-indigo-600 bg-indigo-50 px-1.5 py-0.5 rounded">
                {item.tipo_discurso}
              </span>
            )}
            {item.fase_evento_titulo && (
              <span className="text-[10px] text-slate-400">
                {item.fase_evento_titulo}
              </span>
            )}
          </div>
          {item.sumario && (
            <p className={`text-sm text-slate-700 leading-relaxed ${aberto ? "" : "line-clamp-3"}`}>
              {item.sumario}
            </p>
          )}
          {item.keywords && (
            <div className="flex items-center gap-1 mt-2 flex-wrap">
              <Tag size={10} className="text-slate-400" />
              {item.keywords
                .split(",")
                .slice(0, 5)
                .map((kw) => (
                  <span
                    key={kw.trim()}
                    className="text-[10px] text-slate-500 bg-slate-100 px-1.5 py-0.5 rounded"
                  >
                    {kw.trim()}
                  </span>
                ))}
            </div>
          )}
          {/* Indicadores de correlação */}
          {temCorrelacoes && !aberto && (
            <div className="flex items-center gap-3 mt-2 text-[11px] text-slate-400">
              {item.proposicoes_correlatas.length > 0 && (
                <span className="flex items-center gap-1">
                  <FileText size={11} />
                  {item.proposicoes_correlatas.length} proposiç{item.proposicoes_correlatas.length === 1 ? "ão" : "ões"}
                </span>
              )}
              {item.votacoes_correlatas.length > 0 && (
                <span className="flex items-center gap-1">
                  <Vote size={11} />
                  {item.votacoes_correlatas.length} votaç{item.votacoes_correlatas.length === 1 ? "ão" : "ões"}
                </span>
              )}
            </div>
          )}
        </div>
        <div className="shrink-0 mt-1">
          {aberto ? (
            <ChevronUp size={18} className="text-slate-400" />
          ) : (
            <ChevronDown size={18} className="text-slate-400" />
          )}
        </div>
      </button>

      {/* Conteúdo expandido */}
      {aberto && (
        <div
          data-testid={`discurso-expandido-${item.id}`}
          className="px-4 sm:px-5 pb-4 sm:pb-5 space-y-4 border-t border-slate-100 pt-4"
        >
          {/* Link para texto completo */}
          {item.url_texto && (
            <a
              href={item.url_texto}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1.5 text-xs text-indigo-600 hover:text-indigo-800 font-medium bg-indigo-50 px-3 py-1.5 rounded-lg"
            >
              <ExternalLink size={12} />
              Ler texto taquigráfico no Diário da Câmara
            </a>
          )}

          {/* Proposições correlatas */}
          {item.proposicoes_correlatas.length > 0 && (
            <div>
              <h4 className="text-xs font-semibold text-slate-600 uppercase tracking-wider mb-2 flex items-center gap-1.5">
                <FileText size={12} className="text-blue-500" />
                Proposições Apresentadas ({item.proposicoes_correlatas.length})
              </h4>
              <div className="space-y-2">
                {item.proposicoes_correlatas.map((prop) => (
                  <ProposicaoCard key={prop.id} prop={prop} />
                ))}
              </div>
            </div>
          )}

          {/* Votações correlatas */}
          {item.votacoes_correlatas.length > 0 && (
            <div>
              <h4 className="text-xs font-semibold text-slate-600 uppercase tracking-wider mb-2 flex items-center gap-1.5">
                <Vote size={12} className="text-amber-600" />
                Votações em Plenário ({item.votacoes_correlatas.length})
              </h4>
              <div className="space-y-2">
                {item.votacoes_correlatas.map((vot) => (
                  <VotacaoCard key={vot.id} vot={vot} />
                ))}
              </div>
            </div>
          )}

          {/* Sem correlações */}
          {!temCorrelacoes && (
            <p className="text-xs text-slate-400 italic">
              Nenhuma proposição ou votação correlata identificada para este pronunciamento.
            </p>
          )}
        </div>
      )}
    </div>
  )
}

// ── Componente principal ────────────────────────────────────────────────────
export default function PainelDiscursosAtuacao({
  politicoId,
}: PainelDiscursosAtuacaoProps) {
  const [busca, setBusca] = useState("")
  const [pagina, setPagina] = useState(0)
  const ITENS_POR_PAGINA = 5

  const buscaDebounced = useDebounce(busca, 350)

  // Reseta página quando a busca debounced mudar
  useEffect(() => {
    setPagina(0)
  }, [buscaDebounced])

  const params = useMemo<PoliticoDiscursosAtuacaoParams>(
    () => ({
      limit: ITENS_POR_PAGINA,
      offset: pagina * ITENS_POR_PAGINA,
      ...(buscaDebounced.trim() ? { q: buscaDebounced.trim() } : {}),
    }),
    [buscaDebounced, pagina],
  )

  const { data, isLoading, isFetching, isError } = usePoliticoDiscursosAtuacao(
    politicoId,
    params,
  )

  const hasActiveSearch = Boolean(busca.trim() || buscaDebounced.trim())

  // Se sem discursos no banco (e nenhuma busca em andamento), não polui a página
  if (!hasActiveSearch) {
    if (isError || (!isLoading && (!data || data.total_discursos === 0))) {
      return null
    }
  }

  // Skeleton apenas no carregamento inicial absoluto (sem dados prévios e sem busca)
  if (isLoading && !data && !hasActiveSearch) {
    return (
      <section
        data-testid="section-discursos"
        className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm animate-pulse"
      >
        <div className="flex items-center justify-between mb-4">
          <div className="h-6 w-56 bg-slate-200 rounded-md" />
          <div className="h-5 w-24 bg-slate-100 rounded-full" />
        </div>
        <div className="space-y-3 mt-6">
          <div className="h-24 bg-slate-100 rounded-xl w-full" />
          <div className="h-24 bg-slate-100 rounded-xl w-full" />
          <div className="h-24 bg-slate-100 rounded-xl w-5/6" />
        </div>
      </section>
    )
  }

  const totalDiscursos = data?.total_discursos ?? 0
  const itens = data?.itens ?? []
  const totalPaginas = Math.ceil(totalDiscursos / ITENS_POR_PAGINA)

  return (
    <section data-testid="section-discursos" className="space-y-5">
      {/* ── Cabeçalho ── */}
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div className="flex items-center gap-2">
          <MessageSquareText size={18} className="text-indigo-500" />
          <h2 className="display-font text-xl font-bold text-slate-800">
            Discursos & Atuação
          </h2>
          <span className="text-xs font-semibold text-indigo-600 bg-indigo-50 px-2 py-0.5 rounded-full">
            {totalDiscursos} pronunc.
          </span>
        </div>

        {/* Campo de busca */}
        <div className="relative w-full sm:w-64">
          {isFetching ? (
            <Loader2
              size={14}
              className="absolute left-3 top-1/2 -translate-y-1/2 text-indigo-500 animate-spin"
            />
          ) : (
            <Search
              size={14}
              className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400"
            />
          )}
          <input
            type="text"
            value={busca}
            onChange={(e) => setBusca(e.target.value)}
            placeholder="Buscar nos discursos..."
            className="w-full pl-9 pr-8 py-2 text-sm border border-slate-200 rounded-xl bg-white focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-400 outline-none transition-all"
            data-testid="discursos-search"
          />
          {busca.length > 0 && (
            <button
              type="button"
              onClick={() => setBusca("")}
              aria-label="Limpar busca"
              className="absolute right-2.5 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 p-1 rounded-md transition-colors cursor-pointer"
            >
              <X size={14} />
            </button>
          )}
        </div>
      </div>

      {/* ── Lista de discursos ── */}
      {itens.length > 0 && (
        <div className="space-y-3">
          {itens.map((item) => (
            <DiscursoItem key={item.id} item={item} />
          ))}
        </div>
      )}

      {/* ── Sem resultados na busca ── */}
      {itens.length === 0 && (
        <div className="flex flex-col items-center justify-center py-12 text-slate-400 bg-slate-50/50 rounded-2xl border border-dashed border-slate-200">
          <AlertCircle size={32} className="mb-2 text-slate-400" />
          <p className="text-sm font-medium text-slate-600">
            Nenhum pronunciamento encontrado{busca.trim() ? ` para "${busca.trim()}"` : ""}.
          </p>
          <p className="text-xs text-slate-400 mt-1">
            Tente buscar por outras palavras-chave ou termos legislativos.
          </p>
          {busca.length > 0 && (
            <button
              type="button"
              onClick={() => setBusca("")}
              data-testid="limpar-busca-discursos"
              className="mt-3 px-3 py-1.5 text-xs font-medium text-indigo-600 bg-indigo-50 hover:bg-indigo-100 rounded-lg transition-colors cursor-pointer"
            >
              Limpar busca
            </button>
          )}
        </div>
      )}

      {/* ── Paginação ── */}
      {totalPaginas > 1 && (
        <div className="flex items-center justify-center gap-2 pt-2">
          <button
            type="button"
            onClick={() => setPagina(Math.max(0, pagina - 1))}
            disabled={pagina === 0}
            className="px-3 py-1.5 text-xs font-medium rounded-lg border border-slate-200 text-slate-600 hover:bg-slate-50 disabled:opacity-40 disabled:cursor-not-allowed transition-all min-w-[44px] min-h-[44px] flex items-center justify-center cursor-pointer"
          >
            ← Anterior
          </button>
          <span className="text-xs text-slate-500 font-medium tabular-nums">
            {pagina + 1} / {totalPaginas}
          </span>
          <button
            type="button"
            onClick={() => setPagina(Math.min(totalPaginas - 1, pagina + 1))}
            disabled={pagina >= totalPaginas - 1}
            className="px-3 py-1.5 text-xs font-medium rounded-lg border border-slate-200 text-slate-600 hover:bg-slate-50 disabled:opacity-40 disabled:cursor-not-allowed transition-all min-w-[44px] min-h-[44px] flex items-center justify-center cursor-pointer"
          >
            Próximo →
          </button>
        </div>
      )}

      {/* ── Loading inline sutil ao paginar / buscar quando já há itens ── */}
      {isFetching && itens.length > 0 && (
        <div className="flex items-center justify-center py-2">
          <span className="inline-flex items-center gap-1.5 text-xs text-indigo-600 bg-indigo-50/80 px-2.5 py-1 rounded-full">
            <Loader2 size={12} className="animate-spin" />
            Atualizando resultados...
          </span>
        </div>
      )}
    </section>
  )
}
